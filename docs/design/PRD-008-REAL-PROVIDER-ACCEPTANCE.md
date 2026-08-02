# PRD-008：真实 Provider 全链路验收（配置化执行）

> **状态**：待实施  
> **优先级**：P4  
> **前置条件**：PRD-006 验收通过（全链路测试脚本已就绪），用户已在设置页面完成所有 Provider 配置  
> **负责模型**：claude-haiku-4-5 执行，Opus 复查  
> **解锁**：生产发布

---

## 1. 背景与问题陈述

### 1.1 当前状态

PRD-006 已交付全链路测试脚本（`tests/e2e/test_prd006_full_chain.py`），
但 FC-001～FC-004 在 CI 环境中因缺少真实 Provider 凭据而被跳过。

本 PRD 的目标是：**当用户在设置页面配置好所有凭据后**，
让 claude-haiku-4-5 能够按照本文档的步骤逐步执行验收，无需任何人工干预或额外判断。

### 1.2 前置配置检查清单

执行本 PRD 前，确认以下配置均已在服务页面或 `.env` 中完成：

| 配置项 | 必填 | 说明 |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | GPT-image-2 调用密钥（`sk-...`） |
| `SEEDANCE_BASE_URL` | ✅ | Seedance 2.0 API 地址（`https://...`） |
| `SEEDANCE_MODEL` | ✅ | 默认 `seedance-2.0` |
| `SEEDANCE_API_KEY` | 视配置而定 | 若 Seedance 需要独立 key |
| `E2E_FULL_CHAIN` | ✅ | 必须设为 `1`（启用全链路测试） |
| 项目"青衣"（slug `qingyi`） | ✅ | 本地服务上已存在，workflow 已推进到 scenes 阶段 |
| `mv_api` 服务运行 | ✅ | `uvicorn apps.mv_api:create_app --factory --port 8792` |

---

## 2. 目标与非目标

### 目标

1. claude-haiku-4-5 能够无人工干预地执行全链路验收
2. 验收步骤极其明确：每一步给出完整命令、期望 HTTP 状态码、期望响应字段
3. 每步执行后给出明确的 PASS / FAIL 判断标准
4. 输出结构化测试报告 `TEST_REPORT_PRD008.md`
5. 覆盖 FC-001（背景生成）、FC-002（首帧生成）、FC-003（SSE 事件流）、FC-004（视频生成）

### 非目标

- 不修改业务代码
- 不修改已有测试脚本（以 PRD-006 脚本为准）
- 不实现自动重试失败用例（失败则记录并继续）
- 不验证生成图片的视觉质量（只验证 HTTP 状态和 JSON 结构）

---

## 3. 执行环境规格

### 3.1 服务启动（haiku-4-5 执行前验证）

```bash
# Step 0-A: 确认服务运行
curl -s http://127.0.0.1:8792/readyz
# 期望：HTTP 200，body 包含 "ready"
# FAIL 条件：连接拒绝或 HTTP ≠ 200 → 停止执行，提示用户启动服务
```

```bash
# Step 0-B: 确认项目青衣存在
curl -s http://127.0.0.1:8792/api/v1/projects
# 期望：HTTP 200，返回列表中至少一项 slug="qingyi" 或 brief.title 包含 "青衣"
# FAIL 条件：列表为空或未找到匹配项 → 停止执行，提示用户创建项目
```

```bash
# Step 0-C: 确认环境变量就绪
python3 -c "
import os, sys
missing = [k for k in ('OPENAI_API_KEY','SEEDANCE_BASE_URL','E2E_FULL_CHAIN')
           if not os.environ.get(k)]
if missing:
    print('MISSING:', missing); sys.exit(1)
print('ALL ENV OK')
"
# 期望：输出 "ALL ENV OK"
# FAIL 条件：输出 MISSING → 停止执行，列出缺失变量
```

### 3.2 pytest 执行命令

```bash
# 全链路执行命令（含所有 FC 用例）
PYTHONPATH=. \
OPENAI_API_KEY="$OPENAI_API_KEY" \
SEEDANCE_BASE_URL="$SEEDANCE_BASE_URL" \
SEEDANCE_MODEL="${SEEDANCE_MODEL:-seedance-2.0}" \
E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py -v \
    --timeout=300 \
    --tb=short \
    2>&1 | tee /tmp/prd008_run.log
```

---

## 4. 验收步骤规格（逐步执行）

### Step 1: 环境预检（FC-PRE）

