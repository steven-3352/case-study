# 表现形式竞争 · form_competition · W28D04 AI 帮想视频选题

> 工种：形式策略官 + 平台原生策划 + 纪录片导演 + 动效分镜师
> 位置：`design/form_competition.md`
> 状态：`draft_self_generated` · 2026-07-05
> 依赖：`insights/` 已 pass · `retention_beat_sheet.md`（9 段 55-58s + 7 页轮播）· `scripts/vA.md`（**抖音主推 · chaos-punch-reveal 型**）· `scripts/vB.md` v2（**A/B 备胎 · 双评 pass**）· `design/openmontage_brief.md`（decision=blocked_infrastructure）· `design/design_language.md`（已产出 · 10 色板 · 12 组件）· `design/cover_brief.md`（已产出）

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` **§4.2 最新候选清单**（2026-07-04 版含 OpenMontage/Grok video/GPT-image-2/Remotion/HyperFrames）· §2.4b · §3.1e · §4.2 五维打分 · §3.2 留存铁律 · §3.4 拒稿反例（catalog 拼盘）
- [x] **template refs**：`templates/design/form_competition.md`（§3 候选池完整性自查 + 跨家族强制）· `templates/design/openmontage_brief.md` · `templates/design/design_language.md`
- [x] **memory refs**：
  - `feedback_no-default-tech-stack`（触发词打断）
  - `feedback_pre-node-checklist`
  - `feedback_anti-ai-visual`（禁 AI 味）
  - `feedback_no-neon-palette`（禁 Dracula 紫粉青）
  - `feedback_contrast-hook-3s`（chaos-punch-reveal 屏录三拍是本条差异化资产）
  - `feedback_pipeline-burn-subs`（字幕烧片流程）
  - `feedback_pipeline-full-platform-output`（三平台字号差 42/50/42）
- [x] **姊妹条 refs**：
  - `publish/2026-W28/D02-*/design/form_competition.md` 回炉版实读
  - `publish/2026-W28/D03-*/design/form_competition.md` 实读（**学** 3 方案跨家族结构 · **学** 五维打分逻辑 · **不复用** 深夜 Pexels 素材清单 · **不复用** 92% 群体锚 display 160pt 全屏版式）
  - 本条已产出的 `openmontage_brief.md`（decision=blocked_infrastructure）实读
- [x] **能力清单 refs**：
  - `ls integrations/` = openmontage/（仅 README + env.example + patches + scripts · 未跑通过）
  - `ls pipeline/` 全清单已实查（p001/p002/p004_video/p005/p006/p007 + tts + lib）
  - `ls integrations/openmontage/` 已实查（sibling repo 需外部 checkout）
  - `ls assets/broll/raw/` 已实查（现有素材全部是傍晚/深夜口径：`city_window_dusk` × 2 · `office_desk_dusk` × 3 · `smartphone_notification_night` × 2 · `shop_owner_phone` × 2 · **D04 需要拉白天办公桌 3800-4200K 3800-4200K 新素材**）
  - `pipeline/p004_video/lib` config-driven 架构（W28D01-D06 保 golden reference · D03 修的 4 个 bug 已入 lib · 本条走 pipeline_config.yaml + run_pipeline.py --step all）

**触发词自查（本次开工前主动检查）：**
- [x] 未出现"就走 P004 吧" / "就走 P001 吧" 念头
- [x] 未出现"OpenMontage 太重了不适合"这类未跑 brief 的排除话
- [x] 未出现"D03 走通了直接抄一遍"这类跨条克隆念头
- [x] 3 方案跨家族强制满足

## 3. 候选池完整性自查

### 3.1 候选池来源确认

```yaml
system_ref_version_read: 2026-07-04
candidates_considered:
  native_pipeline:
    - P001 (render_p001.py + gen_evidence.py 高保真仿真)
    - P002 (报纸风轮播 · 与 skin.tone_direction 同行说话不匹配，早排除)
    - P004 (HTML+GSAP · 反 AI 味风险 · memory feedback_anti-ai-visual 已警告 · P004 lib 用于合成合流但不用居中大字 GSAP 首镜)
    - P005/P006/P007 (带货/漫画/漫画图文 · 与形态不匹配 · 早排除)
    - fetch_broll.py Pexels 真实素材 (**需拉白天办公桌 3800-4200K + 摄像头 + 空笔记本 新素材**，现有 dusk/night 库不能覆盖 D04)
    - QuickTime 真机屏录 AI 对话框 (原生能力 · **本条首镜核心手法**)
  integrations:
    - OpenMontage (documentary montage / screen demo / animated explainer / cinematic)
    - Grok video (integrations/openmontage/openmontage.env.example)
    - GPT-image-2 (中转已配 · 本条无需报纸风)
    - MiniMax TTS speech-2.8-turbo (已在 D02/D03 audio_plan 使用)
  raw_materials:
    - 真实拍摄白天办公桌场景 (用户当前无自拍条件 · W28 全周口径)
    - 真人出镜 (Q8 演示型默认不出镜；本条 skin=中腰部创作者·同行说话，出镜与"沉稳同事口吻"匹配，但用户无拍摄条件)
    - Pexels CC0 商用真实拍摄 (已可用 · 需拉白天办公桌 3800-4200K + 摄像头 + 空笔记本 新素材)
    - SVG/CSS 覆盖层 (静态代码 · accent_soft 4 段 badge · accent_red 3 次红叉 · accent_green 表格打勾)
    - drawtext/drawbox 大字快闪 (ffmpeg 原生 · display 140pt 白字入)
