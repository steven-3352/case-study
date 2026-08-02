# PRD-002：场景组与背景母版

> **状态**：待实施  
> **优先级**：P2（业务模型根本修复，后续所有图片生成的正确基础）  
> **前置条件**：PRD-001 验收通过  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-003（组合首帧精化）

---

## 1. 背景与问题陈述

当前代码将背景存储在 `shot-references.json` 的每个 shot 节点下：

```json
{ "shots": { "S001": { "background": "assets/generated/backgrounds/S001-xxx.png" } } }
```

这导致用户面对 25 个分镜时需要逐镜生成背景，昂贵且没有叙事资产复用逻辑。

正确模型应为：**场景组 → 背景母版（场景维度）→ 逐镜引用母版 + 构图变体**。

背景生成入口必须从分镜卡移出，放入独立的"场景与背景"阶段。

---

## 2. 目标与非目标

### 目标

1. 新增 `scene-groups.json` 和 `background-masters.json` 两个文件，存储新实体
2. 系统从 `visual_score.yaml` 的 section 结构自动建议场景组，用户可调整
3. 背景母版归属于场景组，不再属于单个 shot
4. `shot-references.json` 版本升至 v2，新增 `background_master_id` 和 `background_variant` 字段
5. 新增"场景与背景"阶段（scenes），位于 storyboard 和 keyframes 之间
6. 背景生成 API 迁移至场景组维度（保留旧路由但标记为 deprecated）
7. 分镜卡只展示"所属场景组"和构图变体，不再有背景生成按钮

### 非目标

- 不实现 LLM 驱动的场景组建议（使用 section 启发式规则）
- 不删除旧 `shot.background` 字段（向后兼容，迁移时保留）
- 不修改 `visual_score.yaml` 的 shot 结构
- 不改变数据库表结构
- 不实现多背景候选的批量生成（每次生成一张，按需追加）

---

## 3. 数据模型规格

### 3.1 `creative/scene-groups.json`（新文件）

```json
{
  "version": 1,
  "generated_by": "system_heuristic",
  "generated_at": "<ISO timestamp>",
  "scene_groups": [
    {
      "id": "SG001",
      "name": "月下独处",
      "location": "庭院",
      "time_of_day": "夜晚",
      "weather": "晴",
      "emotional_state": "孤独",
      "narrative_world_state": "主角独自回忆",
      "source_section_id": "S-A",
      "shot_ids": ["S001", "S002", "S003"],
      "created_by": "system",
      "created_at": "<ISO timestamp>",
      "updated_at": "<ISO timestamp>"
    }
  ]
}
```

字段约束：
- `id`：格式 `SG\d{3,}`，项目内唯一
- `name`：用户可编辑中文名，≤40 字
- `shot_ids`：引用 visual_score.yaml 中已存在的 shot id，不能有悬挂引用
- `source_section_id`：来源 section，仅用于溯源，不做业务约束
- 每个 shot 只能属于一个场景组（系统保证不重复，用户调整时自动移出旧组）

### 3.2 `creative/background-masters.json`（新文件）

```json
{
  "version": 1,
  "backgrounds": [
    {
      "id": "BG001",
      "scene_group_id": "SG001",
      "status": "candidate",
      "source": "generated",
      "relative_path": "assets/generated/backgrounds/BG001-abc123.png",
      "prompt_zh": "夜晚庭院，月光照射...",
      "prompt_en": "night garden, moonlight...",
      "model": "gpt-image-2",
      "request_id": "image-abc123",
      "translation_audit": { "input_tokens": 120, "output_tokens": 80 },
      "cost_yuan": 0.5,
      "created_at": "<ISO timestamp>"
    }
  ]
}
```

`status` 枚举：
- `candidate`：已生成/上传，待用户选择
- `selected`：用户选定为该场景组的正式母版（每组只能有一个 selected）
- `rejected`：用户明确拒绝，保留记录但不展示为候选

