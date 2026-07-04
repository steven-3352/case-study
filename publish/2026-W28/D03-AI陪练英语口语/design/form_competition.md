# 表现形式竞争 · form_competition · W28D03 AI 陪练英语口语

> 工种：形式策略官 + 平台原生策划 + 纪录片导演 + 动效分镜师
> 位置：`design/form_competition.md`
> 状态：`draft_self_generated` · 2026-07-04
> 依赖：`insights/` 已 pass · `retention_beat_sheet.md` · `scripts/v0.md`（严格版为默认参照）· `design/openmontage_brief.md`（decision=blocked_infrastructure）

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` **§4.2 最新候选清单**（2026-07-04 版含 OpenMontage/Grok video/GPT-image-2/Remotion/HyperFrames）· §2.4b · §3.1e · §4.2 五维打分
- [x] **template refs**：`templates/design/form_competition.md`（§3 候选池完整性自查 + 跨家族强制）· `templates/design/openmontage_brief.md` · `templates/design/design_language.md`
- [x] **memory refs**：`feedback_no-default-tech-stack`（触发词打断） · `feedback_pre-node-checklist` · `feedback_anti-ai-visual` · `feedback_no-neon-palette`
- [x] **姊妹条 refs**：`publish/2026-W28/D02-*/design/form_competition.md` 回炉版实读 · 本条已产出的 `openmontage_brief.md`（decision=blocked_infrastructure）实读
- [x] **能力清单 refs**：`ls integrations/` = openmontage/ · `ls pipeline/` 全清单已实查 · `ls integrations/openmontage/` 已实查（sibling repo 需外部 checkout） · `ls assets/broll/raw/` 已实查（7 条深夜/夜景 Pexels 素材已预下载：`city_window_dusk` × 2 · `office_desk_dusk` × 3 · `smartphone_notification_night` × 2）

**触发词自查（本次开工前主动检查）：**
- [x] 未出现"就走 P004 吧" / "就走 P001 吧" 念头
- [x] 未出现"OpenMontage 太重了不适合"这类未跑 brief 的排除话
- [x] 3 方案跨家族强制满足

## 3. 候选池完整性自查

### 3.1 候选池来源确认

```yaml
system_ref_version_read: 2026-07-04
candidates_considered:
  native_pipeline:
    - P001 (render_p001.py + gen_evidence.py 高保真仿真)
    - P002 (报纸风轮播 · 与 skin.tone_direction 深夜克制不匹配，早排除)
    - P004 (HTML+GSAP · 反 AI 味风险 + memory feedback_anti-ai-visual 已警告)
    - P005/P006/P007 (带货/漫画/漫画图文 · 与形态不匹配)
    - fetch_broll.py Pexels 真实素材 (7 条深夜/夜景已预下载)
    - QuickTime 真机屏录豆包语音 (原生能力)
  integrations:
    - OpenMontage (documentary montage / screen demo / animated explainer / cinematic)
    - Grok video (integrations/openmontage/openmontage.env.example)
    - GPT-image-2 (中转已配)
    - MiniMax TTS speech-2.8-turbo (已在 D02 audio_plan 使用)
  raw_materials:
    - 真实拍摄深夜自习场景 (用户当前无素材)
    - 真人出镜 (Q8 演示型默认不出镜；若走 vA 场景剧型可考虑背影/手部/侧影单开分支)
    - Pexels CC0 商用真实拍摄 (已可用)
    - SVG/CSS 覆盖层 (静态代码)
    - drawtext/drawbox 大字快闪 (ffmpeg 原生)
```

### 3.2 openmontage_brief 判断（已跑）

```yaml
openmontage_brief_status: pass
openmontage_decision: blocked_infrastructure
openmontage_blocked_reason: |
  1. sibling repo 未 checkout 在本机（文档路径 /Users/bubu/... 与当前用户 wmzuo 不匹配）
  2. 项目内无成功 OpenMontage 案例参考（W28D01 disabled_by_choice · W28D02 blocked_infrastructure）
  3. W28 曝光优先·日更节奏承担不起首次跑通的交付风险
  4. 与 skin.tone_direction "沉稳同事口吻、克制、反教程"不匹配（OpenMontage animated explainer 有教程感风险）
  5. 收藏率是 D03 核心 KPI（3 段 role prompt 要截图带走），视频合成不利于逐帧截图；原生 P001 轮播优于合成
