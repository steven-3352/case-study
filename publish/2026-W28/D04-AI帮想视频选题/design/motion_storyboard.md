# 动画分镜 · motion_storyboard · W28D04 AI 帮想视频选题

> 工种：动画导演 / Motion Planner（单跑不双评 · 2026-07-04 起）
> 位置：`design/motion_storyboard.md`
> 状态：`pass_single_run` · 2026-07-05
> 依赖：`scripts/vA.md`（抖音主推 · chaos-punch-reveal 型）· `scripts/vB.md` v2（备胎 · 数字精简+原话情感）· `retention_beat_sheet.md`（9 段 55-58s）· `design/form_strategy.md`（`pass_dual_review` avg=92）· `design/design_language.md`（10 色板 · 12 组件）

## 0. 入口必读打勾（fail-closed）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` §2.3 表达/音画层 · §4.2 候选实现清单
- [x] **CLAUDE refs**：`CLAUDE.md` 表达/音画层 5 工种 · 反例清单
- [x] **template refs**：`templates/design/motion_storyboard.md`（9 字段 · 单跑不双评 · 三风格判定）· `retention_beat_sheet.md`（本条已跑）· `insights/core_message.md`（本条已跑）· `design/form_competition.md`（本条 pass · 紧跟本节点之后）
- [x] **memory refs**：
  - [[feedback_anti-ai-visual]]（禁 AI 味 · 禁一句话配一张 AI 图 Ken Burns）
  - [[feedback_contrast-hook-3s]]（chaos-punch-reveal 是本条差异化视觉资产）
  - [[feedback_no-default-tech-stack]]（不默认 P004 / 不默认 Remotion · 按 §2 判风格）
  - [[feedback_no-neon-palette]]（禁 Dracula 紫粉青）
  - [[feedback_pipeline-burn-subs]]（字幕烧片流程）
- [x] **姊妹条 refs**：同周 D01-D03 均未跑本节点（motion_storyboard 是 2026-07-04 新增岗位 · D04 是首条走此节点的），不复用画面 · 只学 template 结构
- [x] **参考 md refs**：`~/Downloads/两个视频动画设计与实现分析.md` + `~/Downloads/动画分镜与vibe-motion工作流总结.md`（假设已读 · 三风格对照矩阵）

**触发词打断（本次开工前主动检查）：**
- [x] 未出现「就用 P004 HTML+GSAP 拼一版」（本条 P004 lib 只做合流 · 不做居中大字 GSAP）
- [x] 未出现「三张 AI 插画拉一下 Ken Burns 就完了」（本条禁 AI 生图 · 走屏录 + Pexels + drawtext）
- [x] 未出现「先按 WaytoAGI 风格来吧」（本条 Vibe Motion 主 · WaytoAGI 辅 · 按内容比较过）
- [x] 未出现「每段 4 秒统一切换」（本条按 vA/retention 节拍：1s + 0.6s + 1.4s + 5s + 7s + 10s + 15s + 8s + 6s + 4s）

## 1. 结论（导演口径）

```yaml
status: pass_single_run
content_id: W28D04
route_style: 混合  # Vibe Motion 主（屏录 UI/AI 对话框 M2/M3/M6/M7）+ WaytoAGI 辅（M8 表格信息图 + M4 数据锚）+ 少量真实素材 B-roll（M1/M4 白天办公 · 但走 Pexels 非 AI 插画所以不算七七风格）
route_style_rationale: |
  D04 核心是"把 4 段 prompt 给你 + 5 判据表格能用"——是**方法论演示**（WaytoAGI 血统）+ **屏录 UI 实时感**（Vibe Motion 血统）的混合，
  非情绪叙事（不走七七 AI 插画）。首镜 chaos-punch-reveal 三拍是屏录反差（Vibe Motion 血统 · 屏录 AI 对话框实时感），
  中段 M4/M8 数据锚 + 表格是 WaytoAGI 血统（黑底 + 白字 + accent_green 打勾 + 静态出现）。混合的意义是段落切换时用**共用色板**
  （canvas_office_dark + 白字 + accent_soft 淡黄 + accent_green sober + accent_red 血红）避免看起来像两个视频拼的。
handoff_to: design/form_strategy.md → design/motion_tech_plan.md（本条 SKIP · 无 Web 3D/GSAP）→ design/storyboard.yaml + audio_plan.yaml → pipeline/p004_video/lib config-driven
```