### 3.3 `creative/shot-references.json` 升至 v2

在现有每个 shot 节点追加两个可选字段，旧字段 `background` 保留：

```json
{
  "version": 2,
  "shots": {
    "S001": {
      "background": "assets/...",
      "background_master_id": "BG001",
      "background_variant": {
        "shot_size": "medium",
        "camera_angle": "eye_level",
        "lighting_note": "",
        "prop_note": "",
        "crop_note": ""
      },
      "keyframes": [],
      "selected_keyframe": ""
    }
  }
}
```

- `background_master_id` 为空表示该镜尚未绑定背景母版
- `background_variant` 记录该镜相对于母版的构图差异，不能包含人物外形/风格/服装变更
- 旧 `background` 字段在迁移时保留，新代码优先读 `background_master_id`

---

## 4. 迁移规格

### 4.1 触发时机

首次调用 `GET /api/v1/projects/{project_id}/workflow` 且 `scene-groups.json` 不存在时，
服务自动执行一次性迁移，不需要用户手动触发。

### 4.2 迁移步骤

```
Step 1  读取 visual_score.yaml 的 shots 列表
Step 2  按 shot.section 字段归并分组（相同 section → 同一场景组）
Step 3  为每个 section 组创建 SceneGroup，名称取 story_framework.yaml 对应段落的 emotion 字段
        若无对应段落，名称默认为 "场景{N}"
Step 4  读取现有 shot-references.json
Step 5  对每个有 background 路径的 shot，创建一个 BackgroundMaster（status=selected）
        并将该 BackgroundMaster 分配给该 shot 所属的场景组
        若同一场景组有多个不同 background 路径，全部保留为 candidate，最后一个设为 selected
Step 6  写入 scene-groups.json 和 background-masters.json
Step 7  将 shot-references.json version 升至 2，为每个 shot 填写 background_master_id
Step 8  不删除旧 background 字段
```

### 4.3 迁移失败处理

- 若 visual_score.yaml 不存在，跳过迁移（分镜尚未生成，scenes 阶段不需要）
- 若 shot.section 字段缺失，该 shot 归入"默认场景组"
- 迁移过程中任何文件写入失败，回滚（不写入任何新文件），在 backend 日志记录 `event: "scene_group_migration_failed"`

---

## 5. 业务逻辑规格

### 5.1 场景组自动建议规则（启发式，无 LLM）

```python
def suggest_scene_groups(shots: list[dict], story_sections: list[dict]) -> list[SceneGroup]:
    # 按 shot.section 分组
    groups = {}
    for shot in shots:
        section_id = shot.get("section", "_default")
        groups.setdefault(section_id, []).append(shot["id"])
    # 从 story_sections 获取名称
    section_names = {s["id"]: s.get("emotion", "") for s in story_sections}
    result = []
    for i, (section_id, shot_ids) in enumerate(groups.items()):
        result.append(SceneGroup(
            id=f"SG{i+1:03d}",
            name=section_names.get(section_id, f"场景{i+1}"),
            source_section_id=section_id,
            shot_ids=shot_ids,
        ))
    return result
```

### 5.2 用户可执行的场景组操作

| 操作 | 规则 |
|---|---|
| 重命名 | 只改 name，不影响 shot 归属 |
| 合并 | 选两个或多个 SceneGroup，合并为一个，shot 归属转移 |
| 拆分 | 选一个 SceneGroup 中的部分 shots，移出为新 SceneGroup |
| 调整 shot 归属 | 把某个 shot 从一个 SceneGroup 移到另一个 |
| 重新生成建议 | 清空当前 scene-groups.json，重新执行启发式规则 |

**约束**：
- 不允许一个 shot 同时属于多个 SceneGroup
- 每个 shot 必须属于某个 SceneGroup（不允许孤立 shot）
- SceneGroup 可以为空（用户拆分后中间状态），但进入 keyframes 前必须全部有 shot

### 5.3 背景母版操作规则

