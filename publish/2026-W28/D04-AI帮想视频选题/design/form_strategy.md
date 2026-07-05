# 形式策略 · form_strategy · W28D04 AI 帮想视频选题

> 工种：形式策略官（合并 平台原生策划 + 纪录片导演 + 动效分镜师）
> 位置：`design/form_strategy.md`
> 依赖：
> - `design/form_competition.md`（**方案 A 原生 P001 混合 · 屏录 chaos-punch-reveal 首镜型 · 家族 pipeline · 69/60 分**）
> - `design/openmontage_brief.md`（decision=blocked_infrastructure）
> - `design/design_language.md`（10 色板 · 12 组件 · vA/vB v2 逐镜应用）
> - `design/cover_brief.md`（抖音 video_frame 2.4s · 小红书独立共情锚 · 视频号同抖音）
> - `retention_beat_sheet.md`（9 段 55-58s + 7 页轮播）
> - `scripts/vA.md`（**抖音主推 · chaos-punch-reveal 型**）
> - `scripts/vB.md` v2（**A/B 备胎 · 双评 avg 90.5 pass**）
> 状态：`pass_dual_review` · reviewer_A=92 / reviewer_B=92 / avg=92 · 6 硬门全过 · A 提 2 项 must_fix 已就地打补丁（§4-A 首秒音画同频 · §5 vA 4 条原话兜底）· 2026-07-05

## 0. 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` §4.2 五维打分 · §3.1e 承诺=兑现 · §3.2 留存铁律 · §3.4 拒稿反例（catalog 拼盘）
- [x] **template refs**：`templates/design/form_strategy.md` · `templates/design/completion_rate_north_star.md`
- [x] **memory refs**：
  - `feedback_contrast-hook-3s`（chaos-punch-reveal 屏录三拍是差异化视觉资产）
  - `feedback_no-neon-palette`（禁 Dracula）
  - `feedback_anti-ai-visual`（禁 AI 味 · 屏录 UI 原生色 · 无教程感）
  - `feedback_pipeline-burn-subs`（字幕烧片）
  - `feedback_pipeline-full-platform-output`（三平台字号差 42/50/42）
  - `feedback_dense-vo-no-bgm-default`（BGM off）
  - `feedback_dense-vo-no-dead-air`（VO ≥85% 无死区）
  - `feedback_sfx-layer-required`（sfx 独立必需层）
- [x] **姊妹条 refs**：`publish/2026-W28/D03-*/design/form_strategy.md` 实读（学表格结构 · 学数据杠杆声明 · 学 Fail 检查 · **不复用** 深夜 Pexels 清单 · **不复用** 92% 群体锚 display 160pt 全屏版式 · **不复用** role prompt 五段 SVG 标签）
- [x] **能力清单 refs**：`pipeline/p004_video/lib` config-driven（W28D04 走 pipeline_config.yaml + run_pipeline.py --step all）· `fetch_broll.py` 需拉白天办公桌 3800-4200K + 摄像头亮 + 空笔记本新素材

**触发词自查（本次开工前主动检查）：**
- [x] 未出现"D03 form_strategy 表格改字就行"这类跨条克隆念头
- [x] 未出现"catalog 拼盘"念头（本条 9 段明确对应 vA 10 段分镜非套模板）
- [x] 未出现"OpenMontage 也许可以"这类未跑 brief 的复议

## 1. 逐镜表达方案（抖音 55-58s · vA 主推 chaos-punch-reveal 型 10 段镜头）

