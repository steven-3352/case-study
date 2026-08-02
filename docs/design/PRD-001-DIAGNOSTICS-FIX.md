# PRD-001：诊断能力提升与图片生成修复

> **状态**：待实施  
> **优先级**：P1（阻塞后续所有图片/视频生成）  
> **负责模型**：便宜模型实现，Opus 验收  
> **前置条件**：无  
> **解锁**：PRD-002（场景组+背景母版）

---

## 1. 背景与问题陈述

### 1.1 当前故障

`POST /api/v1/projects/{project_id}/shots/{shot_id}/background/generate` 返回 HTTP 423，
前端提示"生图提示词翻译失败，请查看错误日志后重试"。

后端日志只记录：
```
message: image prompt translation failed
```

无法判断是超时、HTTP 4xx/5xx、SSE 格式错误、模型内容过滤，还是其他原因。

### 1.2 根因分析（基于代码审查）

调用链：`_generate_shot_image` → `_translate_image_prompt` → `provider.run(task)`

`provider.run()` 可抛出：
- `SemanticProviderError`：网络超时、HTTP 错误、SSE 格式错误、无效 JSON
- `SemanticResponseError`：有 `input_tokens/cache_read_tokens/output_tokens/finish_reason` 属性，
  finish_reason 为 `length`（截断）、`content_filter`（过滤）或无内容时抛出

当前 `_translate_image_prompt`（service.py:1350-1362）：
```python
except Exception as exc:
    # 只记录 usage（如果有），然后抛 ApplicationBlocked("image prompt translation failed")
    # 没有记录 error_category / http_status / finish_reason / provider / request_id
    raise ApplicationBlocked("image prompt translation failed") from exc
```

`ErrorLogStore.append()` 未被调用，所以日志文件里看不到任何底层错误信息。

### 1.3 附加问题

- 前端只显示最终错误文案，不显示"当前正在执行哪一步"（翻译中 / 调用图片模型中 / 保存中）
- 翻译失败后必须重新点击"生成背景"，没有"只重试翻译"的入口
- 服务 8792 曾瞬时断开，原因未诊断，重启可靠性未验证

---

## 2. 目标与非目标

### 目标

1. 翻译失败时，后端 JSONL 日志包含可诊断字段（error_category / finish_reason / model / request_id）
2. API 错误响应包含 `error_stage` 字段，前端可据此显示"哪一步失败了"
3. 翻译支持一次自动重试（仅网络类错误）
4. 前端在生成过程中显示四阶段进度，失败时显示具体阶段和重试按钮
5. 明确诊断 8792 瞬时断开的原因，记录在本文附录

### 非目标

- 不改变数据库表结构
- 不改变 `ErrorLogStore` 的存储格式（只新增字段）
- 不实现背景生成的业务模型重构（留给 PRD-002）
- 不实现 SSE 流式推送（留给 PRD-005）
- 不改变日志文件的命名规则或目录结构

---

## 3. 需求规格

### 3.1 错误日志增强（service.py `_translate_image_prompt`）

**R-001**：翻译失败时，必须调用 `self.error_logs.append("backend", {...})` 记录一条结构化日志，包含以下字段：

| 字段 | 类型 | 取值规则 |
|---|---|---|
| `event` | str | `"image_prompt_translation_failed"` |
| `error_category` | str | 见下表 |
| `error_message` | str | `str(exc)[:500]`，脱敏处理（ErrorLogStore._clean 已有） |
| `finish_reason` | str | `SemanticResponseError.finish_reason` 或 `""` |
| `model` | str | 实际使用的模型名 |
| `provider_base_url` | str | 脱敏（只保留 host，去掉 scheme 和 path） |
| `request_id` | str | 传入的 request_id |
| `shot_id` | str | context["shot"]["id"] |
| `available_input_tokens` | int | `getattr(exc, "input_tokens", 0)` |
| `available_output_tokens` | int | `getattr(exc, "output_tokens", 0)` |

