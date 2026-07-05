# 发布前预测 · pre_publish_forecast · W28D04 三平台

> 工种：平台表现分析师
> content_id: W28D04
> content_version: vA（主推 chaos-punch-reveal 屏录反差型）+ vB v2 备胎（数字精简+原话情感）
> 北极星：`completion_3s` · `completion_rate` · 收藏（M7 4 段 prompt + M8 5 判据表格双动机）· 私信（CTA 分型清晰）

## 0. 依赖门禁通过状态

| 依赖 | 状态 | 说明 |
|------|------|------|
| 洞察包（4 件套 + external_references） | ✓ pass | 记者+ 4 岗合并产出 · A 级来源 ≥3 |
| retention_beat_sheet.md | ✓ pass | 9 段 55-58s · M7 26% <40% |
| scripts/vA.md + vB.md v2 | ✓ pass_dual_review | 编剧+ avg=91.5 · vB v2 verdict pass |
| form_strategy.md | ✓ pass_dual_review avg=92 | 形式策略官双评 · 6 硬门全过 · A 提 2 must_fix 已就地补 |
| motion_storyboard.md | ✓ pass_single_run | 动画导演单跑不双评（2026-07-04 起 · docs/DECISIONS.md Q11） |
| storyboard.yaml | ✓ pass_self_generated | 10 段 M1-M10 · 白天 3800-4200K · Vibe Motion 主 + WaytoAGI 辅 |
| audio_plan.yaml | ✓ pass_self_generated | BGM off · sfx 34 events · voice_id 复用 D03（same voice diff scene） |
| pipeline_config.yaml | ✓ pass_self_generated | config-driven 已声明 |
| **TTS 前置估算硬门** | ✓ **pass** | 首轮 2 fail-closed → 应用 overrun_fallback → 0 fail · 3 warn ≤22.4%（30% 门下）· 总漂移 4.35s |
| openmontage_brief | ✓ **decision=blocked_infrastructure** | 硬门跑过 · 走原生 pipeline P004/P001 混合 |
| motion_tech_plan | **SKIP**（同 D03）| 无 GSAP/Web 3D/复杂动效 · 走 SVG 静态覆盖 + drawtext + drawbox + ffmpeg + QuickTime 屏录 + Pexels B-roll |

## 1. 内容门（脚本 / 洞察）预测

| 维度 | 评分 | 依据 |
|------|------|------|
| 钩子停划力（0-3s） | 8.5/10 | 屏录 chaos-punch-reveal 三拍：白天办公摄像头亮红点（1s 场景锚）→ 打字 14 字（1.6s 动作锚）→ AI 输出被红叉打掉 + display 大字反差（3s 认知锚）· **同行没做过的差异化视觉资产**（memory: `feedback_contrast-hook-3s`）|
| 反转点强度 | 8.5/10 | M3 反差前置（打「帮我想 10 个」→ AI 全给「如何做好」）· M4 群体锚（9 成中腰部创作者）· M5 反爆款抱怨（40w vs 800）· M6 反面正解 3 段快切 · M7 换个打开方式演示 · 五段反转链 |
| 信息密度 | 9/10 | M7 4 段 prompt 结构（身份卡 / 账号定位 / 粉丝痛点 / 输出约束）· M8 5 判据表格（可测承诺兑现）· 双重收藏动机点 |
| 合规 | 10/10 | 无「必上热门 / 一键爆款 / 涨粉神器」· 竞品 logo 遮挡 · 40w 赞截图马赛克遮真实同行头像 / 账号名 · 单位「赞」显式 · 私信 CTA 走本人 IP · 不导流付费群/星球 |
| CTA 转化潜力 | 8.5/10 | 私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题 · **两选项开放式提问 + 具体可测承诺**「5 条选题」低成本高确定回复 · SLA 24h |
| **总分** | **88.5/100** | honest 过内容门（≥85 门） · 略高于 D03（86.5）· 提升点：屏录反差 + CTA 分型清晰 |

## 2. 形式门（视觉 / 形式）预测

