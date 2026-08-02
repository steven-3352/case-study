# PRD-004：视频 Provider 对接

> **状态**：待实施  
> **优先级**：P4  
> **前置条件**：PRD-003 验收通过（scenes_approved 门禁依赖，selected_keyframe 已有元数据）  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-005（真实 SSE 流式推送）、PRD-006（全链验收）

---

## 1. 背景与问题陈述

### 1.1 当前状态

`start_seedance_shot()` 已存在（service.py:1874），可异步提交一个视频生成 Job 并返回 job_id。
但当前实现存在四个问题：

**问题 1：配置验证缺失**  
Provider 配置（`SEEDANCE_BASE_URL / SEEDANCE_API_KEY / SEEDANCE_MODEL`）仅在调用时才发现缺失，
用户在 Settings 页面无法提前知道配置是否有效。

**问题 2：前置条件检查不完整**  
`start_seedance_shot()` 没有检查：
- `scenes_approved` 是否已通过
- 该 shot 的 `selected_keyframe` 是否存在
- `selected_keyframe` 是否为有效文件路径

**问题 3：QC 验证缺失**  
视频下载后只做 magic bytes 校验（`b"ftyp"`），没有验证：
- 实际时长是否与请求时长吻合（±2s 容差）
- 分辨率是否满足最低要求（720p）
- 文件大小是否在合理范围（> 100KB，< 200MB）

**问题 4：shot-references.json 无视频元数据**  
视频生成结果只保存了路径，没有记录：
- 使用的 keyframe 路径（`source_keyframe`）
- 请求时长（`duration_requested`）
- 实际时长（`duration_actual`）
- 生成费用（`cost_yuan`）
- 任务 ID（`task_id`）
- 生成时间

---

## 2. 目标与非目标

### 目标

1. Settings 页面加入视频 Provider 配置验证入口，可测试连通性（ping）
2. `start_seedance_shot()` 前置条件改为 `scenes_approved` + `selected_keyframe` 非空
3. 视频生成完成后执行 QC（时长、分辨率、文件大小）
4. `shot-references.json` 升至 v4，新增 `video_entries` 字段，记录视频元数据
5. workflow 返回每个 shot 的 `video_entries` 列表
6. 前端 shots 阶段显示：生成状态 + 视频预览 + 元数据（时长/费用）+ 错误阶段定位
7. 错误日志增强：video 生成失败时记录 `error_category`，对齐 PRD-001 的诊断结构

### 非目标

- 不实现多 Provider 切换（仅 Seedance）
- 不实现批量视频生成（每次一个 shot）
- 不改变 Seedance SDK 内部轮询逻辑
- 不实现视频剪辑或后处理
- 不实现视频重试 UI（一期只有"重新生成"替换）

---

## 3. 数据模型规格

### 3.1 `shot-references.json` 升至 v4

在每个 shot 节点追加 `video_entries` 字段（与 `keyframe_entries` 对称）：

```json
{
  "version": 4,
  "shots": {
    "S001": {
      "background": "assets/...",
      "background_master_id": "BG001",
      "background_variant": { "shot_size": "medium", "camera_angle": "eye_level" },
      "keyframes": [...],
      "selected_keyframe": "assets/generated/keyframes/S001-abc123.png",
      "video_entries": [
        {
          "path": "assets/generated/videos/S001-def456.mp4",
          "source_keyframe": "assets/generated/keyframes/S001-abc123.png",
          "duration_requested": 5,
          "duration_actual": 4.97,
          "resolution": "720p",
          "file_size_bytes": 8388608,
          "model": "seedance-2.0",
          "task_id": "task-def456",
          "cost_yuan": 3.0,
          "qc_passed": true,
          "created_at": "2026-08-01T21:05:00+08:00"
        }
      ],
      "selected_video": "assets/generated/videos/S001-def456.mp4",
      "video_selected_at": "2026-08-01T21:06:00+08:00"
    }
  }
}
```