```

### 3.2 openmontage_brief 判断（已跑）

```yaml
openmontage_brief_status: pass
openmontage_decision: blocked_infrastructure
openmontage_blocked_reason: |
  1. sibling repo 未 checkout 在本机（文档路径 /Users/bubu/... 与当前用户 wmzuo 不匹配）
  2. 项目内无成功 OpenMontage 案例参考（W28D01 disabled_by_choice · W28D02/D03 blocked_infrastructure）
  3. W28 曝光优先·日更节奏承担不起首次跑通的交付风险
  4. 与 skin.tone_direction「同行说话·不 preach·不 sell 秘籍」不匹配（OpenMontage animated explainer 有教程感风险 · 同行"AI 一键出爆款"话术打脸靠原生屏录同频代入，OpenMontage 电影感反而稀释）
  5. 收藏率是 D04 核心 KPI（25-40s 4 段 prompt 演示 + 40-48s 5 判据表格 + 小红书 P4-P7 完整 prompt 可截图带走），视频合成不利于逐帧截图；原生 P001 轮播优于合成
  6. 屏录 chaos-punch-reveal 三拍是 D04 唯一同行没做的首镜手法，OpenMontage documentary 电影感反而抹平这个差异化视觉资产
openmontage_review_trigger: 见 openmontage_brief.md decision_review_trigger 字段
```

## 4. 三个候选表现方案（**跨家族强制满足**）

### 方案 A · 原生 P001 混合 · 屏录 chaos-punch-reveal 首镜型（family=`pipeline`）

- **名称：** QuickTime 真机屏录 AI 对话框 chaos-punch-reveal 三拍 + Pexels 白天办公 3800-4200K B-roll + SVG 覆盖 accent_soft 4 段 badge / accent_red 3 次红叉 / accent_green 打勾 + drawtext display 大字 + drawbox 白闪快切 + 分屏静图（马赛克遮挡）+ ffmpeg 合成
- **实现家族：** `pipeline`
- **核心画面机制（对应 vA 主推 10 段镜头）：**
  - **0-1s（M1 · chaos）**：Pexels 白天办公桌俯拍 + 键盘 + 摄像头亮红点 + 手悬键盘不落（3800-4200K 白天光 · 无字幕 · 环境音 + tick sfx 0.3s）
  - **1-1.6s（M2 · punch）**：屏幕特写切入 · AI 对话框光标闪 · 手落键盘 · 打字「帮我想 10 个抖音选题」14 字（真人打字节奏 30ms/字 · 拟音）· 回车 tick sfx · **保留 iOS/macOS 状态栏** · 不打 ChatGPT/DeepSeek/豆包 logo
  - **1.6-3s（M3 · reveal）**：AI 输出 3 条「如何做好家居收纳 / 浅谈 XX 的重要性 / 5 个 XX 误区」→ 3 次 accent_red 红叉 whoosh 打掉 → display 140pt 白字入「打"帮我想 10 个" · AI 全给"如何做好"」屏中央
  - **3-8s（M4 · 群体锚）**：Pexels 白天办公 B-roll（主角背影 + 摄像头亮 + 空笔记本）+ headline 96pt 白字「9 成中腰部创作者遇到选题问题」+ caption 24pt 来源「引 知乎专栏 A 级」
  - **8-15s（M5 · 反爆款抱怨）**：分屏 50/50 · 左「同行 40w 赞」右「我 800 赞」马赛克遮挡个人信息 · 中间 2px 白分割线 · headline 96pt 白字类比锚居中偏下「40w 赞 vs 我 800 赞」
  - **15-25s（M6 · 3 段反例快切）**：3 个 AI 对话框实录屏录 · accent_red 2px 描边强调反例 · 每段 caption 28pt 批注「跳过身份卡」「跳过账号定位」「跳过粉丝痛点」· hit sfx 打点 3 次
  - **25-40s（M7 · 4 段 prompt 演示核心 · 收藏动机段）**：QuickTime 真机屏录 · 打开 AI → 粘贴 4 段 prompt（家居收纳版）→ AI 表格输出 10 条 · **accent_soft `#ffc857` 淡黄底 4 段 badge SVG 覆盖**（身份卡/账号定位/粉丝痛点/输出约束）· 每段淡入 0.5s + 停 3-4s · 底部 caption 28pt「可长按暂停截屏抄」
  - **40-48s（M8 · 5 判据表格）**：canvas_office_dark `#1a1a1a` 灰底 · 表格结构 10 条候选 × 5 判据 · **accent_green `#4caf50` 静态打勾**（8 绿勾）+ accent_red 2 打叉 · headline 96pt 白字「10 里 8 · 能用」+ caption 28pt「5 判据 · 通过 4 条即能用」
  - **48-54s（M9 · 价值锚全屏）**：全屏 canvas_office_dark · display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」· 无 B-roll · 沉稳 VO · ambient sfx 落底 + hit sfx 收尾
  - **54-58s（M10 · CTA）**：canvas_office_dark 灰底 + headline 88pt 白字「私信「你在做什么账号 · 想拍什么方向」→ 我给你 5 条选题」+ caption 28pt 底部小字「同行互助 · 不推服务」
