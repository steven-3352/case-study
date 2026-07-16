# 动效技术方案 · motion_tech_plan · T040 让AI说真话·致命漏洞法

> 工种:动效技术导演
> 依赖:`design/motion_storyboard.md`(逐秒9字段)· `design/form_strategy.md`(逐镜data_lever/成本/风险)
> 触发原因:④指令卡使用 GSAP(kinetic_typography)→ 按 CLAUDE.md 门禁"使用Web3D/GSAP/复杂HTML动效但无motion_tech_plan→禁止render",本条**必须**产出此文件才可进入 storyboard/render

## 0. 入口必读打勾

- [x] `docs/SYSTEM.md` §4.2 候选实现清单(GSAP在候选池内,非默认路线)
- [x] `.agents/skills/` GSAP skills 8 件套已确认项目已装(gsap-core/gsap-timeline 等)
- [x] 按用户 2026-07-16 要求,本条不参照任何历史选题的 motion_tech_plan 做借鉴,技术方案独立设计

## 1. 本条实际动效清单(逐条可行性审查)

### 动效1:④指令卡 GSAP 逐行打字机(0:16-0:19,3s)

- **实现路线:** HTML+GSAP TextPlugin(逐字/逐行显现,非纯CSS `steps()` 打字机——GSAP 能精确控制每行出现的缓动曲线和时间轴,与 VO 节奏对齐更精确)
- **资产需求:** 无外部生成资产,纯文本内容(4条规则指令,来自 domain_notes §3,已定稿不需再生成)+ 项目已有的 GSAP timeline 能力
- **性能评估:** 单卡片4行文字的timeline动画,渲染负担极低(P004管线已多次验证过类似量级的HTML截帧任务),无性能风险
- **导出风险:** HTML→PNG序列→ffmpeg合成mp4,是P004已验证的标准链路(见 `pipeline/p004_video/build.py`),导出风险低
- **可行性结论:** ✅ 可行,复用项目已有 GSAP skills(timeline 技法),不需要新安装依赖
- **任务清单(交渲染执行方):**
  1. 写一个独立 HTML 场景(纯黑`#0a0e14`底,mono字体,4行指令文字初始opacity:0)
  2. GSAP timeline:逐行 `fromTo(opacity:0→1, x:偏移→0)`,每行间隔约0.6-0.7s(3s内4行完整显现留余量)
  3. 截帧(`capture_frames.py` 确定性HTML截帧)→ PNG序列 → ffmpeg 合成进④片段
  4. 末尾停留至0:21(指令卡完整静止段),给观众截图时间

### 动效2:②③长文滚动 + 帧锁接缝急停(0:04-0:14,10s)

- **实现路线(2026-07-16 修正 · 读 `pipeline/p004_video/capture_frames.py` 源码后简化):** 原计划"Playwright 控速滚动+录制"是重复造轮子——`capture_frames.py` 已提供**确定性 GSAP timeline 逐帧渲染**能力(`window.__renderFrame(t)` 对 paused timeline 做确定性 seek),跟④指令卡走**同一套机制**,不需要额外的 Playwright 录屏基础设施。改为:新建一个 HTML 场景,真实 gpt-5.5 文本渲染进卡片,GSAP timeline 驱动 `scrollTop`/`translateY`(4-9s 匀速偏快滚动,9s 处 timeline 触发 CSS `filter:blur()` + `opacity` 急停虚化,10-14s 保持定格),`registerTimeline(tl)` 交给截帧脚本。这就是`type: html`场景,非`type: broll`。
  - **优势(相比原Playwright录制方案):** ①确定性可复现,像素级一致;②VO 时长调整后只需改 timeline 的总时长参数重新截帧,**不需要重新实录**(原方案每次调时长要重新录一遍);③天然满足帧锁接缝(同一个 timeline 内部,9s 切点前后是同一渲染的连续 seek,不存在两段拼接)
- **资产需求:** 真实 gpt-5.5 输出文本(已有,`design/实测_致命漏洞法.md`)渲染进自绘长文卡片HTML模板(需新建,非复用任何历史HTML文件)
- **性能评估:** 纯文字滚动+CSS blur,无3D/复杂计算,与④同量级,P004管线已验证过,无性能风险
- **导出风险:** 低——沿用已验证的HTML→PNG序列→ffmpeg合成链路;**唯一风险点不变:滚动的timeline总时长必须对齐VO精确时长**,若VO时长变化只需改一个duration参数重新截帧(成本远低于原录制方案的"重录")
- **可行性结论:** ✅ 可行,技术路线比原计划更简单更低风险;**执行顺序约束不变但代价降低**:仍需VO精确时长后再定timeline参数,但改参数成本从"重新录制"降为"改一行配置重新截帧"
- **任务清单:**
  1. 建自绘长文卡片HTML模板(surface底`#141922`,body字级,真实文本填入,GSAP timeline 驱动滚动+9s急停blur)
  2. 先出VO音频(见 `audio_plan.yaml`),拿到②③段精确时长
  3. 按精确时长设置 timeline 总 duration + 9s急停触发点参数
  4. `capture_frames.py` 截帧 → PNG序列 → 按 build.py 标准链路合成