| 维度 | 评分 | 依据 |
|------|------|------|
| 视觉同质 | 8.5/10 | Vibe Motion 屏录 UI（62% 时长）+ WaytoAGI 表格信息图（21%）+ Pexels 白天办公 B-roll（15%）三风格混合 · 共用 canvas_office_dark 色板 · 与 D01/D02/D03 视觉族群完全不同（D02 傍晚打工人 · D03 深夜台灯 · **D04 白天 3800-4200K + 摄像头亮红点**）|
| 单焦点保证 | 9/10 | 10 段 6 种形式 ID · 每段一句大字 + 一个视觉主体 · form_strategy §4 已声明单焦点 · M7 演示 15s 主场（<40% 上限 · 26%）|
| 音画三件套 | 9/10 | VO 覆盖 3-58s（55/58=94.8%）· ≥85% 硬门 · 无 BGM（密 VO 演示型默认 off · memory: `feedback_dense-vo-no-bgm-default`）· sfx 34 events（ambient×1 + tick×3 + whoosh×8 + hit×15 + hit_seq×10）· 字幕烧录三平台差异化字号 42/50/42 |
| 注意力硬门 | 8/10 | 10 段镜头 · 每 2-4s 视觉变化 · M7 15s 是最长段位靠 4 段 badge 拆分节奏（每 3s 换段名 + whoosh 段间过渡）· M8 表格分行扫入 + 打勾逐个出现 · 无 3s+ 无变化段位 |
| 禁霓虹色门 | 10/10 | 10 色板 gate_check_palette 全过 · canvas_office_dark #1a1a1a · ink_light #f5f5f0 · accent_soft #ffc857 · accent_green #4caf50 · accent_red #e53935（非 #ff5252）· 无 Dracula #bd93f9/#ff79c6/#8be9fd |
| **总分** | **88.9/100** | honest 过形式门（≥85 门）· 略高于 D03（86.4）· 提升点：三风格混合 + 屏录 UI 演示 |

## 3. 平台预估区间（vA 主推 · chaos-punch-reveal 屏录反差版）

| 指标 | 抖音 | 小红书轮播 | 小红书视频（备胎）| 视频号 | 说明 |
|------|------|------|------|------|------|
| 首屏停留 / 3s 完播 | 36%–46% | 首图停留 3-5s（划完 P0→P1 率 65%–75%） | 32%–42% | 33%–43% | 屏录 chaos-punch-reveal 三拍 · 差异化视觉资产 · 高于 D03（+3-4 pt）|
| 完播率 / 划完率 | 14%–20% | 35%–45%（P0-P6 完整率 · P4/P5/P6 收藏钩 3 处） | 12%–18% | 16%–24% | M7 4 段 badge 拆节奏解决 D03 M7 gap 问题；M8 表格分行出现节奏感强 |
| 收藏率 | 中偏上（6%–10%）| **高**（12%–18% · P5 完整 prompt 长按保存图）| 中（4%–7%）| 中（4%–7%）| **双重收藏动机**（M7 4 段 badge + M8 5 判据表格 · P5 家居收纳版完整 prompt）· 强于 D03（只有 M6 一个 role prompt 全屏 + M9 价值锚）|
| 评论率 | 中（1.5%–2.5%）| 中偏上（2%–3%）| 中（1.5%–2.5%）| 中（1%–1.5%）| M9 反教程价值锚（"不是教你 · 是把 4 段 prompt 给你"）易触发认同评论 |
| **私信率** | 中偏上（0.3%–0.6%）| 中（0.15%–0.3%）| 中（0.15%–0.3%）| 中（0.1%–0.2%）| **CTA 分型清晰 + 具体承诺** · 私信文本模板短「账号 + 方向」低门槛 |
| **综合评级** | **B+** | **A-**（xhs 主推轮播 P0-P6 · 收藏率甜区）| **B** | **B** | 三平台均达外发门（≥ B）· xhs 轮播是本条最强项 |

## 4. vA vs vB v2 决策规则

| 触发条件 | 动作 | 理由 |
|---------|------|------|
| vA 3s 完播 <52% at D+1 | 切 vB v2 备胎（数字精简 + topic_brief 原话情感）| chaos-punch-reveal 屏录不共鸣时用情感锚兜底 |
| vA 完播 <25% | 切 vB v2 + 缩短到 45-48s | 若 M7 15s 拖累留存 · 用日历翻页 + 累字定格情绪叙事替代 |
| vA 私信数 <5 条 at D+2 | 保 vA · CTA 加评论区置顶「私信『账号+方向』我给 5 条」引导 | CTA 力度不足需评论区强化 |
| vA 收藏率 <4% | 保 vA · P4/P5 补长图版发小红书图文（xhs 独立） | 收藏动机 xhs 平台可单独强化 |

## 5. D+2 触发条件（若不达 B 级 → 复盘会补真独立复评）

- **抖音**：`completion_rate` < 12% · `comment_rate` < 0.5% · `私信数` < 5 条
- **xhs 轮播**：划完率 < 25% · 收藏率 < 5%（低于甜区）
- **xhs 视频**：完播率 < 8% · 收藏率 < 3%
- **视频号**：完播率 < 12% · 转发数 < 3

**触发后动作：**
1. 复盘会补**真独立 reviewer**打分（当前 scorecard 除 form_strategy pass_dual_review 外均为 `pass_single_run` / `pass_self_generated`）
2. v2 迭代路径：
   - 首选 A：vA 屏录素材优化（加真人打字 14 字 QuickTime 屏录同频拟音替代 Freesound + 状态栏更清晰）
   - 首选 B：切 vB v2 备胎（数字精简 + topic_brief 原话情感 + 日历翻页）
3. 若 3s 完播仍 <30%（三平台平均）· 退回钩子重写（M1 换成主角背影 + 秒表 30:00 · vB v2 首镜）

## 6. 合规分 vs 效果分

