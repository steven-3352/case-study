---
name: cjk-bold-font-ghosting-fix
description: 大字标题重影根治 — PingFang 无真 900 字重致 Chrome faux-bold 涂抹重影；装思源黑体 Heavy + 改 font-family 栈
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

Chrome headless 渲染中文大字标题（font-weight 800/900、字号 ≥60px）出现「重影/双描边」= faux-bold 涂抹伪影，根治方案如下。

**Why:** font-family 若以 `-apple-system, "PingFang SC"` 打头，中文字形落到苹方，而苹方最粗只到 Semibold（~600），没有真 900 Heavy 面。Chrome 对缺失字重用算法合成加粗（把描边横向涂抹），字号越大、字重越高越明显 → 80px/900 时肉眼可见重影。英文走 SF Pro 有真字重不受影响，所以重影只出现在中文大字。

**How to apply:**
- 字体已装：`~/Library/Fonts/SourceHanSansSC-{Heavy,Normal,Bold}.otf`（思源黑体简中 · OFL 免费商用 · Heavy=真 900）。来源 jsdelivr（国内可达，GitHub 被墙）：`https://cdn.jsdelivr.net/gh/adobe-fonts/source-han-sans@release/OTF/SimplifiedChinese/SourceHanSansSC-{Heavy,Normal,Bold}.otf`
- 所有 `gen_ui_*.py` / `gen_xhs_carousel_*.py` 的 BASE_CSS font-family 一律用：
  `font-family: "SF Pro Text", "Source Han Sans SC", "PingFang SC", sans-serif;`
  （英文→SF Pro 清晰，中文→思源真字重零重影，PingFang 兜底）
- 现有 `font-weight: 900/800/700` 数值**无需改**，会自动落到思源真字面。
- 已修：W28D07 的 gen_ui_w28d07.py + gen_xhs_carousel_w28d07.py（p1_cover 900 大字实测重影消失）。
- 验证：改栈后重出 PNG，肉眼查最大字号/最高字重那张（如封面标题）是否单描边。
- D01–D06 是 golden reference，不回炉重渲；字体已全局装好，未来条目直接用新栈即可。

关联 [[feedback_anti-ai-visual]] · [[feedback_pipeline-full-platform-output]]
