# 实施总指令：PRD-001 ～ PRD-006

> **实施模型**：claude-sonnet-5  
> **验收模型**：Opus（读 TEST_REPORT 文件后给出 PASS / FAIL）  
> **工作目录**：`/Users/wmzuo/Documents/project/case-study`  
> **铁律**：不废弃现有代码，不重写，只追加/修改；所有用户可见文字保持中文；每个 Step 完成后立即跑对应测试，不批量攒着最后跑。

---

## 一、总执行顺序

```
PRD-001 → PRD-002 → PRD-003 → PRD-004 → PRD-005 → PRD-006
```

每个 PRD 必须满足**验收标准全部 ✓** 后才能进入下一个。
若某 PRD 有测试失败，**在当前 PRD 内修复**，不跨 PRD 打补丁。

---

## 二、开工前检查（每次启动时执行一次）

```bash
# 1. 服务是否运行
curl -s http://127.0.0.1:8792/readyz

# 2. 确认工作目录
cd /Users/wmzuo/Documents/project/case-study && git status

# 3. 确认 Python 环境
python -m pytest --version
playwright --version 2>/dev/null || echo "playwright not installed"
```

若服务未运行，先启动：
```bash
python apps/runtime.py &
sleep 3 && curl -s http://127.0.0.1:8792/readyz
```

---

## 三、PRD-001：诊断能力提升与图片生成修复

**PRD 路径**：`docs/design/PRD-001-DIAGNOSTICS-FIX.md`  
**前置条件**：无  

### 实施步骤

按 PRD-001 §8 实施顺序执行，每 Step 后运行对应测试：

| Step | 内容 | 测试命令 |
|---|---|---|
| 1 | 诊断稳定性（R-013），填写附录 A，不动代码 | 手动执行重启 3 次，记录结果 |
| 2 | 扩展 `ApplicationBlocked`（R-004 数据结构） | `pytest tests/mv_platform/unit/test_prd001_diagnostics.py -k "UT006 or UT007" -v` |
| 3 | 增强 `_translate_image_prompt` 错误日志（R-001/002/003） | `pytest tests/mv_platform/unit/test_prd001_diagnostics.py -k "UT001 or UT002 or UT003" -v` |
| 4 | 加翻译重试逻辑（R-006/007/008） | `pytest tests/mv_platform/unit/test_prd001_diagnostics.py -k "UT004 or UT005" -v` |
| 5 | 修改 API 错误响应格式（R-005） | `pytest tests/mv_platform/contract/test_prd001_api.py -v` |
| 6 | 前端阶段进度 + 重试按钮（R-009/010/011/012） | `pytest tests/e2e/test_prd001_browser.py -v` |
| 7 | 全量 | `pytest tests/ -v -k "prd001" --tb=short` |

### 报告命令

```bash
pytest tests/ -k "prd001" --tb=short -v 2>&1 | tee TEST_REPORT_PRD001.md
# 在文件头部插入摘要（见第五节报告格式）
```

---

## 四、PRD-002：场景组与背景母版

**PRD 路径**：`docs/design/PRD-002-SCENE-GROUPS-BACKGROUND-MASTERS.md`  
**前置条件**：PRD-001 TEST_REPORT 中 UT-001～007、CT-001～003 全部 PASSED  

### 实施步骤

| Step | 内容 | 测试命令 |
|---|---|---|
| 1 | 实现 SceneGroup / BackgroundMaster 数据类和文件读写 | `pytest -k "UT010" -v` |
| 2 | 实现迁移逻辑 `_migrate_to_scene_groups` | `pytest -k "UT011 or UT012" -v` |
| 3 | 实现启发式建议 `suggest_scene_groups` | `pytest -k "UT010" -v` |
| 4 | 实现场景组 CRUD + 背景操作逻辑 | `pytest -k "UT013 or UT014 or UT015" -v` |
| 5 | 修改 `get_project_workflow`：插入 scenes 阶段 | `pytest -k "CT013" -v` |
| 6 | 新增 API 路由（§6.1） | `pytest tests/mv_platform/contract/test_prd002_api.py -v` |
| 7 | 修改旧背景生成路由（§6.2，加 deprecated header） | `pytest -k "CT012" -v` |
| 8 | 前端：scenes 阶段页面 + 修改分镜卡 | `pytest tests/e2e/test_prd002_browser.py -k "ET010 or ET011" -v` |
| 9 | 全量 | `pytest tests/ -k "prd002" --tb=short -v` |

### 报告命令

```bash
pytest tests/ -k "prd002" --tb=short -v 2>&1 | tee TEST_REPORT_PRD002.md
```