字段约束：
- `duration_actual`：从 ffprobe 或 MP4 box 解析，若无法解析则为 0.0
- `qc_passed`：所有 QC 检查通过则为 true
- `selected_video`：选定视频的路径字符串（与 `selected_keyframe` 对称）

### 3.2 配置 Ping 响应结构

`POST /api/v1/settings/video-provider/ping` 返回：

```json
{
  "provider": "seedance",
  "reachable": true,
  "model": "seedance-2.0",
  "latency_ms": 342,
  "error": ""
}
```

---

## 4. 业务逻辑规格

### 4.1 前置条件更新（R-040）

`start_seedance_shot()` 在提交 job 前检查：

```python
# 检查 scenes_approved
if decisions.get("scenes", {}).get("action") != "approve":
    raise ApplicationBlocked(
        "scenes approval is required before video generation",
        error_stage="precondition", error_category="precondition",
    )

# 检查 selected_keyframe 存在
shot_ref = references["shots"].get(shot_id, {})
selected_kf = shot_ref.get("selected_keyframe", "")
if not selected_kf:
    raise ApplicationBlocked(
        "shot has no selected keyframe, please complete keyframes stage first",
        error_stage="precondition", error_category="precondition",
    )

# 检查文件实际存在
kf_path = root / selected_kf
if not kf_path.exists():
    raise ApplicationBlocked(
        "selected keyframe file not found on disk",
        error_stage="precondition", error_category="precondition",
    )

# 检查 Provider 配置
if not os.environ.get("SEEDANCE_BASE_URL"):
    raise ApplicationBlocked(
        "Seedance provider not configured",
        error_stage="configuration", error_category="configuration",
    )
```

### 4.2 QC 验证（R-041）

视频下载后，在写入文件之前执行：

```python
def _qc_video(video_bytes: bytes, duration_requested: int) -> tuple[bool, dict]:
    issues = []

    # 1. magic bytes
    if not video_bytes[4:8] == b"ftyp":
        issues.append("not_mp4")

    # 2. 文件大小
    size = len(video_bytes)
    if size < 100_000:
        issues.append("file_too_small")
    if size > 200_000_000:
        issues.append("file_too_large")

    # 3. 时长（从 MP4 mvhd box 解析）
    duration_actual = _parse_mp4_duration(video_bytes)
    if duration_actual == 0.0:
        # 解析失败（分段MP4/CMAF/moov在尾部等格式），标记为 QC 问题而非静默跳过
        issues.append("duration_parse_failed")
    elif abs(duration_actual - duration_requested) > 2.0:
        issues.append(f"duration_mismatch:{duration_actual:.1f}s_vs_{duration_requested}s")

    return len(issues) == 0, {
        "duration_actual": duration_actual,
        "file_size_bytes": size,
        "qc_issues": issues,
    }
```

**R-042**：QC 失败不抛异常，video_entry 保存 `qc_passed=false`，前端提示"视频质量异常，可重新生成"。
不阻断：用户可以选择接受异常视频或重新生成。

### 4.3 时长解析（R-043）

`_parse_mp4_duration(video_bytes: bytes) -> float`：
解析 MP4 文件中的 `mvhd` box，计算 `duration / timescale` 得到秒数。
若解析失败（格式异常），返回 `0.0`，不抛异常。

这样不依赖外部工具（ffprobe），避免部署依赖。

### 4.4 视频元数据写入（R-044）

`_run_seedance_job` 完成后，将结果写入 `shot-references.json`：

```python
entry = {
    "path": relative_path,
    "source_keyframe": selected_kf,
    "duration_requested": duration,
    "duration_actual": qc_info["duration_actual"],
    "resolution": "720p",
    "file_size_bytes": qc_info["file_size_bytes"],
    "model": os.environ.get("SEEDANCE_MODEL", ""),
    "task_id": result.task_id,
    "cost_yuan": round(duration * 0.6, 2),
    "qc_passed": qc_passed,
    "created_at": datetime.now(timezone.utc).isoformat(),
}
shot_ref.setdefault("video_entries", []).append(entry)
```

