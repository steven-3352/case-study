---
name: gsap-skills-available
description: GSAP 全套 skill 在 Claude Code 全局可用（core/timeline/scrolltrigger/plugins/performance/utils/react/frameworks），case-study 项目当前未用但保留能力
metadata: 
  node_type: memory
  type: reference
  originSessionId: 90dfb1a5-fc7e-4105-a51c-31f65c55b631
---

# GSAP Skills 能力登记（case-study 项目）

## 当前状态

**项目内未使用**。case-study 是 Python + Chrome 截图 + GPT-image-2 + ffmpeg/剪映的静态图文/视频流水线，没有 package.json、没有前端动效层、没有任何 `gsap` 引用。

## 但能力随时可调

Claude Code 全局已注册 8 个 GSAP skill：

| Skill | 触发场景 |
|-------|----------|
| `gsap-core` | gsap.to/from/fromTo、easing、stagger、matchMedia（响应式 + prefers-reduced-motion） |
| `gsap-timeline` | 时间线、关键帧编排、position 参数 |
| `gsap-scrolltrigger` | 滚动驱动动画、pin、scrub、视差长页 |
| `gsap-plugins` | ScrollTo / ScrollSmoother / Flip / Draggable / SplitText / ScrambleText / SVG / 物理 |
| `gsap-performance` | 60fps、避免 layout thrash、will-change、批量 |
| `gsap-utils` | clamp / mapRange / interpolate / random / snap / toArray / wrap |
| `gsap-react` | useGSAP、refs、context、cleanup（React/Next.js） |
| `gsap-frameworks` | Vue/Svelte/Nuxt/SvelteKit 生命周期与作用域 |

来源仓库：https://github.com/greensock/gsap-skills.git

## case-study 何时可能用到

未来如果做以下事情，优先调 GSAP skill 而不是手写动画：

- **项目演示落地页**：小老板看到内容后跳到的"我用 AI 做了什么"长滚动案例页（私信转化承接，参考 [[gpt-image-2-api]] 的报纸风也可以做成滚动版）
- **作品集/简历型 web 组件**：交互式时间线、Before/After 对比滑块、ScrollTrigger 拆解动画
- **视频内嵌网页动效**：用 GSAP 做网页动画 → OBS/QuickTime 录屏 → 当 B-roll 进剪映
- **轮播图替代方案**：当报纸风出图（P002）不适合时，用 HTML+GSAP 拼可控版面再截图

## 不适合用的场景

- 当前 P001（真实截图风）/ P002（报纸风出图）流水线 —— 这两条已经跑通，不要为了用 GSAP 重写
- 纯静态图文 —— 不需要动效就别引入