```bash
PYTHONPATH=. .venv/bin/python3 - <<'EOF'
import urllib.request, json, os

def check(label, condition, detail=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status}  {label}" + (f"  [{detail}]" if detail else ""))
    return condition

BASE = "http://127.0.0.1:8792"

# 服务可达
try:
    with urllib.request.urlopen(f"{BASE}/readyz", timeout=5) as r:
        ok = r.status == 200
except Exception as e:
    ok = False
check("服务可达 /readyz", ok)

# 项目青衣存在
try:
    with urllib.request.urlopen(f"{BASE}/api/v1/projects", timeout=5) as r:
        projects = json.loads(r.read())
    if isinstance(projects, dict):
        projects = projects.get("projects", [])
    found = any("qingyi" in p.get("slug","") or "青衣" in p.get("brief",{}).get("title","")
                for p in projects)
except Exception:
    found = False
check("项目青衣存在", found)

# 环境变量
for k in ("OPENAI_API_KEY", "SEEDANCE_BASE_URL", "E2E_FULL_CHAIN"):
    check(f"环境变量 {k}", bool(os.environ.get(k)), os.environ.get(k,"(未设置")[:20])
EOF
```

**期望输出**：所有行为 `✅ PASS`。任何 `❌ FAIL` → 停止，修复后重新执行。

---

### Step 2: FC-001 背景生成（真实 GPT-image-2）

**自动化执行**：

```bash
PYTHONPATH=. E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py::test_full_chain_background_generation \
    -v --timeout=180 -s
```

**期望**：

```
PASSED tests/e2e/test_prd006_full_chain.py::test_full_chain_background_generation
```

**PASS 判断标准**：
- `POST .../background/generate` 返回 HTTP 202
- 响应 body 含 `job_id`（非空字符串）
- 轮询 `GET /api/v1/jobs/{job_id}/inspect`，最终 `runtime_state == "succeeded"`（120s 内）
- `GET /api/v1/projects/{project_id}/workflow` 中对应 shot 的 `background` 或 `background_master_id` 字段非空

**FAIL 条件**：
- 202 以外的状态码（如 423：前置条件不满足，需先推进 workflow 到 backgrounds 阶段）
- job_id 为空
- 120s 内未到达 succeeded 状态
- 超时或 OpenAI 返回错误

---

### Step 3: FC-002 首帧生成（真实 GPT-image-2）

**自动化执行**：

```bash
PYTHONPATH=. E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py::test_full_chain_keyframe_generation \
    -v --timeout=200 -s
```

**期望**：

```
PASSED tests/e2e/test_prd006_full_chain.py::test_full_chain_keyframe_generation
```

**PASS 判断标准**：
- `POST .../keyframes/generate` 返回 HTTP 202
- 响应 body 含 `job_id`
- 轮询至 `runtime_state == "succeeded"`（180s 内）

**常见 FAIL 原因**：
- HTTP 423：场景组的 `background_master_id` 未设置 → 需先完成 FC-001
- 首帧生成依赖背景已存在，若 FC-001 跳过则此处会 skip

---

### Step 4: FC-003 SSE 事件流验证

**自动化执行**：

```bash
PYTHONPATH=. E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py::test_full_chain_sse_events_for_completed_job \
    -v --timeout=200 -s
```

**期望**：

```
PASSED tests/e2e/test_prd006_full_chain.py::test_full_chain_sse_events_for_completed_job
```

**PASS 判断标准**：
- `GET /api/v1/jobs/{job_id}/events` 返回 `text/event-stream`
- 响应体包含 `event: progress`
- 响应体包含 `event: done` 或 `event: error`

**手动验证补充**（haiku-4-5 执行）：

```bash
# 找一个已完成的 job_id（从 Step 2 的输出中提取）
JOB_ID="<从 FC-001 输出中提取的 job_id>"
curl -s "http://127.0.0.1:8792/api/v1/jobs/${JOB_ID}/events" | head -20
# 期望输出包含 "event: progress" 和 "event: done"
```

---

### Step 5: FC-004 视频生成（真实 Seedance 2.0）

**自动化执行**：

```bash
PYTHONPATH=. E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py::test_full_chain_video_generation \
    -v --timeout=400 -s
```

**期望**：

```
PASSED tests/e2e/test_prd006_full_chain.py::test_full_chain_video_generation
```

**PASS 判断标准**：
- `POST .../video/generate` 返回 HTTP 202
- 轮询 workflow，对应 shot 的 `video_entries` 列表长度 ≥ 1（360s 内）
- `video_entries[0]` 含 `path` 字段，文件存在于本地磁盘

**常见 FAIL 原因**：
- `SEEDANCE_BASE_URL` 未配置或无法访问
- 该 shot 没有 `selected_keyframe` → 需先完成 FC-002

---

### Step 6: 全量一键执行（推荐）

