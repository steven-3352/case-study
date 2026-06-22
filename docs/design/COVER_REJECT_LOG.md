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
