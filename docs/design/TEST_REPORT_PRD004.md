# TEST_REPORT_PRD004 · 视频生成集成

**日期**：2026-08-02  
**执行模型**：claude-sonnet-5  
**命令**：`PYTHONPATH=. .venv/bin/python3 -m pytest tests/mv_platform/unit/test_prd004_video.py tests/mv_platform/contract/test_prd004_api.py tests/e2e/test_prd004_browser.py -v`

---

## 总结

| 类别 | 通过 | 跳过 | 失败 |
|------|------|------|------|
| 单元测试 (UT) | 6 | 0 | 0 |
| 契约测试 (CT) | 4 | 0 | 0 |
| E2E 浏览器 (ET) | 1 | 3 | 0 |
| **合计** | **11** | **3** | **0** |

> ET-030~ET-032（浏览器交互）需要 `E2E_UI_TESTS=1` 且本地服务运行，当前 CI 环境下正常跳过。  
> ET-smoke（服务可达性）通过。

---

## 单元测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| UT-030 | `test_qc_video_passes_valid_mp4` | ✅ PASS |
| UT-031 | `test_qc_video_rejects_too_small` | ✅ PASS |
| UT-032 | `test_qc_video_rejects_wrong_duration` | ✅ PASS |
| UT-033 | `test_parse_mp4_duration_returns_correct_seconds` | ✅ PASS |
| UT-034 | `test_generate_video_blocked_without_keyframe` | ✅ PASS |
| UT-035 | `test_generate_video_writes_entry_and_returns_workflow` | ✅ PASS |

---

## 契约测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| CT-030 | `test_video_generate_without_keyframe_returns_423` | ✅ PASS |
| CT-031 | `test_ping_unreachable_without_config` | ✅ PASS |
| CT-032 | `test_video_generate_returns_202_with_workflow` | ✅ PASS |
| CT-033 | `test_select_video_updates_workflow` | ✅ PASS |

---

## E2E 测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| ET-smoke | `test_service_is_reachable` | ✅ PASS |
| ET-030 | `test_shots_stage_shows_video_entries` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-031 | `test_video_generate_button_disabled_without_keyframe` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-032 | `test_ping_button_shows_result` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |

---

## 实施变更摘要

### service.py

- 新增静态方法 `_parse_mp4_duration(video_bytes: bytes) -> float`：解析 mvhd box，支持 version 0（timescale @ j+20, duration @ j+24）和 version 1（timescale @ j+28, duration @ j+32）
- 新增静态方法 `_qc_video(video_bytes: bytes, duration_requested: int) -> tuple[bool, dict]`：校验 ftyp magic bytes、文件大小（100KB–200MB）、实际时长（±2s 容差）
- 新增方法 `generate_shot_video(project_id, shot_id, duration=5)`：前置检查 `selected_keyframe` 非空（R-040），调用 `video_provider.generate_video`，写入 `shot-references.json` v4 格式（`video_entries` 列表），费用 `round(duration * 0.8, 2)` 元/秒
- 新增方法 `select_shot_video(project_id, shot_id, path)`：验证 path 存在于 `video_entries`，写入 `selected_video` 字段
- 新增方法 `ping_video_provider()`：返回 `{provider, reachable, model, latency_ms, error}`；`SEEDANCE_BASE_URL` 未配置时直接返回 `reachable=false`
- 修改 `get_project_workflow` shots 数据构建：新增 `video_entries`（含 `is_selected`）和 `selected_video` 字段
- 修改 shots stage data：补充 `"shots": shots` 键，使前端和测试可直接访问 `stage["data"]["shots"]`
- 修改视频费用计算：`cost_yuan = round(duration * 0.8, 2)`（¥0.8/秒）

### apps/mv_api/\_\_init\_\_.py

- 新增 Pydantic 模型 `ShotVideoGenerateRequest(duration: int = 5)`、`ShotVideoSelectionRequest(path: str)`
- 新增路由 `POST /api/v1/projects/{project_id}/shots/{shot_id}/video/generate` → 202 / 423
- 新增路由 `PUT /api/v1/projects/{project_id}/shots/{shot_id}/videos/selection` → 200
- 新增路由 `POST /api/v1/settings/video-provider/ping` → 200

### apps/mv_api/static/app.js

- 新增 `renderShots(stage)`：展示每镜 `video_entries`（时长、分辨率、费用、QC 状态、已选标记）、生成按钮（无 `selected_keyframe` 时禁用）、全部镜头选定后出现批量确认按钮
- 新增 ping 按钮事件监听：`video-ping-btn` 点击后调用 `/api/v1/settings/video-provider/ping`，将结果写入 `video-ping-result`
- 视频费用提示更新：`(5*0.8).toFixed(2)` 元/5 秒

### apps/mv_api/static/index.html

- 计费说明更新：`视频 ¥0.8/秒`
- settings dialog video fieldset 新增 ping 按钮与结果 span

---

## 回归验证

PRD-001 + PRD-002 + PRD-003 测试（36 个）在本次改动后全部通过，全套测试结果：

```
285 passed, 13 skipped, 0 failed
```

---

## 验收结论

- ✅ UT-030 ～ UT-035 全部通过（含 QC、时长解析、前置条件、mock provider 生成）
- ✅ CT-030 ～ CT-033 全部通过（无首帧 423、ping 无配置、生成 202、选定更新 workflow）
- ✅ ET-030 ～ ET-032 按规格跳过（需要浏览器环境）
- ✅ PRD-001 + PRD-002 + PRD-003 回归 0 failures
- ✅ `shot-references.json` 升级至 v4，新增 `video_entries` 列表与 `selected_video` 字段
- ✅ `generate_shot_video` 前置条件：`selected_keyframe` 非空（R-040），不满足返回 423 + `error_stage=precondition`
- ✅ `_qc_video` 校验 magic bytes / 文件大小 / 实际时长（R-042）
- ✅ `ping_video_provider` 无配置时返回 `reachable=false`（R-043）
- ✅ `select_shot_video` 写入 `selected_video`，workflow `is_selected` 字段正确（R-044）
- ✅ 视频费用统一为 ¥0.8/秒（R-045），前端与后端一致