## 2. 风格判定

### 2.1 内容类型判定

本条脚本核心内容类型：**方法论演示 + 数据锚 + 反面正解 + 情绪释放 + CTA**（多选）

- **概念**：M9「不是教你 · 是把 4 段 prompt 给你」价值锚
- **情绪**：M1 chaos 停划 + M5 反爆款抱怨（40w vs 800）
- **动作**：M2 打字 14 字 + M7 4 段 prompt 演示
- **数据**：M4 9 成 + M8「10 里 8 · 5 判据」
- **流程**：M7 4 段 prompt 结构（身份卡/账号定位/粉丝痛点/输出约束）
- **转折**：M3 reveal「AI 全给'如何做好'」
- **案例**：M5 分屏 40w vs 800（家居博主小林化名）

### 2.2 皮肤

- 受众/皮肤（来自 `insights/topic_brief.md → skin`）：**中腰部创作者 · 同行说话 · 不 preach 不 sell 秘籍**
- landing_intent：私信喂选题（不推服务）
- tone_direction：同行说话 · 克制 · 无 emoji · 无形容词字幕

### 2.3 风格选择

| 风格 | 适配度 | 说明 |
|------|--------|------|
| **WaytoAGI**（信息图 + 黑底网格 + 黄字重点 + 图标） | ★★★☆ | M4 数据锚 + M8 5 判据表格 直接用 · 但不用「AI 助教机器人」拟人化（skin 不接受"教你"感 · 违反 tone_direction） |
| **七七**（AI 插画 + Ken Burns + 人物情绪） | ★☆☆☆ | AI 插画会拉高 AI 味（memory [[feedback_anti-ai-visual]] 硬禁）· 本条主角背影 + 摄像头亮 + 空笔记本走 Pexels 真实素材而非 AI 生图 · **不选** |
| **Vibe Motion**（代码/UI 窗口/终端/实时预览） | ★★★★ | M2/M3/M6/M7 全是屏录 AI 对话框实时演示（UI 原生色 + 光标闪 + 打字节奏 · 是 Vibe Motion 的核心血统 · 唯一同行没做过的差异化视觉资产）|
| **混合** | ★★★★★ | Vibe Motion 主（首镜 + 演示核心 · 屏录 4 场次 · 62% 时长）+ WaytoAGI 辅（M8 表格信息图 + M4 数据锚 · 12s / 21% 时长）+ 真实 B-roll 情绪调剂（M1/M4 白天办公 · 15% 时长）· **共用色板 canvas_office_dark + accent 三色** |

**推荐主风格：** Vibe Motion（屏录 UI 演示 · 62% 时长）
**推荐辅助风格：** WaytoAGI（信息图 · 21% 时长）+ 真实 B-roll（15% 时长 · 段间情绪调剂）
**判定依据：** §2.1 内容类型 + §2.2 skin.tone_direction 双约束下，Vibe Motion 的屏录 UI 实时感与"同行说话"最匹配（同行看到 AI 对话框 UI 会 1s 认领"我上周就打过一模一样的 prompt"）。WaytoAGI 表格信息图承担"承诺兑现"证明（M8 5 判据打勾）。真实 B-roll 承担"这就是我"的共情锚（M4）。
**不选另外两种的理由：**
- 不走**纯 WaytoAGI**：会让首镜变成"信息图开场"，稀释屏录反差差异化视觉资产 · 且拟人化 AI 助教违反 skin.tone_direction
- 不走**七七**：AI 插画会拉 AI 味 · 中腰部创作者一眼看穿是同行套路 · 且 M2/M7 屏录才是本条硬资产
- 不走**纯 Vibe Motion**：M4 数据锚 + M8 5 判据表格用信息图（WaytoAGI 血统）比用代码/终端更直白 · 观众理解成本低

### 2.4 段落切换点