**error_category 映射表**（按此优先级顺序判断，`isinstance` 检查优先于字符串包含检查）：

| 优先级 | 条件 | error_category |
|---|---|---|
| 1 | `isinstance(exc, SemanticResponseError)` 且 finish_reason == `"length"` | `"truncated"` |
| 2 | `isinstance(exc, SemanticResponseError)` 且 finish_reason == `"content_filter"` | `"content_filtered"` |
| 3 | `isinstance(exc, SemanticResponseError)` 且其他 finish_reason | `"invalid_response"` |
| 4 | `isinstance(exc, SemanticProviderError)` 且 `"timed out"` in str(exc).lower() | `"timeout"` |
| 5 | `isinstance(exc, SemanticProviderError)` 且其他情况 | `"http_error"` |
| 6 | 其他所有情况 | `"unknown"` |

注意：`SemanticResponseError` 继承自 `SemanticProviderError`，若先判断 `SemanticProviderError` 会错误吞掉 truncated/content_filtered，因此 `SemanticResponseError` 必须排在前面。

**R-002**：`ApplicationBlocked` 的 `error_category` 通过属性传递，**不拼入消息体**：
```python
raise ApplicationBlocked(
    "image prompt translation failed",
    error_stage="translate_prompt",
    error_category=error_category,
) from exc
```
消息体保持固定字符串，以保证 `__init__.py` 中 `public_details` 字典的现有中文映射（按 `str(exc)` 精确匹配）仍能命中。`error_category` 由 R-004 的 API 响应构造逻辑从 `exc.error_category` 属性读取，不从消息字符串解析。

**R-003**：`ApplicationService` 需要持有 `error_logs: ErrorLogStore` 实例引用。实施前先检查 service.py 中是否已有 `self.error_logs`：

- **若已有**：直接使用，不做任何改动。
- **若无**：**禁止**在 service `__init__` 中直接执行 `ErrorLogStore(workspace_root)`。原因：`app.state.error_logs` 使用 `settings.data_root` 初始化，若两处 `data_root` 不同，日志会写到不同目录，`GET /api/v1/projects/.../logs` 端点将读不到 service 写入的条目。

  正确做法：在 `ApplicationService.__init__` 中加可选参数：
  ```python
  def __init__(self, ..., error_logs: ErrorLogStore | None = None):
      self.error_logs = error_logs or _NoopErrorLogs()
  ```
  由 `create_app` 的 startup 事件将 `app.state.error_logs` 注入。`_NoopErrorLogs` 是一个仅实现 `append()` 方法的 no-op 对象，供测试和 CLI 场景使用，避免强依赖文件系统。

### 3.2 API 错误响应增强（apps/mv_api/__init__.py）

**R-004**：`ApplicationBlocked` 的 HTTP 响应体从 `{"detail": "..."}` 改为：
```json
{
  "detail": "image prompt translation failed: timeout",
  "error_stage": "translate_prompt",
  "error_category": "timeout"
}
```

`error_stage` 的枚举值：
- `"translate_prompt"` — 翻译步骤失败
- `"generate_image"` — 图片 Provider 调用失败
- `"save_result"` — 写文件失败
- `"precondition"` — 前置条件检查失败（如 story 未审批）
- `"configuration"` — Provider 未配置

**实施方式**：在 `ApplicationBlocked` 的消息中约定前缀格式
`"{error_stage}:{error_category}:{human_message}"`，API 层解析后分别填充响应字段。
**或**：给 `ApplicationBlocked` 加可选属性 `error_stage` 和 `error_category`。
推荐后者（更清晰，不用解析字符串）。

**R-005**：现有 `application_error` handler（`__init__.py:257`）保持不变，
只修改从 `ApplicationBlocked` 构造响应的那一分支（`__init__.py:202-203`）。

### 3.3 翻译自动重试（service.py `_translate_image_prompt`）

