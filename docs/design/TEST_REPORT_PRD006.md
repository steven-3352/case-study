# TEST_REPORT_PRD006 · 全链路验收（真实 Provider）

**日期**：2026-08-02  
**执行模型**：claude-sonnet-5  
**命令**：`PYTHONPATH=. .venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py -v`

---

## 总结

| 类别 | 通过 | 跳过 | 失败 |
|------|------|------|------|
| E2E 全链路 (FC) | 2 | 4 | 0 |
| **合计** | **2** | **4** | **0** |

> FC-001~FC-004（真实 Provider 调用）需要 `E2E_FULL_CHAIN=1`、`OPENAI_API_KEY` 和 `SEEDANCE_BASE_URL` 同时配置，当前 CI 环境下正常跳过。  
> FC-000（项目青衣存在性检查）与 smoke（服务可达性）通过。

---

## 测试明细

| 测试 ID | 测试名称 | 结果 |
|---------|----------|------|
| smoke | `test_service_is_reachable` | ✅ PASS |
| FC-000 | `test_project_qingyi_exists_or_skip` | ✅ PASS |
| FC-001 | `test_full_chain_background_generation` | ⏭ SKIP (需要 E2E_FULL_CHAIN=1 + OPENAI_API_KEY + SEEDANCE_BASE_URL) |
| FC-002 | `test_full_chain_keyframe_generation` | ⏭ SKIP (需要 E2E_FULL_CHAIN=1 + OPENAI_API_KEY + SEEDANCE_BASE_URL) |
| FC-003 | `test_full_chain_sse_events_for_completed_job` | ⏭ SKIP (需要 E2E_FULL_CHAIN=1 + OPENAI_API_KEY + SEEDANCE_BASE_URL) |
| FC-004 | `test_full_chain_video_generation` | ⏭ SKIP (需要 E2E_FULL_CHAIN=1 + OPENAI_API_KEY + SEEDANCE_BASE_URL) |

---

## PRD-006 范围说明

PRD-006 不涉及代码变更，只包含测试脚本和验收流程。完整全链路验收需要：

1. 本地 `mv_api` 服务运行（`uvicorn apps.mv_api:create_app --factory --port 8792`）
2. 项目青衣（slug `qingyi`）已在服务中创建并推进到所需阶段
3. 配置环境变量：
   ```bash
   export OPENAI_API_KEY=sk-...
   export SEEDANCE_BASE_URL=https://...
   export SEEDANCE_MODEL=seedance-2.0
   export E2E_FULL_CHAIN=1
   ```
4. 执行：`PYTHONPATH=. .venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py -v`

---

## 全链路测试覆盖范围

| 测试 | 验收内容 |
|------|----------|
| FC-001 | 提交背景生成 job → 真实 GPT-image-2 执行 → job succeeded → background_master 写入 |
| FC-002 | 提交首帧生成 job → 真实 GPT-image-2 执行 → job succeeded → keyframes 写入 |
| FC-003 | GET /jobs/{job_id}/events → SSE 流包含 `event: progress` + `event: done`/`error` |
| FC-004 | 提交视频生成 job → 真实 Seedance 2.0 执行 → job succeeded → video_entries 写入 |

---

## 回归验证

PRD-001 ~ PRD-005 测试在 PRD-006 文件新增后全部通过：

```
142 passed, 20 skipped, 0 failed
```

---

## 验收结论

- ✅ smoke：服务可达，/readyz 返回 200
- ✅ FC-000：project 青衣在服务上存在，workflow 端点返回有效数据
- ✅ FC-001~FC-004：按规格跳过（需要真实 Provider 凭据 + E2E_FULL_CHAIN=1）
- ✅ PRD-001 ~ PRD-005 回归 0 failures
- ✅ 全链路测试脚本已就绪，配置凭据后即可执行真实 Provider 验收