- **0-3s（M1-M3）**：Vibe Motion 屏录 chaos-punch-reveal（Pexels 白天办公 3s → 屏录 AI 对话框 2s · 段内切换用 whoosh + 屏录 UI）
- **3-8s（M4）**：Vibe Motion → **真实 B-roll**（白天办公桌主角背影 · 同一光温 3800-4200K 承接首镜 chaos 的白天光）+ headline 白字叠层（WaytoAGI 血统的数据锚白字）
- **8-15s（M5）**：真实 B-roll → **分屏真机截图**（40w 赞 vs 800 赞 · 两张静图 + 分割线 · 视觉家族=Vibe Motion 分支的 UI 截图）
- **15-25s（M6）**：分屏 → Vibe Motion 屏录（3 段 AI 对话框反例快切）
- **25-40s（M7）**：Vibe Motion 屏录核心（AI 对话框 + accent_soft 4 段 badge 淡入）
- **40-48s（M8）**：Vibe Motion → **WaytoAGI 表格信息图**（canvas_office_dark 灰底 + 10×5 表格 + accent_green 静态打勾 + headline 白字大结论）
- **48-58s（M9-M10）**：WaytoAGI 全屏大字（canvas_office_dark + display 140pt 白字两行）+ CTA 灰底 headline

**过渡镜头：**
- M3→M4 切换：M3 定格 display 大字 0.3s hold 后 fade 0.2s → M4 白天办公 B-roll fade in
- M5→M6 切换：分屏静图 hit sfx 打点后直接 hard cut 到 M6 屏录（同帧同色板 · 无过渡）
- M7→M8 切换：M7 屏录淡出 0.3s → M8 canvas_office_dark 灰底淡入 0.3s（同底色不刺眼）
- M8→M9 切换：M8 表格 hit sfx 收 → M9 灰底大字直接切入（同底色 · 大字放大感承接表格结论）

**共用色板：** canvas_office_dark `#1a1a1a` + ink_light `#f5f5f0` 白字 + accent_soft `#ffc857` 淡黄 badge + accent_green `#4caf50` sober 打勾 + accent_red `#e53935` 红叉 + system_native UI 原生色（AI 对话框深色系）

## 3. 逐秒分镜表（9 字段 · 10 段镜头 M1-M10）

> 铁律：每 2-4 秒必须有明确视觉变化 · 每一秒画面服务旁白（vA 主推）
> 铁律：无 AI 生图 · chaos 用 Pexels + 真机屏录

