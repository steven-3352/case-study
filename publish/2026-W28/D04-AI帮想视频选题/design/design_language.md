# 视觉语言约束 · design_language · W28D04 AI 帮想视频选题

> 工种：视觉语言策展师（合并进"视觉设计+"）
> 依赖：`scripts/vA.md`（抖音主推 · chaos-punch-reveal 三拍 + 4 段 prompt 演示核心）· `scripts/vB.md` v2（备胎 · 数字精简 + 原话情感锚）· `retention_beat_sheet.md`（9 段形式切换）· skin.tone_direction（同行说话 · 不 preach · 不 sell 秘籍）
> 状态：`draft_self_generated` · 2026-07-05
> 依据 memory：`feedback_no-neon-palette`（禁 Dracula 紫粉青）· `feedback_anti-ai-visual`（反 AI 味）· `feedback_pipeline-full-platform-output`（三平台字号差 42/50/42）· `feedback_pipeline-burn-subs`（字幕烧片流程）

## 0. 入口必读（已过）

- [x] SYSTEM refs · §3.2 留存铁律 · §3.2a Q9 视觉路线（禁霓虹/禁 AI 味/证据优先）· §3.4 拒稿反例（catalog 拼盘）
- [x] template refs · `topic_brief.md` skin.tone_direction · `core_message.md` P0-P1 · `retention_beat_sheet.md` 9 段形式切换 · `scripts/vA.md` 主推 · `scripts/vB.md` v2 备胎
- [x] memory refs · `feedback_no-neon-palette`（禁 Dracula 紫粉青）· `feedback_anti-ai-visual`（反 AI 味）· `feedback_contrast-hook-3s`（chaos-punch-reveal 三连）· `feedback_pipeline-burn-subs`（字幕由 pipeline 烧）· `feedback_pipeline-full-platform-output`（字号 42/50/42）
- [x] 姊妹条 refs · D03 design_language.md（**学** token 三段策略（canvas/surface/accent）· 学禁用项写法 · 学逐镜表格结构 · **不复用**深夜黑 `#0a0a0a` 全屏底 · 不复用台灯暖光 · 不复用 92% 群体锚版式；D04 是白天办公桌 + 摄像头场景 · 群体锚 90% 是散点式非全屏）
- [x] 能力清单 refs · `pipeline/p004_video/lib`（config-driven 架构 · 参考 D03 走通经验）· `assets/formats/catalog.yaml`（形式词汇但不套用具体 html 文件名）· 无 DESIGN.md（本项目未维护 · 从 skin.tone_direction + memory 铁律直提）

**触发词打断（已过）：**「用 D03 深夜黑照抄」「Dracula 紫 accent 挺好看」「AI 生图做 chaos 首镜」「花字加封面」「屏录中打上 ChatGPT logo 增加信任」→ 本节 token 全部与 D03 显式区分 · Dracula 全禁 · chaos 用真人真机拍摄 + 屏录 · 竞品 UI 只保原生色不打 logo。

## 0-a. 本条定位

- **content_id:** W28D04
- **平台 / 形态:** 抖音 55-58s 视频（**主推 vA 反差冲击型** · A/B 备胎 vB v2 数字精简型）+ 小红书 7 页轮播（P1 共情锚封面）+ 视频号 65-72s 延伸版（加 15-20s 情绪段）
- **观众行为目标:** **停划**（0-3s chaos-punch-reveal 屏录反差）+ **看懂**（4 段 prompt 结构大字滑入 · 5 判据表格打勾）+ **收藏**（25-40s 4 段 prompt 可暂停截屏 + 40-48s 5 判据表格截屏）+ **评论/私信**（54-58s CTA "私信喂选题"）
- **参考来源:**
  - **DESIGN.md:** N/A（本项目未维护统一 DESIGN.md · 本条从 skin.tone_direction + memory 铁律直提）
  - **选择理由:** 中腰部创作者赛道禁"教程感"（同行"AI 一键出爆款"话术已在 hook_benchmark 打脸）· 禁"AI 味"· 禁 Dracula 霓虹（memory 铁律）· 参考三条实拍语法：
    1. **屏录真机操作**（chaos-punch-reveal 首镜 · 真机 ChatGPT/DeepSeek/豆包 · 保留 iOS 状态栏/输入光标/系统色）
    2. **白天办公桌视角**（俯拍键盘 + 摄像头红点 + 空笔记本 · 不同于 D03 深夜台灯暖光）
    3. **表格 + 打勾兑现**（40-48s 5 判据表格 · 借用 Excel/Notion 的表格视觉语言但不打这些工具的 logo）
  - **不照抄声明:** 本条视觉不参考具体品牌 · 不照抄任何 W27 近作 · 不照抄 D03 深夜自习房（D03 深夜 23:12 台灯暖光 · D04 白天办公桌摄像头亮红点；D03 92% 群体锚 display 160pt 灰底全屏 · D04 9 成群体锚 headline 96pt 白底 B-roll 叠层；D03 无屏录反差首镜 · D04 chaos-punch-reveal 屏录三拍是首镜差异化视觉资产）

