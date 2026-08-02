# PRD-005：真实 SSE 浏览器流式推送

> **状态**：待实施  
> **优先级**：P4  
> **前置条件**：PRD-003 和 PRD-004 均验收通过（active_jobs 依赖 generate_video job 类型）  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-006（全链验收）

---

## 1. 背景与问题陈述

### 1.1 当前状态

系统目前有两类异步机制：

**已有 Job 系统（视频生成）**：
- `start_seedance_shot()` 立即返回 `job_id`
- `GET /api/v1/jobs/{job_id}/events` 已实现 SSE 流（`StreamingResponse`，`text/event-stream`）
- DB `events` 表已有，存储 job 事件
- 前端目前以轮询 `/workflow` 替代 SSE（未使用已有 SSE 端点）

**同步 HTTP（图片生成）**：
- `POST .../background/generate` → 直接阻塞，最长 90s，前端 spinner 无反馈
- `POST .../keyframes/generate` → 同样同步阻塞
- 没有 `job_id`，没有事件流，无法追踪进度
- 若连接超时，前端无法判断操作是否在服务端继续执行

### 1.2 问题

1. 图片生成无法显示真实进度（PRD-001 的四阶段进度是纯视觉 mock）
2. 浏览器 HTTP 超时（约 30s）与图片生成实际耗时（60-90s）不匹配，导致假失败
3. 前端刷新后无法恢复进行中的操作状态
4. 视频生成已有 SSE 端点但前端未使用，属于浪费

---

## 2. 目标与非目标

### 目标

1. 图片生成（background/generate、keyframes/generate）改为异步 Job 提交，立即返回 `job_id`
2. 前端对所有生成操作统一使用 `EventSource` 订阅 job 事件
3. 刷新恢复：页面加载时检查 `workflow` 中的 `active_jobs`，自动重连进行中的 EventSource
4. 统一事件格式：所有 job 类型（图片/视频）发送相同结构的 SSE 事件
5. 旧同步端点保留但加 `X-Async: true` 响应头和 `job_id` 字段（向后兼容）
6. 前端生成操作 UI 统一：提交 → loading with job progress → 完成/失败

### 非目标

- 不废弃旧同步端点（仍可用，但返回值变化）
- 不实现 WebSocket（SSE 单向已足够）
- 不实现 job 队列优先级或取消
- 不改变 DB 表结构
- 不实现跨设备 job 同步

---

## 3. 架构规格

### 3.1 统一 Job 事件格式

所有 job 类型均发送以下结构的 SSE 事件：

```
event: progress
data: {"job_id": "...", "stage": "translate_prompt", "pct": 20, "message": "正在翻译提示词..."}

event: progress  
data: {"job_id": "...", "stage": "generate_image", "pct": 60, "message": "正在调用图片模型..."}

event: done
data: {"job_id": "...", "stage": "save_result", "pct": 100, "result": {"path": "assets/..."}}

event: error
data: {"job_id": "...", "stage": "translate_prompt", "error_category": "timeout", "message": "翻译超时，请重试"}
```

`stage` 枚举（图片生成）：
- `"translate_prompt"` — 翻译中文提示词为英文
- `"generate_image"` — 调用图片 Provider
- `"save_result"` — 写文件 + 更新 shot-references.json

`stage` 枚举（视频生成）：
- `"submit_task"` — 提交到 Seedance
- `"polling"` — 轮询结果（每 5s 一次 progress 事件，pct 随轮询次数递增）
- `"download"` — 下载 MP4
- `"qc_check"` — 质量验证
- `"save_result"` — 写文件 + 更新 shot-references.json

### 3.2 图片生成 Job 化

**原流程**：
```
POST .../background/generate
    → service.generate_shot_background()  [同步阻塞]
    → HTTP 200 / 423
```

**新流程**：
```
POST .../background/generate
    → service.submit_generate_background_job()  [立即返回]
    → HTTP 202, body: {"job_id": "...", "status": "queued"}

GET /api/v1/jobs/{job_id}/events?follow=true
    → SSE stream
    → event: progress ... event: done / error
```

向后兼容：旧端点保留，响应中新增字段 `job_id`，HTTP 状态改为 202。
若已有代码直接判断 200 → 需更新前端。

### 3.3 workflow 中的 active_jobs

`get_project_workflow()` 返回新增字段：

