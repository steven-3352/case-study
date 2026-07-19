# 动效技术方案 · T041 · content v3 · form v4

## 适用性

GSAP 只用于未来事故首次逆推、时间线逆行、双轮响应签和验尸票盖章。这些连续关系分别服务 `completion_3s`、`completion_rate`、理解、收藏与评论；静态 Prompt 阅读段不持续动画。

## 可读性

1080×1920 下主要问句不少于 56px，证据正文不少于 31px、行高不低于 1.45。当前死因是时间线唯一高亮；Prompt 镜隐藏普通字幕并静止至少四秒。

## 资产

真实 A/B 文本从 `insights/premortem_ab_evidence.md` 读取；虚构计划常驻“测试案例”。GSAP 和 helper 使用仓库本地文件，SFX 只取登记的 CC0 本地资产。

## 导出

MiniMax 真实句段时长先锁定，再生成 runtime storyboard；`capture_frames.py` 对 paused timeline 按30fps确定性seek，PNG经libx264 yuv420p编码。禁止用估时拉伸镜头。

## 风险

风险包括D01同构、逆向关系看不懂、长Prompt溢出、字幕遮挡、seek状态不确定。先渲首帧/中点/末帧，再抽动态关键帧和做媒体体检；任一失败退回模板。

> 状态：`draft` · 待技术双评 · 未许可 render

- 路线：P001 真实文本资产 + 专属 HTML/GSAP 场景 + `capture_frames.py` 确定性截帧。
- master timeline：`gsap.timeline({paused:true, defaults:{ease:'power2.out'}})`；每个专属场景独立以 `accident / plan / ordinary / paths / evidence / save / cta` 语义标签起始，真实 TTS 窗口由 runtime storyboard 注入。
- 同时动作用 timeline position parameter，不用分散 `delay`。
- 响应签落位：`scale/autoAlpha`，证物线扣合：SVG 线用 `scaleX` + transformOrigin，时间线倒放：元素 `x` 和 `scale`。
- 文本不做逐字运动；只按语义行显示，避免中文抖动和阅读负担。
- 后续若多个 `fromTo` 操作同一属性，后续 tween 须 `immediateRender:false`。
- 性能：只动 transform/autoAlpha；禁止 width/height/top/left/filter 长时动画。
- 已实现专属场景：`d02_w30_failure_rewind.html`、`d02_w30_fixed_plan.html`、`d02_w30_a_risk_list.html`、`d02_w30_ab_guess.html`（结构对照，非竞猜）、`d02_w30_reveal.html`、`d02_w30_prompt_strip.html`、`d02_w30_boundary_cta.html`。

阻塞：TTS 时长尚未产生；本文未经第二技术 reviewer。