## 1. 视觉关键词

用 5 个词描述本条画面气质，必须能指导取舍：

1. **白天办公桌 · 摄像头亮** — 桌面自然光 3800-4200K 色温（区别于 D03 深夜 3000-3500K）· 键盘 + 摄像头红点 + 空笔记本 = 中腰部创作者标志性场景 · 可拍性高（真机拍摄 · 无需棚拍）
2. **屏录反差 · chaos-punch-reveal** — 0-3s 差异化视觉资产 · AI 对话框光标闪 → 打字「帮我想 10 个」→ AI 输出「如何做好 XX」被红叉 whoosh 打掉 · 屏录是本条唯一"同行没做过"的首镜手法
3. **同行说话 · 克制** — 无 emoji · 无强色堆砌 · 无形容词字幕 · 与 skin.tone_direction "同行说话不 preach" 一致 · 视觉气质向 Muji 无印良品的沉默 + Medium 长文的克制排版靠拢
4. **可截屏兑现** — 25-40s **4 段 prompt 结构大字滑入**（收藏动机第一位）· 40-48s **5 判据表格打勾**（可测承诺兑现）· 小红书 P4-P7 完整 prompt 全屏（一键长按保存图）
5. **数字锚白字大 · 单位显式** — 9 成 / 40w 赞 / 800 赞 / 10 里 8 / 30 分钟 5 条 · 用 headline 96pt 白字 + caption 单位小字（vB v2 verdict 已强制"补单位")· 不用彩色数字 · 不用 GSAP 数字跳动

## 2. Token 提取

### 色板

| 角色 | 色值 | 用途 | 禁用 |
|------|------|------|------|
| **canvas_office_dark** | `#1a1a1a` | 抖音大字入背景（M3 reveal 大字 · M9 价值锚全屏 · M10 CTA 灰底）· 与 D03 深夜 `#0a0a0a` 显式区分（本条办公桌灰而非纯黑，暗示白天而非深夜） | Dracula 紫粉青 · 暖红→冷蓝渐变 · `#000` 纯黑（太重）|
| **canvas_daylight** | 自然日光（Pexels B-roll 自带 3800-4200K）· 允许在实景 B-roll 中出现 | 白天办公桌背景（M1 chaos · M4 3-8s 群体锚 · M5 分屏底）· 不做人工提亮 | 荧光橙 · 3D 玻璃质感 · 反差过强的伪高光 |
| **surface_paper** | `#f5f5f0` | 小红书轮播 P1-P7 底 · 便签 CTA · 视频号加长版 15-20s 情绪段 caption 底 | 亮白 `#ffffff`（太刺眼 · 与克制感不合）· 米黄 `#faf5e6`（会显教程感）|
| **ink** | `#1a1a1a` | 小红书轮播标题 · 正文（P4-P7 完整 prompt 文本）| 纯黑 `#000` · Dracula 深蓝紫 |
| **ink_light** | `#f5f5f0` | 抖音黑底大字（M3 reveal · M9 价值锚 · M10 CTA）· 与 canvas_office_dark 反色配对 | 亮白 `#ffffff` · 冷灰 |
| **muted** | `#7a7a7a` | 来源标注（引 知乎/reporter_notes/人人都是产品经理）· caption 底部小字（"可长按暂停截屏抄"）· 5 判据表格分割线 | 灰紫 · 冷蓝 · Dracula 灰粉 |
| **accent_red** | `#e53935` | reveal 红叉 whoosh（M3 打掉 AI 输出）· 反例烂 prompt 描边（M6 3 段烂做法）· 反差数字描边（可选 40w 反差 vs 800 · 但字幕本身仍白字）| 偏粉红 `#ff5252` · 荧光橙 `#ff6600` · 3D 立体红 |
| **accent_soft** | `#ffc857` | 4 段 prompt 分段标签底色（M7 演示核心 · 身份卡/账号定位/粉丝痛点/输出约束 4 个 badge）· 小红书 P4 4 段结构标注 | 荧光黄 `#ffff00` · 霓虹绿 · 番茄红 |
| **accent_green** | `#4caf50`（sober · 非荧光）| 5 判据表格打勾（M8 · 8 绿勾）· 不做数字动效 · 静态打勾即可 | 荧光绿 · 霓虹绿 · Dracula 青 |
| **system_native** | iOS 蓝 `#007aff` / 微信绿 `#95ec69` / ChatGPT UI 原生 / DeepSeek UI 原生 / 豆包 UI 原生 | 屏录 UI 真实痕迹 · 不打 logo 但保留原生色板 | 自造品牌蓝 · 3D 玻璃质感 |