```python
"active_jobs": [
    {
        "job_id": "...",
        "type": "generate_background",  # generate_background | generate_keyframe | generate_video
        "shot_id": "S001",
        "status": "running",            # queued | running | done | error
        "started_at": "..."
    }
]
```

前端页面加载时：若 `active_jobs` 非空，自动 reconnect EventSource。

### 3.4 Job 执行器（后端）

图片生成 job 在 `execute_job()` 函数中新增两个 handler：

```python
elif job.type == "generate_background":
    _run_generate_background_job(job, project_id, shot_id, emit)

elif job.type == "generate_keyframe":
    _run_generate_keyframe_job(job, project_id, shot_id, emit)
```

`emit(stage, pct, message)` 写一条 DB event 记录，供 SSE 端点读取。

---

## 4. 业务逻辑规格

### 4.1 图片生成 Job 提交（R-050）

新增 `submit_generate_background_job(project_id, shot_id) -> dict`：

```python
def submit_generate_background_job(self, project_id: str, shot_id: str) -> dict:
    # 前置条件检查（复用 generate_shot_background 已有逻辑）
    self._check_preconditions_background(project_id, shot_id)
    job = self.jobs.create(
        project_id=project_id,
        type="generate_background",
        params={"shot_id": shot_id},
    )
    self.executor.submit(job.id)
    return {"job_id": job.id, "status": "queued"}
```

同理，`submit_generate_keyframe_job(project_id, shot_id) -> dict`。

### 4.2 Job 执行器中的图片生成 Handler（R-051）

在 `execute_job()` 中新增两个 handler：

```python
elif job.type == "generate_background":
    shot_id = job.params["shot_id"]
    def emit(stage, pct, message):
        self.events.append(job.id, {"stage": stage, "pct": pct, "message": message})
    # 复用已有 _generate_shot_image 逻辑，但包装 emit 调用
    _run_generate_background_job(job.project_id, shot_id, emit)
```

`_run_generate_background_job` 内部在以下节点调用 `emit`：
- 翻译开始前：`emit("translate_prompt", 10, "正在翻译提示词...")`
- 翻译完成：`emit("translate_prompt", 30, "提示词翻译完成")`
- 图片请求发送：`emit("generate_image", 40, "正在调用图片模型...")`
- 图片接收完成：`emit("generate_image", 80, "图片生成完成")`
- 写文件完成：`emit("save_result", 100, "已保存")`

翻译失败时：`emit_error("translate_prompt", error_category, "翻译失败: ...")`

### 4.3 前端 EventSource 集成（R-052）

前端对所有生成操作统一使用以下模式：

```javascript
async function submitAndStream(submitUrl, params, onProgress, onDone, onError) {
    const resp = await fetch(submitUrl, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(params),
    });
    if (!resp.ok) {
        onError(await resp.json());
        return;
    }
    const { job_id } = await resp.json();
    const es = new EventSource(`/api/v1/jobs/${job_id}/events?follow=true`);
    es.addEventListener("progress", e => onProgress(JSON.parse(e.data)));
    es.addEventListener("done", e => { es.close(); onDone(JSON.parse(e.data)); });
    es.addEventListener("error", e => { es.close(); onError(JSON.parse(e.data)); });
    return () => es.close(); // cleanup
}
```

### 4.4 刷新恢复（R-053）

页面加载（`DOMContentLoaded` 或 React/Vue mount）时：

```javascript
const wf = await fetchWorkflow(projectId);
for (const job of wf.active_jobs || []) {
    if (job.status === "running" || job.status === "queued") {
        reconnectEventSource(job.job_id, job.shot_id, job.type);
    }
}
```

`reconnectEventSource` 复用 `submitAndStream` 的 EventSource 部分（跳过 submit）。

### 4.5 向后兼容（R-054）

旧同步端点（`POST .../background/generate`）仍保留：
- 实现改为调用 `submit_generate_background_job()`
- 返回 HTTP **202**（原 200）+ body: `{"job_id": "...", "status": "queued"}`
- 加响应头 `X-Async: true`

旧前端代码若直接判断 HTTP 200 → 需同步更新为接受 202。

---

## 5. API 变更规格

### 5.1 现有路由变更

