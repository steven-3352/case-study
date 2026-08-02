# PRD-007：前端 SSE 集成与翻译缓存

> **状态**：待实施  
> **优先级**：P4  
> **前置条件**：PRD-005 验收通过（submit_generate_background_job / submit_generate_keyframe_job 已实现，SSE 端点已就绪）  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-008（全链路验收配置化）

---

## 1. 背景与问题陈述

### 1.1 当前状态

PRD-005 完成了后端 Job 化改造：
- `POST .../background/generate` 已返回 202 + `job_id`
- `GET /api/v1/jobs/{job_id}/events` SSE 端点已就绪
- `workflow` 已返回 `active_jobs` 字段

但前端尚未接入 SSE，存在以下问题：

**问题 1：前端未消费 SSE**  
前端仍使用轮询 `/workflow` 或静态 spinner，无法显示真实的 translate_prompt / generate_image / save_result 进度阶段。

**问题 2：刷新后状态丢失**  
页面刷新后，进行中的 job 没有被自动恢复，用户不知道后台是否还在运行。

**问题 3：翻译重复调用**  
同一个场景组的提示词在反复点击"重新生成"时每次都重新调用 OpenAI translate，增加延迟和费用。

**问题 4：错误状态无阶段定位**  
生成失败时，前端只显示通用错误提示，用户不知道是翻译失败还是图片生成失败。

---

## 2. 目标与非目标

### 目标

1. 前端对 background/generate 和 keyframes/generate 统一使用 `EventSource` 订阅进度
2. 进度步骤实时显示：translate_prompt → generate_image → save_result
3. 刷新恢复：页面加载时检查 `active_jobs`，自动重连进行中的 EventSource
4. 翻译缓存：hash(zh_prompt) → en_prompt，相同提示词跳过翻译步骤
5. 错误状态显示：带阶段名称 + 重试按钮（inline，不弹窗）
6. 视频生成使用同一套 EventSource 逻辑（stages 不同，组件复用）

### 非目标

- 不实现 WebSocket（SSE 已足够）
- 不实现 job 取消（后端 job 自然超时或完成）
- 不实现多 job 并发进度（同一 shot 同时只有一个活跃 job）
- 不修改后端 SSE 格式（以 PRD-005 规格为准）
- 不实现翻译缓存持久化到服务器（只在本地 sessionStorage）

---

## 3. 架构规格

### 3.1 前端 EventSource 统一模块（R-071）

新建 `static/js/sse_client.js`（或对应前端框架的 hook/store）：

```javascript
/**
 * submitAndStream — 提交 POST 请求并立即订阅 SSE 进度流
 * @returns cancel 函数（关闭 EventSource）
 */
function submitAndStream(submitUrl, params, { onProgress, onDone, onError }) {
    return fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
    })
    .then(resp => {
        if (!resp.ok) return resp.json().then(body => { onError(body); });
        return resp.json().then(({ job_id }) => {
            return attachEventSource(job_id, { onProgress, onDone, onError });
        });
    });
}

/**
 * attachEventSource — 对已有 job_id 订阅 SSE（刷新恢复用）
 * @returns cancel 函数
 */
function attachEventSource(job_id, { onProgress, onDone, onError }) {
    const es = new EventSource(`/api/v1/jobs/${job_id}/events?follow=true`);
    es.addEventListener("progress", e => onProgress(JSON.parse(e.data)));
    es.addEventListener("done",     e => { es.close(); onDone(JSON.parse(e.data)); });
    es.addEventListener("error",    e => { es.close(); onError(JSON.parse(e.data)); });
    return () => es.close();
}
```

### 3.2 进度组件规格（R-072）

统一的 `GenerationProgress` 组件：

```
状态示例（背景生成）：

● 翻译提示词 (20%)     ← 当前阶段 spinner
○ 生成图片             ← 等待中
○ 保存结果             ← 等待中

失败状态：

✗ 翻译提示词 — 翻译超时，请重试
[重试]  [关闭]
```

Stage 映射表（图片生成）：

| stage | 中文标签 | 进度区间 |
|---|---|---|
| `translate_prompt` | 翻译提示词 | 10% ~ 30% |
| `generate_image` | 生成图片 | 40% ~ 80% |
| `save_result` | 保存结果 | 90% ~ 100% |

Stage 映射表（视频生成，复用同一组件）：

| stage | 中文标签 | 进度区间 |
|---|---|---|
| `submit_task` | 提交任务 | 10% |
| `polling` | 等待结果 | 20% ~ 70% |
| `download` | 下载视频 | 80% |
| `qc_check` | 质量验证 | 90% |
| `save_result` | 保存结果 | 100% |

### 3.3 刷新恢复逻辑（R-073）

