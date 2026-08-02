# PRD-003：组合首帧精化

> **状态**：待实施  
> **优先级**：P3  
> **前置条件**：PRD-002 验收通过（scenes_approved 门禁依赖 scenes 阶段存在）  
> **负责模型**：便宜模型实现，Opus 验收  
> **解锁**：PRD-004（视频 Provider 对接）

---

## 1. 背景与问题陈述

### 1.1 当前状态

"组合首帧"（keyframe）是视频模型的完整场景第一帧：人物 + 背景已合成、构图已确定。
但当前实现存在三个问题：

**问题 1：元数据不完整**  
`shot-references.json` 里 keyframes 是路径字符串数组，没有记录：
- 使用了哪个背景母版（`background_master_id`）
- 使用了哪些人物资产
- 中/英文提示词是什么
- 是系统生成还是用户上传
- 单张花费

`image-generation-audit.json` 只记录了 `source_prompt_hash`（哈希），不记录明文提示词，
用户和后续模型无法追溯"这张图是怎么生成的"。

**问题 2：前置条件错误**  
`generate_shot_keyframe()` 检查 `storyboard_approved`（service.py:1505），
但 PRD-002 引入了 scenes 阶段，正确前置条件应为 `scenes_approved`。

**问题 3：UI 没有解释用途**  
页面没有说明"这是视频模型的完整第一帧"，用户可能误以为是另一张立绘或背景图。

---

## 2. 目标与非目标

### 目标

1. `shot-references.json` 升至 v3：keyframes 数组元素从路径字符串改为元数据对象
2. 生成和上传均记录：source、background_master_id、character_ids、prompt_zh、prompt_en、model、cost_yuan
3. `generate_shot_keyframe` 前置条件改为 `scenes_approved`
4. workflow 返回每张 keyframe 的完整元数据
5. 前端关键帧选择阶段显示：用途说明 + 每张候选的来源/背景/提示词/费用/状态
6. 批量确认：所有镜头均有 selected_keyframe 后，一键全部确认进入单镜制作

### 非目标

- 不改变 `image-generation-audit.json` 的结构（只在 shot-references.json 里补信息）
- 不实现 per-keyframe 重试或取消功能（留给后续）
- 不改变图片生成的核心逻辑（`_generate_shot_image` 内部不变，只补元数据写入）
- 不实现多候选批量生成（每次一张，按需追加）

---

## 3. 数据模型规格

### 3.1 `shot-references.json` 升至 v3

keyframes 数组元素从字符串变为对象，**兼容旧字符串**（读时自动升级）：

```json
{
  "version": 3,
  "shots": {
    "S001": {
      "background": "assets/...",
      "background_master_id": "BG001",
      "background_variant": { "shot_size": "medium", "camera_angle": "eye_level" },
      "keyframes": [
        {
          "path": "assets/generated/keyframes/S001-abc123.png",
          "source": "generated",
          "background_master_id": "BG001",
          "character_ids": ["C001"],
          "prompt_zh": "夜晚庭院，青衣站立...",
          "prompt_en": "night garden, character standing...",
          "model": "gpt-image-2",
          "request_id": "image-abc123",
          "cost_yuan": 0.5,
          "created_at": "2026-08-01T21:00:00+08:00"
        }
      ],
      "selected_keyframe": "assets/generated/keyframes/S001-abc123.png",
      "keyframe_selected_at": "2026-08-01T21:01:00+08:00"
    }
  }
}
```

字段约束：
- `source`：`"generated"` | `"uploaded"` | `"legacy"`（迁移旧条目用）
- `background_master_id`：可为空字符串（上传时无法确定）
- `character_ids`：可为空数组
- `prompt_zh` / `prompt_en`：上传时为空字符串
- `cost_yuan`：上传时为 0

### 3.2 兼容性读取规则

`_read_keyframe_entries(shot_refs_shot: dict) -> list[dict]` 辅助函数：

```python
def _read_keyframe_entries(shot: dict) -> list[dict]:
    result = []
    for item in shot.get("keyframes", []):
        if isinstance(item, str):
            result.append({"path": item, "source": "legacy", "background_master_id": "",
                           "character_ids": [], "prompt_zh": "", "prompt_en": "",
                           "model": "", "request_id": "", "cost_yuan": 0.0, "created_at": ""})
        elif isinstance(item, dict) and item.get("path"):
            result.append(item)
    return result
```

**不执行文件写入迁移**：读时即时升级，只有下次写入（生成/上传）才会将 v3 格式写回文件。
这样不引入额外的迁移步骤，旧字符串条目自然消亡。