- **服务指标：**
  - **completion_3s**：屏录 chaos-punch-reveal 三拍 → 同行"我上周就打过一模一样的 prompt"1s 认领（比 D02 打工人下班 + D03 深夜台灯共情锚更锐利，因为**动作可复现**）
  - **completion_rate**：9 段形式切换 + 每 3-8s 变化点 + 25-40s prompt 演示动作性变化最丰富
  - **收藏率**：小红书 P4-P7 完整 4 段 prompt CSS 静态 → 可截图带走（保守估 save_rate ≥6%）· 抖音 M7 底部 caption「可长按暂停截屏抄」明示动机
  - **评论率**：CTA「你在做什么账号 · 想拍什么方向」两选项开放式提问 · 具体可答
- **优点：**
  - **与 SYSTEM Q9 chaos_must_be_real_footage 100% 一致**（Pexels 白天办公需拉 + QuickTime 真机屏录 = 真实素材）
  - **屏录 chaos-punch-reveal 是同行没做的首镜手法**（core_message P0-2 反面正解前置的差异化视觉资产）
  - 与 skin.tone_direction「同行说话 · 不 preach · 不 sell 秘籍」完全匹配（屏录 UI 原生色 · 无教程感包装）
  - `.env` 已配 MiniMax TTS 和 GPT-image-2 · 无阻塞
  - `pipeline/p004_video/lib` config-driven 架构已成熟（D03 修的 4 个 bug 已入 lib · W28D04 直接走 pipeline_config.yaml + run_pipeline.py --step all）
  - 制作成本可控（1-2 天完成 · 复用 D03 pipeline 能力但不复用画面）
  - **姊妹条 D03 已跑通同样架构**，本条复用能力（不复用画面），风险最低
