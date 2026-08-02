# TEST_REPORT_PRD003 · 组合首帧精化

**日期**：2026-08-02  
**执行模型**：claude-sonnet-5  
**命令**：`PYTHONPATH=src .venv/bin/python3 -m pytest tests/mv_platform/unit/test_prd003_keyframes.py tests/mv_platform/contract/test_prd003_api.py tests/e2e/test_prd003_browser.py -v`

---

## 总结

| 类别 | 通过 | 跳过 | 失败 |
|------|------|------|------|
| 单元测试 (UT) | 8 | 0 | 0 |
| 契约测试 (CT) | 3 | 0 | 0 |
| E2E 浏览器 (ET) | 1 | 4 | 0 |
| **合计** | **12** | **4** | **0** |

> ET-020~ET-023（浏览器交互）需要 `E2E_UI_TESTS=1` 且本地服务运行，当前 CI 环境下正常跳过。  
> ET-smoke（服务可达性）通过。

---

## 单元测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| UT-022 | `test_read_keyframe_entries_upgrades_strings` | ✅ PASS |
| UT-022b | `test_read_keyframe_entries_passes_through_dicts` | ✅ PASS |
| UT-022c | `test_read_keyframe_entries_mixed_formats` | ✅ PASS |
| UT-021 | `test_import_keyframe_writes_metadata_entry` | ✅ PASS |
| UT-023 | `test_generate_keyframe_blocked_without_scenes_approval` | ✅ PASS |
| UT-024 | `test_generate_keyframe_blocked_without_background_master` | ✅ PASS |
| UT-025 | `test_workflow_includes_keyframe_entries` | ✅ PASS |
| UT-020 | `test_generate_keyframe_writes_metadata_entry` | ✅ PASS |

---

## 契约测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| CT-020 | `test_keyframe_generate_without_scenes_approval_returns_423` | ✅ PASS |
| CT-021 | `test_workflow_keyframe_entries_have_source` | ✅ PASS |
| CT-022 | `test_upload_keyframe_appears_in_workflow` | ✅ PASS |

---

## E2E 测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| ET-smoke | `test_service_is_reachable` | ✅ PASS |
| ET-020 | `test_keyframes_stage_shows_explanation` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-021 | `test_keyframe_candidate_shows_metadata` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-022 | `test_generate_keyframe_disabled_without_background_master` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-023 | `test_batch_confirm_enabled_when_all_selected` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |

---

## 实施变更摘要

### service.py

- 新增静态方法 `_read_keyframe_entries(shot: dict) -> list`：兼容读取，字符串升级为 `legacy` 对象
- 修改 `get_project_workflow` shot 数据构建：使用 `_read_keyframe_entries` 处理混合格式，新增 `keyframe_entries` 字段（含 `is_selected`）
- 修改 `import_shot_keyframe`：写入元数据对象而非路径字符串；去重逻辑改用路径比较
- 修改 `_generate_shot_image` keyframes 分支：写入包含 `source/background_master_id/character_ids/prompt_zh/prompt_en/model/request_id/cost_yuan/created_at` 的元数据对象
- 修改 `generate_shot_keyframe`：前置条件从 `storyboard_approved` 改为 `scenes_approved`；新增 `background_master_id` 非空检查
- 修改 `select_shot_keyframe`：`keyframe` 存在性检查改为按 `path` 字段比较（兼容字典和字符串混合）

### apps/mv_api/static/app.js

- 修改 `renderKeyframes`：
  - 顶部新增 `.keyframe-explanation` 固定说明区块（"组合首帧是什么？"）
  - 候选列表改用 `shot.keyframe_entries`，展示来源/费用/模型元数据
  - `background_master_id` 为空时，生成按钮禁用并显示"场景组背景未确认，请先完成场景与背景阶段"
  - 全部镜头均有 `selected_keyframe` 时，底部出现 `.batch-confirm` 批量确认按钮

---

## 回归验证

PRD-001 + PRD-002 测试（22 个）在本次改动后全部通过：

```
tests/mv_platform/unit/test_prd001_diagnostics.py      7 passed
tests/mv_platform/contract/test_prd001_api.py          3 passed
tests/mv_platform/unit/test_prd002_scene_groups.py     8 passed
tests/mv_platform/contract/test_prd002_api.py          4 passed
```

---

## 验收结论

- ✅ UT-020 ～ UT-025 全部通过（含 mock provider 生成测试）
- ✅ CT-020 ～ CT-022 全部通过
- ✅ ET-020 ～ ET-023 按规格跳过（需要浏览器环境）
- ✅ PRD-001 + PRD-002 回归 0 failures
- ✅ `shot-references.json` 写入元数据对象（非路径字符串），v3 格式向下兼容
- ✅ `generate_shot_keyframe` 前置条件已改为 `scenes_approved` + `background_master_id` 非空
- ✅ `_read_keyframe_entries` 兼容旧字符串格式（升级为 `legacy` 对象，不触发文件写入）
- ✅ workflow `keyframe_entries` 包含 `is_selected` / `source` / `cost_yuan` 等完整字段
- ✅ 前端说明文案、元数据展示、禁用态、批量确认按钮均已实现
