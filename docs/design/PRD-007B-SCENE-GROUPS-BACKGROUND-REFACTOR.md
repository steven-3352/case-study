# PRD-007B：场景组规划与背景生成重构

> **状态**：待实施  
> **优先级**：P4  
> **前置条件**：PRD-002 验收通过（background-masters.json 已有），PRD-005 验收通过（Job 基础设施已有）  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-008（全链路验收配置化）

---

## 1. 背景与问题陈述

### 1.1 当前状态

PRD-002 实现了 background-masters 模型：
- 手动指定 `background_master_id`（shot → scene group 映射）
- `background-masters.json` 存储候选图与选定状态
- Shot 通过 `background_master_id` 继承背景

但存在以下问题：

**问题 1：场景组缺乏规划步骤**  
当前工作流在分镜审批后直接进入背景生成，没有明确的"场景组规划"阶段。用户不知道系统会自动把哪些 shots 归为同一背景组，也无法在生成前调整分组。

**问题 2：候选数量未标准化**  
未规定每个场景组生成几张候选背景，导致实现不一致。

**问题 3：LLM 可以辅助分组但尚未集成**  
场景组的划分依赖视觉相似性（地点、时间、人物），LLM 可以分析分镜文本和 visual score 自动建议分组，目前完全靠人工。

**问题 4：分组后无法调整**  
Shot 与 scene group 的映射一旦写入 shot-references.json 就难以修改，用户如果对自动分组不满意，没有操作入口。

---

## 2. 目标与非目标

### 目标

1. 在分镜审批后、背景生成前，新增"场景组规划"阶段（workflow stage `scene_planning`）
2. LLM 自动分析分镜内容，建议场景组（按地点/时间/主要人物聚类）
3. 用户可查看、修改系统提示词和任务提示词，重新触发 LLM 建议
4. 用户可手动调整：新增/删除场景组，在组间移动 shots
5. 用户确认后锁定分组，进入背景生成阶段
6. 每个场景组生成 **2 张候选背景**（用户选其中一张为 master）
7. 用户从 2 张候选中选定 master，写入 `background-masters.json` status `"selected"`
8. Master 自动继承到该组所有 shots 的 `background_master_id`
9. 支持单个 shot 覆盖（override）：用特定背景替换继承来的 master

### 非目标

- 不实现自动选 master（必须用户确认）
- 不实现 3 张或更多候选（固定 2 张）
- 不实现跨项目场景组模板复用
- 不修改视频生成阶段的 shot 粒度模型
- 不实现场景组合并/拆分后的历史追踪

---

## 3. 数据模型规格

### 3.1 新增 workflow stage：`scene_planning`

`workflow.stages` 新增一个阶段，位于 `storyboard`（分镜审批）之后、`backgrounds`（背景生成）之前：

```python
{
    "id": "scene_planning",
    "name": "场景组规划",
    "status": "pending" | "in_progress" | "approved",
    "data": {
        "groups": [
            {
                "group_id": "SG001",
                "name": "书房-白天",
                "shots": ["S001", "S003", "S007"],
                "prompt_zh": "书房场景，白天自然光，木质书架...",
                "notes": "LLM 建议：地点相同，时间相近",
                "locked": false
            }
        ],
        "llm_suggestion_used": true,
        "system_prompt": "...",  # 用户可编辑的系统提示词
        "task_prompt": "..."     # 用户可编辑的任务提示词
    }
}
```

### 3.2 `background-masters.json` 升至 v3

```json
{
    "version": 3,
    "groups": {
        "SG001": {
            "group_id": "SG001",
            "name": "书房-白天",
            "shots": ["S001", "S003", "S007"],
            "prompt_zh": "书房场景，白天自然光，木质书架...",
            "prompt_en": "Study room, daytime natural light, wooden bookshelf...",
            "candidates": [
                {
                    "candidate_id": "SG001-C1",
                    "path": "assets/backgrounds/SG001-C1.jpg",
                    "generated_at": "2026-08-02T10:00:00Z",
                    "status": "selected"
                },
                {
                    "candidate_id": "SG001-C2",
                    "path": "assets/backgrounds/SG001-C2.jpg",
                    "generated_at": "2026-08-02T10:01:00Z",
                    "status": "candidate"
                }
            ],
            "master_id": "SG001-C1",
            "locked": true
        }
    }
}
```