| 时间 | 旁白 | 内容类型 | 画面主体 | 动画动作 | 镜头运动 | 屏幕文字 | 素材需求 | 推荐实现方式 | 设计目的 |
|------|------|----------|---------|---------|---------|---------|---------|-------------|---------|
| **0:00-0:01** | （无 VO · 静默钉子）| 情绪/场景 | Pexels 白天办公桌俯拍 · 键盘 + 摄像头亮红点 + 手悬键盘不落 | 手悬静止（微微颤 · 拟态"要不要打字"的迟疑）· 摄像头红点稳定发光 | 静止俯拍 · 无推拉 | 无字幕（首秒故意留白）| Pexels 白天办公桌 3800-4200K 俯拍 × 1（新拉）· 摄像头亮红点可见 | Pexels fetch_broll.py 拉 `daylight office desk overhead` + `webcam recording setup` 新素材 | M1 chaos · 服务 completion_3s · 1s 认领"这就是我的桌面"（差异化 vs D02 傍晚 · D03 深夜）|
| **0:01-0:016** | （无 VO · 打字声真实拟音）| 动作 | 屏幕特写切入 · AI 对话框深色系 · 光标闪 · 手落键盘 | 光标闪（500ms/次）· 手落键盘 · 打字 14 字「帮我想 10 个抖音选题」（30ms/字 · 真人节奏）· 敲回车 | 硬切从 M1 俯拍到屏幕特写（无过渡镜头 · 同拍点 tick sfx 承接）| mono 32pt 屏内文字（打字过程本身即视觉字幕）· 保留 iOS/macOS 状态栏 · 不打 AI 工具 logo | QuickTime 真机屏录 macOS/iPhone × 1 场次（ChatGPT UI 建议 · 识别度高）| QuickTime 真机屏录 + ffmpeg 时间戳裁剪 | M2 punch · 动作可复现（打字过程本身认领感强）· 差异化视觉资产 |
| **0:016-0:03** | （无 VO · whoosh + hit sfx）| 转折 | AI 对话框输出 3 条「如何做好家居收纳 / 浅谈 XX 的重要性 / 5 个 XX 误区」→ 3 次 accent_red 红叉 whoosh 从右上横向划过打掉 → display 140pt 白字入「打"帮我想 10 个" · AI 全给"如何做好"」屏中央 | AI 输出 3 条文字 1s 内快速打字机式出现 → whoosh sfx × 3 每次 0.3s + hit sfx × 1 拍点 · accent_red SVG 红叉从右上滑入（静态 SVG + CSS transition · 禁 GSAP 弹跳）· display 大字 drawtext 淡入 0.3s | 屏内切镜 · 无镜头运动 | display 140pt 白字「打"帮我想 10 个" / AI 全给"如何做好"」两行 · 屏中央 · 2px canvas_office_dark 深色描边 | QuickTime 屏录续场 + SVG accent_red 红叉 × 3 覆盖 + ffmpeg drawtext | M3 reveal · 反差爆点 · 反面正解前置激发"那我该怎么办"期待反转 |
| **0:03-0:08** | 「上周我也这样。9 成中腰部创作者早期都遇到选题问题——不是你的问题。」| 数据/共鸣 | Pexels 白天办公 B-roll（主角背影 + 摄像头亮 + 空笔记本 · 白天光 3800-4200K）+ headline 96pt 白字叠层 | B-roll 静止俯拍或缓慢向前推 0.5%/s（几乎不可察觉）· headline 白字 3.5s 处淡入 0.3s + hold 到 8s · caption 来源小字同时淡入 | 缓推 · 增加视频感（避免静图感）| headline 96pt 白字「9 成中腰部创作者遇到选题问题」+ caption 24pt「引 知乎专栏 A 级」右下角 | Pexels fetch_broll.py 拉 `hand hovering keyboard morning` 或 `blank notebook desk` 新素材 × 1 | Pexels B-roll + ffmpeg drawtext + drawbox（若需 subtle 半透明底衬） | M4 共鸣锚 · 释放"不是我不行"羞耻感 · 服务 completion_rate |
| **0:08-0:15** | 「你翻了半小时竞品，存了 8 张截图，还是一条不想拍。同行 40w 赞我也拍过——我只有 800。」| 情感冲击/对比 | 分屏 50/50 · 左「同行 40w 赞截图」右「我 800 赞截图」· 中间 2px ink_light 白分割线 · 大字类比锚居中偏下 | 8s 处 hard cut 硬切进分屏（同 hit sfx 拍点）· 两张截图静态并列 · headline 大字 9.5s 处淡入 0.3s + hold · caption 副标 10s 处淡入 | 静止分屏 · 无镜头运动 | headline 96pt 白字「40w 赞 vs 我 800 赞」居中偏下 + caption 32pt「翻竞品 30 分钟存 8 张截图 · 一条不想拍」| 真机截图 × 2（马赛克遮挡真实同行头像/账号名 · 单位显式"赞"字必须出现）| PhotoRoom/PixelMator 打马赛克 + ffmpeg drawtext 分屏 hstack + drawbox | M5 情感冲击 · 反爆款抱怨"我也这样"· vA 主推兜底：此处需 M4 或 M9 补 1 条 topic_brief 原话直引，否则强制切 vB v2 |
| **0:15-0:25** | 「我以前也这么干：让 AI 帮我想 10 个 → 都是「如何做好 XX」·『加平台词』→ 同行都在拍的模板 · 让 AI 抄爆款 → 换个数字的同质品。」| 反面正解 | 屏录 3 段快切 · 3 个 AI 对话框实录（每段约 3.3s）· accent_red 2px 描边强调关键错误行 · caption 28pt 大字批注 | 每段 3.3s 内：屏录 1.5s AI 对话展示 → accent_red 描边淡入 0.3s → caption 大字批注 drawtext 淡入 0.3s → hit sfx 拍点 · 段间 whoosh 快速过渡 | 屏内切镜 × 3 · 无镜头运动 | mono 32pt AI 对话内容 + caption 28pt drawtext「跳过身份卡」「跳过账号定位」「跳过粉丝痛点」| QuickTime 屏录 × 3 段（3 个 AI 对话框实录）+ SVG accent_red 描边 | QuickTime 屏录续场 + SVG 覆盖 + ffmpeg drawtext + concat | M6 反面正解 · 激发"那我该怎么办"期待反转 · 3 段快切保节奏 |
| **0:25-0:40** | 「换个打开方式。打开 AI，粘上 4 段 prompt：身份卡、账号定位、粉丝痛点、输出约束。同一个 AI，10 条候选，标题、场景、钩子、成本、差异化都齐了。」| 演示核心/流程 | QuickTime 屏录 AI 对话框深色系 · 粘贴完整 4 段 prompt（家居收纳版 · JetBrains Mono 32-40pt）→ AI 表格输出 10 条候选 · **accent_soft 淡黄底 4 段 badge SVG 覆盖**（身份卡/账号定位/粉丝痛点/输出约束）· 每段淡入 0.5s + 停 3-4s | 25-27s：屏录粘贴 4 段 prompt 全屏可见 · 27-40s：AI 表格输出 10 条候选 · 每条 1s 打字机式出现 · accent_soft badge 4 段依次淡入 0.5s + 停 3-4s（4 段总时长 3.5s × 4 = 14s 恰在 15s 段内 · whoosh sfx × 4 段间过渡 -12dB）| 屏内保持 · 无镜头运动（观众需暂停截屏 · 镜头晃会伤截屏动机）| mono 32-40pt 4 段 prompt 全文（观众可暂停截屏）+ accent_soft badge headline 88pt 段名 + caption 28pt 底部「可长按暂停截屏抄」 | QuickTime 屏录 × 1 场次（15s 连续 · 主场）+ SVG accent_soft badge × 4 + ffmpeg drawtext | **M7 收藏动机第一位** · 服务收藏率 · 26% 全片占比（最长段）· 可长按暂停截屏 |
| **0:40-0:48** | 「10 条里 8 条能用——用 5 判据筛（具体场景 / 前 3s 钩子 / 差异化 / 可拍性 / 粉丝相关），通过 4 条就能拍。」| 数据/流程/兑现 | canvas_office_dark `#1a1a1a` 灰底 + 表格结构 10 条候选 × 5 判据 · accent_green sober 静态打勾 × 8 · accent_red 静态打叉 × 2 · headline 96pt 白字大结论「10 里 8 · 能用」+ caption 28pt 副标 | 40-41s：灰底淡入 0.3s + 表格从上到下扫入 0.5s（10 行）· 41-45s：accent_green 打勾从左到右逐个静态出现（禁 GSAP 弹跳 · 每个 hit sfx 打点）+ accent_red 打叉 2 个静态出现 · 45-48s：headline 大字「10 里 8 · 能用」从下到上淡入 + hit sfx 强拍点 | 屏内保持 · 无镜头运动（表格需暂停看清） | headline 96pt「10 里 8 · 能用」+ caption 28pt「5 判据 · 通过 4 条即能用」+ mono 表格：**表头 headline 42pt · 单元格 body 32pt**（form_strategy §5 硬约束）| SVG 表格 + accent_green ✓ 打勾 SVG + accent_red ✗ 打叉 SVG + ffmpeg drawtext | **M8 收藏动机第二位** · 承诺兑现证明（P0-4）· WaytoAGI 血统信息图 · 5 判据 = 可测承诺 |
| **0:48-0:54** | 「不是教你用 AI —— 是把我上周 30 分钟搞定下周 5 条的那 4 段 prompt，直接给你。」| 概念/价值锚 | 全屏 canvas_office_dark `#1a1a1a` 灰底 · display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」· 无 B-roll 只有字 | 48-48.5s：M8 表格淡出 0.3s → 灰底全屏无字 0.2s hold（呼吸）· 48.5-50s：第 1 行「不是教你」display 大字 drawtext 淡入 0.5s + hold · 50-52s：第 2 行「是把 4 段 prompt 给你」display 大字下方淡入 0.5s + hold · 52-54s：两行 hold 2s + ambient sfx 落底 + hit sfx 收尾 | 无镜头运动（大字权威感靠静止感）| display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」· 权重 900 · 居中对齐 · 无 emoji 无花字 | 无外部素材 · 纯 drawtext + canvas_office_dark 灰底 | ffmpeg drawtext + drawbox 灰底 + ambient/hit sfx | **M9 反教程价值锚** · 差异化承诺 · 服务评论率 · 同事口吻替代博主感 |
| **0:54-0:58** | 「私信『你在做什么账号、想拍什么方向』——我给你 5 条选题。同行互助，不推服务。」| CTA/承诺 | canvas_office_dark 灰底 + headline 88pt 白字 CTA + caption 28pt 底部小字 | 54-54.5s：M9 大字淡出 0.3s → 灰底 hold 0.2s · 54.5-56s：CTA headline 白字 drawtext 淡入 0.5s + hold · 56-57s：caption 底部小字淡入 0.3s + hold · 57-58s：hit sfx 收尾 + hold | 无镜头运动 | headline 88pt 白字「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ caption 28pt「同行互助 · 不推服务」 | 无外部素材 · 纯 drawtext | ffmpeg drawtext + drawbox 灰底 + hit sfx | **M10 CTA** · 两选项开放式提问 + 具体承诺"5 条选题"低成本高确定回复 · 服务评论率 + 私信率 · 私信 SLA 24h（form_strategy §5 硬约束）|