| 操作 | 规则 |
|---|---|
| 生成背景（AI） | 调用 GPT-image-2，结果以 candidate 状态加入该场景组 |
| 上传背景 | 用户上传图片，以 candidate 状态加入，source=uploaded |
| 选定背景 | 将 candidate 改为 selected，同组其他 selected 降为 candidate |
| 生成预估费用 | 翻译¥约 0.02 + 图片¥0.50 = 约¥0.52/张 |

**禁止**：
- 一个场景组不能同时有两个 selected 背景
- 未 selected 背景的场景组不能进入 keyframes 阶段

### 5.4 scenes 阶段门禁

- **进入条件**：storyboard 已 approved
- **通过条件（允许 approve）**：所有场景组均有且仅有一个 selected 背景
- **批量确认**：一键确认所有场景组背景（需全部有 selected），进入 keyframes

---

## 6. API 变更规格

### 6.1 新增路由

```
POST /api/v1/projects/{project_id}/scene-groups/suggest
    → 触发启发式规则，写 scene-groups.json，返回 workflow
    → 需要 storyboard_approved；若 scene-groups.json 已存在则覆盖

GET  /api/v1/projects/{project_id}/scene-groups
    → 返回 scene-groups.json + background-masters.json 合并视图

PUT  /api/v1/projects/{project_id}/scene-groups/{sg_id}
    body: { name?, shot_ids? }
    → 更新场景组；shot_ids 变更时自动处理其他组的归属冲突

POST /api/v1/projects/{project_id}/scene-groups/merge
    body: { source_ids: ["SG001","SG002"], target_name: "合并场景" }

POST /api/v1/projects/{project_id}/scene-groups/{sg_id}/backgrounds/generate
    → 生成一张背景候选（类似旧路由，但归属 SceneGroup 而非 shot）
    → 需要 storyboard_approved

POST /api/v1/projects/{project_id}/scene-groups/{sg_id}/backgrounds
    → 上传背景图片，加为 candidate

PUT  /api/v1/projects/{project_id}/scene-groups/{sg_id}/backgrounds/{bg_id}/select
    → 选定背景母版，同组其他 selected 降为 candidate
```

### 6.2 旧路由处理

```
POST /api/v1/projects/{project_id}/shots/{shot_id}/background/generate
```

保留路由，但实现改为：
1. 找到该 shot 所属的 SceneGroup
2. 若 SceneGroup 不存在，报错 `error_stage: "precondition"`, `detail: "请先在场景与背景阶段建立场景组"`
3. 若存在，重定向逻辑到 scene group 级别的背景生成
4. 在响应头加 `X-Deprecated: use /scene-groups/{sg_id}/backgrounds/generate`

### 6.3 workflow 返回值变更

在 stages 列表中 storyboard 和 keyframes 之间插入：

```python
stage("scenes", "场景与背景", "确认场景分组和每组背景母版",
      status=<见 5.4>,
      decision=scenes_decision,
      can_approve=<所有组有 selected 背景>,
      data={"scene_groups": [...], "all_have_background": bool},
      stage_prompts=("image.background.generate_requested",),
      cost_steps=("image.background.generate_requested",))
```

`keyframes` 阶段的进入条件改为：scenes 已 approved。

---

## 7. 前端规格

### 7.1 新阶段"场景与背景"UI 结构

```
┌─ 场景与背景 ────────────────────────────────────────┐
│  [系统已建议 N 个场景组] [重新生成建议]               │
│                                                     │
│  ┌─ 场景组: 月下独处 ───────────────────────────┐  │
│  │  分镜: S001 S002 S003  [编辑归属]             │  │
│  │  背景候选:                                    │  │
│  │  [图] 候选1 ✓选定  [图] 候选2  [+生成] [+上传]│  │
│  │  预计费用: 约 ¥0.52/张                       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  [一键确认所有场景背景 →进入关键帧]                  │
└─────────────────────────────────────────────────────┘
```