`status` 枚举：`"candidate"` | `"selected"` | `"rejected"`  
每个 group 恰好 2 个 candidates（固定）。

### 3.3 `shot-references.json` 扩展

每个 shot 节点新增 `scene_group_id` 字段：

```json
"S001": {
    "scene_group_id": "SG001",
    "background_master_id": "SG001-C1",
    "background_override": null,   # 若非 null，使用 override 而非 master
    ...
}
```

若 `background_override` 非 null，该 shot 的背景使用 override 路径，忽略 master 继承。

---

## 4. 业务逻辑规格

### 4.1 LLM 场景组建议（R-080）

新增 `suggest_scene_groups(project_id, system_prompt=None, task_prompt=None) -> dict`：

```python
def suggest_scene_groups(
    self,
    project_id: str,
    system_prompt: str | None = None,
    task_prompt: str | None = None,
) -> dict:
    """调用 LLM 分析分镜，建议场景组。"""
    shots = self._load_storyboard_shots(project_id)
    system_prompt = system_prompt or DEFAULT_SCENE_GROUP_SYSTEM_PROMPT
    task_prompt = task_prompt or _build_default_task_prompt(shots)
    response = self.llm_client.chat(system_prompt, task_prompt)
    groups = _parse_scene_group_response(response)
    return {
        "groups": groups,
        "system_prompt": system_prompt,
        "task_prompt": task_prompt,
    }
```

**默认系统提示词**（`DEFAULT_SCENE_GROUP_SYSTEM_PROMPT`）：
```
你是一位专业的影视分镜分析师。
根据分镜描述，将镜头按"背景场景组"归类：同一地点、相近时间段、背景视觉高度相似的镜头归为一组。
每组给出一个简短名称（格式：地点-时段，如"书房-白天"）和一句背景描述提示词（中文，≤50字）。
输出 JSON 数组，每项包含 group_name, shots(镜头编号数组), prompt_zh。
```

**默认任务提示词模板**：
```
以下是分镜列表，请按场景组归类：

{shots_json}

要求：不遗漏任何镜头，每个镜头只能属于一个组。
```

### 4.2 用户编辑与重新建议（R-081）

`update_scene_planning(project_id, payload) -> dict`：

接受 payload：
```json
{
    "action": "regenerate_suggestion",
    "system_prompt": "...",  # 用户修改的系统提示词
    "task_prompt": "..."     # 用户修改的任务提示词
}
```

或：
```json
{
    "action": "update_groups",
    "groups": [...]  # 用户手动编辑后的分组
}
```

### 4.3 手动调整分组（R-082）

支持以下操作（通过 `update_scene_planning` action=`"update_groups"`）：

- 新增场景组：groups 数组中新增一项（无 `group_id` → 系统自动分配）
- 删除场景组：groups 数组中移除某项，其 shots 自动归入 `"uncategorized"` 虚组
- 移动 shot：从 A 组的 shots 数组移除，加入 B 组
- 修改提示词：直接更新 group 的 `prompt_zh`

### 4.4 确认锁定（R-083）

`approve_scene_planning(project_id) -> dict`：

- 校验：所有 shots 都已分配到某个 group（无 uncategorized shots）
- 写入 `background-masters.json`（groups 结构，status 为 `"candidate"`，master_id 为空）
- 写入每个 shot 的 `scene_group_id`
- 设置 workflow stage `scene_planning` status = `"approved"`
- 解锁 `backgrounds` 阶段

### 4.5 背景候选生成（R-084）

每个场景组生成 **恰好 2 张**候选背景：

`submit_generate_group_background_job(project_id, group_id) -> dict`：

- 前置条件：`scene_planning` 已 approved
- 创建 2 个 `generate_background` Job（candidate_index=1, 2）
- 返回 `{"group_id": "SG001", "job_ids": ["...", "..."]}`