- **风险：**
  - **Pexels 白天办公桌 + 摄像头亮 + 空笔记本**素材需新拉（现有库全是 dusk/night · fetch_broll.py 需跑 3-4 条候选拉取）
  - 屏录真机 AI 对话框需要准备本地帐号 + 4 段 prompt 演示样本（家居收纳版 · 1 小时准备）
  - 分屏 40w 赞 vs 800 赞截图需真机（不打 logo · 只用赞数 + 马赛克遮挡个人信息 · 见 vA/vB 合规自查）
- **制作成本：** ★★ 中（1-2 天）

### 方案 B · OpenMontage 混合（family=`integrations`）

- **名称：** OpenMontage documentary montage 前段（电影感首镜） + screen demo 中段（豆包/AI 演出） + cinematic 结尾（价值锚情感落点）
- **实现家族：** `integrations`
- **核心画面机制：**
  - 0-6s：OpenMontage documentary montage 电影感钉子（Grok video 生成或 Pexels 素材由 OpenMontage 剪辑）
  - 6-32s：OpenMontage screen demo pipeline（AI 对话框演出 · 比 QuickTime 屏录更连续）
  - 32-58s：OpenMontage cinematic 情感落点 + 反教程价值锚
- **首屏：** OpenMontage 剪辑电影感开场（3 秒沉默钉子会更连贯）
- **中段：** screen demo 电影感演出（比 QuickTime 屏录更连续）
- **CTA：** cinematic 收尾 + 大字
- **服务指标：**
  - completion_3s：**理论上电影感钉子 > Pexels 拼接**（+3-5%）· 但**牺牲屏录反差同频代入**（vA 首镜差异化视觉资产被稀释 · 净效果不明）
  - completion_rate：连续镜头感 > 分段拼接
  - 收藏：小红书视频版可能有帮助，**但轮播 P4-P7 仍需原生 P001**（合成视频不利于 4 段 prompt 逐帧截图带走 · 与 D03 口径一致）
  - 评论：情感感染力更强
- **优点：**
  - 电影感能拉高首镜 completion_3s（理论）
  - 连续镜头比拼接更专业
  - 若成功可复用到 W29 破圈实验
- **风险：**
  - **🔴 基础设施阻塞（`blocked_infrastructure`）**：sibling repo 未 checkout · Grok video 无成功案例参考 · export_request → collect_output 跨仓库首跑
  - 项目内无 OpenMontage 成功案例（W28D01/D02/D03 均未跑通）
  - W28 日更节奏承担不起首跑失败
  - **与 skin.tone_direction「同行说话 · 不 preach」不匹配**（电影感/animated explainer 有过度倾向，会拉高"我教你"感 · 同行"AI 一键出爆款"话术打脸靠原生屏录同频代入，被 OpenMontage 稀释）
  - **稀释屏录 chaos-punch-reveal 差异化视觉资产**（本条唯一同行没做的首镜手法，被 documentary montage 覆盖等于自废武功）
  - **与 D04 收藏率 KPI 冲突**：4 段 prompt 走轮播 P4-P7 需原生静态页 · OpenMontage 视频合成路线无法覆盖
- **制作成本：** ★★★★ 高（若跑通 3-5 天含 sibling repo 搭建 + 首跑调优）
- **决策：** 因 `openmontage_brief.decision = blocked_infrastructure` **本方案排除**

