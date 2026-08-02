# PRD-006：全链验收规格

> **状态**：待实施  
> **优先级**：P5  
> **前置条件**：PRD-001 ～ PRD-005 全部验收通过  
> **负责模型**：便宜模型执行测试，Opus 最终验收  
> **解锁**：立绘MV Web 可向用户发布

---

## 1. 背景与目标

### 1.1 背景

PRD-001 ～ PRD-005 分别验收了各自的单元测试（UT）、API 契约测试（CT）、浏览器测试（ET）。
但各阶段测试使用 mock 或局部 fixture，无法替代"用真实 Provider 跑完整个流程"的验证。

PRD-006 是**端到端全链验收**：
- 使用真实项目（青衣）
- 使用真实 Provider（GPT-image-2 + Seedance 2.0）
- 用真实浏览器走完所有阶段
- 自动捕获每一步的通过/失败，输出 `TEST_REPORT_PRD006.md`

### 1.2 测试项目

| 字段 | 值 |
|---|---|
| 项目名 | 青衣 |
| 项目路径 | `/Users/wmzuo/Desktop/青衣` |
| 预计分镜数 | 约 25 镜 |
| 图片 Provider | GPT-image-2（`gpt-image-2`） |
| 视频 Provider | Seedance 2.0（`doubao-seedance-2-0`） |
| 验收用镜数 | 全部镜（P5 全链）；快速验收可只走前 2 镜 |
| 验收模式 | full（全部 25 镜）或 smoke（前 2 镜，约 10 分钟） |

### 1.3 验收目标

1. 完整走完 `import → story → storyboard → scenes → keyframes → shots → delivery` 全链
2. 每个阶段：自动验证状态、数据文件、UI 可见性
3. 生成的视频 QC 通过率 ≥ 80%（smoke: 2 镜均通过）
4. 所有页面可见文字为中文（无英文状态码暴露）
5. 服务崩溃恢复：重启后可继续上次进度
6. 费用记录完整：每次生成均有 cost_entries 记录

---

## 2. 测试环境规格

### 2.1 服务准备

```bash
# 确认服务运行
curl -s http://127.0.0.1:8792/readyz | python3 -m json.tool
# 预期: {"status": "ready"}

# 确认 Provider 配置
curl -s -X POST http://127.0.0.1:8792/api/v1/settings/video-provider/ping | python3 -m json.tool
# 预期: {"reachable": true, ...}
```

### 2.2 测试项目状态

测试开始前，确保青衣项目处于一个已知状态。
测试脚本支持两种启动模式：

**full-reset**（从头开始）：
- 备份当前 `creative/` 目录为 `creative-backup-{timestamp}/`
- 清空 `creative/decisions.json`（仅保留 story 内容）
- 清空 `creative/scene-groups.json`、`creative/background-masters.json`
- 重置 `shot-references.json` 到 v1（仅有 shots key，无 background/keyframes/video）

**resume**（从上次断点继续）：
- 读取当前 workflow 状态，从第一个未 approved 的阶段开始

测试命令：
```bash
pytest tests/e2e/test_prd006_full_chain.py -v --mode=smoke --project-path=/Users/wmzuo/Desktop/青衣
pytest tests/e2e/test_prd006_full_chain.py -v --mode=full --project-path=/Users/wmzuo/Desktop/青衣
```

---

## 3. 测试阶段规格

### 阶段 0：服务就绪检查

**ET-060**：服务在 5 秒内就绪

```python
def test_service_ready(page):
    resp = requests.get("http://127.0.0.1:8792/readyz", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
```

**ET-061**：青衣项目可访问

```python
def test_project_accessible(test_client, project_id):
    resp = test_client.get(f"/api/v1/projects/{project_id}/workflow")
    assert resp.status_code == 200
    stages = resp.json()["stages"]
    assert any(s["id"] == "story" for s in stages)
```

---

### 阶段 1：Story 审批

**ET-062**：story 阶段已 approved 或可 approve