Job 完成后写入 `background-masters.json` 对应 group 的 candidates 列表。

### 4.6 用户选定 Master（R-085）

`select_background_master(project_id, group_id, candidate_id) -> dict`：

- 将指定 candidate 的 status 改为 `"selected"`
- 其他 candidate 改为 `"rejected"`
- 设置 `master_id = candidate_id`
- **自动更新**该组所有 shots 的 `background_master_id = candidate_id`
- 返回 `{"group_id": "SG001", "master_id": "SG001-C1", "shots_updated": ["S001", "S003", "S007"]}`

### 4.7 单 Shot Override（R-086）

`set_shot_background_override(project_id, shot_id, override_path: str | None) -> dict`：

- 若 `override_path` 非 null：写入 shot 的 `background_override` 字段
- 若 `override_path` 为 null：清除 override，shot 恢复继承 group master
- 返回 `{"shot_id": "S001", "background_master_id": "...", "background_override": "..."}`

---

## 5. API 变更规格

### 5.1 新增路由

| 方法 | 路由 | 说明 |
|---|---|---|
| `GET` | `/api/v1/projects/{project_id}/scene-planning` | 获取当前场景组规划状态 |
| `POST` | `/api/v1/projects/{project_id}/scene-planning/suggest` | LLM 建议（body: system_prompt?, task_prompt?） |
| `PUT` | `/api/v1/projects/{project_id}/scene-planning` | 更新分组（body: groups） |
| `POST` | `/api/v1/projects/{project_id}/scene-planning/approve` | 确认锁定 |
| `POST` | `/api/v1/projects/{project_id}/groups/{group_id}/background/generate` | 提交该组 2 张候选生成 Job |
| `POST` | `/api/v1/projects/{project_id}/groups/{group_id}/background/select` | 选定 master（body: candidate_id） |
| `PUT` | `/api/v1/projects/{project_id}/shots/{shot_id}/background-override` | 设置/清除 shot override |

### 5.2 workflow 变更

`GET /api/v1/projects/{project_id}/workflow` 新增 `scene_planning` stage，位于 `storyboard` 之后：

```json
{
    "id": "scene_planning",
    "name": "场景组规划",
    "status": "pending",
    "data": {
        "groups": [],
        "llm_suggestion_used": false
    }
}
```

---

## 6. 前端规格

### 6.1 场景组规划页面布局

```
场景组规划
──────────────────────────────────────────────

[生成建议]  [修改系统提示词]  [修改任务提示词]

┌─── SG001: 书房-白天 ─────────────────────┐
│  S001 | S003 | S007                      │
│  提示词：书房场景，白天自然光，木质书架...  │
│  [编辑提示词]  [移入]  [移出]  [删除此组]  │
└───────────────────────────────────────────┘

┌─── SG002: 庭院-黄昏 ─────────────────────┐
│  S002 | S005                             │
│  提示词：庭院，黄昏暖光，落叶...          │
└───────────────────────────────────────────┘

[+ 新增场景组]

────────────────────────────────────────────
未分配镜头：（无）

[确认锁定分组]
```

### 6.2 背景候选选择页面

```
SG001: 书房-白天  —  选择背景 Master

┌──────────────┐   ┌──────────────┐
│  候选 1       │   │  候选 2       │
│  [图片预览]   │   │  [图片预览]   │
│              │   │              │
│  [✓ 选定]    │   │  [选定]      │
└──────────────┘   └──────────────┘

当前 Master：候选 1
适用镜头：S001, S003, S007
```

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd007b_scene_groups.py`）

**UT-080**：suggest_scene_groups 返回 groups 列表

```python
def test_suggest_scene_groups_returns_groups(tmp_path, monkeypatch):
    service, project_id = _setup_project_with_storyboard(tmp_path, "ut080")
    monkeypatch.setattr(service, "llm_client", FakeLLMClient(
        response='[{"group_name":"书房-白天","shots":["S001"],"prompt_zh":"书房"}]'
    ))
    result = service.suggest_scene_groups(project_id)
    assert len(result["groups"]) >= 1
    assert result["groups"][0]["shots"] == ["S001"]