### 7.2 分镜卡变更（storyboard 阶段）

**移除**：
- "用 GPT-image-2 生成背景图片" 按钮
- 背景图片选择下拉和独立上传入口

**新增**：
- "所属场景组：{name}" 标签（点击跳转到 scenes 阶段）
- 构图变体编辑区：景别、机位、光线备注、道具备注

**保留**：
- 已绑定背景图的预览（来源改为 background_master）

### 7.3 背景母版图片地址

`GET /api/v1/projects/{project_id}/files?path={relative_path}` 已有，复用。

---

## 8. 测试用例规格

### 8.1 单元测试（`tests/mv_platform/unit/test_prd002_scene_groups.py`）

**UT-010**：启发式规则按 section 归并分组

```python
def test_suggest_scene_groups_groups_by_section(shots_fixture):
    # shots: S001-S003 section=A, S004-S005 section=B
    # result: 2 个 SceneGroup，SG001.shot_ids=["S001","S002","S003"]
```

**UT-011**：迁移时已有 background 路径创建 BackgroundMaster

```python
def test_migration_creates_background_master_from_existing(project_with_background):
    # shot-references.json version=1, S001.background="assets/.../bg.png"
    # 执行迁移后：
    #   background-masters.json 有一条 BG001, status=selected, source=uploaded
    #   shot-references.json version=2, S001.background_master_id="BG001"
    #   S001.background 字段仍存在（向后兼容）
```

**UT-012**：迁移不存在 visual_score 时静默跳过

```python
def test_migration_skips_when_no_visual_score(project_without_visual_score):
    # 不写任何文件，不抛异常
```

**UT-013**：shot 只能属于一个场景组

```python
def test_shot_cannot_belong_to_two_groups(service, project_id):
    # 把 S001 从 SG001 移到 SG002
    # 结果: SG001.shot_ids 不含 S001，SG002.shot_ids 含 S001
```

**UT-014**：选定背景时同组只能有一个 selected

```python
def test_select_background_deselects_previous(service, project_id):
    # SG001 有 BG001(selected) 和 BG002(candidate)
    # select BG002 → BG001 变 candidate, BG002 变 selected
```

**UT-015**：有未 selected 场景组时不能进入 keyframes

```python
def test_scenes_approve_blocked_when_group_has_no_selected(service, project_id):
    # SG001 没有 selected 背景
    # record_workflow_decision("scenes", "approve") → ApplicationBlocked
```

### 8.2 API 契约测试（`tests/mv_platform/contract/test_prd002_api.py`）

**CT-010**：POST suggest 返回场景组列表

```python
def test_suggest_scene_groups_returns_groups(test_client, project_with_storyboard_approved):
    resp = test_client.post(f"/api/v1/projects/{project_id}/scene-groups/suggest")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["stages"]) == 9  # 新增 scenes 阶段
    scenes_stage = next(s for s in data["stages"] if s["id"] == "scenes")
    assert len(scenes_stage["data"]["scene_groups"]) > 0
```

**CT-011**：PUT 更新场景组名称

```python
def test_update_scene_group_name(test_client, project_with_scene_groups):
    resp = test_client.put(f".../scene-groups/SG001", json={"name": "新名称"})
    assert resp.status_code == 200
    # scenes stage data 中 SG001.name == "新名称"
```

**CT-012**：旧 background/generate 路由返回 deprecated header

```python
def test_old_background_generate_returns_deprecated_header(test_client, ...):
    resp = test_client.post(f".../shots/S001/background/generate")
    assert "X-Deprecated" in resp.headers
```

**CT-013**：workflow stages 包含 scenes 在正确位置

```python
def test_workflow_has_scenes_stage_between_storyboard_and_keyframes(test_client, ...):
    data = test_client.get(f".../workflow").json()
    ids = [s["id"] for s in data["stages"]]
    assert ids.index("scenes") == ids.index("storyboard") + 1
    assert ids.index("keyframes") == ids.index("scenes") + 1
```