**核心色策略：**
- 主色 = **办公桌灰 + 白天光 + 纸黄轮播底 + 屏幕内 UI 原生色**（画面 50% 深色系 / 30% 白天光 B-roll / 20% 原生 UI 高光）
- accent_red 只用于 **reveal 红叉 + 反例描边** 两处（每帧 ≤ 5%）· 不做全片背景色
- accent_soft 只用于 **4 段 prompt 分段标签**（M7 · 4 个 badge · 每帧 ≤ 8%）
- accent_green 只用于 **5 判据打勾**（M8 · 8 绿勾静态 · 每帧 ≤ 6%）
- 允许竞品 UI 原生色（ChatGPT 深绿、DeepSeek 蓝、豆包紫）——真实屏录痕迹优先，但**禁打 logo**
- 数字锚（9 成 / 40w / 800 / 10 里 8 / 30 分钟 5 条）用 ink_light 白 + 可选 accent_red 极细描边 · **不用彩色数字**（禁 D04 视觉曾出现的彩虹数字堆砌 · 见 memory `feedback_no-neon-palette`）

### 字体与层级

| 层级 | 字号 / 字重 | 行高 | 用途 | 单屏上限 |
|------|-------------|------|------|----------|
| **display** | 140-180pt / 900 | 1.0 | M3 reveal 大字入「打"帮我想 10 个" · AI 全给"如何做好"」· M9 全屏价值锚「不是教你 · 是把 4 段 prompt 给你」· 抖音封面主标 | 8 字以内单行 |
| **headline** | 88-112pt / 700 | 1.1 | M4 群体锚（9 成中腰部创作者遇到选题问题）· M5 反差大字（40w 赞 vs 我 800 赞）· M8 表格大结论（10 里 8 能用）· M10 CTA（私信「账号方向」→ 5 条选题） | 10 字以内 |
| **body** | **抖音 42pt** / **小红书 50pt** / **视频号 42pt** · 权重 500 | 1.3 | 中段字幕（口播文本转字幕）· 三平台字号差按 `feedback_pipeline-full-platform-output` 硬约束 · pipeline 烧片时自动切 | 12 字以内单行 |
| **caption** | 28-32pt / 400 | 1.4 | 来源标注（"引 知乎专栏"/"人人都是产品经理"）· 时间戳（vB v2 秒表小字 30:00）· 底部小字（"可长按暂停截屏抄"）· CTA 底部小字 | 10 字以内 |
| **mono** | 32-40pt / 400 | 1.4 | M7 演示核心的 4 段 prompt 代码块（屏录满屏 · 观众可暂停截屏）· 小红书 P4-P7 完整 prompt 全屏 | 覆盖满屏 · 每行 40 字以内 |

**字体族：**
- 中文：**苹方 / 思源黑体**（PingFang SC / Source Han Sans）· 权重区分而非字体族切换
- 英文数字：**San Francisco / Inter**（数字锚 · 数字标签 · UI 英文）
- 代码 / prompt：**JetBrains Mono / SF Mono**（等宽 · 屏录中的 4 段 prompt 文本）