### 4.5 Provider Ping（R-045）

`_ping_video_provider() -> dict`：向 Seedance base URL 发一个轻量请求（如 GET /health 或 HEAD /），
记录延迟，返回 ping 结构。若无 `/health` 端点，改为检查环境变量是否完整（不做真实网络请求）。

### 4.6 workflow 返回值更新（R-046）

`get_project_workflow()` 在每个 shot 数据中新增 `video_entries`：

```python
"video_entries": [
    {
        "path": e["path"],
        "duration_requested": e["duration_requested"],
        "duration_actual": e["duration_actual"],
        "cost_yuan": e["cost_yuan"],
        "qc_passed": e["qc_passed"],
        "is_selected": e["path"] == shot_ref.get("selected_video", ""),
        "created_at": e["created_at"],
    }
    for e in shot_ref.get("video_entries", [])
],
"selected_video": shot_ref.get("selected_video", ""),
```

---

## 5. API 变更规格

### 5.1 新增路由

```
POST /api/v1/settings/video-provider/ping
    → 测试 Seedance 配置连通性
    → 返回 ping 结构（3.2）
    → 不需要登录，仅需本地服务

PUT  /api/v1/projects/{project_id}/shots/{shot_id}/videos/selection
    body: { "path": "assets/generated/videos/S001-xxx.mp4" }
    → 设置 selected_video
    → 同步更新 shot-references.json

POST /api/v1/projects/{project_id}/workflow/shots/decision
    body: { "action": "approve" }
    → 所有 shot 均有 selected_video 后可 approve
    → 解锁 delivery 阶段
```

### 5.2 现有路由变更

```
POST /api/v1/projects/{project_id}/shots/{shot_id}/video/generate
```

（此路由若已存在）内部改为：
- 执行 R-040 前置条件检查
- 提交 Job（已有 start_seedance_shot 逻辑）
- 返回 `{"job_id": "...", "status": "queued"}`，HTTP 202

若该路由不存在，新增（与 background/generate 路由对称）。

### 5.3 `allowed_stages` 更新

service.py 的 `allowed_stages` 加入 `"shots"` 和 `"delivery"`（若未包含）：

```python
allowed_stages = {"story", "storyboard", "scenes", "keyframes", "shots", "delivery"}
```

---

## 6. 前端规格

### 6.1 Settings 页面 · Provider 配置

在 Settings 页加入视频 Provider 配置区：

```
┌─ 视频生成 Provider ─────────────────────────────────────┐
│  Provider:  Seedance 2.0                                 │
│  Base URL:  [输入框，默认读取已配置值，仅显示 host 部分]   │
│  API Key:   [密码输入框，已配置则显示 ••••••••]           │
│  Model:     [输入框，默认 seedance-2.0]                  │
│                                                          │
│  [测试连接]  ← 点击后显示 ping 结果                      │
│  ✓ 连接正常  延迟 342ms   或  ✗ 配置缺失 / 连接失败       │
└──────────────────────────────────────────────────────────┘
```

**注意**：Base URL 和 API Key 只做展示，不在前端修改（修改仍需编辑 .env）。
"测试连接"按钮调用 `POST .../settings/video-provider/ping`。

### 6.2 单镜制作阶段 · 视频生成 UI

每个 shot 的视频生成区（shots 阶段）：

```
S001 | 月下独处（选定首帧: [缩略图]）
┌─ 已生成视频 ───────────────────────────────────────────┐
│ [视频预览占位 120×68]  时长: 5.0s  费用: ¥3.00  ✓QC    │
│ 模型: seedance-2.0  任务: task-xxx  08-01 21:05        │
│ [选定此视频] [重新生成]                                  │
└────────────────────────────────────────────────────────┘
[生成视频（约¥3.00，5秒）]
```

若 `qc_passed=false`，在视频卡片上显示警告：
`⚠ 视频质量异常（时长偏差/文件过小），建议重新生成`