**R-006**：对 `error_category == "timeout"` 或 `error_category == "http_error"` 的情况，
自动重试一次（最多 1 次，不递归）。重试前记录一条 `event: "image_prompt_translation_retrying"` 日志。

**R-007**：重试失败时，最终抛出的 `ApplicationBlocked` 反映最后一次错误的 category。
不因重试而隐藏原始错误链。

**R-008**：非网络类错误（content_filtered / truncated / invalid_response）**不重试**，直接失败并记录日志。

### 3.4 前端阶段进度（app.js）

**R-009**：点击"用 GPT-image-2 生成背景图片"按钮后，按钮区域替换为四阶段进度展示：

```
● 整理中文指令  →  ● 翻译执行稿  →  ● 调用图片模型  →  ● 保存结果
```

阶段以 loading spinner + 文字表示当前步骤，已完成步骤显示 ✓，失败步骤显示 ✗。

**R-010**：当前后端是同步 HTTP（不是 SSE），前端无法知道"现在在哪一步"。
**过渡方案（不做 SSE）**：
- 请求发出后，按固定时序推进前三个阶段的 UI 状态（纯视觉，不代表真实进度）
- 请求完成（成功/失败）后，根据响应的 `error_stage` 字段定位到具体失败阶段并显示错误信息

这是临时 UX 改善，不是真实流式。真实流式在 PRD-005 实现。

**R-011**：失败时，在失败阶段旁边显示一个"重试"按钮，点击重新发起同一 POST 请求。
不需要重载页面，不需要重新填写任何内容。

**R-012**：成功时，进度区域消失，显示生成的背景图片缩略图（现有逻辑保留）。

### 3.5 服务稳定性诊断（诊断任务，非代码改动）

**R-013**：实施模型在开始改代码前，必须完成以下诊断并将结果写入本 PRD 的"附录 A"：

1. 查看 `apps/runtime.py` 的启动方式，确认 `os.execv` 重启逻辑
2. 检查日志中是否有 8792 断开的记录
3. 手动执行重启接口（`POST /api/v1/system/restart`），验证服务是否能在 10 秒内重新 ready
4. 重复步骤 3 三次，记录每次结果

若三次重启均成功，视为"稳定性可接受，继续观察"。
若有失败，记录失败原因并报告给 Opus 决定是否扩大修复范围。

---

## 4. API 变更规格

### 4.1 `ApplicationBlocked` 类扩展（service.py）

```python
class ApplicationBlocked(ApplicationError):
    def __init__(self, message: str, *, error_stage: str = "", error_category: str = ""):
        super().__init__(message)
        self.error_stage = error_stage
        self.error_category = error_category
```

**兼容性**：现有所有 `raise ApplicationBlocked("...")` 调用无需修改，
`error_stage` 和 `error_category` 默认为空字符串，API 响应中只在非空时输出。

### 4.2 API 错误响应格式（__init__.py 的 ApplicationBlocked 分支）

```python
elif isinstance(exc, ApplicationBlocked):
    status = 423
    detail = str(exc)
    payload = {"detail": detail}
    if getattr(exc, "error_stage", ""):
        payload["error_stage"] = exc.error_stage
    if getattr(exc, "error_category", ""):
        payload["error_category"] = exc.error_category
    return JSONResponse(payload, status_code=status)
```

### 4.3 不新增路由

不新增"单独重试翻译"的路由，重试逻辑在 service 内部（R-006）。
前端的"重试"按钮复用现有 `POST .../background/generate` 路由。

---

## 5. 测试用例规格

> 实施模型按此规格编写测试脚本。
> 执行命令：`pytest tests/ -v --tb=short -k "prd001"` 或按层执行。
> 完成后输出 `TEST_REPORT_PRD001.md`，Opus 基于此文件验收。

### 5.1 单元测试（`tests/mv_platform/unit/test_prd001_diagnostics.py`）