### 方案 C · 纯真人拍摄（family=`raw`）

- **名称：** 全片真人拍摄 + 剪映后期
- **实现家族：** `raw`
- **核心画面机制：**
  - 0-3s：真实白天办公桌 + 摄像头亮 + 空笔记本 + 手悬键盘（真人手部 · 不出脸）
  - 3-8s：真人对镜（背影或侧影 · 不露脸）+ 白天办公场景
  - 8-40s：真机操作 AI 对话框（真人手 + 真实屏幕 + 真实旁白）
  - 40-58s：真人手写便签 CTA + 桌面场景
- **首屏：** 真实白天办公桌 + 真人手部（不出脸）+ 摄像头红点
- **中段：** 真人操作 AI 4 段 prompt 全流程 + 真机 5 判据表格演示
- **CTA：** 真人手写便签「同行互助 · 私信喂选题」
- **服务指标：**
  - 3s 停划：真实拍摄可信度最高（A 级证据 > Pexels B 级 > OpenMontage 合成 C 级）
  - 完播：真人动作连续性最强
  - 收藏：真实操作可复制性最强
  - 评论：真实感激发共鸣 · vA 场景剧型天然适配真人拍摄
- **优点：**
  - 完全真实（A 级证据 > Pexels B 级 > OpenMontage 合成 C 级）
  - 与 skin.persona_anchor「做自媒体引擎的同行」契合度最高
  - 屏录 chaos-punch-reveal 三拍 + 真人手落键盘 + 真机 AI 对话框 = A 级证据链完整
- **风险：**
  - **🔴 素材缺失阻塞**：**用户当前无白天办公桌自拍条件**（W28 全周承继口径——本项目 Phase 0-1 无自拍资源）
  - 无法在无用户素材前提下执行
- **制作成本：** ★★★ 中（若用户能拍 · 1 天）
- **决策：** 因**素材缺失**（W28 全周承继口径）**本方案排除**

## 跨家族满足自查

- [x] 3 方案覆盖 3 个不同家族（`pipeline` + `integrations` + `raw`）✅
- [x] 3 方案不是同家族变体（不是"P001 A/B/C"或"P004 A/B/C"）
- [x] 方案 B 因 `integrations` 家族基础设施 `blocked_infrastructure` 排除，理由明确
- [x] 方案 C 因 `raw` 家族素材缺失排除，理由明确
- [x] 方案 A 是可执行的唯一候选，不因"缩水"而是"客观唯一"

## 5. 选择与不选择

### 推荐方案

- **推荐：** 方案 A · 原生 P001 混合 · **屏录 chaos-punch-reveal 首镜型**（QuickTime 真机屏录 + Pexels 白天办公 3800-4200K + SVG accent_soft 4 段 badge + accent_red 红叉 + accent_green 打勾 + drawtext 大字 + drawbox 白闪 + 分屏静图 + ffmpeg）
- **对应 chosen script：**
  - **抖音主推**：`scripts/vA.md`（chaos-punch-reveal 型）
  - **抖音 A/B 备胎**：`scripts/vB.md` v2（数字精简+原话情感 · 双评 avg 90.5 pass · 若 vA 3s 完播 <52% 换 vB v2 试第二镜头）
  - **小红书 P1 封面 + P4-P7 完整 prompt**：从 vA reveal 帧取 · 或独立设计共情锚（见 cover_brief.md）
  - **视频号 65-72s 加长版**：v0 场景共情 + vB v2 数字锚 + 原话情绪段材料源