```

**UT-081**：approve_scene_planning 要求所有 shots 已分组

```python
def test_approve_fails_if_uncategorized_shots_exist(tmp_path):
    service, project_id = _setup_project_with_storyboard(tmp_path, "ut081")
    # 故意只分配 S001，不分配 S002
    service.update_scene_planning(project_id, {
        "action": "update_groups",
        "groups": [{"group_name": "书房", "shots": ["S001"], "prompt_zh": "书房"}],
    })
    with pytest.raises(ApplicationBlocked, match="uncategorized"):
        service.approve_scene_planning(project_id)
```

**UT-082**：approve_scene_planning 成功后 workflow stage 变为 approved

```python
def test_approve_scene_planning_sets_stage_approved(tmp_path, monkeypatch):
    service, project_id = _setup_project_all_shots_grouped(tmp_path, "ut082")
    service.approve_scene_planning(project_id)
    wf = service.get_project_workflow(project_id)
    sp_stage = next(s for s in wf["stages"] if s["id"] == "scene_planning")
    assert sp_stage["status"] == "approved"
```

**UT-083**：select_background_master 自动更新该组所有 shots 的 background_master_id

```python
def test_select_master_updates_all_shots_in_group(tmp_path):
    service, project_id = _setup_project_with_two_candidates(tmp_path, "ut083")
    result = service.select_background_master(project_id, "SG001", "SG001-C1")
    assert set(result["shots_updated"]) == {"S001", "S003", "S007"}
    refs = service.repository.load_shot_references(project_id)
    for shot_id in ["S001", "S003", "S007"]:
        assert refs[shot_id]["background_master_id"] == "SG001-C1"
```

**UT-084**：set_shot_background_override 覆盖单 shot 背景

```python
def test_shot_override_does_not_affect_siblings(tmp_path):
    service, project_id = _setup_project_with_master(tmp_path, "ut084")
    service.set_shot_background_override(project_id, "S001", "assets/custom/override.jpg")
    refs = service.repository.load_shot_references(project_id)
    assert refs["S001"]["background_override"] == "assets/custom/override.jpg"
    # 组内其他 shots 不受影响
    assert refs["S003"]["background_override"] is None
    assert refs["S003"]["background_master_id"] == "SG001-C1"
```

**UT-085**：set_shot_background_override 传 None 清除 override

```python
def test_clear_shot_override_restores_master_inheritance(tmp_path):
    service, project_id = _setup_project_with_override(tmp_path, "ut085")
    service.set_shot_background_override(project_id, "S001", None)
    refs = service.repository.load_shot_references(project_id)
    assert refs["S001"]["background_override"] is None
```

**UT-086**：submit_generate_group_background_job 创建 2 个 job

```python
def test_submit_group_background_job_creates_two_jobs(tmp_path):
    service, project_id = _setup_project_planning_approved(tmp_path, "ut086")
    result = service.submit_generate_group_background_job(project_id, "SG001")
    assert len(result["job_ids"]) == 2
```

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd007b_api.py`）

**CT-080**：POST /scene-planning/suggest 返回 200 + groups

```python
def test_scene_planning_suggest_returns_groups(client, project_id, mock_llm):
    resp = client.post(f"/api/v1/projects/{project_id}/scene-planning/suggest")
    assert resp.status_code == 200
    assert "groups" in resp.json()
```

**CT-081**：PUT /scene-planning 更新成功返回 200

```python
def test_update_scene_planning_returns_200(client, project_id):
    resp = client.put(
        f"/api/v1/projects/{project_id}/scene-planning",
        json={"groups": [{"group_name": "书房", "shots": ["S001"], "prompt_zh": "书房"}]},
    )
    assert resp.status_code == 200
```

**CT-082**：POST /scene-planning/approve 有未分配 shot 时返回 423

```python
def test_approve_with_uncategorized_shots_returns_423(client, project_id):
    resp = client.post(f"/api/v1/projects/{project_id}/scene-planning/approve")
    assert resp.status_code == 423
```