## 4. vB v2 备胎逐镜差异（仅列与 vA 主推分镜不同点）

| 镜 | vA（主推）分镜 | vB v2（备胎）分镜差异 | 备注 |
|----|---------------|---------------------|------|
| **M1（0-3s）** | Pexels 白天办公 + 屏录 chaos-punch-reveal 三拍 | Pexels 白天办公主角背影 + 摄像头亮 + 秒表小字 caption 32pt muted 灰色「30:00」右下 · 静态非动画 + display 140pt 白字入「空半小时 · 0 条选题」屏中央 | 备胎定位下的场景锚版本 · 无屏录 · 秒表**静态**不做反向倒数动画（vB v1 已删）|
| **M4（8-13s）** | 反爆款抱怨（40w vs 800）headline 大字 + caption 副标 | 同 vA + 加 topic_brief 原话 #2 直引「为什么我抄爆款别人爆我不爆啊」引号符号（「」）+ **JetBrains Mono 32pt**（区别于旁白 body 42pt · 视觉上明显区分"这是原话"）| mono 字体 + 引号符号 双标识"这是原话" |
| **M5（13-18s）** | vA 无此镜（并入 M5 40w vs 800）| 独立成节拍 · 日历翻页视觉（1080×1920 竖屏日历动画 · 一周格 → 半月格 · whoosh + tick 组合拟音）+ topic_brief 原话 #3 直引「每周发一篇变成半个月发一篇」+ caption 32pt 数字标签「上周 1 → 这周 0」| 日历翻页拟音（whoosh -12dB + tick × 3 -15dB）· 数字对比冲击 |
| **M6 末尾** | 3 段烂做法收尾 hit sfx | 3 段收尾后加全屏定格「累」一字 · display 140pt 权重 900 · 独立 hit sfx 深长版（-8dB · 1.2s 尾音）· hold 1s | 情绪落点 · topic_brief 原话 #5 直引 · 全屏定格权威感 |