- **为什么最能服务北极星：**
  - completion_3s：**屏录 chaos-punch-reveal 三拍是同行没做的首镜手法**（M1 chaos 白天办公 → M2 punch 打字 14 字 → M3 reveal AI 输出被红叉打掉 + display 大字入），同行"我上周就打过一模一样的 prompt"1s 认领 · 比 D02/D03 场景锚更锐利（因为动作可复现）
  - completion_rate：25-40s 屏录 4 段 prompt 大字滑入 + SVG accent_soft 4 段 badge 打点 → 中段动作性变化最丰富（15s · 26% 占比）
  - 收藏：小红书 P4-P7 完整 4 段 prompt CSS 静态 → 可截图带走（保守估 save_rate ≥6%）· 抖音 M7 底部 caption「可长按暂停截屏抄」明示动机
  - 评论：CTA「你在做什么账号 · 想拍什么方向」两选项开放式提问 + 具体承诺「我给你 5 条选题」→ 低成本高确定回复
- **与最近 5 条最大差异：**
  - 与 W27D01-D06 老板圈 catalog 完全不同（audience 池切换到中腰部创作者·同行说话 · 视觉从"agent_grid 卡片"切换到"屏录反差 + 白天办公 + 4 段 prompt badge + 5 判据表格"）
  - 与 W28D01 老板圈方法论方向不同（D01 老板圈 · D04 中腰部创作者）
  - 与 W28D02 打工人周报方向不同（D02 打工人下班「18:55」 · D04 白天办公「摄像头亮红点」；D02 无屏录反差首镜 · D04 chaos-punch-reveal 是首镜差异化视觉资产）
  - 与 W28D03 深夜自习房方向不同（D03 深夜 23:12 台灯 3000-3500K · **D04 白天办公桌 3800-4200K 摄像头红点**；D03 92% 群体锚 display 160pt 全屏 · **D04 9 成群体锚 headline 96pt 白字实景叠层**；D03 无屏录反差首镜 · **D04 chaos-punch-reveal 三拍是本条唯一同行没做的首镜手法**）

### 不选其他方案原因

| 方案 | 不选原因 | 是否可作为后续备选 |
|------|----------|--------------------|
| A | 已选 | — |
| B | OpenMontage sibling repo 基础设施未 checkout + 项目内无成功案例 + W28 日更承担不起首跑风险 + 与 skin.tone_direction「同行说话」不匹配 + 稀释 chaos-punch-reveal 差异化视觉资产 + 与 D04 收藏率 KPI 冲突 | ✅ **待 sibling repo 到位 + 首个成功案例 + D04 首轮 3s 完播 <50%（同行反差首镜未达预期）后重新评估**（见 openmontage_brief.decision_review_trigger） |
| C | 用户当前无白天办公桌自拍条件（W28 全周一致） | ✅ **待用户有拍摄条件后可切换 · 若走 vA 主推 + 用户能拍第一人称手部/背影/办公桌，可优先启用**（A 级证据 > B 级 Pexels 拼接） |

## 6. 禁止从旧 storyboard 开始改

- [x] 本条不是复制上一条 storyboard 后改字（D03 深夜 23:12 台灯自习房，本条**白天办公桌 摄像头亮**；D03 92% 群体锚全屏灰底，本条 9 成群体锚实景叠层）
- [x] 本条不是旧模板换标题、换颜色、换字幕
- [x] 复用 P001 + Pexels + QuickTime 屏录 + pipeline/p004_video/lib 时明确声明"复用能力，不复用画面"（见 visual_originality_gate.md 下节点）
- [x] 分镜从本条视觉命题「屏录 chaos-punch-reveal → 白天办公群体锚 → 分屏爆款对比 → 3 段反例快切 → 4 段 prompt 演示 → 5 判据表格 → 反教程价值锚 → CTA」生成

## 7. 进入 form_strategy 的条件

- [x] 至少 3 个候选方案完整（本次严格 3 个 · 跨 3 家族）
- [x] 3 个方案覆盖 ≥2 个不同家族（本次 3 家族全覆盖）
- [x] 有明确推荐方案（方案 A）
- [x] 写清楚不选其他方案原因（B 基础设施 blocked · C 素材缺失）
- [x] 写清楚与最近 5 条的差异（W27 老板圈 vs D02 打工人 vs D03 学英语党 vs **D04 中腰部创作者·屏录反差首镜**）
- [x] 明确禁止旧 storyboard 改字
- [x] **`openmontage_brief.md` 已跑，decision 明确（blocked_infrastructure）**
- [x] **候选池完整性自查 §3 五条全过**

