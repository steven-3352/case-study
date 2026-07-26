---
name: feedback_no-neon-palette
description: "禁用 Dracula 主题霓虹色板(紫/粉/青)和暖红→冷蓝渐变背景,这是\"AI 味\"零容忍的具体落地"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9454e7a7-84bb-426d-88ad-0485259de3b7
---

W27D04 抖音封面用了 `linear-gradient(135deg,#2a0e0e,#0a0e14)` 暗紫红→深蓝黑渐变,被用户当场退稿。根因:`pipeline/p004_video/shared/style.css` 沿用了 Dracula 主题(VS Code/Copilot 圈最常见的霓虹色板),`--purple:#bd93f9 / --pink:#ff79c6 / --blue:#8be9fd` 这三件套是"AI 味"的视觉签名。

**Why:** 之前 memory [[feedback_anti-ai-visual]] 只写了「AI 味零容忍」抽象原则,没具体到色板 hex,导致每次写 HTML 模板时落实不了。

**How to apply:**
- 任何 P004/P00X HTML 模板,主视觉 + 封面 + 大字 + 强调色: 禁用 `var(--purple) / var(--pink) / var(--blue)` 和它们的 hex 值,style.css 里这三个 token 已标 DO NOT USE
- 渐变背景:禁 `linear-gradient(*,#2a0e0e,#0a0e14)` 这一类暖红→冷蓝过渡,改纯黑 `#000` 或 `#0a0e14` 单色
- 强调红:用血红 `#e53935`,不要 `#ff5252`(偏粉) 或 `#ff7e7e`(偏珊瑚)
- 允许真截屏自带的系统蓝/微信绿/淘宝橙(这是真实痕迹不是色板)
- 自检:出主视觉前抠一帧看主色,落在 H=240~290(蓝紫区间) 且非真截屏来源 → 重做
- 全局禁单见 [docs/DECISIONS.md](../../docs/DECISIONS.md) Q9 「禁霓虹色细则」

相关:[[feedback_anti-ai-visual]]