**禁用字体：**
- ❌ 站酷高端黑（AI 味重灾区 · 中腰部创作者一眼看穿是同行套路）
- ❌ 阿里巴巴普惠体（太企业 · 与"同行说话"皮肤冲突）
- ❌ 手写体（会显做作 · 与克制感冲突）
- ❌ 装饰性衬线（宋朝体、颜体等 · 中腰部创作者不需要仪式感）
- ❌ 花字（W27D04 教训 · 会拉低克制感）
- ❌ 站酷小薇 LOGO 体（俏皮感 · 与同行说话皮肤冲突）

### 形状与间距

- **圆角**：屏幕 UI 元素跟随原生（iOS `12rpx` 状态栏、ChatGPT UI 原生、DeepSeek UI 原生、豆包 UI 原生），自造元素用 `4rpx` 硬边角（不做圆润卡片）
- **边框**：几乎不用；只在 M6 反例烂 prompt 上用 `2px accent_red` 描边（3 段烂做法各一次）· M7 4 段 prompt 分段标签用 `accent_soft` 淡黄底色不加边框
- **阴影 / 深度**：**禁用装饰性阴影** · 只保留系统 UI 原生（微信气泡默认阴影、iOS UI 阴影、桌面 UI 窗口阴影）· 白天办公桌 B-roll 自带光线阴影够用
- **留白密度**：单屏一个主信息 · 大字周围至少留 1.5 倍字号的空白 · 4 段 prompt 每段之间留 1.2 倍行高
- **卡片最大层级**：**2 层**（背景 + 单卡片） · **禁止 3 层堆叠**（agent_grid / 备忘录风的多层卡片 · SYSTEM Q9 明确禁）
- **屏录内间距**：AI 对话框内文本按原生间距不改 · 只在 SVG 覆盖层加 `accent_soft` 标签块

## 3. 组件规则

| 组件 | 应该怎么画 | 不该怎么画 |
|------|------------|------------|
| **抖音封面** | 从 vA M3 reveal 段（1.6-3s）取 `video_frame` · AI 输出被红叉的定格 + display 140pt 白字「AI 全给"如何做好"」· 或全屏 `douyin_punch` 黑底大字 | 分屏静图 · 3D 效果 · 「学英语党狂喜！」感叹式 · light_split / phone_ui（cover_standards 明确禁抖音用）|
| **小红书封面 P1** | 主角背影 + 摄像头亮 + 空笔记本（白天光）· display 140pt 白字「对着摄像头空半小时」+ 副标 caption 32pt「你不是不行 · 是没告诉 AI 你是谁」| 3D 效果 · 全彩背景 · 「点击查看」箭头 · 花字装饰 |
| **屏录 AI 对话框**（M1-M3 chaos-punch-reveal · M6 反例 · M7 演示核心）| 保留系统状态栏（iOS 或 macOS 顶部 bar）· 保留 AI 对话框原生 UI · 光标闪 · 打字节奏 30ms/字 真实拟音 · 输出用系统字体 | 裁掉状态栏 · 抠白底 · 加自造装饰性框 · 打 ChatGPT/DeepSeek/豆包 logo（中立 · 只保原生 UI 色）|
| **红叉 whoosh 打掉**（M3 reveal）| accent_red 大红叉 · 每条 AI 输出被 whoosh 从右上角横向划过打掉 · 每次 0.3s · 3 次连打 | 静态红叉贴图 · 彩色叉 · 3D 立体叉 · GSAP 弹跳动画 |
| **4 段 prompt 分段标签**（M7 演示核心 · 15s 收藏动机段）| accent_soft 淡黄底 badge · 黑字 headline 88pt 段名「身份卡 · 账号定位 · 粉丝痛点 · 输出约束」· 每段淡入 0.5s + 停 3-4s · 底部 caption 28pt「可长按暂停截屏抄」 | 4 段挤在一屏 · 段名彩色 · 数字 GSAP 跳动 · 每段之间加装饰性图标 |
| **数据数字**（9 成 / 40w 赞 / 800 赞 / 10 里 8 / 30 分钟 5 条）| headline 96pt 白字 + caption 单位小字（"赞"字 32pt · 避免 800 粉起号歧义 · vB v2 verdict 硬约束）· 可选 accent_red 极细 1px 描边强调关键数字 | 彩色数字堆砌 · GSAP 滚动特效 · 数字 + emoji · 数字跳动放大缩小 · 无单位数字（歧义源头）|
| **分屏爆款对比**（M5 40w 赞 vs 800 赞）| 两张真实截图（马赛克遮挡个人信息）· 50/50 横向并列 · 中间 2px ink_light 白色分割线 · 大字类比锚居中偏下「40w 赞 vs 我 800 赞」headline 96pt | 三分屏以上 · 图之间加装饰性边框 · 大字叠图中间遮挡视觉焦点 · 打真实同行 logo |
| **5 判据表格**（M8 · 40-48s）| 表格结构：横行 = 10 条候选选题，纵列 = 5 判据（具体场景 / 前 3s 钩子 / 差异化 / 可拍性 / 粉丝相关）· 打勾用 accent_green 静态 · 打叉用 accent_red 静态 · 大结论 headline 96pt「10 里 8 · 能用」· 无 GSAP 打勾动画（直接显示即可） | 打勾动画 · 表格 3D 效果 · 花色底 · 表格外加装饰边框 · 大结论用彩色数字 |
| **群体锚数字**（M4 3-8s 9 成中腰部）| 实景 B-roll（主角背影 + 摄像头亮）叠层 · 白字 headline 88pt「9 成中腰部创作者遇到选题问题」+ caption 24pt 来源「引 知乎专栏 A 级」 | 全屏灰底大字（**这是 D03 版式 · D04 禁复用**）· 无来源标注 · 彩色渐变数字 |
| **秒表小字**（vB v2 备胎版 M1 · 0-3s 场景锚辅助）| caption 32pt · muted 灰色 `#7a7a7a` · 右下角 · 静态「30:00」（不做反向倒数动画 · vB v2 verdict 已删）| GSAP 反向倒数动画 · 秒表大字占屏 · 时间戳动效跳动 |
| **CTA 大字**（M10 54-58s）| canvas_office_dark 灰底 + headline 88pt 白字「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ caption 底部小字「同行互助 · 不推服务」 | 亮色 CTA 按钮 · 「点这里」箭头 · 弹幕特效 · emoji 装饰 |
| **价值锚全屏**（M9 48-54s）| canvas_office_dark 灰底 + display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」· 无 B-roll 只有字 + 沉稳 VO | 3 行标题 · emoji + 感叹号 · 花字 · 背景加装饰性 pattern |