### 动效3:⑤实测打脸左侧"回顾"缩略播放(0:23-0:26,3s)

- **实现路线:** 左侧栏内嵌②③场景已渲染的 mp4 作为纹理源,4x播放速度+灰度滤镜(`hue=s=0`),非独立重新设计的动画——**技术依赖②③场景先完成渲染**,交付顺序:②③ → ⑤左栏
- **资产需求:** 复用②③渲染产出的 mp4(非新素材)
- **性能/导出风险:** 低,ffmpeg `setpts` 加速 + `hue` 灰度是标准滤镜,无新技术风险
- **可行性结论:** ✅ 可行,但**有渲染顺序依赖**(②③先出片,⑤才能引用其产出),已记入下方任务清单顺序

### 动效4:④真实打字闪回(0:14-0:16,2s)

- **实现路线:** 非动效,是真实屏幕录制(raw),裁切合成
- **资产需求:** 真实操作一次(打开一个AI工具,敲入指令,发送),QuickTime/OBS录制
- **性能/导出风险:** 无(标准视频裁切合成)
- **可行性结论:** ✅ 可行,**唯一风险是合规而非技术**——录制时必须用干净会话,紧裁输入框+回复区,禁止带出侧边栏(design_language §5 Don't 已硬性约束),建议录制后由人工逐帧确认再进合成

## 2. 排除的动效方案(曾考虑但主动排除)

| 曾考虑 | 排除理由 |
|---|---|
| ②③⑤全部走"真实连续录屏"(不用HTML控速,直接肉眼手动滚动录制) | 手动滚动速度不可控,无法精确对齐9s帧锁接缝点和VO时长;改用 HTML+GSAP timeline 确定性控速滚动(`capture_frames.py`机制,见动效2),同样是"真实文档内容"但节奏完全可控、可复现 |
| ④用 Remotion TerminalScene(OpenMontage screen-demo synthetic_terminal) | 已在 form_competition/openmontage_brief 判定:终端窗口皮肤与本条"纯黑指令卡"设计冲突,且指令是自然语言非CLI命令,套用牵强 |
| ⑤分屏用3D翻转转场 | catalog.yaml"eng�3d"家族tech_risk=高且需声明数据杠杆,本条分屏对比的数据杠杆是"信任·completion_rate"(直觉理解为主),3D炫技不服务这个杠杆,反而分散注意力 |
| ②用GSAP camera pan模拟滚动(即对一张静态长文截图做Ken Burns运镜特效,而非真实滚动渲染文本) | 这是"伪装运镜"而非"真实内容动了"——GSAP camera pan 对**静态截图**做平移缩放,画面里的文字并未真实滚动,只是镜头在动;而动效2采用的方案是 GSAP timeline 驱动**真实渲染文本 DOM 的 scrollTop**,文字本身在滚动,内容 100% 真实可核对。两者都用了GSAP,但前者是"演动感"、后者是"真的在滚",本条采用后者,排除前者 |

## 3. 若未来升级动效的触发条件

| 数据信号 | 可评估的升级方案 | 前置条件 |
|---|---|---|
| ②-③段完播断崖(该段跳出率显著高于其他段) | 评估是否因10s滚动+急停节奏仍偏慢,可考虑拆得更细碎(每2-3s一个小变化点) | 需48h真实数据支撑,非猜测 |
| ④指令卡收藏率低于预期 | 评估是否GSAP逐行速度太快/太慢,调timeline时间轴,不需要换技术路线 | 同上 |

## 4. 交付清单(给下一环节)

- **storyboard.yaml:** 本文件的"任务清单"直接可转成渲染任务,按 form_strategy.md 逐镜表 + motion_storyboard.md 逐秒表生成
- **pipeline出片:** 走 P004(GSAP指令卡④ + ②③GSAP timeline控速滚动,均走`capture_frames.py`同一套机制)+ QuickTime真实录制(④真实打字闪回)+ P001/ffmpeg合成(其余静态镜 + ⑤左侧回顾滤镜处理)混合路径
- **音画方案依赖:** ②③的 GSAP timeline duration 参数必须等 audio_plan.yaml 出精确VO时长后才能定稿(非"录制",是改配置重新截帧),这是硬顺序依赖,不可颠倒

## 5. 签字

- **动效技术导演:** 可行 · 3处动效逐条审查通过,1处有硬顺序依赖(②③需先有VO时长)已标注
- **下一步:** audio_plan.yaml(先定VO精确时长)→ 回填②③ timeline duration 参数 → storyboard.yaml