页面加载时（`DOMContentLoaded` 或框架 mount 钩子）：

```javascript
async function restoreActiveJobs(projectId) {
    const wf = await fetch(`/api/v1/projects/${projectId}/workflow`).then(r => r.json());
    for (const job of wf.active_jobs ?? []) {
        if (["queued", "running"].includes(job.status)) {
            showProgressBanner(job);
            attachEventSource(job.job_id, {
                onProgress: p  => updateJobProgress(job.shot_id, p),
                onDone:     d  => finalizeJob(job.shot_id, "done", d),
                onError:    e  => finalizeJob(job.shot_id, "error", e),
            });
        }
    }
}
```

若 `active_jobs` 非空，在页面顶部显示横幅：
```
⚡ 有 N 个生成任务正在进行中  [查看进度]
```

### 3.4 翻译缓存（R-074）

翻译缓存存储在 `sessionStorage`（页面会话级，不跨 tab，不持久化服务器）：

```javascript
const CACHE_KEY = "mv_translate_cache";

function getCachedTranslation(zhPrompt) {
    const cache = JSON.parse(sessionStorage.getItem(CACHE_KEY) ?? "{}");
    return cache[hashPrompt(zhPrompt)] ?? null;
}

function setCachedTranslation(zhPrompt, enPrompt) {
    const cache = JSON.parse(sessionStorage.getItem(CACHE_KEY) ?? "{}");
    cache[hashPrompt(zhPrompt)] = enPrompt;
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(cache));
}

function hashPrompt(str) {
    // djb2 — 足够用于 cache key，不需要密码学强度
    let h = 5381;
    for (let i = 0; i < str.length; i++) h = (h * 33) ^ str.charCodeAt(i);
    return (h >>> 0).toString(36);
}
```

**缓存触发时机**：`event: progress` 中 `stage === "translate_prompt"` 且 `pct === 30`（翻译完成）时，
从事件 `payload.en_prompt` 字段写入缓存。

**缓存使用时机**：用户点击"重新生成"时，前端在 POST 请求 body 中携带 `en_prompt`（若已缓存），
后端检测到 `en_prompt` 字段非空时跳过翻译步骤，直接进入 `generate_image` 阶段。

### 3.5 错误状态 UI（R-075）

生成失败时，在对应 shot 卡片内联显示：

```
┌─────────────────────────────────────┐
│  ✗ 生成失败                          │
│  阶段：翻译提示词                    │
│  原因：翻译超时，请重试              │
│                                     │
│  [重试]          [手动输入英文提示词] │
└─────────────────────────────────────┘
```

- **重试**：重新调用 `submitAndStream`，使用原始参数（带缓存的 en_prompt 若有）
- **手动输入英文提示词**：展开文本框，用户可直接输入 en_prompt 绕过翻译，提交时带入 body

---

## 4. 业务逻辑规格

### 4.1 后端：翻译结果回写到 SSE 事件（R-071 后端部分）

`_execute_background_job` 在翻译完成后，progress 事件 payload 中新增 `en_prompt` 字段：

```python
emit("translate_prompt", 30, {
    "message": "提示词翻译完成",
    "en_prompt": translated_en_prompt,  # 新增，前端写入缓存
})
```

### 4.2 后端：接受 en_prompt 跳过翻译（R-074 后端部分）

`submit_generate_background_job` 接受可选参数 `en_prompt: str | None = None`：

```python
def submit_generate_background_job(
    self, project_id: str, shot_id: str, en_prompt: str | None = None
) -> dict:
    ...
    job = self.jobs.create(
        project_id=project_id,
        type="generate_background",
        params={"shot_id": shot_id, "en_prompt": en_prompt},
    )
```

`_execute_background_job` 检测 `job.params.get("en_prompt")`，若非空则跳过翻译，直接 emit `generate_image` 阶段。

API 路由同步更新，接受 `body: { en_prompt?: string }`：

```python
@router.post(".../background/generate")
async def generate_background(
    project_id: str, shot_id: str,
    body: GenerateBackgroundRequest = Body(default=GenerateBackgroundRequest()),
):
    result = svc.submit_generate_background_job(
        project_id, shot_id, en_prompt=body.en_prompt
    )
```

---

## 5. API 变更规格

### 5.1 现有路由扩展

| 路由 | 变更 |
|---|---|
| `POST .../background/generate` | body 新增可选字段 `en_prompt: string`（跳过翻译时传入） |
| `POST .../keyframes/generate` | 同上，body 新增可选字段 `en_prompt: string` |

**注意**：字段为可选，不传则行为不变（向后兼容）。

### 5.2 SSE 事件格式扩展

`translate_prompt` 阶段完成时（pct=30），`data` 新增字段：