## 4. 逐镜应用（对应 vA 主推 10 段镜头 · retention_beat_sheet.md 9 段形式切换）

| 镜 | 时间 | 主色 | 字体层级 | 组件 | 关键约束 |
|----|------|------|----------|------|----------|
| **M1** | 0-1s（chaos）| canvas_daylight 白天光（俯拍 · 桌面自然光）| 无字幕（**首秒故意留白**）| 电脑桌俯拍 + 键盘 + 摄像头红点 + 主角右手悬在键盘上不落 | 无 BGM · 无 VO · 只有环境音（AC 底噪 + 远处交通 + tick sfx 0.3s）· 摄像头红点必须清晰可见（构图右上或右下）|
| **M2** | 1-1.6s（punch）| 屏幕特写切入（AI 对话框光标闪）· 保留 iOS/macOS 状态栏 | 无字幕（打字过程本身即视觉字幕）· mono 32pt 屏幕内文字 | 屏录 · 手落键盘 · 打字「帮我想 10 个抖音选题」14 字（真人打字节奏 · 每字 30ms）· 回车 | 拟音打字声真实录（14 声 · -8dB）· 回车 tick sfx · 无字幕 · UI 原生 · 不打 AI 工具 logo |
| **M3** | 1.6-3s（reveal）| 屏幕（AI 对话框深色系）+ display 140pt 白字入 · accent_red 红叉动效 | display 140pt 白字「打"帮我想 10 个" · AI 全给"如何做好"」屏中央 | AI 输出 3 条「如何做好家居收纳 / 浅谈 XX 的重要性 / 5 个 XX 误区」→ 3 次 whoosh + hit 依次打掉 → display 大字入 | 前 3s VO 静默已完 · 3 次 whoosh（-10dB）+ 1 次 hit（-8dB · 大字入拍点）· 红叉必须 whoosh 从右上横划非静态贴图 |
| **M4** | 3-8s | canvas_daylight 实景 B-roll（主角背影 + 摄像头亮 + 空笔记本）+ headline 白字叠层 | headline 96pt 白字「9 成中腰部创作者遇到选题问题」+ caption 24pt 来源「引 知乎专栏 A 级」 | 实景 B-roll（真人拍摄 · 白天办公场景 · 3800-4200K 自然光）+ 数据大字叠层 | 3s 处 VO 起「上周我也这样。9 成中腰部创作者早期都遇到选题问题——不是你的问题」+ tick sfx（-15dB）· 数据大字必须比 D03 版本收敛（不用全屏灰底）· 来源可见但小 |
| **M5** | 8-15s | 屏录真实截图（40w 赞 · 800 赞 · 马赛克遮挡个人信息）+ ink_light 白分割线 + headline 白字 | headline 96pt 白字「40w 赞 vs 我 800 赞」+ caption 32pt「翻竞品 30 分钟存 8 张截图 · 一条不想拍」 | 分屏 50/50 · 左「同行 40w 赞」右「我 800 赞」· 中间 2px 白分割线 · 大字类比锚居中偏下 | 单位显式（"赞"字必须出现 · vB v2 verdict 硬约束）· 马赛克遮挡真实同行头像/账号名 · 竞品收藏夹截图允许出现但不打真实账号 logo |
| **M6** | 15-25s | 屏录 3 段快切（3 个 AI 对话框实录）+ accent_red 描边强调反例 | mono 32pt 反例 prompt + caption 28pt 大字批注「跳过身份卡」「跳过账号定位」「跳过粉丝痛点」 | 屏录 3 段：①「帮我想 10 个」→ 通用套话 ②「加平台词」→ 同行都在拍 ③ 让 AI 抄爆款 → 数字加一档同质品 · 每段用 accent_red 2px 描边框 · hit sfx 打点 3 次 | 三段等时长（约 3s 每段）· 反例描边只出现在关键错误行不全屏描边 · 大字批注用 accent_red 描边强调「跳过 X」 |
| **M7** | 25-40s | 屏录 AI 对话框深色系 + accent_soft 淡黄底 4 段标签 SVG 覆盖 + caption 底部小字 | mono 32-40pt 4 段 prompt 全文 + accent_soft 淡黄底 headline 88pt 段名 badge + caption 28pt「可长按暂停截屏抄」| **收藏动机第一位** · 屏录：打开 AI → 粘贴完整 4 段 prompt（家居收纳版）→ AI 表格输出 10 条候选（标题/场景/钩子/成本/差异化 每条 1s 打字机式出现）· whoosh sfx 每段结构切换（4 次） | 每段 accent_soft 淡黄底 badge 淡入 0.5s + 停 3-4s · **4 段结构**「身份卡 · 账号定位 · 粉丝痛点 · 输出约束」badge 明确 · 底部 caption 小字必须出现「可长按暂停截屏抄」（收藏动机点）|
| **M8** | 40-48s | canvas_office_dark 灰底 + 表格结构 + accent_green 打勾 + accent_red 打叉 + headline 白字大结论 | headline 96pt 白字「10 里 8 · 能用」+ caption 28pt「5 判据 · 通过 4 条即能用」+ mono 28pt 表格条目 | 表格上屏：10 条候选左列 + 5 判据（具体场景/前3s钩子/差异化/可拍性/粉丝相关）横排 · 打勾 accent_green 静态 · 打叉 accent_red 静态 · 大结论「10 里 8 · 能用」+ hit sfx 打点 | **打勾用静态**（禁 GSAP 动画）· 表格外无装饰性边框 · 大结论 headline 96pt 白字（不用彩色数字）· 5 判据每条 caption 28pt 可读 |
| **M9** | 48-54s | 全屏 canvas_office_dark 灰底 · 无 B-roll 只有字 | display 140pt 白字两行 · 权重 900 | 全屏文字「不是教你」（第 1 行）/「是把 4 段 prompt 给你」（第 2 行）· 沉稳 VO · ambient sfx 落底 · hit sfx 收尾 | 两行分行必须清晰 · 每行 6-8 字 · 居中对齐 · 无 B-roll 干扰 · 无 emoji · 无花字 |
| **M10** | 54-58s | canvas_office_dark 灰底 + headline 白字 + caption 底部小字 | headline 88pt 白字 CTA + caption 28pt 底部小字 | CTA：「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ 大字浮动 + hit sfx 收尾 | CTA 大字居中 · 底部 caption 小字「同行互助 · 不推服务」呼应 skin.landing_intent 硬约束 · 无箭头 emoji |