### 8.3 浏览器 E2E 测试（`tests/e2e/test_prd002_browser.py`）

**ET-010**：场景与背景阶段可见，且在 storyboard 和 keyframes 之间

```python
def test_scenes_stage_visible_in_nav(page, project_at_scenes):
    nav_items = page.locator(".stage-nav-item").all_text_contents()
    idx_storyboard = nav_items.index("分镜工作台")
    idx_scenes = nav_items.index("场景与背景")
    idx_keyframes = nav_items.index("关键帧选择")
    assert idx_storyboard < idx_scenes < idx_keyframes
```

**ET-011**：分镜卡不再有"生成背景"按钮

```python
def test_shot_card_has_no_generate_background_button(page, project_at_storyboard):
    page.goto("http://127.0.0.1:8792")
    assert page.locator("text=用 GPT-image-2 生成背景图片").count() == 0
    # 改为"所属场景组"标签
    assert page.locator("text=所属场景组").count() > 0
```

**ET-012**：可以在场景与背景阶段生成一张背景候选

```python
def test_generate_background_in_scenes_stage(page, project_at_scenes_with_real_provider):
    # 点击第一个场景组的"生成"按钮
    # 等待最多 120s
    # 断言：出现图片缩略图，状态为"候选"
    # 断言：费用页面有 ¥0.50 图片费用记录
```

**ET-013**：选定背景后"一键确认"按钮变为可用

```python
def test_approve_scenes_enabled_after_all_selected(page, project_at_scenes):
    # 所有场景组都有 selected 背景后
    # 断言："一键确认所有场景背景" 按钮不是 disabled 状态
```

---

## 9. 验收标准

- [ ] UT-010 ～ UT-015 全部通过
- [ ] CT-010 ～ CT-013 全部通过
- [ ] ET-010 ～ ET-011 通过（不需要真实 Provider）
- [ ] ET-012 通过（需要真实 Provider，可选择延后到 P5 全链验收）
- [ ] ET-013 通过
- [ ] 手动检查：用 `qingyi2` 项目，workflow 返回 9 个 stages
- [ ] 手动检查：`scene-groups.json` 和 `background-masters.json` 文件格式正确
- [ ] 手动检查：旧 `shot-references.json` 的 `background` 字段未被删除
- [ ] 手动检查：分镜卡无"生成背景"按钮，有"所属场景组"标签

---

## 10. 废弃与归档说明

**标记为 deprecated（保留代码，加注释）**：
- `service.py` 中 `generate_shot_background()` 方法：注释 `# DEPRECATED: use scene-group level generation`
- API 路由 `POST /shots/{shot_id}/background/generate`：返回 `X-Deprecated` 响应头
- `storyboard` 阶段的 `image.background.generate_requested` prompt 步骤：保留数据，阶段移至 scenes

**不删除任何文件**，不清除任何 shot-references.json 中的旧字段。

---

## 11. 实施顺序建议（给便宜模型）

```
Step 1  读 visual_score.yaml 结构，确认 shot.section 字段存在
Step 2  实现 SceneGroup / BackgroundMaster 数据类和文件读写方法（service.py）
Step 3  实现迁移逻辑（_migrate_to_scene_groups），写单元测试 UT-011/012
Step 4  实现启发式建议（suggest_scene_groups），写 UT-010
Step 5  实现场景组 CRUD + 背景操作逻辑，写 UT-013/014/015
Step 6  修改 get_project_workflow：插入 scenes 阶段，更新 keyframes 门禁
Step 7  新增 API 路由（6.1），写 CT-010/011/012/013
Step 8  修改旧背景生成路由（6.2），加 deprecated header
Step 9  前端：scenes 阶段页面（7.1），修改分镜卡（7.2）
Step 10 全量执行：pytest -k "prd002"，输出 TEST_REPORT_PRD002.md
```