---

## 4. 业务逻辑规格

### 4.1 前置条件更新

**R-030**：`generate_shot_keyframe()` 前置条件改为：

```python
if decisions.get("scenes", {}).get("action") != "approve":
    raise ApplicationBlocked(
        "scenes approval is required before keyframe generation",
        error_stage="precondition", error_category="precondition",
    )
```

同时检查：
- 该 shot 的 `background_master_id` 非空（即该镜已绑定背景母版）
- 项目有至少一个有效人物资产

若背景母版未绑定：
```python
raise ApplicationBlocked(
    "shot has no background master, please complete scenes stage first",
    error_stage="precondition", error_category="precondition",
)
```

### 4.2 生成时保存元数据（`_generate_shot_image`）

**R-031**：在 output_kind == "keyframes" 分支写入 shot-references.json 时，
将字符串路径替换为元数据对象：

```python
entry = {
    "path": relative_text,
    "source": "generated",
    "background_master_id": references["shots"].get(shot_id, {}).get("background_master_id", ""),
    "character_ids": [c["id"] for c in context["characters"]],
    "prompt_zh": context.get("_prompt_zh", ""),   # 见 R-032
    "prompt_en": prompt,                           # 已有变量
    "model": getattr(provider, "model", ""),
    "request_id": request_id,
    "cost_yuan": 0.5,
    "created_at": datetime.now(timezone.utc).isoformat(),
}
```

**R-032**：`_generate_shot_image` 需要从提示词 catalog 读取中文任务提示词并传入 context，
以便 R-031 能保存 `prompt_zh`。具体：在 `_generate_shot_image` 中，
调用 `_translate_image_prompt` 前先读取 `prompts[event_type]`，存入 `context["_prompt_zh"]`。
该字段仅用于写元数据，不传入 LLM。

### 4.3 上传时保存元数据（`import_shot_keyframe`）

**R-033**：`import_shot_keyframe` 写入 shot-references.json 时，
把路径字符串改为元数据对象：

```python
entry = {
    "path": relative_text,
    "source": "uploaded",
    "background_master_id": "",
    "character_ids": [],
    "prompt_zh": "", "prompt_en": "",
    "model": "", "request_id": "",
    "cost_yuan": 0.0,
    "created_at": datetime.now(timezone.utc).isoformat(),
}
```

并更新：`candidates.append(entry)`（替代原来的 `candidates.append(relative_text)`）

### 4.4 `selected_keyframe` 字段保持路径字符串

`selected_keyframe` 继续存字符串路径，不改为对象。
这样 `generate_shot_keyframe`（include_background=True）读取 selected_keyframe 时
不需要改现有路径解析逻辑。

### 4.5 workflow 返回值更新

**R-034**：`get_project_workflow` 读取每个 shot 的 keyframes 时，
使用 `_read_keyframe_entries()` 返回对象列表，
并在每个 shot 的数据中补充：

```python
"keyframe_entries": [
    {
        "path": entry["path"],
        "source": entry["source"],
        "background_master_id": entry["background_master_id"],
        "character_ids": entry["character_ids"],
        "prompt_zh": entry["prompt_zh"],
        "model": entry["model"],
        "cost_yuan": entry["cost_yuan"],
        "created_at": entry["created_at"],
        "is_selected": entry["path"] == selected_keyframe,
    }
    for entry in keyframe_entries
],
```

保留原有 `keyframes`（路径字符串列表）和 `selected_keyframe` 字段不变，
`keyframe_entries` 是新增字段，前端可选择使用。

---

## 5. API 变更规格

### 5.1 不新增路由

所有变更在现有路由的实现层面完成：
- `POST .../keyframes/generate` — 内部改用 R-031 写元数据
- `POST .../keyframes` — 内部改用 R-033 写元数据
- `PUT .../keyframes/selection` — 保持不变（仍传路径字符串）
- `GET .../workflow` — 返回新增 `keyframe_entries` 字段

### 5.2 `allowed_stages` 更新

service.py:616 的 `allowed_stages` 加入 `"scenes"`：

```python
allowed_stages = {"story", "storyboard", "scenes", "keyframes", "shots", "delivery"}
```

---

## 6. 前端规格

### 6.1 阶段说明文案

在关键帧选择阶段顶部显示固定说明（不可折叠）：