| 路由 | 原行为 | 新行为 |
|---|---|---|
| `POST .../background/generate` | 同步阻塞，200 / 423 | 立即 202，返回 `job_id` |
| `POST .../keyframes/generate` | 同步阻塞，200 / 423 | 立即 202，返回 `job_id` |
| `GET /api/v1/jobs/{job_id}/events` | 已有，但前端未使用 | 前端正式使用，加 `follow=true` |

**注意**：视频生成 `POST .../video/generate` 已经是 Job 模式（PRD-004 规格），不变。

### 5.2 workflow 返回值新增字段

```python
"active_jobs": [
    {
        "job_id": str,
        "type": "generate_background" | "generate_keyframe" | "generate_video",
        "shot_id": str,
        "status": "queued" | "running" | "done" | "error",
        "started_at": str,  # ISO timestamp
    }
]
```

实现：`get_project_workflow()` 查询 `jobs` 表，过滤 `status IN ('queued', 'running')`，
映射为 `active_jobs` 列表。

### 5.3 Job 事件写入接口

后端 `events` 表已有，SSE 端点已有。本 PRD 只需确认事件写入格式：

```python
# 写进度事件
self.events.append(job_id, {
    "type": "progress",
    "stage": "translate_prompt",
    "pct": 20,
    "message": "正在翻译提示词...",
})

# 写完成事件
self.events.append(job_id, {
    "type": "done",
    "stage": "save_result",
    "pct": 100,
    "result": {"path": "assets/..."},
})

# 写错误事件
self.events.append(job_id, {
    "type": "error",
    "stage": "translate_prompt",
    "error_category": "timeout",
    "message": "翻译超时，请重试",
})
```

SSE 端点读取时，将 `type` 字段映射为 SSE `event:` 名称。

---

## 6. 前端规格

### 6.1 统一生成进度组件

复用同一个 `GenerationProgress` 组件（图片/视频生成均使用）：

```
● 翻译提示词 (20%)  →  ● 调用图片模型 (60%)  →  ● 保存结果 (100%)
[  进行中 spinner  ]     [  等待中   ]             [  等待中  ]
```

图片生成 stages：translate_prompt → generate_image → save_result  
视频生成 stages：submit_task → polling (N%) → download → qc_check → save_result

### 6.2 失败状态

```
✗ 翻译提示词 — 翻译超时，请重试
[重试]  [取消]
```

点击"重试"重新提交同一请求（复用 `submitAndStream`）。
点击"取消"仅关闭 UI，不取消后端 job（后端 job 会自然超时或完成）。

### 6.3 刷新后恢复提示

若刷新后发现 active_jobs，在页面顶部显示：
```
⚡ 有 2 个生成任务正在进行中 [重连进度]
```

点击"重连进度"触发 R-053 逻辑。

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd005_sse.py`）

**UT-040**：submit_generate_background_job 立即返回 job_id

```python
def test_submit_background_job_returns_job_id(service, project_scenes_approved):
    result = service.submit_generate_background_job(project_id, "S001")
    assert "job_id" in result
    assert result["status"] == "queued"
```

**UT-041**：Job 执行过程发出 progress 事件

```python
def test_background_job_emits_progress_events(service, project_scenes_approved, mock_image_provider):
    result = service.submit_generate_background_job(project_id, "S001")
    job_id = result["job_id"]
    # 同步等待执行完成（测试环境）
    service._run_pending_jobs_sync()
    events = service.events.list(job_id)
    stages = [e["stage"] for e in events]
    assert "translate_prompt" in stages
    assert "generate_image" in stages
    assert "save_result" in stages
```

**UT-042**：翻译失败时发出 error 事件，不发 done 事件

```python
def test_background_job_emits_error_on_translate_fail(service, project_scenes_approved, mock_translate_timeout):
    result = service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()
    events = service.events.list(result["job_id"])
    assert any(e.get("type") == "error" and e["stage"] == "translate_prompt" for e in events)
    assert not any(e.get("type") == "done" for e in events)
```

**UT-043**：workflow 返回 active_jobs（job 进行中时）

```python
def test_workflow_active_jobs_while_running(service, project_with_running_job):
    wf = service.get_project_workflow(project_id)
    assert len(wf["active_jobs"]) > 0
    assert wf["active_jobs"][0]["status"] in ("queued", "running")
```

**UT-044**：workflow active_jobs 为空（job 完成后）

```python
def test_workflow_no_active_jobs_after_done(service, project_with_completed_job):
    wf = service.get_project_workflow(project_id)
    assert wf["active_jobs"] == []
