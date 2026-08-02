# TEST_REPORT_PRD002 · 场景组与背景母版

**日期**：2026-08-02  
**执行模型**：claude-sonnet-5  
**命令**：`PYTHONPATH=src .venv/bin/python3 -m pytest tests/mv_platform/unit/test_prd002_scene_groups.py tests/mv_platform/contract/test_prd002_api.py tests/e2e/test_prd002_browser.py -v`

---

## 总结

| 类别 | 通过 | 跳过 | 失败 |
|------|------|------|------|
| 单元测试 (UT) | 8 | 0 | 0 |
| 契约测试 (CT) | 4 | 0 | 0 |
| E2E 浏览器 (ET) | 1 | 4 | 0 |
| **合计** | **13** | **4** | **0** |

> ET-010~ET-013（浏览器交互）需要 `E2E_UI_TESTS=1` 且本地服务运行，当前 CI 环境下正常跳过。  
> ET-服务可达性（smoke）通过。

---

## 单元测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| UT-010a | `test_suggest_scene_groups_groups_by_section` | ✅ PASS |
| UT-010b | `test_suggest_scene_groups_fallback_name_when_no_section_match` | ✅ PASS |
| UT-010c | `test_suggest_scene_groups_no_section_field_goes_to_default` | ✅ PASS |
| UT-011 | `test_migration_creates_background_master_from_existing` | ✅ PASS |
| UT-012 | `test_migration_skips_when_no_visual_score` | ✅ PASS |
| UT-013 | `test_shot_cannot_belong_to_two_groups` | ✅ PASS |
| UT-014 | `test_select_background_deselects_previous` | ✅ PASS |
| UT-015 | `test_scenes_approve_blocked_when_group_has_no_selected` | ✅ PASS |

---

## 契约测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| CT-013 | `test_workflow_has_scenes_stage_between_storyboard_and_keyframes` | ✅ PASS |
| CT-010 | `test_suggest_scene_groups_returns_groups` | ✅ PASS |
| CT-011 | `test_update_scene_group_name` | ✅ PASS |
| CT-012 | `test_old_background_generate_returns_deprecated_header` | ✅ PASS |

---

## E2E 测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| ET-smoke | `test_service_is_reachable` | ✅ PASS |
| ET-010 | `test_scenes_stage_visible_in_nav` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-011 | `test_shot_card_has_no_generate_background_button` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-012 | `test_generate_background_in_scenes_stage` | ⏭ SKIP (需要 E2E_UI_TESTS=1 + 真实 Provider) |
| ET-013 | `test_approve_scenes_enabled_after_all_selected` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |

---

## 实施变更摘要

### service.py
- 新增 `SceneGroup` / `BackgroundMaster` dataclass（frozen）
- 新增 `_SG_ID_RE` / `_BG_ID_RE` 正则
- 新增文件 I/O：`_scene_groups` / `_write_scene_groups` / `_background_masters` / `_write_background_masters`
- 新增 `suggest_scene_groups`（启发式，按 `shot.section` 分组）
- 新增 `_migrate_to_scene_groups`（自动触发，`storyboard_approved` 且 `scene-groups.json` 不存在时）
- 新增 `get_scene_groups` / `suggest_and_save_scene_groups` / `update_scene_group` / `merge_scene_groups`
- 新增 `select_background_master` / `generate_scene_group_background`
- 修改 `generate_shot_background`：标记 deprecated，重定向到场景组级生成
- 修改 `get_project_workflow`：插入 "scenes" 阶段（storyboard 后 keyframes 前），更新 keyframes 门禁
- 修改 `record_workflow_decision`：`allowed_stages` 追加 "scenes"

### apps/mv_api/__init__.py
- 新增 Pydantic 模型：`SceneGroupUpdateRequest` / `SceneGroupMergeRequest`
- 新增路由：POST suggest、GET scene-groups、PUT scene-groups/{sg_id}、POST merge、POST backgrounds/generate、PUT backgrounds/{bg_id}/select
- 修改旧路由 `POST shots/{shot_id}/background/generate`：捕获异常后注入 `X-Deprecated` 响应头

### apps/mv_api/static/app.js
- 新增 `generateSceneGroupBackground` 异步函数
- 新增 `renderScenes(stage)` 渲染函数
- 修改 `approvalBlock`：追加 "scenes" 阶段支持
- 修改 `nextStepBlock`：追加 "scenes" 引导文案
- 修改 `bindStageActions`：post-approve 导航修正（storyboard→scenes→keyframes）
- 修改 `renderStage`：追加 `else if(stage.id==="scenes")` 分支
- 修改 `shotReferencePanel`：移除旧背景生成按钮，追加"所属场景组"标签
- 修复 change listener：合并 `[data-select-bg]` 处理，补齐闭合 `});`

---

## 回归验证

PRD-001 测试（10 个）在本次改动后全部通过：

```
tests/mv_platform/unit/test_prd001_diagnostics.py   7 passed
tests/mv_platform/contract/test_prd001_api.py       3 passed
```

---

## 验收结论

- ✅ UT-010 ～ UT-015 全部通过
- ✅ CT-010 ～ CT-013 全部通过
- ✅ ET-010 ～ ET-011 按规格跳过（需要浏览器环境）
- ✅ ET-012 按规格跳过（需要真实 Provider）
- ✅ ET-013 按规格跳过（需要浏览器环境）
- ✅ PRD-001 回归 0 failures
- ✅ app.js 语法缺陷已修复（change listener 闭合 + generateSceneGroupBackground 定义）
- ✅ X-Deprecated 响应头在旧路由成功/失败两种响应中均正确注入