---

## 五、PRD-003：组合首帧精化

**PRD 路径**：`docs/design/PRD-003-COMPOSITE-FIRST-FRAME.md`  
**前置条件**：PRD-002 TEST_REPORT 中 UT-010～015、CT-010～013 全部 PASSED  

### 实施步骤

| Step | 内容 | 测试命令 |
|---|---|---|
| 1 | 实现 `_read_keyframe_entries()` 兼容函数 | `pytest -k "UT022" -v` |
| 2 | 更新 `import_shot_keyframe`：写元数据对象 | `pytest -k "UT021" -v` |
| 3 | 更新 `_generate_shot_image` keyframes 分支：写元数据对象（含 prompt_zh） | `pytest -k "UT020" -v` |
| 4 | 更新 `generate_shot_keyframe`：前置条件改为 scenes_approved | `pytest -k "UT023 or UT024" -v` |
| 5 | 更新 `allowed_stages` 加 `"scenes"` | 运行服务，`curl .../workflow` 确认 |
| 6 | 更新 `get_project_workflow`：返回 `keyframe_entries` | `pytest -k "UT025" -v` |
| 7 | 新增 API 契约测试 CT-020/021/022 | `pytest tests/mv_platform/contract/test_prd003_api.py -v` |
| 8 | 前端：关键帧阶段说明 + 候选元数据展示 + 批量确认按钮 | `pytest tests/e2e/test_prd003_browser.py -k "ET020 or ET021 or ET023" -v` |
| 9 | 前端：生成按钮无背景母版时 disabled 状态 | `pytest -k "ET022" -v` |
| 10 | 全量 | `pytest tests/ -k "prd003" --tb=short -v` |

### 报告命令

```bash
pytest tests/ -k "prd003" --tb=short -v 2>&1 | tee TEST_REPORT_PRD003.md
```

---

## 六、PRD-004：视频 Provider 对接

**PRD 路径**：`docs/design/PRD-004-VIDEO-PROVIDER.md`  
**前置条件**：PRD-003 TEST_REPORT 中 UT-020～025、CT-020～022 全部 PASSED  

### 实施步骤

| Step | 内容 | 测试命令 |
|---|---|---|
| 1 | 实现 `_parse_mp4_duration()` | `pytest -k "UT033" -v` |
| 2 | 实现 `_qc_video()` | `pytest -k "UT032" -v` |
| 3 | 更新 `start_seedance_shot()` 前置条件 | `pytest -k "UT030 or UT031" -v` |
| 4 | 更新 `_run_seedance_job` 结果写入 `video_entries` | `pytest -k "UT034" -v` |
| 5 | 更新 `get_project_workflow()` 返回 `video_entries` | `pytest -k "UT035" -v` |
| 6 | 新增 `/settings/video-provider/ping` 路由 | `pytest -k "CT031" -v` |
| 7 | 更新 `/shots/{id}/video/generate` 返回 202+job_id | `pytest -k "CT030 or CT032" -v` |
| 8 | 新增 `/shots/{id}/videos/selection` 路由 | `pytest -k "CT033" -v` |
| 9 | 更新 `allowed_stages` | 运行服务确认 |
| 10 | 前端：Settings Provider 配置区 | `pytest -k "ET030" -v` |
| 11 | 前端：shots 阶段视频生成 UI | `pytest -k "ET031" -v` |
| 12 | 全量 | `pytest tests/ -k "prd004" --tb=short -v` |

### 报告命令

```bash
pytest tests/ -k "prd004" --tb=short -v 2>&1 | tee TEST_REPORT_PRD004.md
```

---

## 七、PRD-005：真实 SSE 浏览器流式推送

**PRD 路径**：`docs/design/PRD-005-SSE-STREAMING.md`  
**前置条件**：PRD-003 和 PRD-004 均 TEST_REPORT PASSED  

### 实施步骤

| Step | 内容 | 测试命令 |
|---|---|---|
| 1 | 确认 `events.append(job_id, payload)` 接口，写 UT-043/044 | `pytest -k "UT043 or UT044" -v` |
| 2 | 实现 `submit_generate_background_job()` | `pytest -k "UT040" -v` |
| 3 | 实现 `_run_generate_background_job()`（带 emit 调用） | `pytest -k "UT041 or UT042" -v` |
| 4 | 实现 `submit_generate_keyframe_job()` + handler（对称） | 同上 |
| 5 | 更新 `/background/generate`：返回 202+job_id | `pytest -k "CT040" -v` |
| 6 | 更新 `/keyframes/generate`：返回 202+job_id | `pytest -k "CT041" -v` |
| 7 | 确认 `GET /jobs/{id}/events` SSE 格式正确 | `pytest -k "CT042" -v` |
| 8 | 更新 `get_project_workflow()` 返回 `active_jobs` | `pytest -k "CT043 or UT043 or UT044" -v` |
| 9 | 前端：统一 GenerationProgress 组件 | `pytest -k "ET040" -v` |
| 10 | 前端：刷新恢复逻辑 | `pytest -k "ET041" -v` |
| 11 | 全量 | `pytest tests/ -k "prd005" --tb=short -v` |