**UT-001**：翻译超时时记录 error_category=timeout

```python
@pytest.mark.unit
def test_translate_logs_timeout_category(service_with_mock_logs, mock_provider_timeout):
    # Arrange: provider.run() 抛出 SemanticProviderError("semantic provider request timed out")
    # Act: _translate_image_prompt(project_id, event_type, context, request_id)
    # Assert:
    #   - 抛出 ApplicationBlocked，消息包含 "timeout"
    #   - error_logs.append 被调用一次，event=="image_prompt_translation_failed"
    #   - 记录的 error_category == "timeout"
    #   - 记录的 request_id 与传入值相同
    #   - 记录的 model 非空
```

**UT-002**：翻译被内容过滤时记录 error_category=content_filtered

```python
@pytest.mark.unit
def test_translate_logs_content_filtered(service_with_mock_logs, mock_provider_content_filter):
    # SemanticResponseError(finish_reason="content_filter")
    # error_category == "content_filtered"
    # 不发生重试
```

**UT-003**：翻译截断时记录 error_category=truncated，不重试

```python
@pytest.mark.unit
def test_translate_logs_truncated_no_retry(service_with_mock_logs, mock_provider_truncated):
    # SemanticResponseError(finish_reason="length")
    # error_category == "truncated"
    # provider.run 只被调用一次（无重试）
```

**UT-004**：网络错误时自动重试一次

```python
@pytest.mark.unit
def test_translate_retries_once_on_http_error(service_with_mock_logs, mock_provider_http_error):
    # 第一次抛 SemanticProviderError("request failed"), 第二次成功返回
    # provider.run 被调用两次
    # error_logs.append 被调用一次（带 event="image_prompt_translation_retrying"）
    # 最终不抛异常，返回英文 prompt
```

**UT-005**：连续两次网络错误最终失败

```python
@pytest.mark.unit
def test_translate_fails_after_one_retry(service_with_mock_logs, mock_provider_always_fail):
    # 两次都失败，最终 ApplicationBlocked，error_category=="http_error"
    # provider.run 被调用两次
```

**UT-006**：ApplicationBlocked 携带 error_stage 和 error_category

```python
@pytest.mark.unit
def test_application_blocked_carries_stage_and_category():
    exc = ApplicationBlocked("test", error_stage="translate_prompt", error_category="timeout")
    assert exc.error_stage == "translate_prompt"
    assert exc.error_category == "timeout"
```

**UT-007**：现有 ApplicationBlocked 调用（无 stage/category）仍正常工作

```python
@pytest.mark.unit
def test_application_blocked_backward_compatible():
    exc = ApplicationBlocked("workspace_root is required")
    assert exc.error_stage == ""
    assert exc.error_category == ""
    assert str(exc) == "workspace_root is required"
```

### 5.2 API 契约测试（`tests/mv_platform/contract/test_prd001_api.py`）

**CT-001**：翻译失败时响应包含 error_stage

```python
@pytest.mark.contract
def test_background_generate_translate_fail_includes_error_stage(test_client, project_with_approved_story):
    # Arrange: mock service.generate_shot_background 抛
    #   ApplicationBlocked("...", error_stage="translate_prompt", error_category="timeout")
    # Act: POST /api/v1/projects/{id}/shots/S001/background/generate
    # Assert:
    #   - status_code == 423
    #   - body["error_stage"] == "translate_prompt"
    #   - body["error_category"] == "timeout"
    #   - body["detail"] 是人类可读的中文或英文说明
```

**CT-002**：无 stage/category 的 ApplicationBlocked 仍返回 423

```python
@pytest.mark.contract
def test_application_blocked_without_stage_still_423(test_client):
    # 保持向后兼容
    # body 不含 error_stage 字段（或为空字符串）
```

**CT-003**：precondition 失败（story 未审批）的错误包含正确 stage