## 5. 风格专项规范执行清单

### 5.1 Vibe Motion 段（M1-M3 · M6 · M7 · 62% 时长）

- [x] 屏录 UI（AI 对话框深色系 · 保留 iOS/macOS 状态栏）
- [x] 光标闪 + 打字节奏 30ms/字 真人节奏（M2 拟音 14 声 -8dB）
- [x] 因果感：M2 打字 → M3 AI 输出被红叉打掉 · 因果链 3s 内完成
- [x] 无复杂 3D 炫技 · 静态 SVG 覆盖（禁 GSAP）
- [x] Git 提交/终端 skip（本条 AI 对话框是主 UI · 不需终端）
- [x] 参考 `~/Downloads/浙大猫学长-vibe+git=无限动画*.mp4`（假设已看过 · UI 分层节奏）

### 5.2 WaytoAGI 段（M4 数据锚 + M8 表格 · 21% 时长）

- [x] 建立"稳定舞台"：canvas_office_dark 灰底 + headline/display 白字层 + 表格层
- [x] 每个信息点逐个出现（M8 表格 accent_green 打勾从左到右逐个出现 · 禁一次性堆屏）
- [x] 重要数字放大高亮（M4「9 成」headline 96pt + M8「10 里 8」headline 96pt · 白字非黄字 · 呼应 skin.tone_direction 克制感 · 淡黄仅用于 M7 badge）
- [x] 角色关系表达 skip（本条 skin.tone_direction 拒绝「AI 助教」拟人化 · 用屏录 UI 承担人格）
- [x] 抽象概念可视化：「筛选」→ accent_green ✓ 打勾 + accent_red ✗ 打叉；「结构」→ accent_soft badge 4 段
- [x] 穿插真实素材（M4 Pexels 白天办公 B-roll · 避免全片黑底）

### 5.3 真实 B-roll 段（M1/M4 · 15% 时长）

- [x] Pexels 白天办公 3800-4200K（新拉 · 现有 assets/broll/raw 全是 dusk/night · 见 form_strategy §4-A）
- [x] 主角背影 + 摄像头亮 + 空笔记本（不露脸 · 保代入性）
- [x] 白天光 3800-4200K（区别 D03 深夜台灯 3000-3500K）