若 `selected_keyframe` 为空（未完成关键帧阶段），按钮显示为 disabled：
`[请先在关键帧阶段选定首帧]`

### 6.3 批量确认

所有 shot 均有 `selected_video` 后，底部出现：

```
✓ 全部 25 镜已有选定视频
[一键确认所有视频 → 进入交付]
```

点击后调用 `POST .../workflow/shots/decision`，body: `{"action": "approve"}`。

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd004_video.py`）

**UT-030**：无 selected_keyframe 时 start_seedance_shot 报错

```python
def test_start_seedance_blocked_without_keyframe(service, project_scenes_approved_no_kf):
    with pytest.raises(ApplicationBlocked) as exc_info:
        service.start_seedance_shot(project_id, "S001", duration=5)
    assert exc_info.value.error_stage == "precondition"
    assert "keyframe" in str(exc_info.value).lower()
```

**UT-031**：Provider 未配置时 start_seedance_shot 报错

```python
def test_start_seedance_blocked_without_config(service, project_with_keyframe, monkeypatch):
    monkeypatch.delenv("SEEDANCE_BASE_URL", raising=False)
    with pytest.raises(ApplicationBlocked) as exc_info:
        service.start_seedance_shot(project_id, "S001", duration=5)
    assert exc_info.value.error_stage == "configuration"
```

**UT-032**：QC 验证：时长偏差超过 2s 时 qc_passed=False

```python
def test_qc_fails_on_duration_mismatch(valid_mp4_5s_bytes):
    # 请求 5s，MP4 实际 8s
    qc_passed, info = _qc_video(valid_mp4_5s_bytes_faked_8s, duration_requested=5)
    assert not qc_passed
    assert any("duration_mismatch" in issue for issue in info["qc_issues"])
```

**UT-033**：QC 验证：正常 MP4 通过

```python
def test_qc_passes_on_valid_video(valid_mp4_5s_bytes):
    qc_passed, info = _qc_video(valid_mp4_5s_bytes, duration_requested=5)
    assert qc_passed
    assert info["duration_actual"] == pytest.approx(5.0, abs=0.5)
```

**UT-034**：视频生成结果写入 video_entries

```python
def test_video_entry_written_after_generation(service, project_with_keyframe, mock_seedance):
    service.start_seedance_shot(project_id, "S001", duration=5)
    # 等待 job 完成（mock seedance 立即返回）
    refs = service._shot_references(root)
    entry = refs["shots"]["S001"]["video_entries"][0]
    assert entry["cost_yuan"] == 3.0
    assert entry["task_id"] != ""
    assert "duration_actual" in entry
```

**UT-035**：workflow 返回 video_entries

```python
def test_workflow_includes_video_entries(service, project_with_video):
    wf = service.get_project_workflow(project_id)
    shots_stage = next(s for s in wf["stages"] if s["id"] == "shots")
    shot = shots_stage["data"]["shots"][0]
    assert "video_entries" in shot
    assert shot["video_entries"][0]["qc_passed"] in (True, False)
```

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd004_api.py`）

**CT-030**：无 selected_keyframe 时 /video/generate 返回 423

```python
def test_video_generate_without_keyframe_returns_423(test_client, project_scenes_approved):
    resp = test_client.post(f".../shots/S001/video/generate", json={"duration": 5})
    assert resp.status_code == 423
    assert resp.json()["error_stage"] == "precondition"
```

**CT-031**：Provider 未配置时 /settings/video-provider/ping 返回 reachable=false

```python
def test_ping_unreachable_without_config(test_client, monkeypatch):
    monkeypatch.delenv("SEEDANCE_BASE_URL", raising=False)
    resp = test_client.post("/api/v1/settings/video-provider/ping")
    assert resp.status_code == 200
    assert resp.json()["reachable"] == False
```

**CT-032**：视频生成提交后返回 202 + job_id

