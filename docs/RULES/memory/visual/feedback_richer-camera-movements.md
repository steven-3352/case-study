---
name: feedback_richer-camera-movements
description: 用户要求重点运用复杂运镜提升视觉效果；列出8类必用镜头手法
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c1075b53-4425-4e4d-ab2a-ebd66cd0f73e
---

以后纸片人 MV 及所有运动画面要重点运用复杂运镜，不能只靠 push_in / pull_out / dutch / orbit 四种简单手法。

**必须在 SOLO_SEQ / GRP_SEQ 中覆盖的运镜类型（8 类）：**
- 摇镜 `pan`：横向平移带视差
- 甩镜头 `whip_right` / `whip_left`：快速甩动+残影
- 跟拍 `track`：立绘跟焦微移横走
- 仰拍 `low_angle`：向上视角，人物高耸
- 俯视 `bird_eye`：轻度俯压
- 环绕 `orbit_fast`：大弧度高频环绕（区别于慢摆 orbit）
- 旋转 `spin`：入场快速旋转定住
- 推 `push_in` / 拉 `pull_out`（保留原有）

**Why:** 用户明确要求"以后要重点运用复杂运镜提升画面视觉效果"——单靠静态缩放不够，需让每个子镜的运镜类型各异、有戏剧感。

**How to apply:** 每次写 `SOLO_SEQ`/`GRP_SEQ` 或手排 `build_shots()` 时，循环里必须出现≥5 种不同 `cam` 类型；禁止连续 3 镜用同一 cam；分镜表里先列 cam 类型再写参数。