```python
@pytest.mark.contract
def test_background_generate_precondition_fail(test_client, project_without_story_approval):
    # error_stage == "precondition"
    # status_code == 423
```

### 5.3 浏览器 E2E 测试（`tests/e2e/test_prd001_browser.py`）

使用 Playwright，测试对象为运行中的 `http://127.0.0.1:8792`。

**ET-001**：点击生成背景后出现进度状态

```python
@pytest.mark.e2e
def test_background_generate_shows_progress(page, project_at_storyboard):
    # 1. 导航到分镜工作台
    # 2. 点击某 shot 的"用 GPT-image-2 生成背景图片"按钮
    # 3. Assert: 按钮区域变为包含"翻译执行稿"或"调用图片模型"字样的进度展示
    #    （文字出现即可，不要求精确阶段顺序）
    # 4. 等待请求完成（超时 60s）
```

**ET-002**：翻译失败时显示失败阶段和重试按钮（需 mock 后端失败）

```python
@pytest.mark.e2e
def test_background_generate_shows_retry_on_fail(page, project_at_storyboard, mock_translate_fail):
    # 1. mock：注入后端使翻译返回 423 + error_stage=translate_prompt
    # 2. 点击生成按钮
    # 3. Assert: 页面显示含"翻译"字样的失败提示
    # 4. Assert: 页面有"重试"按钮
    # 5. 取消 mock，点击重试
    # 6. Assert: 进度继续，不刷新整页
```

**ET-003**：服务重启后 /readyz 在 15 秒内恢复

```python
@pytest.mark.e2e
def test_service_restart_recovers(page):
    # 1. POST /api/v1/system/restart（需无运行中任务）
    # 2. 轮询 GET /readyz，最多 15 秒
    # 3. Assert: status == "ready"
    # 4. Assert: GET /api/v1/projects 正常返回（服务状态完整）
    # 重复三次（参数化）
```

---

## 6. 验收标准

Opus 基于 `TEST_REPORT_PRD001.md` 验收，通过条件：

- [ ] UT-001 ～ UT-007 全部通过
- [ ] CT-001 ～ CT-003 全部通过
- [ ] ET-001 通过（进度状态可见）
- [ ] ET-002 通过（失败阶段 + 重试按钮）
- [ ] ET-003 三次重启均成功（通过）
- [ ] 手动检查：触发一次真实背景生成（或模拟失败），后端 JSONL 日志包含 `error_category` 字段
- [ ] 手动检查：所有页面可见文字仍为中文，无新增英文状态码暴露给用户

---

## 7. 废弃与归档说明

**不废弃任何现有代码**。本 PRD 全部是在现有代码上追加字段和分支，不删除任何方法。

已有的 `tests/manual/e2e_mvp_browser.py` 和 `tests/manual/verify_qingyi2_workflow.py` 保持不动，
不因本 PRD 的自动化测试而删除（它们用于手动专项验证）。

---

## 8. 实施顺序建议（给便宜模型）

```
Step 1  诊断稳定性（R-013），写入附录 A，不动代码
Step 2  扩展 ApplicationBlocked（R-004 数据结构部分），跑 UT-006/007
Step 3  增强 _translate_image_prompt 错误日志（R-001/002/003），跑 UT-001/002/003
Step 4  加翻译重试逻辑（R-006/007/008），跑 UT-004/005
Step 5  修改 API 错误响应格式（R-005），跑 CT-001/002/003
Step 6  前端阶段进度 + 重试按钮（R-009/010/011/012），启动服务，跑 ET-001/002/003
Step 7  全量执行：pytest tests/ -v -k "prd001"，输出 TEST_REPORT_PRD001.md
```

---

## 附录 A：服务稳定性诊断结果

> 由实施模型填写，实施 Step 1 完成后更新此节。

- 诊断时间：[待填]
- runtime.py 重启方式：[待填]
- 三次重启结果：[待填]
- 已知断开原因：[待填]