| 镜 | 时间 | 主意图 | 表达形式 | 形式 ID | 数据杠杆声明 |
|----|------|--------|----------|---------|------------|
| M1 | 0-1s | 停划 · chaos 白天办公空场 | Pexels 白天办公桌俯拍 + 键盘 + 摄像头亮红点 + 手悬键盘不落（3800-4200K）| `chaos_broll` 实景 B-roll | `completion_3s`：**摄像头亮红点是中腰部创作者标志性场景锚**（区别 D02 打工人下班 / D03 深夜台灯）· 1s 认领"这是我在做视频前的桌面" |
| M2 | 1-1.6s | punch · 打字冲击 | QuickTime 屏录 AI 对话框光标闪 → 手落键盘打字「帮我想 10 个抖音选题」14 字（真人打字节奏 30ms/字）→ 回车 | `broll_demo` 真机屏录 UI | `completion_3s`：**打字过程本身即视觉字幕**（同行"我上周就打过一模一样的 prompt"1s 认领 · 无字幕但认领感强）· 保留 iOS/macOS 状态栏 · 不打 AI 工具 logo |
| M3 | 1.6-3s | reveal · 反差爆点 | QuickTime 屏录 AI 输出 3 条「如何做好 XX / 浅谈 XX / 5 个 XX 误区」→ accent_red `#e53935` 3 次红叉 whoosh 打掉 → display 140pt 白字入「打"帮我想 10 个" · AI 全给"如何做好"」屏中央 | `broll_demo` 屏录 + SVG accent_red 覆盖 + `punch_black` drawtext 大字入 | `completion_3s` + **差异化视觉资产**：屏录反差是同行没做的首镜手法（core_message P0-2 反面正解前置）· 大字入拍点 hit sfx 强化反差冲击 |
| M4 | 3-8s | 认领 · 群体锚 | Pexels 白天办公 B-roll（主角背影 + 摄像头亮 + 空笔记本 3800-4200K）+ headline 96pt 白字叠层「9 成中腰部创作者遇到选题问题」+ caption 24pt 来源「引 知乎专栏 A 级」| `chaos_broll` 实景 + `punch_black` 叠层大字 | `completion_rate`：**9 成群体锚一秒释放"不是你的问题"羞耻感**（引 external_references #4 A 级）· **实景叠层 vs D03 全屏灰底显式区分**（D04 白天办公 vs D03 深夜黑） |
| M5 | 8-15s | 情绪释放 · 反爆款抱怨 | 分屏 50/50 · 左「同行 40w 赞截图」右「我 800 赞截图」（马赛克遮挡真实同行头像/账号名）· 中间 2px ink_light 白分割线 · headline 96pt 白字类比锚居中偏下「40w 赞 vs 我 800 赞」+ caption 32pt「翻竞品 30 分钟存 8 张截图 · 一条不想拍」| `before_after` 分屏静图 + `punch_black` 大字 | `completion_rate`：**单位显式硬约束**"赞"字必须出现（vB v2 verdict 硬约束 · 避 800 粉起号歧义）· 反爆款抱怨情绪冲击 · 类比锚 |
| M6 | 15-25s | 反面正解 · 3 段烂 prompt | 屏录 3 段快切（3 个 AI 对话框实录）· accent_red 2px 描边强调反例 · 每段 caption 28pt 批注「跳过身份卡」「跳过账号定位」「跳过粉丝痛点」· hit sfx 打点 3 次 | `broll_demo` 屏录快切 + SVG accent_red 描边 + drawtext 批注 | `completion_rate` + 理解：反面正解激发"那我该怎么办"期待反转 · 屏录真机保证 A 级证据链 · 3 段 hit 打点节奏保持 |
| M7 | **25-40s（15s · 26% 占比 · 全片最长）** | **演示核心 · 4 段 prompt · 收藏动机第一位** | QuickTime 屏录 AI 对话框深色系 · 打开 AI → 粘贴完整 4 段 prompt（家居收纳版 · JetBrains Mono 32-40pt）→ AI 表格输出 10 条候选（每条 1s 打字机式出现）· **accent_soft `#ffc857` 淡黄底 4 段 badge SVG 覆盖**（身份卡/账号定位/粉丝痛点/输出约束）· 每段淡入 0.5s + 停 3-4s · 底部 caption 28pt「可长按暂停截屏抄」 | `broll_demo` 屏录 + SVG accent_soft badge + drawtext 段名 + drawtext 底部 caption | `completion_rate` + **收藏率**：真机屏录动作性变化 + 4 段 badge 打点动态 + prompt 全屏可截屏（保守估 save_rate ≥6% · 呼应小红书 P4-P7 完整 prompt 可长按保存图）· **收藏动机点**明示 |
| M8 | 40-48s | 筛选表格 · 5 判据 · "10 里 8" | canvas_office_dark `#1a1a1a` 灰底 + 表格结构 10 条候选 × 5 判据（具体场景 / 前 3s 钩子 / 差异化 / 可拍性 / 粉丝相关）· **accent_green `#4caf50` sober 静态打勾 8 个** + accent_red 2 打叉 · headline 96pt 白字大结论「10 里 8 · 能用」+ caption 28pt「5 判据 · 通过 4 条即能用」+ hit sfx 打点 | `punch_black` 灰底 + 表格 SVG + drawtext 大结论 + accent_green 静态打勾 | `completion_rate` + **收藏率** + 可测承诺兑现：**5 判据表格截图**是第二收藏动机点（P0-4 承诺兑现证明）· **静态打勾**（禁 GSAP 动画 · 避 AI 味） |
| M9 | 48-54s | 价值锚 · 反教程 | 全屏 canvas_office_dark 灰底 · display 140pt 白字两行「不是教你」（第 1 行）/「是把 4 段 prompt 给你」（第 2 行）· 无 B-roll 只有字 · 沉稳 VO · ambient sfx 落底 + hit sfx 收尾 | `punch_black` 全屏灰底大字 | 评论率：**反教程价值锚是核心差异化承诺**（同行都在"教你 AI 一键出爆款" · 我们把 prompt 给你 · 同事口吻替代博主感） |
| M10 | 54-58s | 互动 CTA · 喂选题 | canvas_office_dark 灰底 + headline 88pt 白字 CTA「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ caption 28pt 底部小字「同行互助 · 不推服务」+ hit sfx 收尾 | `punch_black` + CTA 大字 + drawtext 底部小字 | 评论率 + 私信率：**两选项开放式提问 + 具体承诺**「5 条选题」低成本高确定回复 · skin.landing_intent 硬约束「不推服务」明示 |

