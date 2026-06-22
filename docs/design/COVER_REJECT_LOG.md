# 封面反例登记

> 用户/视觉设计 Agent 判定 **不可外发** 的封面，记录根因，避免复现。

---

## 2026-06-22 · W26D01 · 抖音 cover.png

**文件：** `publish/2026-W26/D01-美甲撞档/douyin/cover.png`  
**判定：** ❌ **完全不可用**（用户原话）  
**视觉设计验收：** ❌ **未做**（讨论室仅写了 hook 两行文案，未审 render 产出）

### 问题（像素级）

1. **无场景** — 回落 `render.py` 默认「深色暖金径向渐变」，中间 60% 空黑，零美甲/微信/预约语境  
2. **黑金模板感** — kicker 金色描边 pill + 黄底 mark + 棕黑底，与 DECISIONS「忌黑金 PPT / 非报纸风」冲突  
3. **高亮切字** — `mark: 两个人` 只高亮末词，「约了两个人」呈现割裂、括号感  
4. **形式错位** — 定为 F2 强钩子，封面却是纯 typography，无 chat/metric 角标或证据帧  
5. **缩略图测试** — 信息流 1:1 缩略时仅见黑块+黄条，CTR 预期极差  

### 根因链

```
视觉设计 Agent 只输出「两行 hook」文字 brief
  → 无 cover_brief.md / 无 shot_ref / 无 projects/W26D01/coverbg/
  → render.py pick_cover_bg() 第 4 档回落渐变
  → cover_png() 套通用 CSS 模板
  → 无 cover_review 门禁 → 直接进入 publish 包
```

### 应改为

- 底：微信聊天截帧模糊 / 预约表 note 卡 / 门店实拍 blur  
- 主钩子：整句「同一时段约了两个人」或分行但不拆 mark  
- 角标：小 metric「撞档 2 次/周」  
- 须经 `design/cover_review.md` **pass** 后再发布  

---

## 2026-06-22 · W26D03 · 抖音 cover.png

**文件：** `publish/2026-W26/D03-试吃反馈/douyin/cover.png`  
**判定：** ❌ **完全不可用**（用户原话：「完全没有审美，无脑的产出」）  
**视觉设计验收：** ❌ **假 pass**（cover_review 写了 light_split，实际 render 回落黑金渐变）

### 问题（像素级）

1. **无 style** — `topics_content` 未设 `cover.style`，触发 `render.py` 默认黑金径向渐变  
2. **无场景** — 中间 60% 空黑，零试吃/微信群语境  
3. **黑金模板感** — 与 D01 反例同款：kicker 金边 pill + 黄底 mark + 棕黑底  
4. **形式错位** — F2 强钩子却纯 typography，无 chat/metric 证据  
5. **门禁失效** — cover_review 未对照 PNG 签字

### 根因链

```
W26D03 cover 仅写 hook 文案，无 style / panel_detail
  → render_platform cover-only 路径不生成 panel
  → cover_png() 第 5 档回落黑金渐变
  → cover_review 按 spec 文字 pass，未审像素
```

### 已改为

- `style: video_frame` + `at: 1.2`（P004 成片 punch 定格「反馈17份」）  
- `render.py`：抖音 **禁止** `light_split` / `phone_ui`  
- 备选 `douyin_punch`（全屏黑底大字，无分屏）

---

## 2026-06-22 · W26D03 · 抖音 cover v2（light_split）

**文件：** 同上 · light_split + 右栏微信窗口  
**判定：** ❌ **布局违和**（用户：「100% 平台不喜欢，用户看了也很怪」）

### 问题

1. **分屏幻灯片** — 左 58% 文案 + 右 macOS 窗口 mock，像 B2B 提案页  
2. **非抖音原生** — 信息流里像 PPT 封面，不像短视频定格  
3. **与成片脱节** — 视频是 punch/agent_grid，封面却是另一套视觉语言

### 已改为

- `video_frame @1.2s` — 直接截取成片 punch 镜，封面=视频缩略图

---