## 6. 禁用清单（本岗位红线自查）

- [x] 无 PPT 式文字淡入淡出（有节拍变化 · 有 SVG 覆盖 · 有 whoosh/hit sfx 支撑）
- [x] 无「每个物体都动」（M8 表格 accent_green 打勾逐个静态出现 · 不做同时打勾）
- [x] 无抽象背景 + 抽象文字（M4 具体白天办公场景 · M5 具体截图对比 · M9 灰底大字但服务价值锚兜底）
- [x] 无「一句话配一张 AI 图 + Ken Burns 一路推进」（全条禁 AI 生图 · Pexels 真实 + QuickTime 屏录）
- [x] 已判风格（§2）· 未直接进分镜
- [x] 每个镜头服务旁白（vA 主推 M1-M10 逐镜对齐）
- [x] 每个镜头服务节拍表（retention_beat_sheet 9 段对齐 · 单场景占比 M7 26% <40%）
- [x] 无复杂 3D 炫技（motion_tech_plan SKIP · 无 Web 3D/GSAP）
- [x] 无 Dracula 霓虹紫粉青（design_language 10 色板 · gate_check_palette.py 兜底）

## 7. 交接给下游

- **形式策略官 · form_competition** → 本节点后于 form_competition（form_competition 已 pass · 五维打分方案 A=69 胜）· 本表提供**方案 A 落地的逐秒分镜**，form_strategy pass_dual_review avg=92 已确认逐镜表达
- **形式策略官 · form_strategy** → 本表 §3 逐秒表 = form_strategy §1 逐镜表达方案的**秒级细化**（form_strategy 是镜头级 · 本表是秒级 · 一致性核查已内嵌）
- **动效技术导演 · motion_tech_plan** → 本条 **SKIP**（无 Web 3D · 无 GSAP · 无 Remotion · 无 Manim · 无 Three.js · 只用 SVG 静态覆盖 + drawtext + drawbox + ffmpeg + QuickTime 屏录 + Pexels B-roll · 详 form_strategy §7）· 需登记 SKIP 理由（同 D03）
- **导演 · storyboard.yaml** → 本表 §3 的 10 段 × 9 字段直接映射为 storyboard.yaml 的 shots 数组 · 素材需求映射为 assets 字段 · 推荐实现方式映射为 render_engine 字段
- **声音设计师 · audio_plan.yaml** → 本表 §3 的动画动作与拍点直接映射为 sfx 时间戳（whoosh × 4 + tick × 3 + hit × 5-8 + ambient 全片 · BGM off · TTS 时长前置估算 tts-estimate-duration-pre-synth 硬约束）· 首秒钉子（0-1s ambient + tick 0.3s）已 §3 M1 明示

## 8. Audience-First 自查三问（motion_storyboard 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ M1 首秒摄像头亮红点 + 手悬键盘不落 = 中腰部创作者一眼认领（Vibe Motion 屏录 UI 是本条差异化视觉资产）· M2 打字 14 字动作可复现 · M4 白天办公主角背影释放"不是我不行"· M9 反教程价值锚同事口吻 |
| 画面**观赏性**够吗？ | ✅ 9 段节拍 · 3 种风格血统（Vibe Motion 62% + WaytoAGI 21% + 真实 B-roll 15%）共用 canvas_office_dark 色板 · 每 2-4s 视觉变化（M1 静止 → M2 打字 → M3 红叉打掉 → M4 B-roll → M5 分屏 → M6 3 段快切 → M7 badge 4 段 → M8 表格打勾 → M9 大字 → M10 CTA）· sfx 10+ 次事件音撑节奏 |
| 内容**真材实料**吗？ | ✅ M2/M3/M6/M7 全屏录真机 AI 对话框（A 级证据）· M4 Pexels 真实素材（B 级）· M5 真机截图（A 级）· M7 15s 4 段 prompt 可长按暂停截屏（收藏动机第一位）· M8 5 判据表格 accent_green 打勾 = 承诺兑现（收藏动机第二位）· 无 AI 生图 · 无假素材 |

## 9. 变更历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-05 | v1.0 | 新建 · draft_self_generated → pass_single_run · Vibe Motion 主 + WaytoAGI 辅 + 真实 B-roll 混合风格 · 10 段 × 9 字段逐秒分镜 · vB v2 备胎差异 4 段 · motion_tech_plan SKIP 已声明 |