> **组合首帧是什么？**  
> 组合首帧是视频模型的完整场景第一帧：人物已合成到背景中，构图、景别、光线已确定。  
> 它不是立绘，也不是背景图，而是视频的起始画面。每镜必须有一张被确认的组合首帧才能进入视频生成。

### 6.2 每镜候选列表

每个 shot 展开后显示：

```
S001 | 月下独处（来自场景组）
┌─ 候选 1 [已选定 ✓] ────────────────────────────────┐
│ [图片缩略图 120×180]                                │
│ 来源: 系统生成  背景: 月下独处-主版  人物: 青衣      │
│ 模型: gpt-image-2  费用: ¥0.50  时间: 08-01 21:00  │
│ 提示词: [展开查看中文提示词]                         │
└─────────────────────────────────────────────────────┘
┌─ 候选 2 ────────────────────────────────────────────┐
│ [图片缩略图]  来源: 用户上传  背景: 不适用            │
│ [选定此帧]                                          │
└─────────────────────────────────────────────────────┘
[+ 生成新候选（约¥0.52）]  [+ 上传]
```

若 `background_master_id` 为空（scenes 未完成），"生成新候选"按钮显示为：
`[场景组背景未确认，请先完成场景与背景阶段]`（disabled）

### 6.3 批量确认

所有 shot 均有 `selected_keyframe` 后，底部出现：

```
✓ 全部 25 镜已选定组合首帧
[一键确认所有关键帧 → 进入单镜制作]
```

点击后调用 `POST .../workflow/keyframes/decision`，body: `{"action": "approve"}`。

### 6.4 候选图片展示

复用现有 `GET /api/v1/projects/{project_id}/files?path=...` 加载图片。
使用 `keyframe_entries[].path` 作为 path 参数。

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd003_keyframes.py`）

**UT-020**：生成关键帧时写入元数据对象而非路径字符串

```python
def test_generate_keyframe_writes_metadata_entry(service, project_with_scenes_approved):
    service.generate_shot_keyframe(project_id, "S001")
    refs = service._shot_references(root)
    entry = refs["shots"]["S001"]["keyframes"][0]
    assert isinstance(entry, dict)
    assert entry["source"] == "generated"
    assert entry["background_master_id"] == "BG001"
    assert entry["prompt_en"] != ""
    assert entry["cost_yuan"] == 0.5
    assert entry["model"] != ""
```

**UT-021**：上传关键帧时写入元数据对象

```python
def test_import_keyframe_writes_metadata_entry(service, project_id, tmp_png_file):
    service.import_shot_keyframe(project_id, "S001", tmp_png_file, "frame.png")
    refs = service._shot_references(root)
    entry = refs["shots"]["S001"]["keyframes"][0]
    assert entry["source"] == "uploaded"
    assert entry["cost_yuan"] == 0.0
    assert entry["prompt_en"] == ""
```

**UT-022**：旧字符串格式在 `_read_keyframe_entries` 中被升级为 legacy 对象

```python
def test_read_keyframe_entries_upgrades_strings(shot_with_string_keyframes):
    entries = _read_keyframe_entries(shot_with_string_keyframes)
    assert all(isinstance(e, dict) for e in entries)
    assert entries[0]["source"] == "legacy"
    assert entries[0]["path"] == "assets/generated/keyframes/S001-old.png"
```

**UT-023**：scenes 未 approved 时生成关键帧报错

```python
def test_generate_keyframe_blocked_without_scenes_approval(service, project_with_storyboard_approved):
    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_keyframe(project_id, "S001")
    assert exc_info.value.error_stage == "precondition"
    assert "scenes" in str(exc_info.value).lower()
```

**UT-024**：background_master_id 为空时生成关键帧报错

```python
def test_generate_keyframe_blocked_without_background_master(service, project_with_scenes_approved_no_bg):
    with pytest.raises(ApplicationBlocked) as exc_info:
        service.generate_shot_keyframe(project_id, "S001")
    assert "background master" in str(exc_info.value).lower()
```

**UT-025**：workflow 返回 keyframe_entries 列表

```python
def test_workflow_includes_keyframe_entries(service, project_with_keyframes):
    wf = service.get_project_workflow(project_id)
    shots = next(s for s in wf["stages"] if s["id"] == "keyframes")["data"]["shots"]
    assert "keyframe_entries" in shots[0]
    assert shots[0]["keyframe_entries"][0]["is_selected"] in (True, False)
```

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd003_api.py`）

**CT-020**：scenes 未 approved 时 /keyframes/generate 返回 423 + precondition stage