## 2. vB v2 备胎版差异（若 vA 3s 完播 <52% 切换 · 仅列出与 vA 不同镜头）

| 镜 | vA（主推） | vB v2（备胎 · 数字精简+原话情感）| 视觉切换点 |
|----|-----------|----------------------------------|----------|
| **M1（0-3s）** | 屏录 chaos-punch-reveal 三拍 | 主角背影 + 摄像头亮 + 秒表小字 30:00（右下 muted `#7a7a7a` 灰色 · 静态非动画）+ display 140pt 白字入「空半小时 · 0 条选题」 | vB v2 用实景 B-roll + display 大字 · 无屏录（备胎定位下的场景锚版本）· 秒表小字 caption 32pt muted 灰色 · 静态非动画（vB v1 反向倒数已删） |
| **M4（8-13s）** | 反爆款抱怨（40w vs 800）| 加 topic_brief 原话 #2 直引「为什么我抄爆款别人爆我不爆啊」引号符号（「」）+ JetBrains Mono 32pt 字体（区别于旁白 body 42pt）| 视觉上明显区分"这是原话"（区别于旁白）· 引号符号 + mono 字体双标 |
| **M5（13-18s）** | vA 无此镜（并入 M5 40w vs 800）| 独立成节拍 · 日历翻页视觉 + topic_brief 原话 #3 直引「每周发一篇变成半个月发一篇」+ caption 32pt 数字标签 | 日历翻页拟音（whoosh + tick 组合）+ 上周 1 → 这周 0 视觉冲击 · 数字标签独立节拍 |
| **M6 末尾** | 3 段烂做法收尾 | 末尾加 display 140pt 大字「累」（topic_brief 原话 #5 直引 · 全屏定格）| 全屏定格「累」一字 · display 权重 900 · 情绪落点 · 独立 hit sfx 深长版（-8dB · 1.2s 尾音） |