### 报告命令

```bash
pytest tests/ -k "prd005" --tb=short -v 2>&1 | tee TEST_REPORT_PRD005.md
```

---

## 八、PRD-006：全链验收

**PRD 路径**：`docs/design/PRD-006-FULL-CHAIN-ACCEPTANCE.md`  
**前置条件**：PRD-001 ～ PRD-005 全部 TEST_REPORT PASSED  

### 实施步骤

```bash
# Step 1: 实现辅助函数
# 编写 tests/e2e/helpers_prd006.py

# Step 2-7: 实现各阶段测试（ET-060～076）

# Step 8: Smoke 模式执行（前 2 镜，约 20 分钟）
pytest tests/e2e/test_prd006_full_chain.py -v \
  --mode=smoke \
  --project-path=/Users/wmzuo/Desktop/青衣 \
  2>&1 | tee TEST_REPORT_PRD006.md

# Step 9: 修复失败项后提交报告
```

---

## 九、TEST_REPORT 格式规范

每份 TEST_REPORT_PRD00X.md **必须包含以下结构**，由实施模型手动在文件头部插入（pytest 原始输出附在后面）：

```markdown
# TEST_REPORT_PRD00X

生成时间：<ISO 时间戳>
实施模型：claude-sonnet-5
PRD 版本：docs/design/PRD-00X-xxx.md（最后 commit hash）

## 结果摘要

| 测试类型 | 用例数 | 通过 | 失败 | 跳过 |
|---|---|---|---|---|
| 单元测试（UT） | N | N | 0 | 0 |
| 契约测试（CT） | N | N | 0 | 0 |
| E2E 测试（ET） | N | N | 0 | 0 |
| **合计** | **N** | **N** | **0** | **0** |

## 验收标准逐项确认

- [x] UT-0xx ～ UT-0xx 全部通过
- [x] CT-0xx ～ CT-0xx 全部通过
- [x] ET-0xx 通过
- [x] 手动检查 1：<描述>  结果：<通过/失败>
- [x] 手动检查 2：<描述>  结果：<通过/失败>

## 失败用例（若有）

| 用例 ID | 失败原因 | 已修复 |
|---|---|---|
| UT-xxx | <原因> | <是/否，若是说明修复方式> |

## pytest 原始输出

​```
<pytest -v --tb=short 原始输出粘贴于此>
​```
```

**不允许提交给 Opus 的报告**：
- 有任何 FAILED 且未标注"已修复"
- 缺少"验收标准逐项确认"节
- 无 pytest 原始输出

---

## 十、遇到问题时的处理规则

| 情况 | 处理方式 |
|---|---|
| 测试 fixture 未定义 | 在当前 PRD 对应的测试文件 `conftest.py` 中补充，不跨 PRD 共用 fixture |
| 现有代码与 PRD 规格冲突 | **先阅读现有代码**，若冲突可解决则按 PRD 规格修改；若冲突影响更大范围，**停止并报告给 Opus**，不自行决策 |
| 服务崩溃无法启动 | 记录错误日志，报告给 Opus，不自行修改 `runtime.py` |
| E2E 测试中 Playwright 定位失败 | 优先检查 PRD 规格中的文案是否已正确实现，再检查 selector |
| 某 ET 用例需要真实 Provider 但当前无 key | 跳过（`pytest.skip`），在报告中标注"需真实 Provider，已跳过" |
| 超过 2 次相同思路修复仍失败 | 停止，将失败日志写入报告，提交给 Opus 决策 |

---

## 十一、禁止事项

- ❌ 删除任何现有方法、路由、或 JSON 字段
- ❌ 修改 `docs/RULES/` 下任何文件
- ❌ 直接 `git push origin main`
- ❌ 在没有读现有代码的情况下修改 service.py
- ❌ 把 `error_category` 拼入 `ApplicationBlocked` 消息字符串（见 PRD-001 C-01 修复说明）
- ❌ 在 service 层新建 `ErrorLogStore` 实例（见 PRD-001 C-02 修复说明）