```python
def test_keyframe_generate_without_scenes_approval_returns_423(test_client, project_storyboard_approved):
    resp = test_client.post(f".../shots/S001/keyframes/generate")
    assert resp.status_code == 423
    assert resp.json()["error_stage"] == "precondition"
```

**CT-021**：workflow 返回的 keyframe_entries 包含 source 字段

```python
def test_workflow_keyframe_entries_have_source(test_client, project_with_generated_keyframe):
    data = test_client.get(f".../workflow").json()
    shots = next(s for s in data["stages"] if s["id"] == "keyframes")["data"]["shots"]
    entry = shots[0]["keyframe_entries"][0]
    assert entry["source"] in ("generated", "uploaded", "legacy")
```

**CT-022**：upload keyframe 后 workflow 中 keyframe_entries 包含该条

```python
def test_upload_keyframe_appears_in_workflow(test_client, project_with_scenes_approved, png_bytes):
    test_client.post(f".../shots/S001/keyframes", content=png_bytes, params={"filename": "f.png"})
    data = test_client.get(f".../workflow").json()
    shots = next(s for s in data["stages"] if s["id"] == "keyframes")["data"]["shots"]
    assert any(e["source"] == "uploaded" for e in shots[0]["keyframe_entries"])
```

### 7.3 浏览器 E2E 测试（`tests/e2e/test_prd003_browser.py`）

**ET-020**：关键帧阶段顶部有组合首帧说明文案

```python
def test_keyframes_stage_shows_explanation(page, project_at_keyframes):
    page.goto("http://127.0.0.1:8792")
    # 导航到关键帧选择阶段
    assert page.locator("text=视频模型的完整场景第一帧").is_visible()
```

**ET-021**：候选列表显示来源和费用信息

```python
def test_keyframe_candidate_shows_metadata(page, project_with_keyframe_candidate):
    # 断言：候选卡片含"系统生成"或"用户上传"文字
    assert page.locator("text=系统生成").count() > 0 or page.locator("text=用户上传").count() > 0
    # 断言：候选卡片含"¥0.50"或"¥0"
    assert page.locator("text=¥0").count() > 0
```

**ET-022**：scenes 未完成时"生成新候选"按钮为 disabled

```python
def test_generate_keyframe_disabled_without_scenes(page, project_at_keyframes_no_scenes):
    btn = page.locator("button:has-text('生成新候选')")
    assert btn.is_disabled() or btn.count() == 0
    assert page.locator("text=场景组背景未确认").is_visible()
```

**ET-023**：全部选定后批量确认按钮可用

```python
def test_batch_confirm_enabled_when_all_selected(page, project_with_all_keyframes_selected):
    btn = page.locator("button:has-text('一键确认所有关键帧')")
    assert not btn.is_disabled()
```

---

## 8. 验收标准

- [ ] UT-020 ～ UT-025 全部通过
- [ ] CT-020 ～ CT-022 全部通过
- [ ] ET-020 ～ ET-023 全部通过
- [ ] 手动检查：生成一张关键帧后，`shot-references.json` 中该条目为对象（非字符串）
- [ ] 手动检查：workflow 返回的 `keyframe_entries` 包含 `prompt_en`（非空）
- [ ] 手动检查：无 scenes_approved 时，前端生成按钮被禁用，页面有中文说明
- [ ] 手动检查：页面所有文字仍为中文，无新增英文状态码暴露

---

## 9. 废弃与归档说明

**无废弃**。本 PRD 全部是在现有代码上追加字段，不删除任何方法或路由。

旧字符串格式的 keyframe 路径通过 `_read_keyframe_entries()` 兼容读取，
无需专项迁移脚本。

---

## 10. 实施顺序建议（给便宜模型）

```
Step 1  实现 _read_keyframe_entries() 兼容函数，写 UT-022
Step 2  更新 import_shot_keyframe：写元数据对象，写 UT-021
Step 3  更新 _generate_shot_image keyframes 分支：写元数据对象（含 prompt_zh），写 UT-020
Step 4  更新 generate_shot_keyframe：前置条件改为 scenes_approved，写 UT-023/024
Step 5  更新 allowed_stages 加 "scenes"
Step 6  更新 get_project_workflow：返回 keyframe_entries，写 UT-025
Step 7  新增 API 契约测试 CT-020/021/022
Step 8  前端：关键帧阶段说明 + 候选元数据展示 + 批量确认按钮
Step 9  前端：生成按钮无背景母版时 disabled 状态
Step 10 全量执行：pytest -k "prd003"，输出 TEST_REPORT_PRD003.md
```
