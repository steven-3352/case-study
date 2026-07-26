---
name: feedback_contrast-hook-3s
description: P004+ 视频开头必须用 chaos→punch→reveal 三连反差钩子（1.0s+0.6s+1.4s），不直接进 HTML 单版面打字机
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aa552821-755b-48d2-86a9-de9821d9721e
---

P004 及后续视频的前 3 秒必须按「真实糙素材 → 黑底大字 → 系统就位」三连反差结构开头。
不能像旧 01_hook.html 那样单版面打字机直进。

**Why:** 2026-06-21 用户拿一条 38s 抖音爆款做范本（720×1280，前 3s 4 个 scene cut，平均 0.6s 一刀），明确要求项目套用此节奏抓注意力增加完播率。同时与 [[feedback_anti-ai-visual]] 一致——AI 味的 chaos 帧是无效素材，必须真实手机自拍或 Pexels 真人素材。

**How to apply:**
- `pipeline/p004_video/storyboard.yaml` 头三个 scene 固定为 `01a_chaos`(broll 1.0s)/`01b_punch1`(html 0.6s)/`01c_punch2`(html 1.4s)
- 钩子结构有两种,按需选: ① **chaos→punch→reveal** (用 01c_reveal.html 9 圆点) — 适合带 reveal 揭示动作的选题; ② **chaos→punch1→punch2** (双 black 静帧,01b_punch.html 复用两次) — 适合"重复/反复/又是"类痛点,留白到反转点用全片自证。K1 实体店老板版用②(见 [[project_audience-brick-mortar]])
- chaos 来源优先级: iPhone 自拍 > Pexels (用 `fetch_broll.py`) > Storyblocks > Sora 兜底
- punch 必须纯黑底 + 字号占 80% 宽 + 无渐变无阴影;只播 0.08s scale-in 后静帧到底
- reveal/punch2 接当前 scene 主视觉,色彩从冷过渡或继续压抑(取决于结构①还是②)
- 素材组登记在 `assets/broll/catalog.yaml` 的 `contrast_pairs:` 段,每形态(演示/知识/带货/出镜)各备一组
- 反例: 第 1 帧居中对称、AI 出图、标题卡、品牌 logo —— 命中任一立刻划走