```python
def test_video_generate_returns_202_with_job_id(test_client, project_with_keyframe, mock_seedance):
    resp = test_client.post(f".../shots/S001/video/generate", json={"duration": 5})
    assert resp.status_code == 202
    assert "job_id" in resp.json()
```

**CT-033**：选定视频后 workflow 反映 selected_video

```python
def test_select_video_updates_workflow(test_client, project_with_video):
    path = "assets/generated/videos/S001-xxx.mp4"
    test_client.put(f".../shots/S001/videos/selection", json={"path": path})
    wf = test_client.get(f".../workflow").json()
    shots = next(s for s in wf["stages"] if s["id"] == "shots")["data"]["shots"]
    assert shots[0]["selected_video"] == path
```

### 7.3 浏览器 E2E 测试（`tests/e2e/test_prd004_browser.py`）

**ET-030**：Settings 页面有视频 Provider 配置区

```python
def test_settings_has_video_provider_section(page):
    page.goto("http://127.0.0.1:8792")
    # 导航到 Settings
    assert page.locator("text=视频生成 Provider").is_visible()
    assert page.locator("text=测试连接").count() > 0
```

**ET-031**：无 selected_keyframe 时视频生成按钮 disabled

```python
def test_video_generate_disabled_without_keyframe(page, project_at_shots_no_kf):
    btn = page.locator("button:has-text('生成视频')")
    assert btn.is_disabled() or page.locator("text=请先在关键帧阶段选定首帧").count() > 0
```

**ET-032**（需真实 Provider）：生成一个视频后出现视频卡片

```python
def test_generate_video_shows_result(page, project_with_keyframe_selected):
    # 点击生成视频（约¥3.00）
    page.locator("button:has-text('生成视频')").first.click()
    # 等待最多 180s（Seedance 轮询）
    page.wait_for_selector("text=时长:", timeout=180_000)
    # 断言视频卡片出现
    assert page.locator("text=¥3.00").count() > 0 or page.locator("text=¥").count() > 0
```

---

## 8. 验收标准

- [ ] UT-030 ～ UT-035 全部通过
- [ ] CT-030 ～ CT-033 全部通过
- [ ] ET-030 ～ ET-031 通过（不需要真实 Provider）
- [ ] ET-032 通过（需真实 Provider，可延后到 PRD-006 全链验收）
- [ ] 手动检查：生成一个视频后，`shot-references.json` 中 `video_entries` 包含完整元数据
- [ ] 手动检查：QC 失败的视频在前端显示警告，而非阻断
- [ ] 手动检查：Settings 页面"测试连接"可区分已配置/未配置状态
- [ ] 手动检查：workflow 的 shots 阶段 shots 列表包含 `video_entries` 和 `selected_video`

---

## 9. 废弃与归档说明

**无废弃**。本 PRD 全部是在现有代码上追加字段和前置条件，不删除任何方法或路由。

`start_seedance_shot()` 的核心实现不变，仅在入口处增加前置条件检查（R-040）和在结果写入时增加元数据（R-044）。

---

## 10. 实施顺序建议（给便宜模型）

```
Step 1  实现 _parse_mp4_duration()，写 UT-033（正常 MP4 解析时长）
Step 2  实现 _qc_video()，写 UT-032（时长偏差检测）
Step 3  更新 start_seedance_shot() 前置条件（R-040），写 UT-030/031
Step 4  更新 _run_seedance_job 结果写入（R-044），写 UT-034
Step 5  更新 get_project_workflow() 返回 video_entries（R-046），写 UT-035
Step 6  新增 /settings/video-provider/ping 路由（R-045），写 CT-031
Step 7  更新 /shots/{shot_id}/video/generate 返回 202+job_id，写 CT-030/032
Step 8  新增 /shots/{shot_id}/videos/selection 路由，写 CT-033
Step 9  更新 allowed_stages
Step 10 前端：Settings Provider 配置区（ET-030）
Step 11 前端：shots 阶段视频生成 UI（ET-031，ET-032）
Step 12 全量执行：pytest -k "prd004"，输出 TEST_REPORT_PRD004.md
```