`status: pass · decision: proceed_to_form_strategy`

## 五维打分（对照 SYSTEM §4.2）

| 维度 | 权重 | 方案 A | 方案 B | 方案 C |
|------|------|--------|--------|--------|
| 停划力（首镜 ×2） | ×2 | 10 → 20（屏录 chaos-punch-reveal 是差异化视觉资产 · 同行没做过）| 8 → 16（电影感稀释屏录反差 · 净效果不明）| 10 → 20 |
| 看懂速度 | ×2 | 9 → 18 | 7 → 14 | 8 → 16 |
| 节奏变化 | ×1 | 9 | 9 | 7 |
| 互动钩子 | ×1 | 9（4 段 prompt badge + 5 判据表格 + CTA 两选项）| 7 | 9 |
| 信任/证据 | ×1 | 9（屏录真机 UI 原生色 · A 级证据 · 4 条 topic_brief 原话直引）| 5 | 10 |
| 交付风险 | ×0.5 | 8 → 4（pipeline/p004_video/lib 已成熟 · 白天办公 B-roll 需新拉但流程标准）| **1 → 0.5**（blocked） | **1 → 0.5**（blocked） |
| **合计 / 60** | | **69** | **51.5**（+blocked 惩罚 = 25.75 实际不可选）| **62.5**（+blocked 惩罚 = 31.25 实际不可选） |

**方案 A 胜出，且是唯一可执行方案。**

（方案 A 比 D03 方案 A 高 3 分：D04「停划力」+ 1 因屏录 chaos-punch-reveal 是差异化视觉资产 · 「互动钩子」+ 0.5 因 4 段 badge + 5 判据表格双动机 · 「信任/证据」+ 1 因 4 条 topic_brief 原话直引跨过编剧硬门禁。）

## 决策总结

- **决策：** 方案 A 原生 P001 混合 · **屏录 chaos-punch-reveal 首镜型**
- **家族：** pipeline
- **不启用 OpenMontage 的原因：** blocked_infrastructure（非 disabled_by_choice · 且屏录反差是本条差异化视觉资产不能被 documentary montage 稀释）
- **不用真人拍摄的原因：** 素材缺失（W28 全周口径）
- **候选池预先缩水的教训：** 已入 memory `feedback_no-default-tech-stack` + template `form_competition.md` §3
- **未来 revisit 条件：** 见 openmontage_brief.md `decision_review_trigger`

## Audience-First 自查三问（form_competition 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ 方案 A 屏录 chaos-punch-reveal 三拍保留同行"我上周就打过一模一样的 prompt"1s 认领 · 白天办公 B-roll 保留真实痕迹 · 9 成群体锚释放"不是我不行" · 4 段 prompt 演示"同行说话"沉稳口吻 · 中腰部创作者共同体感强于 OpenMontage 电影感合成 |
| 画面**观赏性**够吗？ | ✅ 方案 A 9 段形式切换（屏录 chaos-punch-reveal + Pexels 白天办公 B-roll + 分屏爆款对比 + 3 段反例快切屏录 + 4 段 prompt 演示屏录 + 5 判据表格 + 全屏价值锚 + CTA），单场景占比最大 M7 25-40s（15s · 26%）< 40% 上限 |
| 内容**真材实料**吗？ | ✅ 4 段 prompt 走真机屏录（原生优势）· 完整 4 段 prompt 走小红书轮播 P4-P7 CSS 静态 → 可截图收藏；5 判据表格 accent_green 静态打勾（承诺兑现）；4 条 topic_brief 原话直引（跨过编剧硬门禁）；Pexels 白天办公 3800-4200K 需新拉但 chaos_must_be_real_footage 满足 |