所有步骤正常后，使用以下命令一键运行：

```bash
PYTHONPATH=. \
OPENAI_API_KEY="$OPENAI_API_KEY" \
SEEDANCE_BASE_URL="$SEEDANCE_BASE_URL" \
SEEDANCE_MODEL="${SEEDANCE_MODEL:-seedance-2.0}" \
E2E_FULL_CHAIN=1 \
.venv/bin/python3 -m pytest tests/e2e/test_prd006_full_chain.py -v \
    --timeout=400 \
    --tb=short \
    -p no:randomly \
    2>&1 | tee /tmp/prd008_full_run.log

echo "---"
echo "测试结果摘要："
grep -E "passed|failed|error|PASSED|FAILED|ERROR" /tmp/prd008_full_run.log | tail -5
```

---

## 5. 回归验收

全链路测试结束后，执行完整回归确保无破坏：

```bash
PYTHONPATH=. .venv/bin/python3 -m pytest \
    tests/mv_platform/unit/ \
    tests/mv_platform/contract/ \
    -v --timeout=60 \
    2>&1 | tee /tmp/prd008_regression.log

echo "---"
echo "回归结果："
tail -3 /tmp/prd008_regression.log
```

**期望**：`X passed, Y skipped, 0 failed`（X ≥ 142）

---

## 6. 测试报告模板（haiku-4-5 填写后输出）

haiku-4-5 执行完成后，按以下模板填写并写入 `TEST_REPORT_PRD008.md`：

```markdown
# TEST_REPORT_PRD008 · 真实 Provider 全链路验收

**日期**：YYYY-MM-DD  
**执行模型**：claude-haiku-4-5  
**服务地址**：http://127.0.0.1:8792  

---

## 总结

| 测试 | 结果 | 耗时 |
|------|------|------|
| FC-PRE | ✅ PASS / ❌ FAIL | Ns |
| FC-001 背景生成 | ✅ PASS / ❌ FAIL / ⏭ SKIP | Ns |
| FC-002 首帧生成 | ✅ PASS / ❌ FAIL / ⏭ SKIP | Ns |
| FC-003 SSE 事件流 | ✅ PASS / ❌ FAIL / ⏭ SKIP | Ns |
| FC-004 视频生成 | ✅ PASS / ❌ FAIL / ⏭ SKIP | Ns |
| **回归（PRD-001~007B）** | ✅ PASS / ❌ FAIL | Ns |

---

## FC-001 详情

- job_id：`xxx`
- 最终状态：succeeded / failed
- 耗时：Ns
- background_master_id：`xxx`（成功时）
- 失败原因：（如适用）

## FC-002 详情

...

## FC-003 详情

- events 流前 3 行：
  ```
  event: progress
  data: {...}
  
  event: done
  data: {...}
  ```

## FC-004 详情

...

---

## 回归验证

```
X passed, Y skipped, 0 failed
```

---

## 验收结论

- ✅ / ❌ FC-001：背景生成
- ✅ / ❌ FC-002：首帧生成  
- ✅ / ❌ FC-003：SSE 事件流
- ✅ / ❌ FC-004：视频生成
- ✅ / ❌ 回归 0 failures
```

---

## 7. 常见问题排查

| 症状 | 原因 | 解决方法 |
|---|---|---|
| FC-001 返回 423 | story/storyboard 未审批，或 scene_groups 未配置 | 在 UI 推进 workflow 到 backgrounds 阶段 |
| FC-002 返回 423 | background_master_id 未设置 | 先完成 FC-001，或手动选定背景 master |
| FC-004 返回 423 | selected_keyframe 未设置 | 先完成 FC-002，或手动选定首帧 |
| job 停在 queued | 后台执行器未启动 | 确认 `asyncio.ensure_future` 正常工作；检查服务日志 |
| OpenAI 返回 429 | 速率限制 | 等待 60s 后重试 |
| Seedance 连接超时 | `SEEDANCE_BASE_URL` 无法访问 | 检查网络和配置值 |
| SSE 事件流返回空 | job 未完成时读取 events | 等待 job succeeded 后再读 events |

---

## 8. 验收标准

- [ ] FC-PRE：所有环境变量和服务检查通过
- [ ] FC-001：背景生成 job 达到 succeeded，background_master_id 写入
- [ ] FC-002：首帧生成 job 达到 succeeded
- [ ] FC-003：SSE 流包含 `event: progress` 和 `event: done`/`event: error`
- [ ] FC-004：视频生成 job 完成，video_entries 写入 workflow
- [ ] 回归：全套单元+契约测试 0 failures（142+ passed）
- [ ] `TEST_REPORT_PRD008.md` 已写入项目根目录