## 3. 形式切换密度（防中段塌陷）

- **9 段镜头 · 6 种形式 ID**：`chaos_broll` × 1（M1）· `broll_demo` × 5（M2 + M3 + M6 + M7）· `punch_black` × 5（M3 大字入 + M4 叠层 + M8 灰底 + M9 全屏 + M10 CTA）· `before_after` × 1（M5 分屏）· SVG accent_soft badge × 1（M7）· SVG accent_green 打勾 × 1（M8）
- **超过 SYSTEM Q9 铁律要求**（≥3 种观感）
- **单一形式最大占比**：`broll_demo` 25-40s 屏录 15s（M7）= 全片 26% < 40% 上限 ✅
- **每 3-8s 有明确视觉变化** · 与 retention_beat_sheet.md「每 5-8s 视觉变化清单」9 段一一对齐

## 4. 关键场景细化

### 场景 A · 屏录 chaos-punch-reveal 首镜（M1-M3，0-3s）

**Q9 铁律：** chaos 必须是真实素材，禁用 AI 生图

**0-1s 音画同频配置（与 retention_beat_sheet 首秒钉子对齐 · 交付给 audio_plan）：**
- 无 VO · 无字幕 · 无 BGM
- 环境音 ambient（-24dB · AC 底噪 + 远处交通）+ tick sfx 0.3s（-15dB · 手悬键盘不落拍点）
- 首秒无字幕故意留白 = 让"这就是我上周做的"1s 认领感成立

- **M1 主 B-roll**：**Pexels 白天办公桌 3800-4200K + 键盘 + 摄像头亮红点 + 空笔记本**
  - 现有 assets/broll/raw/ 全部是 dusk/night 口径（`office_desk_dusk` × 3 · `smartphone_screen_notification_night` × 2 · `city_window_dusk` × 2）· **不匹配 D04 白天办公场景**
  - **需新拉 Pexels 关键词**：`daylight office desk overhead` + `webcam recording setup` + `blank notebook desk` + `hand hovering keyboard morning` · 目标 4-6 条候选 · 优先"俯拍 + 摄像头红点可见"的一条
  - 若无摄像头红点素材，用 drawtext + drawbox 小红点覆盖右上角（真机风格 · 不做发光特效）
- **M2 屏录**：**QuickTime 真机屏录 AI 对话框**
  - 本机 macOS 或 iPhone 录 ChatGPT/DeepSeek/豆包 AI 对话框（工具中立 · 建议用 ChatGPT 界面识别度高）
  - 保留 iOS/macOS 状态栏 + AI 对话框原生 UI + 光标闪
  - 打字节奏 30ms/字 · 真人打字（14 声真实拟音 · -8dB）· 敲回车 tick sfx
- **M3 屏录 + SVG 覆盖**：
  - AI 输出 3 条固定文案（可复现 · 家居收纳版）：「如何做好家居收纳」「浅谈家居收纳的重要性」「5 个家居收纳误区」
  - accent_red 3 次红叉 whoosh 从右上横划打掉（每次 0.3s · **静态 SVG + CSS transition，禁 GSAP 弹跳**）
  - display 140pt 白字入「打"帮我想 10 个" · AI 全给"如何做好"」· 屏中央 · 描边 2px canvas_office_dark 深色描边
- **不用**：
  - 3D 渲染的摄像头 / AI 生成的办公桌 / HTML 仿真的 AI 对话框
  - AI 工具 logo（ChatGPT/DeepSeek/豆包）
  - 亮白 `#ffffff` 底 · Dracula 紫粉青

### 场景 B · 白天办公群体锚（M4，3-8s）

- 主 B-roll：**主角背影 + 摄像头亮 + 空笔记本 3800-4200K**
- Pexels 素材需新拉（同 M1 白天办公库 · 可复用不同镜头）
- 数据大字：headline 96pt 白字「9 成中腰部创作者遇到选题问题」+ caption 24pt 来源「引 知乎专栏 A 级」（fact_check #P0-1 A 级）
- **不用**：
  - D03 92% 群体锚 display 160pt 全屏灰底版式（**D04 白天办公实景叠层显式区分**）
  - 「必上热门」「一键爆款」等承诺
  - 泛化"打工人焦虑"（D04 群体是中腰部创作者 · 非打工人）