**vB v2 备胎逐镜差异（仅列出与 vA 不同点）：**

| 镜 | vA（主推） | vB v2（备胎 · 数字精简 + 原话情感） | 视觉切换点 |
|----|-----------|-----------------------------------|----------|
| **M1（0-3s）** | 屏录 chaos-punch-reveal 三拍 | 主角背影 + 摄像头亮 + 秒表小字 30:00（右下 muted 灰色）+ display 大字入「空半小时·0 条选题」 | vB 用实景 B-roll + display 大字 · 无屏录（备胎定位下的场景锚版本）· 秒表小字 caption 32pt muted 灰色 · 静态非动画 |
| **M4（8-13s）** | 反爆款抱怨（40w vs 800）| 加 topic_brief 原话 #2「为什么我抄爆款别人爆我不爆啊」引号直引 | 原话直引用引号符号（「」）+ mono 32pt 字体（区别于旁白 body 42pt）· 视觉上明显区分"这是原话"|
| **M5（13-18s）** | vA 无此镜（并入 M5 40w vs 800）| 独立成节拍 · 日历翻页视觉 + topic_brief 原话 #3「每周发一篇变成半个月发一篇」| 日历翻页拟音 + 上周 1 → 这周 0 视觉冲击 · 数字标签 caption 32pt |
| **M6 末尾** | 3 段烂做法收尾 | 末尾加 display 140pt 大字「累」（topic_brief 原话 #5 直引）| 全屏定格「累」一字 · display 权重 900 · 情绪落点 · 独立 hit sfx 深长版 |