```python
def test_story_approved(page, project_id):
    wf = fetch_workflow(project_id)
    story = next(s for s in wf["stages"] if s["id"] == "story")
    if story["decision"]["action"] != "approve":
        # 点击 approve
        page.goto("http://127.0.0.1:8792")
        page.locator("button:has-text('确认故事框架')").click()
        page.wait_for_selector("text=故事框架已确认", timeout=10_000)
    # 验证
    wf = fetch_workflow(project_id)
    story = next(s for s in wf["stages"] if s["id"] == "story")
    assert story["decision"]["action"] == "approve"
```

---

### 阶段 2：Storyboard 审批

**ET-063**：storyboard 阶段已 approved 或可 approve

```python
def test_storyboard_approved(page, project_id):
    # 若未 approved，点击确认分镜
    # 验证 workflow storyboard.decision.action == "approve"
    assert_stage_approved(page, project_id, "storyboard", "确认分镜")
```

---

### 阶段 3：场景与背景（scenes）

**ET-064**：scene-groups.json 自动生成

```python
def test_scene_groups_auto_generated(project_path):
    sg_path = project_path / "creative" / "scene-groups.json"
    assert sg_path.exists()
    data = json.loads(sg_path.read_text())
    assert len(data["scene_groups"]) > 0
```

**ET-065**：每个场景组生成一张背景（smoke: 前 1 组）

```python
@pytest.mark.parametrize("sg_id", get_first_n_scene_groups(n=1))
def test_generate_background_for_scene_group(page, project_id, sg_id):
    # 导航到 scenes 阶段
    # 点击该场景组的"生成背景"按钮
    # 等待最多 120s
    page.wait_for_selector(f"[data-sg-id='{sg_id}'] text=候选", timeout=120_000)
    # 选定背景
    page.locator(f"[data-sg-id='{sg_id}'] button:has-text('选定')").first.click()
    # 验证 background-masters.json 有 selected 记录
    bm = get_background_masters(project_id)
    selected = [b for b in bm["backgrounds"] if b["scene_group_id"] == sg_id and b["status"] == "selected"]
    assert len(selected) == 1
```

**ET-066**：所有场景组有选定背景后 approve scenes

```python
def test_approve_scenes(page, project_id):
    # 确保每组都有 selected 背景（由前序步骤完成）
    page.locator("button:has-text('一键确认所有场景背景')").click()
    assert_stage_approved(page, project_id, "scenes", None)
```

---

### 阶段 4：关键帧选择（keyframes）

**ET-067**：每镜生成一张关键帧（smoke: 前 2 镜）

```python
@pytest.mark.parametrize("shot_id", get_first_n_shots(n=2))
def test_generate_keyframe_for_shot(page, project_id, shot_id):
    # 导航到 keyframes 阶段
    # 点击该镜的"生成新候选"按钮
    page.wait_for_selector(f"[data-shot-id='{shot_id}'] text=系统生成", timeout=120_000)
    # 选定首帧
    page.locator(f"[data-shot-id='{shot_id}'] button:has-text('选定此帧')").first.click()
    # 验证 shot-references.json
    refs = get_shot_references(project_id)
    entry = refs["shots"][shot_id]["keyframes"][0]
    assert isinstance(entry, dict)
    assert entry["source"] == "generated"
    assert refs["shots"][shot_id]["selected_keyframe"] != ""
```

**ET-068**：keyframe_entries 包含 prompt_en（非空）

```python
def test_keyframe_entries_have_prompt(project_id):
    wf = fetch_workflow(project_id)
    kf_stage = next(s for s in wf["stages"] if s["id"] == "keyframes")
    for shot in kf_stage["data"]["shots"]:
        for entry in shot.get("keyframe_entries", []):
            if entry["source"] == "generated":
                assert entry["prompt_en"] != "", f"Shot {shot['id']} has empty prompt_en"
```

**ET-069**：approve keyframes

```python
def test_approve_keyframes(page, project_id):
    page.locator("button:has-text('一键确认所有关键帧')").click()
    assert_stage_approved(page, project_id, "keyframes", None)
```

---

### 阶段 5：单镜视频制作（shots）

**ET-070**：每镜生成一段视频（smoke: 前 2 镜）