### 场景 C · 分屏爆款对比（M5，8-15s）

**合规铁律：** 40w 赞截图必须马赛克遮挡真实同行头像/账号名（见 vA/vB 合规自查 · fact_check #P0-1）

- 左半屏：**同行「40w 赞」爆款截图**（马赛克遮挡个人信息 · 只留赞数 + 分类）
- 右半屏：**「我 800 赞」自己截图**（同样马赛克 · 单位显式硬约束"赞"字必须出现）
- 中间 2px ink_light `#f5f5f0` 白分割线
- 大字类比锚居中偏下：「40w 赞 vs 我 800 赞」（drawtext + 苹方 headline 96pt 白字）· 副标 caption 32pt「翻竞品 30 分钟存 8 张截图 · 一条不想拍」
- 静态分屏 · 无 GSAP 动画 · 只用 CSS transition 或 ffmpeg drawtext 淡入
- **不用**：三分屏以上 · 图之间加装饰性边框 · 大字叠图中间遮挡视觉焦点 · 打真实同行 logo

### 场景 D · 3 段烂 prompt 反面（M6，15-25s）· 反面正解快切

- 屏录 3 段快切（每段约 3s）· 3 个 AI 对话框实录：
  - ①「帮我想 10 个」→ 通用套话
  - ②「加平台词」→ 同行都在拍模板
  - ③ 让 AI 抄爆款 → 换个数字的同质品
- accent_red `#e53935` 2px 描边框（**只在关键错误行不全屏描边**）
- 每段大字批注 caption 28pt「跳过身份卡」「跳过账号定位」「跳过粉丝痛点」· accent_red 描边强调「跳过 X」
- hit sfx 打点 3 次
- **不用**：全屏描边（视觉负担重）· 装饰性图标 · emoji

### 场景 E · 4 段 prompt 演示核心（M7，25-40s）· 全片核心 · 收藏动机第一位

**关键动作路径：**
1. QuickTime 屏录本机 macOS 或手机开 AI 对话框（ChatGPT/DeepSeek/豆包 · 中立 · 建议用 ChatGPT 识别度高）
2. 打开 AI → **粘贴完整 4 段 prompt（家居收纳版 · JetBrains Mono 32-40pt）**
3. AI 输出 10 条候选（表格样式：标题/场景/钩子/成本/差异化 · 每条 1s 打字机式出现）
4. 底部标注**「可长按暂停截屏抄」**（caption 28pt · **收藏动机点明示**）

**SVG 打点策略：**
- 不做复杂 GSAP 动画
- 只做**静态 SVG 高亮 badge + 淡入淡出**（0.5s 淡入 · 停 3-4s · 淡出 0.5s）
- **4 段 badge**：「身份卡 · 账号定位 · 粉丝痛点 · 输出约束」
- 每段 badge 用 accent_soft `#ffc857` 淡黄底 + 黑字 headline 88pt 段名 · 禁 Dracula 霓虹 · 禁装饰性边框
- 段间 whoosh sfx 4 次（-12dB）过渡

### 场景 F · 5 判据表格 · "10 里 8"（M8，40-48s）· 收藏动机第二位

- canvas_office_dark `#1a1a1a` 灰底
- 表格结构：横行 = 10 条候选选题左列 · 纵列 = 5 判据（具体场景 / 前 3s 钩子 / 差异化 / 可拍性 / 粉丝相关）
- **accent_green `#4caf50` sober 静态打勾 8 个**（**禁 GSAP 动画** · 直接显示即可）
- accent_red `#e53935` 静态打叉 2 个（同 sober 口径）
- 大结论 headline 96pt 白字「10 里 8 · 能用」 + caption 28pt「5 判据 · 通过 4 条即能用」
- hit sfx 打点（"10 里 8"落地拍点）
- **不用**：打勾动画 · 表格 3D 效果 · 花色底 · 表格外加装饰边框 · 大结论用彩色数字

