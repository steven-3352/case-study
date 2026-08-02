# TEST_REPORT_PRD005 · SSE 流式进度推送

**日期**：2026-08-02  
**执行模型**：claude-sonnet-5  
**命令**：`PYTHONPATH=. .venv/bin/python3 -m pytest tests/mv_platform/unit/test_prd005_sse.py tests/mv_platform/contract/test_prd005_api.py tests/e2e/test_prd005_browser.py -v`

---

## 总结

| 类别 | 通过 | 跳过 | 失败 |
|------|------|------|------|
| 单元测试 (UT) | 5 | 0 | 0 |
| 契约测试 (CT) | 4 | 0 | 0 |
| E2E 浏览器 (ET) | 1 | 3 | 0 |
| **合计** | **10** | **3** | **0** |

> ET-041~ET-043（浏览器交互）需要 `E2E_UI_TESTS=1` 且本地服务运行，当前 CI 环境下正常跳过。  
> ET-smoke（服务可达性）通过。

---

## 单元测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| UT-040 | `test_submit_background_job_returns_job_id` | ✅ PASS |
| UT-041 | `test_background_job_emits_progress_events` | ✅ PASS |
| UT-042 | `test_background_job_emits_error_on_translate_fail` | ✅ PASS |
| UT-043 | `test_workflow_active_jobs_while_queued` | ✅ PASS |
| UT-044 | `test_workflow_no_active_jobs_after_done` | ✅ PASS |

---

## 契约测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| CT-040 | `test_background_generate_without_approval_returns_423` | ✅ PASS |
| CT-041 | `test_background_generate_returns_202_with_job_id` | ✅ PASS |
| CT-042 | `test_keyframe_generate_without_scenes_approval_returns_423` | ✅ PASS |
| CT-043 | `test_keyframe_generate_returns_202_and_events_readable` | ✅ PASS |

---

## E2E 测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| ET-smoke | `test_service_is_reachable` | ✅ PASS |
| ET-041 | `test_background_generate_shows_async_progress` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-042 | `test_keyframe_generate_shows_async_progress` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |
| ET-043 | `test_sse_progress_steps_visible_in_ui` | ⏭ SKIP (需要 E2E_UI_TESTS=1) |

---

## 实施变更摘要

### mv_platform/domain/contracts.py

- `_OPS` 集合新增 `"generate_background"` 和 `"generate_keyframe"`，使 `JobSpec.operation` 可接受这两种操作类型

### mv_platform/application/service.py

- 新增 `_emit_mini_event(job_id, event_type, payload)` — 以 `BEGIN IMMEDIATE` 事务向 `events` 表追加 SSE 事件（严格单调 seq）
- 新增 `_set_mini_job_state(job_id, state)` — 更新 `job_status.runtime_state`
- 新增 `submit_generate_background_job(project_id, shot_id)` — 前置检查场景组归属 → 创建 `generate_background` mini-job → 返回 `{job_id, status: "queued"}`
- 新增 `submit_generate_keyframe_job(project_id, shot_id)` — 前置检查 scenes 批准 + `background_master_id` → 创建 `generate_keyframe` mini-job → 返回 `{job_id, status: "queued"}`
- 新增 `run_generate_background_job(job_id)` / `run_generate_keyframe_job(job_id)` — API 后台任务入口，从 `job.input_refs[0]` 取 `shot_id` 后调用对应 `_execute_*` 方法
- 新增 `_execute_background_job` / `_execute_keyframe_job` — 执行体：设置 running → emit progress × 2 → 调用业务方法 → emit done / emit error + set failed
- 新增 `_run_pending_jobs_sync()` — 测试辅助：同步跑完所有 queued 的 image-gen mini-job
- 新增 `_get_active_image_jobs(project_id)` — 返回 queued/running image-gen jobs 列表
- 修改 `get_project_workflow` — 返回字典新增 `"active_jobs"` 字段

### apps/mv_api/__init__.py

- `POST .../background/generate` — 改为调用 `submit_generate_background_job` 返回 202 + `X-Async: true` + `X-Deprecated`；后台异步触发 `run_generate_background_job`
- `POST .../keyframes/generate` — 改为调用 `submit_generate_keyframe_job` 返回 202；后台异步触发 `run_generate_keyframe_job`

### tests/mv_platform/contract/test_prd001_api.py（回归修复）

- CT-001 / CT-002 / CT-003 的 mock 目标从 `generate_shot_background` 更新为 `submit_generate_background_job`，与新路由一致

---

## 回归验证

PRD-001 + PRD-002 + PRD-003 + PRD-004 测试在本次改动后全部通过，全套测试结果：

```
142 passed, 20 skipped, 0 failed
```

---

## 验收结论

- ✅ UT-040：`submit_generate_background_job` 立即返回 `{job_id, status: "queued"}`
- ✅ UT-041：`_run_pending_jobs_sync` 成功后 events 表包含 `translate_prompt` / `generate_image` / `save_result` 三阶段 progress 及 done 事件
- ✅ UT-042：`generate_shot_background` 抛出 `error_stage="translate_prompt"` 时，error 事件携带正确 stage，且无 done 事件
- ✅ UT-043：job 提交后 workflow `active_jobs` 非空，包含 `shot_id` 和 `status` 字段
- ✅ UT-044：`_run_pending_jobs_sync` 完成后 workflow `active_jobs == []`
- ✅ CT-040：无 story 批准时 background/generate 返回 423
- ✅ CT-041：场景组就绪时 background/generate 返回 202 + `X-Async: true` + `job_id`
- ✅ CT-042：无 scenes 批准时 keyframes/generate 返回 423
- ✅ CT-043：scenes 就绪时 keyframes/generate 返回 202；`_run_pending_jobs_sync` 后 `GET /jobs/{job_id}/events` 返回含 `progress` 和 `done` 的 SSE 文本流
- ✅ PRD-001 ~ PRD-004 回归 0 failures