```python
@pytest.mark.parametrize("shot_id", get_first_n_shots(n=2))
def test_generate_video_for_shot(page, project_id, shot_id):
    # 导航到 shots 阶段
    # 点击该镜的"生成视频"按钮
    page.wait_for_selector(f"[data-shot-id='{shot_id}'] text=时长:", timeout=300_000)
    # 选定视频
    page.locator(f"[data-shot-id='{shot_id}'] button:has-text('选定此视频')").first.click()
    # 验证 shot-references.json
    refs = get_shot_references(project_id)
    entries = refs["shots"][shot_id].get("video_entries", [])
    assert len(entries) > 0
    assert entries[0]["qc_passed"] in (True, False)  # 记录即可，不要求 True
    assert refs["shots"][shot_id].get("selected_video", "") != ""
```

**ET-071**：视频 QC 通过率 ≥ 80%（smoke: 2/2 通过）

```python
def test_video_qc_pass_rate(project_id):
    refs = get_shot_references(project_id)
    all_entries = []
    for shot in refs["shots"].values():
        all_entries.extend(shot.get("video_entries", []))
    if not all_entries:
        pytest.skip("no video entries yet")
    pass_rate = sum(1 for e in all_entries if e["qc_passed"]) / len(all_entries)
    assert pass_rate >= 0.8, f"QC pass rate {pass_rate:.0%} below threshold 80%"
```

**ET-072**：cost_entries 有视频费用记录

```python
def test_video_cost_tracked(project_id):
    # 查询 cost_entries 表，确认有 type=video 的记录
    costs = get_cost_entries(project_id, type="video")
    assert len(costs) > 0
    assert all(c["amount_yuan"] > 0 for c in costs)
```

---

### 阶段 6：交付检查（delivery）

**ET-073**：delivery 阶段可访问

```python
def test_delivery_stage_accessible(page, project_id):
    wf = fetch_workflow(project_id)
    delivery = next((s for s in wf["stages"] if s["id"] == "delivery"), None)
    assert delivery is not None
```

---

### 阶段 7：全局质量检查

**ET-074**：所有页面可见文字无暴露英文状态码

```python
def test_no_english_status_codes_visible(page):
    page.goto("http://127.0.0.1:8792")
    # 检查常见英文错误关键字
    for text in ["ApplicationBlocked", "error_stage", "500 Internal", "Traceback"]:
        assert page.locator(f"text={text}").count() == 0, f"Found '{text}' in page"
```

**ET-075**：服务重启后可继续工作（重复 3 次）

```python
@pytest.mark.parametrize("run", [1, 2, 3])
def test_service_restart_and_recover(run):
    # POST /api/v1/system/restart
    resp = requests.post("http://127.0.0.1:8792/api/v1/system/restart")
    assert resp.status_code in (200, 202)
    # 轮询 /readyz，最多 15 秒
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = requests.get("http://127.0.0.1:8792/readyz", timeout=2)
            if r.status_code == 200 and r.json().get("status") == "ready":
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        pytest.fail(f"Service did not recover within 15s (run {run})")
    # 确认 workflow 仍可访问
    r = requests.get(f"http://127.0.0.1:8792/api/v1/projects/{project_id}/workflow")
    assert r.status_code == 200
```

**ET-076**：所有后端日志包含 error_category（有错误发生时）

```python
def test_error_logs_have_category(project_path):
    # 读取 logs/ 目录下最近 1 天的 backend JSONL
    log_files = sorted((project_path / "logs").glob("backend-*.jsonl"))
    if not log_files:
        pytest.skip("no log files")
    for line in log_files[-1].read_text().splitlines():
        entry = json.loads(line)
        if "failed" in entry.get("event", ""):
            assert "error_category" in entry, f"Missing error_category in: {entry}"
```

---

## 4. 测试辅助函数规格

所有测试辅助函数收录在 `tests/e2e/helpers_prd006.py`：

```python
def fetch_workflow(project_id: str) -> dict: ...
def get_shot_references(project_id: str) -> dict: ...
def get_background_masters(project_id: str) -> dict: ...
def get_cost_entries(project_id: str, type: str | None = None) -> list: ...
def get_first_n_shots(n: int) -> list[str]: ...
def get_first_n_scene_groups(n: int) -> list[str]: ...
def assert_stage_approved(page, project_id: str, stage_id: str, btn_text: str | None): ...
```

---

## 5. 测试报告格式

`TEST_REPORT_PRD006.md` 由测试脚本自动生成，格式：