### 场景 G · 反教程价值锚 + CTA（M9-M10，48-58s）

- **M9 全屏**：canvas_office_dark `#1a1a1a` + display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」（drawtext + 苹方权重 900）
- 每行 6-8 字 · 居中对齐 · 无 B-roll 干扰 · 无 emoji · 无花字
- ambient sfx 落底 + hit sfx 收尾
- **M10 CTA**：canvas_office_dark 灰底 + headline 88pt 白字「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ caption 28pt 底部小字「同行互助 · 不推服务」
- 无箭头 emoji · 无「点这里」引导 · 无弹幕特效

## 5. Fail 检查（避免"承诺 ≠ 兑现"事故 · SYSTEM §3.1c）

| 检查项 | 承诺 | 兑现方式 |
|--------|------|----------|
| chaos 用真实素材 | form_competition 方案 A 承诺 | Pexels 白天办公 3800-4200K 需新拉 · QuickTime 真机屏录 · 严禁 AI 生图 |
| 真机屏录 AI 对话框 | form_competition 承诺"真机屏录 chaos-punch-reveal + 4 段 prompt 演示" | QuickTime + 本机 macOS 或 iPhone · 不用 HTML 模拟 · 保留 iOS/macOS 状态栏 · 不打 AI 工具 logo |
| SVG 打点非 GSAP | 方案 A 声明"少量 SVG accent_soft badge + accent_green 打勾" | 简单 SVG + CSS transition 或 drawtext 淡入淡出 · 不引 GSAP 库 · 打勾**静态** |
| 分屏静图 | 方案 A 声明"静态分屏 40w vs 800" | 真机截图 · 静态图 · 无动效 · 马赛克遮挡个人信息 |
| ≥3 种观感 | rules.min_distinct_formats: 3 | 6 种形式 ID · 已达标 |
| 单场景占比 <40% | rules.single_scene_max: 40% | M7 屏录 15s = 26% · 已达标 |
| 不打竞品 logo | fact_check.md 红区 | AI 工具（ChatGPT/DeepSeek/豆包）UI 原生色允许但**禁打 logo** · 同行爆款截图必须马赛克遮挡真实头像/账号名 |
| 数据锚同帧口径 | fact_check.md 黄区 | vA/vB v2 严格保留"10 里 8"= "5 判据 · 通过 4 条即能用" 同帧显式（M8 表格 caption 28pt 明示） |
| 单位显式 | vB v2 verdict 硬约束 | M5 分屏字幕"40w 赞 vs 我 800 赞"（**赞字必须出现** · 避 800 粉起号歧义） |
| 4 条原话进片 | 编剧硬门禁 pass | vA/vB v2 已跨过（vB v2 M4/M5/M6 末尾 + M4 转述共 4 条 · vA M4 群体锚 1 条转述 · vA 主推靠场景锚 · 若走 vB v2 备胎自动带 4 条原话）· **vA 主推兜底约束**：若拍摄期 vA 走确认，M4 或 M9 必须至少补 1 条 topic_brief 原话直引（#2/#3/#5 任选 · 引号符号 + mono 32pt · 与旁白 body 42pt 区分），否则**强制切 vB v2 备胎** |
| BGM off | feedback_dense-vo-no-bgm-default | 密 VO 演示型 · BGM off · sfx 4 类必覆盖 |
| VO 覆盖 ≥85% | feedback_dense-vo-no-dead-air | 3-58s VO 全程覆盖 · 段间衔接词最大 1.5s 空白 |
| M8 表格可读性 | design_language 字号约束 | 表头 headline 42pt · 单元格 body 32pt · 10 条候选 × 5 判据在 1080×1920 竖屏可读 |
| M10 CTA 承诺兑现 | skin.landing_intent 硬约束 | 私信 SLA 24h 内回 · 走本人 IP 私信而非群/星球/客服 · 避免评论区反噬 |

