# 动效技术方案 · motion_tech_plan · W28D03 AI 陪练英语口语

> 工种：动效技术导演 / Web 3D 技术导演
> 依赖：form_competition.md（方案 A · 家族 pipeline · 无 Web 3D/GSAP）· form_strategy.md（10 段 · 5 种形式 ID · 无复杂动效）· design_language.md（禁 GSAP 数字跳动 · 禁复杂 HTML 动效）
> 状态：`draft_self_generated · SKIP · 登记理由` · 2026-07-04

## 0. SKIP 判断

**本条 SKIP motion_tech_plan 深度审查**，理由如下：

### SKIP 触发条件（对照 CLAUDE.md 门禁「使用 Web 3D/GSAP/复杂 HTML 动效但无 motion_tech_plan → 禁止 render」）

| 触发条件 | 本条是否触发 | 说明 |
|----------|-------------|------|
| 使用 GSAP 库 | ❌ 否 | form_strategy 明确"少量 SVG 覆盖 + CSS transition · 不引 GSAP 库" |
| 使用 Three.js / Web 3D | ❌ 否 | 全片无 3D 元素 · 全部走 2D pipeline |
| 使用复杂 HTML 动效（Lottie / Rive / 自研 canvas） | ❌ 否 | 只用 drawtext + drawbox（ffmpeg 原生）+ 静态 SVG 淡入淡出 |
| 使用 GSAP skills 8 件套 | ❌ 否 | 本条不启用；项目 GSAP skills 备查但本条不激活 |
| 使用 Remotion / HyperFrames 视频合成 | ❌ 否 | OpenMontage decision=blocked_infrastructure（见 openmontage_brief.md）· 不启用 |

**结论：** 本条**不触发** motion_tech_plan 门禁的任一条件，SKIP 合法。

## 1. 本条实际动效清单（走原生 pipeline 能力）

| 动效类型 | 使用位置 | 实现方式 | 风险 |
|----------|----------|----------|------|
| drawtext 大字滑入 | M1 3s / M2 3-8s / M5 20-24s / M6 24-36s / M8 42-48s / M9 48-54s / M10 54-58s | ffmpeg drawtext + alpha 淡入 0.3s | 无（ffmpeg 原生能力 · D02 已跑通） |
| drawbox 描边框 | M4 15-20s（反例 accent_red 描边）· M6 五段标签底色 | ffmpeg drawbox + accent_soft/accent_red | 无（原生） |
| SVG 静态高亮框（M6 role prompt 五段） | M6 24-36s | 静态 SVG + CSS opacity transition | 无（无 JS · 无 GSAP · 纯 CSS） |
| B-roll 淡入淡出（M1/M8） | M1 0-3s / M8 42-48s | ffmpeg xfade | 无（原生） |
| 分屏静图（M5） | M5 20-24s | ffmpeg vstack / hstack + 2px 分割线（drawbox） | 无（原生） |
| 真机屏录接入（M6/M7） | M6 24-36s / M7 36-42s | QuickTime 屏录导出 mp4 + ffmpeg concat/trim | 无（原生 · 需准备真机 role prompt 演示样本） |
| 字幕烧录 | 全片 3-58s | pipeline gen_subs → SRT/ASS → ffmpeg-full libass 烧录 | 无（memory `feedback_pipeline-burn-subs` 已固化路径） |
| 无 BGM · VO 全程覆盖 | 3-58s | MiniMax / Edge TTS 生成 VO · loudnorm -16 dB | 无（memory `feedback_dense-vo-no-bgm-default` + `feedback_dense-vo-no-dead-air`）· 前 3s 环境音钉子 |

## 2. 排除的动效方案（曾考虑但主动排除）

| 曾考虑 | 排除理由 |
|--------|---------|
| GSAP TextPlugin 数字滚动 | design_language.md 禁项 · 会显 AI 味 · 数据锚数字用 punch-in 静态大字 |
| GSAP MotionPath role prompt 五段沿路径滑入 | 过度复杂 · 静态 SVG + CSS opacity 就够用 · 无技术必要 |
| Three.js 3D 手机模型 | 与 skin.tone_direction「深夜克制」不匹配 · 会显做作 · 真机屏录足够真实 |
| Lottie 卡通动画（AI 陪练拟人化） | 违反 chaos_must_be_real_footage 铁律 · Q9 明确禁"AI 生图作主视觉" |
| Remotion 视频合成（TypeScript 组件化） | 与 OpenMontage 同 blocked_infrastructure · 项目内无成功案例 · 首跑风险高 |
| HTML+GSAP 居中大字动效 | memory `feedback_anti-ai-visual` 明确警告"居中对齐是错的起点" |

## 3. 若未来升级动效的触发条件

若首轮数据回填出现以下情况，可评估升级到复杂动效：

| 数据信号 | 可评估的升级方案 | 需先满足的前置 |
|----------|------------------|----------------|
| M6 role prompt 段位完播断崖（>10% 跳出） | 引入 GSAP MotionPath 让五段标签依次沿 role prompt 文字滑入，增强动作性 | 先通过 form_competition 回炉 · 通过本文件正式动效审查 |
| completion_3s < 55%（钩子失效） | 引入 OpenMontage documentary montage 增强首镜电影感（**先解 blocked_infrastructure**） | openmontage_brief.decision_review_trigger 满足 |
| 收藏率 < 4%（P5-P7 prompt 页收藏动机弱） | 加 SVG 微动效（如光标闪 / 复制提示浮标）· 但仍不引 GSAP · 用 CSS keyframes | 无（属轻度升级） |

## 4. 交付清单（给下一环节）

- **storyboard.yaml**：本文件无技术约束需带入，直接按 form_strategy.md 10 段镜头 + design_language.md token 生成分镜
- **pipeline 出片**：走 `pipeline/p004_video/` 或 `pipeline/render_p001.py` 混合路径（P001 出图 + drawtext + ffmpeg 合成 · 无 GSAP JS 依赖）
- **音画方案**：无 BGM（密 VO 演示型 · 默认 off）· VO 全程覆盖 · 字幕烧录

## 5. 签字

- **动效技术导演：** SKIP_no_advanced_motion · 本条无 Web 3D / GSAP / 复杂 HTML 动效 · 全走 ffmpeg 原生 + 静态 SVG + 真机屏录
- **编导采纳：** pass_skip_no_risk
- **下一步：** 进入 storyboard.yaml + audio_plan.yaml

## 6. Audience-First 自查三问（motion_tech_plan 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ 无过度动效 · 保留深夜克制感 · drawtext 大字 punch-in 干脆有力 · 学英语党不会觉得"这条视频在炫技" |
| 画面**观赏性**够吗？ | ✅ 10 段形式切换（B-roll + 大字 + UI 分屏 + 静图对比 + 屏录 + SVG 打点）+ 每 3-6s 变化点 · 无需复杂动效补 |
| 内容**真材实料**吗？ | ✅ 真机屏录 role prompt + Pexels 深夜 B-roll + 讯飞录数据锚截屏 · 全部真实素材 · 无 AI 生图/合成动效 |