- **合规分：** 10/10（红线全避）
  - 无「必上热门 / 一键爆款 / 涨粉神器 / 流量密码 / 变现秘籍」承诺
  - ChatGPT/DeepSeek/豆包 竞品 logo 遮挡（UI 原生色允许）
  - M5 40w 赞截图头像 + 账号名马赛克 · 单位「赞」显式（vB v2 verdict 硬约束）
  - 私信 CTA 走本人 IP · 不导流付费群/星球/课程
  - 不站队骂同行 · 不评价具体博主
  - 「10 里 8」承诺可测（M8 5 判据表格兑现证明）

- **效果分：** honest 88.5（内容门）+ 88.9（形式门）· 双门都在 B+/A- 级
- **平台风险登记：**
  - 抖音 60s 上限：TTS 预估总长 62.35s · **超 2.35s 需处理**（选项：主动 tail 裁 · 或延到 60s 段位 · 或 MiniMax 实际发声可能比估算快 5% 落到 59-60s 内 · 建议 render 后 QC 决定）
  - 小红书轮播主推 · 视频版 ≤60s 备胎（同抖音超时风险）· 若视频超 60s 只走轮播
  - 视频号 60-90s 甜区：58s 微短于甜区下沿 · 密度足够 · 观察 D+7 数据决定是否补 D04B 长版
  - QuickTime 屏录 4 场次 + Pexels 白天办公 B-roll 均未拉齐 · **render 阻塞 · 见 BUILD_NOTES.md § 1**

## 7. 铁律 0 三问自检（Audience-First）

| 问 | 判 | 依据 |
|---|---|---|
| **观众看完会共鸣吗？** | ✓ | M1 白天办公摄像头亮红点 1s 认领「这是我」· M4 群体锚「9 成中腰部创作者遇到选题问题——不是你的问题」共情释放 · M5 反爆款抱怨「40w vs 800」情绪冲击 · M9 反教程价值锚「不是教你 · 是把 prompt 给你」认知重构 · **四层情感锚** |
| **强观赏性？** | ✓（有余量）| 三风格混合（Vibe Motion 62% + WaytoAGI 21% + Pexels 15%）· 每 2-4s 视觉变化 · 10 段 6 种形式 ID · sfx 34 事件音撑节奏 · **屏录反差差异化视觉资产** |
| **强内容？** | ✓ | M7 4 段 prompt 结构（身份卡 / 账号定位 / 粉丝痛点 / 输出约束）可复用可核验 · M8 5 判据（具体场景 / 前 3s 钩子 / 差异化 / 可拍性 / 粉丝相关）可测 · M10 CTA 具体承诺「5 条选题」· 双收藏动机（M7 + M8）+ CTA 分型 |

## 8. 与 D03 差异化（Q6 铁律 · 与上条差异）

| 差异维度 | D03（英语口语）| D04（帮想选题）|
|---------|--------------|--------------|
| 场景 | 深夜 23:12 台灯 3000-3500K | 白天 3800-4200K + 摄像头亮红点 |
| 群体锚 | 92% 中国人不敢开口 display 160pt 全屏灰底 | 9 成中腰部创作者 headline 96pt 白字实景叠层 |
| 反面正解 | AI 十条建议废话（1 屏静态）| 3 段烂 prompt 快切屏录（3 屏动态） |
| 收藏点 | M6 role prompt 全屏 1 处 | M7 4 段 badge + M8 5 判据表格 2 处 |
| CTA | 评论区关键词四选一（面试/雅思/日常/旅游）| 私信「账号 + 方向」→ 5 条选题 |
| 视觉血统 | Vibe Motion（角色卡文本主）| Vibe Motion 主（屏录 UI 演示）+ WaytoAGI 辅（表格信息图）|
| 情感锚 | 学英语孤独感 | 中腰部创作者选题焦虑 |

**结论：** D04 与 D03 无视觉族群重叠 · 无同段位复用 · form_competition H6 门禁通过

## 9. 结论

- **允许**：外发三平台 mp4 + 小红书 7 页轮播（`build/w28d04_*_no_bgm.mp4` · 前提是 BUILD_NOTES.md § 1 前置资产齐 + render 完成）
- **不允许**：在 `room/verdict.yaml` 写 pass/approved（当前 scorecard 除 form_strategy pass_dual_review 外均 pass_single_run / pass_self_generated · 无真独立复评 · 与 D03 同待遇 · 允许外发但不允许 approved）
- **必做**：
  1. BUILD_NOTES.md § 1 前置资产齐（Pexels 白天 B-roll + QuickTime 4 场次屏录 + 4 段 prompt 家居版全文 + gen_ui_w28d04.py + Freesound sfx 10 项）
  2. render 后跑 gate_check_palette.py 兜底（禁 Dracula）
  3. D+2 回填三平台数据 · 若跌破 B 级下限 → 触发复盘会补人评 + v2 迭代
  4. D+7 判断是否补 D04B 长版（xhs skin 化 · 家居收纳外的美妆 / 母婴 / 数码 skin prompt）