```

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd005_api.py`）

**CT-040**：background/generate 返回 202 + job_id

```python
def test_background_generate_returns_202(test_client, project_scenes_approved):
    resp = test_client.post(f".../shots/S001/background/generate")
    assert resp.status_code == 202
    assert "job_id" in resp.json()
    assert resp.headers.get("X-Async") == "true"
```

**CT-041**：keyframes/generate 返回 202 + job_id

```python
def test_keyframe_generate_returns_202(test_client, project_scenes_approved_with_bg):
    resp = test_client.post(f".../shots/S001/keyframes/generate")
    assert resp.status_code == 202
    assert "job_id" in resp.json()
```

**CT-042**：job events SSE 端点返回 text/event-stream

```python
def test_job_events_returns_sse(test_client, project_with_running_job, job_id):
    resp = test_client.get(f"/api/v1/jobs/{job_id}/events?follow=false")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
```

**CT-043**：workflow 包含 active_jobs 字段

```python
def test_workflow_has_active_jobs_field(test_client, project_id):
    data = test_client.get(f".../workflow").json()
    assert "active_jobs" in data
    assert isinstance(data["active_jobs"], list)
```

### 7.3 浏览器 E2E 测试（`tests/e2e/test_prd005_browser.py`）

**ET-040**：背景生成显示真实进度条（非 mock）

```python
def test_background_generate_shows_real_progress(page, project_scenes_approved):
    page.locator("button:has-text('生成背景')").first.click()
    # 等待进度组件出现
    page.wait_for_selector("text=翻译提示词", timeout=5_000)
    # 等待完成
    page.wait_for_selector("text=已保存", timeout=120_000)
```

**ET-041**：刷新后自动重连进行中的 job

```python
def test_refresh_reconnects_active_job(page, project_with_running_background_job):
    page.reload()
    # 断言：恢复提示或进度条出现
    assert (
        page.locator("text=有").count() > 0 or
        page.locator("text=生成任务").count() > 0 or
        page.locator("text=翻译提示词").count() > 0
    )
```

**ET-042**：翻译失败时显示重试按钮（需 mock）

```python
def test_translate_fail_shows_retry_button(page, project_scenes_approved, mock_translate_fail):
    page.locator("button:has-text('生成背景')").first.click()
    page.wait_for_selector("text=翻译超时", timeout=30_000)
    assert page.locator("button:has-text('重试')").count() > 0
```

---

## 8. 验收标准

- [ ] UT-040 ～ UT-044 全部通过
- [ ] CT-040 ～ CT-043 全部通过
- [ ] ET-040 通过（真实进度条可见）
- [ ] ET-041 通过（刷新恢复）
- [ ] ET-042 通过（失败重试按钮）
- [ ] 手动检查：background/generate 和 keyframes/generate 均返回 202，无阻塞等待
- [ ] 手动检查：刷新页面后进行中的 job 能自动重连，不丢失状态
- [ ] 手动检查：所有进度/错误文字为中文

---

## 9. 废弃与归档说明

**标记为废弃（不删除）**：
- PRD-001 R-009/R-010 的"伪进度条"逻辑（纯视觉 mock），保留代码但前端切换为真实 EventSource 后自然不再触发
- 若旧代码中有 `setTimeout` 驱动的假进度，加注释 `# DEPRECATED: replaced by real SSE in PRD-005`

---

## 10. 实施顺序建议（给便宜模型）

```
Step 1  确认 events 表写入接口存在（或实现 events.append(job_id, payload)），写 UT-043/044
Step 2  实现 submit_generate_background_job()，写 UT-040
Step 3  实现 _run_generate_background_job()（带 emit 调用），写 UT-041/042
Step 4  实现 submit_generate_keyframe_job() + handler，对称实现
Step 5  更新 /background/generate 端点：返回 202 + job_id，写 CT-040
Step 6  更新 /keyframes/generate 端点：返回 202 + job_id，写 CT-041
Step 7  确认 GET /jobs/{id}/events SSE 格式正确，写 CT-042
Step 8  更新 get_project_workflow() 返回 active_jobs，写 CT-043 / UT-043/044
Step 9  前端：统一 GenerationProgress 组件（ET-040）
Step 10 前端：刷新恢复逻辑（ET-041）
Step 11 全量执行：pytest -k "prd005"，输出 TEST_REPORT_PRD005.md
```