openmontage_review_trigger: 见 openmontage_brief.md decision_review_trigger 字段
```

## 4. 三个候选表现方案（**跨家族强制满足**）

### 方案 A · 原生 P001 混合（family=`pipeline`）

- **名称：** Pexels 深夜暖光 B-roll + QuickTime 真机屏录豆包 + SVG 覆盖 + 分屏静图 + drawtext 大字 + ffmpeg 合成
- **实现家族：** `pipeline`
- **核心画面机制：**
  - **0-3s**：Pexels 深夜台灯 B-roll（`office_desk_dusk_evening_empty` × 3 已下载）+ 手部特写握英语课本 + iPhone 锁屏「23:12」大字（真机拍摄或 UI 仿真）· 环境音钉子
  - **3-8s**：`punch_black` 灰底大字快切「92% 中国人不敢开口」「78% 缺安全场合」+ 讯飞录官方引用截图（真截屏）
  - **8-15s**：多邻国 App 打卡记录截屏（不打 logo · 只用连击数字）+ 手机视频通话 UI 沉默 3s（真截屏或高保真仿真）· 分屏
  - **15-20s**：AI 打字对话框 UI 截屏（对着 AI 打字问「怎么练口语」→ 通用建议列表）+ 摇头动作 B-roll 快切
  - **20-24s**：分屏静图（左：游泳教程 book cover · 右：跃入泳池瞬间）+ 大字类比锚「读游泳教程 vs 跳进泳池」
  - **24-36s**：QuickTime 真机屏录豆包语音 · 长按语音键 · role prompt 大字滑入（drawtext + SVG 覆盖高亮五段标签）
  - **36-42s**：真机屏录 AI 英文追问 + 用户回答（字幕英中对照）
  - **42-48s**：Pexels 侧躺 B-roll（`smartphone_screen_notification_night` × 2 已下载）+ 时间戳「22:45」大字
  - **48-54s**：全屏大字价值锚「不是教你 · 是把 prompt 给你」（drawtext + 黑底）
  - **54-58s**：CTA 大字 + 底部四选项标签
- **服务指标：**
  - 3s 停划：真实深夜暖光 B-roll + 时间戳锚 → 学英语党 1s 认领「这是我」
  - 完播：10 段形式切换 + 每 3-6s 变化点 + 24-36s role prompt 真机屏录动作性变化
  - 收藏：小红书 P5-P7 完整 3 段 role prompt 静态页 CSS 可截图带走
  - 评论：CTA 四选项（面试/雅思/日常/旅游）具体可答
- **优点：**
  - 与 SYSTEM Q9 chaos_must_be_real_footage 100% 一致（Pexels 深夜素材已下载）
  - 与 skin.tone_direction「沉稳同事口吻 · 反教程」完全匹配
  - `.env` 已配 MiniMax TTS 和 GPT-image-2，无阻塞
  - 制作成本可控（1-2 天完成）
  - **姊妹条 D02 方案 A 已跑通**，本条复用能力（不复用画面），风险最低
- **风险：**
  - 首镜纯 Pexels 素材可能与深夜自学赛道其他 AI 教程号撞（差异化靠"沉默 3s + 咽口水 + 时间戳 23:12"设计）
  - 真机屏录豆包需要准备本地帐号 + role prompt 演示样本（1 小时准备）
  - 多邻国 App 打卡截屏需真机（不打 logo · 只用连击数字，见 v0/vB 合规自查）
- **制作成本：** ★★ 中（1-2 天）

### 方案 B · OpenMontage 混合（family=`integrations`）

- **名称：** OpenMontage documentary montage 前段 + screen demo 中段 + cinematic 结尾
- **实现家族：** `integrations`
- **核心画面机制：**
  - 0-6s：OpenMontage documentary montage 电影感钉子（Grok video 或 Pexels 素材由 OpenMontage 剪辑）
  - 6-32s：OpenMontage screen demo pipeline（豆包语音演出）
  - 32-58s：OpenMontage cinematic 情感落点 + 反教程价值锚
- **首屏：** OpenMontage 剪辑电影感开场（3 秒沉默钉子会更连贯）
- **中段：** screen demo 电影感演出（比 QuickTime 屏录更连续）
- **CTA：** cinematic 收尾 + 大字
- **服务指标：**
  - 3s 停划：**理论上电影感钉子 > Pexels 拼接** → completion_3s 可能 +5-8%
  - 完播：连续镜头感 > 分段拼接
  - 收藏：小红书视频版可能有帮助，**但轮播 P5-P7 仍需原生 P001**（合成视频不利于截图带走）
  - 评论：情感感染力更强
- **优点：**
  - 电影感能拉高首镜 completion_3s（理论）
  - 连续镜头比拼接更专业
  - 若成功可复用到 W28 其他条目和 W29 破圈实验
- **风险：**
  - **🔴 基础设施阻塞（`blocked_infrastructure`）**：sibling repo 未 checkout · Grok video 无成功案例参考 · export_request → collect_output 跨仓库首跑
  - 项目内无 OpenMontage 成功案例（W28D01/D02 均未跑通）
  - W28 日更节奏承担不起首跑失败
  - 与 skin.tone_direction「沉稳克制」不匹配（电影感/animated explainer 有过度倾向，会拉高"我教你"感）
  - **与 D03 收藏率 KPI 冲突**：3 段 role prompt 走轮播 P5-P7 需原生静态页，OpenMontage 视频合成路线无法覆盖
- **制作成本：** ★★★★ 高（若跑通 3-5 天含 sibling repo 搭建 + 首跑调优）
- **决策：** 因 `openmontage_brief.decision = blocked_infrastructure` **本方案排除**

### 方案 C · 纯真人拍摄（family=`raw`）

- **名称：** 全片真人拍摄 + 剪映后期
- **实现家族：** `raw`
- **核心画面机制：**
  - 0-6s：真实深夜自习场景（台灯 + 手 + 英语课本 + 手机锁屏 23:12）
  - 6-15s：主角背影对墙念 + 咽口水 + 闭嘴（不出脸 · 只拍侧影/嘴部）
  - 15-42s：真机操作豆包语音（真人手 + 真实屏幕 + 真实旁白）
  - 42-58s：真人到侧躺 + 台灯关 + 手写便签 CTA
- **首屏：** 真实深夜台灯 + 真人手部（不出脸）
- **中段：** 真人操作豆包语音全流程 + 真机 role prompt 演示
- **CTA：** 真人手写便签 + 时间戳
- **服务指标：**
  - 3s 停划：真实拍摄可信度最高（A 级证据 > Pexels B 级 > OpenMontage 合成 C 级）
  - 完播：真人动作连续性最强
  - 收藏：真实操作可复制性最强
  - 评论：真实感激发共鸣 · vA 第一人称版天然适配真人拍摄
- **优点：**
  - 完全真实（A 级证据 > Pexels B 级 > OpenMontage 合成 C 级）
  - 与 skin.persona_anchor「学英语同路人」契合度最高
  - vA 场景剧型第一人称版可以直接对接
- **风险：**
  - **🔴 素材缺失阻塞**：**用户当前无深夜拍摄条件**（W28 承继 D02 判断——本项目 Phase 0-1 无自拍资源）
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

- **推荐：** 方案 A · 原生 P001 混合（Pexels 深夜暖光 + QuickTime 真机屏录 + SVG + drawtext 大字 + 分屏静图 + ffmpeg）
- **对应 chosen script：** `scripts/v0.md`（严格执行版为默认；vA 场景剧型作为抖音 A/B 备胎，vB 数据锚型作为高信息密度受众备胎）
- **为什么最能服务北极星：**
  - completion_3s：Pexels 深夜台灯素材（已下载 3 条 `office_desk_dusk`）+ 手部特写 + 时间戳 23:12 → 学英语党 1s 认领（比"打工人下班"泛化少）
  - completion_rate：24-36s 屏录 role prompt 大字滑入 + SVG 五段标签打点 → 中段动作性变化最丰富
  - 收藏：小红书 P5-P7 完整 3 段 role prompt CSS 静态 → 可截图带走（保守估 save_rate ≥6%）
  - 评论：CTA「面试/雅思/日常/旅游」四选项 + 具体承诺「我发对应 role prompt」→ 低成本高确定回复
- **与最近 5 条最大差异：**
  - 与 W27D01-D06 老板圈 catalog 完全不同（audience 池切换到学英语党 · 视觉从"agent_grid 卡片"切换到"深夜台灯 + 群体锚 + 分屏对比"）
  - 与 W28D01 老板圈方法论方向不同（D01 老板圈 · D03 学英语党）
  - 与 W28D02 打工人周报方向不同（D02 打工人下班「18:55」 · D03 学英语党深夜「23:12」；D02 无群体锚 · D03 有 92% 群体锚定；D02 演示 prompt 五段 SVG 标签 · D03 演示 role prompt 一段完整可截图）

### 不选其他方案原因

| 方案 | 不选原因 | 是否可作为后续备选 |
|------|----------|--------------------|
| A | 已选 | — |
| B | OpenMontage sibling repo 基础设施未 checkout + 项目内无成功案例 + W28 日更承担不起首跑风险 + 与 D03 收藏率 KPI 冲突 | ✅ **待 sibling repo 到位 + 首个成功案例后重新评估**（见 openmontage_brief.decision_review_trigger） |
| C | 用户当前无深夜自拍条件（W28 全周一致） | ✅ **待用户有拍摄条件后可切换 · 若走 vA 场景剧型 + 用户能拍第一人称背影/手部，可优先启用** |

## 6. 禁止从旧 storyboard 开始改

- [x] 本条不是复制上一条 storyboard 后改字（D02 白天 18:55 傍晚办公室，本条深夜 23:12 台灯自习房）
- [x] 本条不是旧模板换标题、换颜色、换字幕
- [x] 复用 P001 + Pexels + QuickTime 屏录时明确声明"复用能力，不复用画面"（见 visual_originality_gate.md 下节点）
- [x] 分镜从本条视觉命题「深夜孤独钉子 → 群体锚释放 → 打卡幻灭 → 顿悟锚 → role prompt 演示 → 侧躺共同体 → 反教程价值锚 → CTA」生成

## 7. 进入 form_strategy 的条件

- [x] 至少 3 个候选方案完整（本次严格 3 个 · 跨 3 家族）
- [x] 3 个方案覆盖 ≥2 个不同家族（本次 3 家族全覆盖）
- [x] 有明确推荐方案（方案 A）
- [x] 写清楚不选其他方案原因（B 基础设施 blocked · C 素材缺失）
- [x] 写清楚与最近 5 条的差异（W27 老板圈 vs D02 打工人 vs D03 学英语党 · 首屏机制不同）
- [x] 明确禁止旧 storyboard 改字
- [x] **`openmontage_brief.md` 已跑，decision 明确（blocked_infrastructure）**
- [x] **候选池完整性自查 §3 五条全过**

`status: pass · decision: proceed_to_form_strategy`

## 五维打分（对照 SYSTEM §4.2）

| 维度 | 权重 | 方案 A | 方案 B | 方案 C |
|------|------|--------|--------|--------|
| 停划力（首镜 ×2） | ×2 | 9 → 18 | 8 → 16 | 10 → 20 |
| 看懂速度 | ×2 | 9 → 18 | 7 → 14 | 8 → 16 |
| 节奏变化 | ×1 | 9 | 9 | 7 |
| 互动钩子 | ×1 | 9 | 7 | 9 |
| 信任/证据 | ×1 | 8 | 5 | 10 |
| 交付风险 | ×0.5 | 8 → 4 | **1 → 0.5**（blocked） | **1 → 0.5**（blocked） |
| **合计 / 60** | | **66** | **51.5**（+blocked 惩罚 = 25.75 实际不可选） | **62.5**（+blocked 惩罚 = 31.25 实际不可选） |

**方案 A 胜出，且是唯一可执行方案。**

（方案 A 比 D02 方案 A 高 4 分：D03「看懂速度」+ 1 因 92% 群体锚快速释放羞耻 · 「节奏变化」+ 1 因 10 段形式切换 vs D02 9 段 · 「互动钩子」+ 1 因 CTA 四选项 + 3 段 prompt 双动机。）

## 决策总结

- **决策：** 方案 A 原生 P001 混合
- **家族：** pipeline
- **不启用 OpenMontage 的原因：** blocked_infrastructure（非 disabled_by_choice）
- **不用真人拍摄的原因：** 素材缺失（W28 全周口径）
- **候选池预先缩水的教训：** 已入 memory `feedback_no-default-tech-stack` + template `form_competition.md` §3
- **未来 revisit 条件：** 见 openmontage_brief.md `decision_review_trigger`

## Audience-First 自查三问（form_competition 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ 方案 A 保留深夜台灯 B-roll 真实痕迹 · 群体锚 92% 释放羞耻感 · 学英语党共同体感强 |
| 画面**观赏性**够吗？ | ✅ 方案 A 10 段形式切换（Pexels B-roll + 大字快切 + 多邻国分屏 + AI 打字反例 + 分屏静图 + role prompt 屏录 + 真对话字幕 + 侧躺 B-roll + 全屏大字 + CTA 大字），单场景占比最大 24-36s（12s · 20.7%）< 40% 上限 |
| 内容**真材实料**吗？ | ✅ role prompt 走真机屏录（原生优势）· 3 段完整 role prompt 走轮播 P5-P7 CSS 静态 → 可截图收藏；Pexels 深夜素材已下载（chaos_must_be_real_footage 满足） |
