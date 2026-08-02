# TEST REPORT · PRD-007B Scene Groups Background Refactor

**Date**: 2026-08-02  
**Result**: PASS — 309 passed, 0 failed

---

## New Tests Added

### Unit tests (`tests/mv_platform/unit/test_prd007b_scene_groups.py`)

| ID | Test | Result |
|----|------|--------|
| UT-080 | `test_suggest_scene_groups_returns_groups` — LLM suggest writes draft + returns groups | PASS |
| UT-081 | `test_approve_fails_if_uncategorized_shots_exist` — approve raises ApplicationBlocked when shots unassigned | PASS |
| UT-082 | `test_approve_scene_planning_sets_stage_approved` — approve sets status, writes scene-groups.json, shot-references.json | PASS |
| UT-083 | `test_select_background_master_auto_updates_shots` — select writes background_master_id to all shots in group | PASS |
| UT-084 | `test_set_shot_background_override_sets_value` — override_path stored in shot-references.json | PASS |
| UT-085 | `test_set_shot_background_override_clears_value` — override_path set to None | PASS |
| UT-086 | `test_get_scene_planning_returns_not_started_initially` — returns not_started when no file | PASS |

### Contract tests (`tests/mv_platform/contract/test_prd007b_api.py`)

| ID | Test | Result |
|----|------|--------|
| CT-080 | `GET /api/v1/projects/{id}/scene-planning` → `{status: not_started, groups: []}` | PASS |
| CT-081 | `PUT /api/v1/projects/{id}/scene-planning` action=update_groups → persists groups | PASS |
| CT-082 | `POST /api/v1/projects/{id}/scene-planning/approve` → `{status: approved, groups: 1}` | PASS |
| CT-083 | `POST /api/v1/projects/{id}/groups/{gid}/background/select` → auto-updates shots | PASS |
| CT-084 | `PUT /api/v1/projects/{id}/shots/{sid}/background-override` set + clear | PASS |

---

## Existing Tests Updated

| File | Change |
|------|--------|
| `tests/mv_platform/contract/test_prd002_api.py::test_workflow_has_scenes_stage_between_storyboard_and_keyframes` | Updated: `scene_planning` now sits between `storyboard` and `scenes` |
| `tests/mv_platform/unit/test_application.py::test_project_workflow_surfaces_storyboard_and_requires_explicit_user_gates` | Updated: stage count 9 → 10 |

---

## Implementation Summary

### New files
- `tests/mv_platform/unit/test_prd007b_scene_groups.py`
- `tests/mv_platform/contract/test_prd007b_api.py`

### Modified files

**`mv_platform/application/service.py`**
- Added `_scene_planning(root)` / `_write_scene_planning(root, value)` helpers (near line 352)
- Added `_DEFAULT_SCENE_GROUP_SYSTEM_PROMPT` class attribute
- Added `suggest_scene_groups_llm(project_id, system_prompt, task_prompt)` — LLM-based suggest, writes `creative/scene-planning.json`
- Added `get_scene_planning(project_id)` — read current planning state
- Added `update_scene_planning(project_id, payload)` — supports `update_groups` and `regenerate_suggestion` actions
- Added `approve_scene_planning(project_id)` — validates full coverage, propagates to `shot-references.json` and `scene-groups.json`
- Added `submit_generate_group_background_job(project_id, group_id)` — submits 2 background jobs for a scene group
- Added `set_shot_background_override(project_id, shot_id, override_path)` — per-shot background override
- Updated `select_background_master` — now auto-updates `background_master_id` on all shots in the group (backward-compatible)
- Updated `get_project_workflow` — added `scene_planning` stage between `storyboard` and `scenes`; `scenes` now unlocks after `scene_planning_approved`

**`apps/mv_api/__init__.py`**
- Added `ScenePlanningSuggestRequest`, `ScenePlanningUpdateRequest`, `SelectMasterRequest`, `BackgroundOverrideRequest` Pydantic models
- Added 7 new API routes: GET/POST/PUT scene-planning, POST approve, POST generate, POST select, PUT background-override