```
event: progress
data: {"job_id": "...", "stage": "translate_prompt", "pct": 30, "message": "提示词翻译完成", "en_prompt": "..."}
```

其余事件格式不变（PRD-005 规格不变）。

---

## 6. 前端规格

### 6.1 Background 阶段 UI 流程

```
用户点击 [生成背景]
    │
    ├─ 检查 sessionStorage 缓存（hash 当前提示词）
    │   ├─ 命中 → POST body 携带 en_prompt
    │   └─ 未命中 → POST body 不含 en_prompt
    │
    ├─ fetch POST .../background/generate → 202 + job_id
    │
    ├─ EventSource /jobs/{job_id}/events?follow=true
    │   ├─ event: progress (stage=translate_prompt, pct=30) → 写入缓存 en_prompt
    │   ├─ event: progress (stage=generate_image)
    │   ├─ event: done → 刷新 shot 缩略图，关闭 ES
    │   └─ event: error → 显示内联错误 + 重试按钮，关闭 ES
    │
    └─ GenerationProgress 组件更新（每个 progress 事件驱动）
```

### 6.2 Keyframe 阶段 UI 流程

与 Background 一致（shot 粒度，`en_prompt` 同样缓存）。

### 6.3 Video 阶段 UI 流程

```
用户点击 [生成视频]
    │
    ├─ fetch POST .../video/generate → 202 + job_id（PRD-004 已有）
    ├─ EventSource /jobs/{job_id}/events?follow=true
    │   ├─ event: progress (stage=polling, pct=N%) → 更新进度条
    │   ├─ event: done → 显示视频预览
    │   └─ event: error → 显示内联错误
```

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd007_translate_cache.py`）

**UT-071**：submit_generate_background_job 接受 en_prompt 跳过翻译

```python
def test_submit_background_with_en_prompt_skips_translation(tmp_path, monkeypatch):
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut071")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    service.submit_generate_background_job(project_id, "S001", en_prompt="sky at dusk")
    service._run_pending_jobs_sync()
    assert len(translate_called) == 0, "translate should be skipped when en_prompt provided"
```

**UT-072**：无 en_prompt 时仍调用翻译

```python
def test_submit_background_without_en_prompt_calls_translation(tmp_path, monkeypatch):
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut072")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()
    assert len(translate_called) == 1
```

**UT-073**：翻译完成后 progress 事件包含 en_prompt 字段

```python
def test_translate_done_event_includes_en_prompt(tmp_path, monkeypatch):
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut073")
    monkeypatch.setattr(service, "_translate_prompt", lambda *a, **kw: "blue sky")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)
    result = service.submit_generate_background_job(project_id, "S001")
    service._run_pending_jobs_sync()
    events = service.repository.list_events(result["job_id"])
    translate_done = next(
        (e for e in events
         if e.event_type == "progress"
         and e.payload.get("stage") == "translate_prompt"
         and e.payload.get("pct", 0) >= 30),
        None,
    )
    assert translate_done is not None
    assert translate_done.payload.get("en_prompt") == "blue sky"
```

**UT-074**：job 参数含 en_prompt 时，events 不含 translate_prompt 阶段

```python
def test_no_translate_progress_event_when_en_prompt_cached(tmp_path, monkeypatch):
    service, project_id, _ = _setup_project_for_background(tmp_path, "ut074")
    monkeypatch.setattr(service, "generate_shot_background", lambda *a, **kw: None)
    result = service.submit_generate_background_job(
        project_id, "S001", en_prompt="blue sky"
    )
    service._run_pending_jobs_sync()
    events = service.repository.list_events(result["job_id"])
    stages = [e.payload.get("stage") for e in events if e.event_type == "progress"]
    assert "translate_prompt" not in stages
    assert "generate_image" in stages
```

**UT-075**：submit_generate_keyframe_job 同样支持 en_prompt 跳过翻译

```python
def test_submit_keyframe_with_en_prompt_skips_translation(tmp_path, monkeypatch):
    service, project_id, _ = _setup_project_for_keyframe(tmp_path, "ut075")
    translate_called = []
    monkeypatch.setattr(service, "_translate_prompt",
                        lambda *a, **kw: translate_called.append(1) or "translated")
    service.submit_generate_keyframe_job(project_id, "S001", en_prompt="close-up portrait")
    service._run_pending_jobs_sync()
    assert len(translate_called) == 0
```

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd007_api.py`）

**CT-071**：POST background/generate 携带 en_prompt 返回 202

```python
def test_background_generate_with_en_prompt_returns_202(client, project_id):
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
        json={"en_prompt": "blue sky at dusk"},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()
```

**CT-072**：POST background/generate 不含 en_prompt 仍返回 202