```markdown
# TEST_REPORT_PRD006 · 全链验收

生成时间：2026-08-01T22:00:00+08:00  
项目：青衣  
验收模式：smoke（前 2 镜）  
总耗时：约 18 分钟  

## 结果摘要

| 阶段 | 测试数 | 通过 | 失败 | 跳过 |
|---|---|---|---|---|
| 服务就绪 | 2 | 2 | 0 | 0 |
| Story | 1 | 1 | 0 | 0 |
| Storyboard | 1 | 1 | 0 | 0 |
| Scenes | 3 | 3 | 0 | 0 |
| Keyframes | 3 | 3 | 0 | 0 |
| Shots | 3 | 3 | 0 | 0 |
| Delivery | 1 | 1 | 0 | 0 |
| 全局质量 | 3 | 3 | 0 | 0 |
| **合计** | **17** | **17** | **0** | **0** |

## 费用统计

| 类型 | 数量 | 单价 | 合计 |
|---|---|---|---|
| 背景生成 | 1 张 | ¥0.52 | ¥0.52 |
| 关键帧生成 | 2 张 | ¥0.52 | ¥1.04 |
| 视频生成 | 2 段×5s | ¥3.00 | ¥6.00 |
| **总计** | — | — | **¥7.56** |

## 视频 QC

| 镜号 | 时长 | 文件大小 | QC 结果 |
|---|---|---|---|
| S001 | 4.97s | 8.2MB | ✓ 通过 |
| S002 | 5.02s | 7.9MB | ✓ 通过 |

QC 通过率：100%（≥80% 阈值）

## 失败详情

（无）

## 服务重启

| 次数 | 恢复时间 | 结果 |
|---|---|---|
| 1 | 6.2s | ✓ |
| 2 | 5.8s | ✓ |
| 3 | 6.5s | ✓ |
```

---

## 6. 验收标准

**Smoke 模式（最低要求）**：
- [ ] ET-060 ～ ET-063 通过（服务就绪 + story + storyboard）
- [ ] ET-064 ～ ET-066 通过（scenes：1 组背景 + approve）
- [ ] ET-067 ～ ET-069 通过（keyframes：前 2 镜 + approve）
- [ ] ET-070 ～ ET-072 通过（shots：前 2 镜视频 + QC ≥ 100%）
- [ ] ET-074 通过（无英文状态码暴露）
- [ ] ET-075 通过（3 次重启均成功）
- [ ] 费用记录完整（背景 + 关键帧 + 视频均有 cost_entries）

**Full 模式（发布前）**：
- [ ] Smoke 全部通过，且覆盖全部 25 镜
- [ ] ET-073 通过（delivery 阶段可访问）
- [ ] ET-076 通过（错误日志有 error_category）
- [ ] 视频 QC 通过率 ≥ 80%
- [ ] 手动人工检查：随机抽取 3 张关键帧和 3 段视频，视觉确认内容正确

---

## 7. 废弃与归档说明

本 PRD 不涉及代码变更，只包含测试脚本和验收流程。

测试脚本位置：
- `tests/e2e/test_prd006_full_chain.py`
- `tests/e2e/helpers_prd006.py`

报告输出位置：
- `TEST_REPORT_PRD006.md`（项目根目录）

---

## 8. 实施顺序建议（给便宜模型）

```
Step 1  实现 helpers_prd006.py（辅助函数，无测试逻辑）
Step 2  实现阶段 0（ET-060/061）：服务就绪 + 项目可访问
Step 3  实现阶段 1-2（ET-062/063）：story + storyboard approve
Step 4  实现阶段 3（ET-064/065/066）：scenes（需 PRD-002 完成）
Step 5  实现阶段 4（ET-067/068/069）：keyframes（需 PRD-003 完成）
Step 6  实现阶段 5（ET-070/071/072）：shots + video QC（需 PRD-004 完成）
Step 7  实现阶段 6-7（ET-073/074/075/076）：delivery + 全局质量
Step 8  实现报告自动生成（pytest-html 或自定义 pytest plugin）
Step 9  执行 smoke 模式，输出 TEST_REPORT_PRD006.md（smoke）
Step 10 修复失败项，Opus 最终验收
Step 11（可选）执行 full 模式，全量验收
```