## 5. 禁用项汇总（一键 fail 触发条件）

- ❌ **Dracula 霓虹紫 `#bd93f9` / 粉 `#ff79c6` / 青 `#8be9fd`** — 项目全局禁（SYSTEM Q9 · memory `feedback_no-neon-palette`）· pipeline `gate_check_palette.py` 会硬拦
- ❌ **偏粉红 `#ff5252`** — 用血红 `#e53935` 代替
- ❌ **暖红→冷蓝渐变** — 用 `#1a1a1a` canvas_office_dark 单色底
- ❌ **HTML+GSAP 居中大字** — 会显 AI 味（memory `feedback_anti-ai-visual`）· 本条用真实屏录 + drawtext 大字 + SVG 覆盖代替
- ❌ **卡片堆叠 3 层以上** — 避免与 W27D01/D05 agent_grid / pain_stack 撞形
- ❌ **报纸风版面** — 避免与 W27D04 撞形
- ❌ **备忘录风统一 HTML 模版** — SYSTEM Q9 明确禁
- ❌ **AI 生图作主视觉** — Q9 铁律 · chaos 尤禁 · 本条 M1 chaos 必须真机 + 真人拍摄
- ❌ **合成假 BGM**（ffmpeg aevalsrc/sine 拼的）— memory `feedback_no-synth-bgm`（本条密 VO 演示型默认无 BGM · memory `feedback_dense-vo-no-bgm-default`）
- ❌ **打 ChatGPT / DeepSeek / 豆包 / 通义 / 天工 logo** — 保留原生 UI 色但不打 logo · 工具中立
- ❌ **点名真实同行账号**（家居博主小林是化名 · 40w 赞截图必须马赛克遮挡真实头像/账号名）· 不打脸不背书
- ❌ **数字跳动 GSAP 特效** — 9 成 / 40w / 800 / 10 里 8 全部静态大字 · 不用滚动动效（会显 AI 味）
- ❌ **秒表反向倒数动画**（vB v1 曾用 · 已删）— 静态「30:00」小字辅助即可 · 不做动效
- ❌ **花字 / 装饰性衬线** — 会拉低克制感（W27D04 教训）
- ❌ **D03 深夜黑 `#0a0a0a` 全屏底** — D04 用 `#1a1a1a` canvas_office_dark 显式区分白天场景
- ❌ **D03 92% 群体锚 display 160pt 灰底全屏** — D04 9 成群体锚是实景叠层 headline 96pt 白字 · 显式区分版式
- ❌ **无单位数字**（「40w vs 800」缺"赞"字）— vB v2 verdict 硬约束 · pipeline `gate_check` 会 fail