## 6. 数据杠杆声明（每高级视觉服务哪个指标）

| 镜 | 数据杠杆（服务哪一项指标） | 说明 |
|----|-----------------------------|------|
| M1-M3 | `completion_3s`（3s 停划）| 屏录 chaos-punch-reveal 三拍 · 同行"我上周就打过一模一样的 prompt"1s 认领 · **差异化视觉资产** |
| M4 | `completion_rate` + 认领 | 9 成群体锚释放"不是我不行" · 白天办公实景叠层与 D03 全屏灰底显式区分 |
| M5 | `completion_rate` + 情感冲击 | 40w vs 800 反爆款抱怨 · 单位显式硬约束"赞"字 · 视觉负担控在分屏 50/50 |
| M6 | `completion_rate` + 理解 | 反面正解激发"那我该怎么办"期待反转 · 3 段屏录快切保 A 级证据 |
| M7 | `completion_rate` + **收藏率** | 真机屏录 + 4 段 badge SVG 打点 + 全屏可截屏 · 收藏动机第一位（呼应小红书 P4-P7 完整 prompt） |
| M8 | `completion_rate` + **收藏率** + 可测承诺 | 5 判据表格 + accent_green 静态打勾 · 收藏动机第二位（P0-4 承诺兑现证明） |
| M9 | 评论率 | 反教程价值锚 · 同事口吻替代博主感 · 差异化承诺 |
| M10 | 评论率 + 私信率 | CTA 两选项开放式提问 + 具体承诺「5 条选题」低成本高确定回复 |

## 7. 交付给下一环节

- **动画导演**（motion_storyboard.md · 单跑不双评）：本条 9 段镜头的逐秒 9 字段分镜（时间/旁白/内容类型/画面主体/动画动作/镜头运动/屏幕文字/素材需求/推荐实现方式/设计目的）
- **动效技术导演**（motion_tech_plan.md）：本条 **SKIP**——未使用 Web 3D/GSAP/复杂动效，只用 SVG 覆盖层（accent_soft badge · accent_red 红叉 · accent_green 打勾）+ drawtext display 大字 + drawbox 白闪 + Pexels B-roll + 真机屏录；需登记 SKIP 理由（同 D03）
- **导演/摄像**（storyboard.yaml）：本条 9 段镜头的画面清单（Pexels 白天办公库需新拉 4-6 条候选 · QuickTime 屏录 4 场次 · 分屏 40w vs 800 真机截图 · 表格 SVG）
- **声音设计师**（audio_plan.yaml）：BGM off · sfx 4 类必覆盖（whoosh 4 次 M3 红叉 + M7 段切换 · tick 3 次 M1/M4/M10 · hit 5-8 次 M3/M5/M6×3/M8/M9/M10 · ambient 全片氛围铺底）· TTS 时长前置估算（`tts-estimate-duration-pre-synth` 硬约束）

## 8. Audience-First 自查三问（form_strategy 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ M1-M3 屏录 chaos-punch-reveal 三拍（"我上周就打过一模一样的 prompt"）+ M4 9 成群体锚（"不是我不行"）+ M5 40w vs 800 反爆款抱怨（"我也这样"）+ M9 反教程价值锚（"同事口吻·不推服务"）· 四层情感锚一路铺垫 · **差异化视觉资产**（屏录反差首镜同行没做过） |
| 画面**观赏性**够吗？ | ✅ 9 段镜头 · 6 种形式 ID · 每 3-8s 有明确视觉变化 · 单场景占比最大 M7 26% < 40% · sfx 4 类事件音 10+ 次撑节奏 |
| 内容**真材实料**吗？ | ✅ M7 4 段 prompt 屏录 + 全屏可截图 + M8 5 判据 accent_green 静态打勾 + M9 反教程价值锚 + M10 具体承诺"5 条选题" · **收藏 + 评论 + 私信三重动机** · 呼应小红书 P4-P7 完整 prompt 可长按保存 |