**CT-083**：POST /groups/{group_id}/background/select 返回 200 + shots_updated

```python
def test_select_master_returns_shots_updated(client, project_id_with_candidates):
    resp = client.post(
        f"/api/v1/projects/{project_id_with_candidates}/groups/SG001/background/select",
        json={"candidate_id": "SG001-C1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "shots_updated" in body
    assert len(body["shots_updated"]) > 0
```

**CT-084**：workflow 包含 scene_planning stage

```python
def test_workflow_has_scene_planning_stage(client, project_id):
    resp = client.get(f"/api/v1/projects/{project_id}/workflow")
    assert resp.status_code == 200
    stage_ids = [s["id"] for s in resp.json()["stages"]]
    assert "scene_planning" in stage_ids
```

### 7.3 浏览器 E2E 测试（`tests/e2e/test_prd007b_browser.py`）

**ET-080**：点击"生成建议"后显示场景组列表

```python
@requires_ui
def test_suggest_shows_group_list(page, project_id_storyboard_approved):
    page.goto(f"{BASE_URL}/projects/{project_id_storyboard_approved}/scene-planning")
    page.click("button:has-text('生成建议')")
    page.wait_for_selector(".scene-group-card", timeout=30_000)
    assert page.locator(".scene-group-card").count() >= 1
```

**ET-081**：用户确认锁定后"背景生成"阶段解锁

```python
@requires_ui
def test_approve_unlocks_backgrounds_stage(page, project_id_all_shots_grouped):
    page.goto(f"{BASE_URL}/projects/{project_id_all_shots_grouped}/scene-planning")
    page.click("button:has-text('确认锁定分组')")
    page.wait_for_selector("text=场景组规划已锁定", timeout=10_000)
    page.goto(f"{BASE_URL}/projects/{project_id_all_shots_grouped}/backgrounds")
    assert page.locator("button.bg-generate:not([disabled])").count() > 0
```

---

## 8. 验收标准

- [ ] UT-080 ～ UT-086 全部通过
- [ ] CT-080 ～ CT-084 全部通过
- [ ] ET-080 通过（LLM 建议分组可见）
- [ ] ET-081 通过（确认锁定后背景生成解锁）
- [ ] 手动检查：每个场景组生成恰好 2 张候选背景
- [ ] 手动检查：选定 master 后，该组所有 shots 的 background_master_id 自动更新
- [ ] 手动检查：单 shot override 不影响组内其他 shots
- [ ] 手动检查：workflow 顺序为 storyboard → scene_planning → backgrounds
- [ ] 手动检查：有未分配 shot 时，"确认锁定"按钮禁用或点击报错

---

## 9. 废弃与归档说明

- PRD-002 中的"手动指定 background_master_id"流程被本 PRD 的"场景组规划 → 候选生成 → 选定 master → 自动继承"流程替代
- `shot-references.json` v2（background_master_id 字段）仍兼容读取，写入时升至 v3（新增 scene_group_id, background_override）

---

## 10. 实施顺序建议（给便宜模型）

```
Step 1  domain/contracts.py：新增 SceneGroup、ScenePlanningData 数据类
Step 2  repository：scene_planning 状态持久化（存 background-masters.json 的 groups 节点）
Step 3  service：suggest_scene_groups()（UT-080），接入 fake LLM 先写通测试
Step 4  service：update_scene_planning() 处理 action=update_groups（UT-082）
Step 5  service：approve_scene_planning() 含前置检查（UT-081/082）
Step 6  service：submit_generate_group_background_job()，2 个 Job（UT-086）
Step 7  service：select_background_master()，自动更新 shots（UT-083）
Step 8  service：set_shot_background_override()（UT-084/085）
Step 9  get_project_workflow() 新增 scene_planning stage（CT-084）
Step 10 API 路由：7 个新路由（CT-080~083）
Step 11 前端：场景组规划页面（ET-080/081）
Step 12 全量执行：pytest -k "prd007b"，输出 TEST_REPORT_PRD007B.md
```