```python
def test_background_generate_without_en_prompt_returns_202(client, project_id):
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate"
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()
```

**CT-073**：POST keyframes/generate 携带 en_prompt 返回 202

```python
def test_keyframe_generate_with_en_prompt_returns_202(client, project_id):
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/keyframes/generate",
        json={"en_prompt": "close-up portrait in warm light"},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()
```

**CT-074**：en_prompt 字段为 null 时行为与不传相同

```python
def test_background_generate_null_en_prompt_behaves_same_as_absent(client, project_id):
    resp = client.post(
        f"/api/v1/projects/{project_id}/shots/S001/background/generate",
        json={"en_prompt": None},
    )
    assert resp.status_code == 202
```

### 7.3 浏览器 E2E 测试（`tests/e2e/test_prd007_browser.py`）

**ET-071**：背景生成显示真实 SSE 进度步骤

```python
@requires_ui
def test_background_generate_shows_sse_progress_steps(page, project_id):
    page.goto(f"{BASE_URL}/projects/{project_id}/backgrounds")
    page.locator("button.bg-generate:not([disabled])").first.click()
    page.wait_for_selector("text=翻译提示词, .progress-step[data-stage='translate_prompt']",
                           timeout=10_000)
    page.wait_for_selector("text=生成图片, .progress-step[data-stage='generate_image']",
                           timeout=120_000)
    page.wait_for_selector("text=保存结果, .progress-step[data-stage='save_result']",
                           timeout=120_000)
```

**ET-072**：刷新后有 active_job 时显示恢复横幅

```python
@requires_ui
def test_refresh_shows_active_job_banner(page, project_id_with_running_job):
    page.goto(f"{BASE_URL}/projects/{project_id_with_running_job}/backgrounds")
    page.reload()
    banner = page.locator("text=生成任务正在进行中, [data-banner='active-jobs']")
    assert banner.count() > 0
```

**ET-073**：第二次生成相同提示词不显示翻译进度（命中缓存）

```python
@requires_ui
def test_second_generate_skips_translate_step(page, project_id):
    page.goto(f"{BASE_URL}/projects/{project_id}/backgrounds")
    # 第一次生成
    page.locator("button.bg-generate:not([disabled])").first.click()
    page.wait_for_selector(".progress-step[data-stage='save_result']", timeout=120_000)
    # 第二次生成
    page.locator("button.bg-generate:not([disabled])").first.click()
    # 翻译步骤不应出现（直接到 generate_image）
    translate_step = page.locator(".progress-step[data-stage='translate_prompt']")
    assert translate_step.count() == 0 or "active" not in (translate_step.get_attribute("class") or "")
```

---

## 8. 验收标准

- [ ] UT-071 ～ UT-075 全部通过
- [ ] CT-071 ～ CT-074 全部通过
- [ ] ET-071 通过（真实 SSE 进度步骤可见，非 mock）
- [ ] ET-072 通过（刷新恢复横幅）
- [ ] ET-073 通过（第二次生成跳过翻译阶段）
- [ ] 手动检查：POST body 携带 `en_prompt` 时，后端 events 无 `translate_prompt` 阶段事件
- [ ] 手动检查：点击"重试"时，若缓存存在则自动携带 `en_prompt`，页面进度直接从 `generate_image` 开始
- [ ] 手动检查：失败错误消息为中文，阶段名称正确

---

## 9. 废弃与归档说明

- PRD-001 R-009/R-010 的前端伪进度 mock（`setTimeout` 驱动）在本 PRD 实施后自然失效
- 旧前端中若有 `resp.status === 200` 的硬判断，改为 `resp.ok`（接受 202）

---

## 10. 实施顺序建议（给便宜模型）

```
Step 1  后端：_execute_background_job 在翻译完成事件中写入 en_prompt 字段（UT-073）
Step 2  后端：submit_generate_background_job 支持 en_prompt 参数，跳过翻译（UT-071/072/074）
Step 3  后端：submit_generate_keyframe_job 同样支持 en_prompt（UT-075）
Step 4  后端：API 路由 body schema 添加可选 en_prompt 字段（CT-071~074）
Step 5  前端：实现 sse_client.js (submitAndStream / attachEventSource)
Step 6  前端：实现 GenerationProgress 组件（stage 映射表）
Step 7  前端：background/generate 按钮接入 submitAndStream（ET-071）
Step 8  前端：实现 sessionStorage 翻译缓存（setCachedTranslation / getCachedTranslation）
Step 9  前端：刷新恢复逻辑 restoreActiveJobs（ET-072）
Step 10 前端：第二次生成时查缓存并携带 en_prompt（ET-073）
Step 11 全量执行：pytest -k "prd007"，输出 TEST_REPORT_PRD007.md
```