## 6. 通过检查

- [x] 关键词 5 个（白天办公桌 · 屏录反差 · 同行说话 · 可截屏兑现 · 数字锚白字大 · 全部具体可指导取舍）
- [x] 色板含 canvas / surface / ink / muted / accent / accent_soft / accent_green / system_native（本次 10 类 · 与 D03 显式区分）
- [x] 字体层级 5 级（display / headline / body 三平台差异 / caption / mono · 三平台字号差 42/50/42 与 `feedback_pipeline-full-platform-output` 一致）
- [x] 组件规则含 Do / Don't 对（本次 12 组件）
- [x] 逐镜应用完整（vA 主推 10 段镜头全覆盖 + vB v2 差异点单列 4 段）
- [x] 禁用项与 SYSTEM Q9 + memory 一致（禁霓虹 / 禁 AI 味 / 禁合成 BGM / 禁竞品 logo / 禁 GSAP 数字跳动 / 禁 D03 版式复用 / 禁无单位数字）
- [x] 未复用任何 W27 近作 token（W27 老板圈无本条使用色板 / 组件）· 显式与 D03 深夜自习房区分（白天办公 vs 深夜台灯 · 屏录反差 vs 无屏录首镜 · 9 成叠层 vs 92% 全屏）

## 7. 移交下一环节

- **form_strategy.md（步 7）**：本 design_language 提供 token 与组件约束 · form_strategy 逐镜选表达方式（实拍 / 屏录 / SVG 覆盖 / drawtext / 表格动画）· 每镜必须声明服务哪一项数据杠杆
- **openmontage_brief.md（步 8）**：每条必跑判断 enabled/disabled/blocked · 本条视频合成 runtime 待定
- **motion_storyboard.md（步 9 · 动画导演）**：本 design_language 直接用于逐秒 9 字段分镜的画面/字幕/组件规则输入 · 动画导演单跑不双评
- **motion_tech_plan.md**：本条 M3 red 叉 whoosh + M7 4 段 badge 淡入 + M8 表格静态打勾 · 使用 SVG 静态 + drawtext 大字 + drawbox 白闪（M5/M8 快切标注）· 无 Web 3D / GSAP 复杂动效 · 单独登记 SKIP 理由 → 待审
- **storyboard.yaml（步 10）**：本 design_language 直接用于分镜的画面 / 字幕 / 组件规则
- **audio_plan.yaml（步 11）**：BGM 情绪跟随本条 tone_direction 关键词「同行说话 · 克制」→ **默认无 BGM**（密 VO 演示型 · `feedback_dense-vo-no-bgm-default`）· sfx 4 类必覆盖（tick 3 次 + whoosh 4-6 次 + hit 5-8 次 + ambient 全片）
- **cover_brief.md（本节同时产出）**：抖音主推 `video_frame` 从 M3 reveal 段（1.6-3s）取定格 · 小红书 P1 共情锚 · 视频号同抖音口径

## 8. Audience-First 自查三问（design_language 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ **白天办公桌 + 摄像头亮 + 空笔记本**是中腰部创作者的日常场景（不是 D03 深夜自习房 · 不是 W27 老板会议室）· 屏录 chaos-punch-reveal 三拍击中"我上周就打过一模一样的 prompt"· 4 段 prompt 结构 badge 呼应 skin.tone_direction「同行说话 · 把 prompt 给你」的视觉气质 |
| 画面**观赏性**够吗？ | ✅ 10 类色板互斥不打架 · 3 层视觉资产（屏录 + 实景 + 表格）· 数字/字幕/UI 层级清晰 · 单段最长 M7 4 段 prompt 演示 15s · 26% · 未超 catalog 拼盘门 35% · sfx 10+ 次撑节奏 · 每 3-8s 变化点足够 |
| 内容**真材实料**吗？ | ✅ M7 4 段 prompt mono 字体全屏可截屏（P0-3 核心方法论）+ M8 5 判据表格 accent_green 打勾（P0-4 兑现证明）+ 小红书 P4-P7 完整 prompt 全屏（收藏动机点）· 无 AI 生图假素材 · 屏录真机 · 白天办公 B-roll 走 Pexels CC0 或真人拍摄 |
