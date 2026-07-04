# 系统说明 · Agent / 人类首读

> **任何模型接入本仓库，先读本文。** 跨模型入口见 [`AGENTS.md`](../AGENTS.md)；Claude Code 特定执行细则见 [`CLAUDE.md`](../CLAUDE.md)；辩论锁定见 [`docs/DECISIONS.md`](DECISIONS.md)。
>
> 最后同步：**2026-07-04** · 维护规则见 [§7 文档维护](#7-文档维护)
>
> **2026-07-04 战略变更：** 取消固定内容皮肤（原「小老板烦事 → 能跑的小系统」）。改为**开放选题 · 选题定皮肤**：受众开放到「任何对 AI 工具/AI 应用感兴趣的人」，每条选题在洞察包首步声明自己的临时皮肤（受众、人设锚、话术方向）。详见 [§1.3](#13-皮肤按选题激活开放选题) · `docs/DECISIONS.md` Q10。

---

## 1. 系统宗旨

### 1.0 北极星（最高优先级 · 一切决策为此服务）

**本系统的最大价值：做出用户愿意看完、且互动高的内容。**

**Audience-First, Not Pipeline-First** — 交付的评判基准是**观众成果**，不是**工程产出**。

| 三要素 | 含义 | 反面（禁） |
|---|---|---|
| **内容共鸣** | 命中真实情绪/场景，观众愿意在评论里接话 | 干货堆砌 · 泛泛而谈 · 蹭热点无锚 |
| **强观赏性** | 每 2-4s 视觉变化 · 首屏停划 · 中段不塌 · 音画同步 | 单场景占大部分时长 · 静态字幕 · catalog 拼盘 |
| **强内容** | 信息密度真材实料 · 可复现的方法/prompt/清单 | 空喊口号 · AI 拼凑 · 概念糊弄 |

**反例（工程完成心态 · 全部不算交付达标）**：
- ❌「pipeline 跑通了」
- ❌「15 步走完了」
- ❌「所有工种产出都齐了」
- ❌「render 无报错」
- ❌「发布包三平台文案齐了」

**唯一交付判据**：`pre_publish_forecast` 评级 ≥ B + 投后观众数据（3s 完播 · 完播率 · 互动 · 收藏）达标。

| 载体 | 「看完」 | 「互动高」 |
|------|----------|------------|
| **视频** | `completion_3s` · `completion_rate` · `avg_watch_s` | 评论率 · 收藏率 · 讨论型 CTA 效果 |
| **图文轮播** | 划完全部张 · 停留点不塌 | 收藏动机 · 评论争议点/共鸣点 |

**第二条铁律：所有决定都以北极星为中心。** 工种、pipeline、技术栈、讨论室打分、是否 render、选 GSAP 还是实拍——唯一合法问题是：**会不会让观众多停几秒、多看懂一点、更愿意评一句/收藏？**

| 层次 | 含义 | 与北极星的关系 |
|------|------|----------------|
| **意义** | 用内容证明「AI 工具/AI 应用在真实场景里能落地」，等私信转化 | 观众须**先看完、愿意聊** |
| **远景** | 你每周 <30 分钟定方向；生产、采集、报告其余半自动 | 只有成片**数据变好**自动化才有意义 |
| **引擎** | 选题 → 工种 → 流水线 → 发布 → 进化 | **提高**完播/互动的成功率与迭代速度 |
| **技术栈** | GSAP / Three / P001 / P002 / 实拍… | **某一镜**的停划、看懂、互动 — 见 [§4.2](#42-实现方式选型北极星决策流) |

**引擎价值（内化公式）：** （完播 + 互动提升幅度）× 可迭代条数 ÷ 你的周投入时间。

与 `docs/DECISIONS.md` Q6 的关系：**无硬性 KPI** = Phase 0 不因曝光未达标而焦虑；**不等于**放低单条片质。每条决策仍须对北极星负责。

详规：`templates/design/completion_rate_north_star.md` · `templates/design/pre_publish_forecast.md`

### 1.1 我们建的是什么（手段，非目的）

**自媒体内容自动化生产引擎** — 不是某个垂直行业的单点工具；是达成 [§1.0 北极星](#10-北极星最高优先级--一切决策为此服务) 的**手段**。

针对 `queue/topics.yaml` 中的**指定选题**，半自动完成：

```
选题立项 → 采料 → 多 Agent 工种编排 → 流水线出片 → 发布包验收 → 投后数据反馈
```

**终态：** 你每周 <30 分钟定选题和方向；生产、采集、报告其余自动化。

### 1.2 引擎 vs 内容皮肤

| 层次 | 含义 | 可换吗 |
|------|------|--------|
| **引擎** | 选题驱动的多 Agent 内容生产系统 | 架构固定，持续演进 |
| **内容皮肤** | 每条选题对外讲的故事、人设锚、话术、垂直场景 | **每条选题独立声明**（详见 §1.3） |

换一批选题 / 行业 / 形态，**同一套引擎仍应跑通**。

### 1.3 皮肤按选题激活（开放选题）

**2026-07-04 起：本仓库不再锁定单一内容皮肤。**

- **受众开放** — 任何对 AI 工具/AI 应用感兴趣的人都是受众；不预设「实体店老板」「小老板」「内容创作者」等固定圈层
- **每条选题声明自己的皮肤** — 在 `insights/topic_brief.md` 的 `skin:` 段落写清本条的：受众画像、人设锚（这条我是谁）、话术方向（第一人称口吻、关键词、禁词）、钉子场景、转化落点
- **默认参考** — `persona/persona.yaml` 仅作默认/兜底参考；每条选题的 `skin:` 覆盖默认值
- **禁跨条克隆皮肤** — 一条选题的皮肤不得直接套到下一条；每条重新声明（可以复用「模板结构」，不得复用「具体表达」）
- **转化仍是等私信**（正文不导流）· 见 `docs/CONVERSION.md`
- 历史锁定策略与本次战略变更见 `docs/DECISIONS.md` Q10

### 1.4 无标准内容模板

**没有可套用的「标准成片模板」，也没有固定内容皮肤。** 每条内容从洞察包与分镜单独设计；禁止克隆上一条画面、catalog 拼盘交差、也禁止套上一条的皮肤（受众/人设锚/话术）。用语见 `templates/README.md`。

**模板边界：** 可以模板化的是判断流程、脚本结构、调研字段、合规检查和数据回收；不能模板化的是首屏画面、中段表达机制、动效语言、B-roll 选择、字幕设计、封面构图、CTA 视觉、以及本条选题的**皮肤声明**。
一句话：**模板只能约束判断，不允许决定画面，也不允许决定「这条我是谁、讲给谁听」。**

---

## 2. 工作方式

### 2.1 五层架构

```
Layer 0  你           定选题 + 方向（queue/topics.yaml）
Layer 1  选题引擎      读 metrics + 规则推荐选题（Phase 2+）
Layer 2  多 Agent 编排  工种并行 → 脚本/分镜/合规/文案
Layer 3  生产流水线     脚本 → 画面 → 配音 → 拼接 → 导出
Layer 4  发布采集       人工发布 → 48h/7d 指标
Layer 5  反馈修正       rules.yaml → 周报 → 下批选题/标准进化
```

### 2.2 新选题标准流程（15 步 · v4）

| 步 | 动作 | 产出 | 门禁 |
|----|------|------|------|
| 1 | 立项 | 进 `queue/topics.yaml` | — |
| 2 | 并行调研 | 记者笔记 + 网络调研 | ≥3 URL、≥2 网络原话 |
| 3 | **洞察包** | `insights/` 四件套 + external_references | 未完成 → **禁止写稿** |
| 4 | 留存设计 | `retention_beat_sheet.md` | 视频/强互动图文必跑 |
| 5 | 脚本三版 | v0/vA/vB（仅引用洞察 P0/P1） | — |
| 6 | 视觉路线 | 形式词汇 ≥3 种观感；封面 brief | 非套旧渲染场景 |
| 7 | 表现形式竞争 | `design/form_competition.md` | 少于 3 个候选方案 / 未写不选原因 / 未比近 5 条 → **禁止 form_strategy / storyboard** |
| 8 | 形式策略会 | `design/form_strategy.md` | 无逐镜表达方案竞争 → **禁止 storyboard 定稿** |
| 9 | 视觉语言约束 | `design/design_language.md` | 无色板/字体/组件/禁用项/逐镜应用 → **禁止 storyboard 定稿** |
| 10 | 视觉原创门 | `design/visual_originality_gate.md` | 不能证明首屏/中段/CTA 与近作不同 → **禁止 storyboard 定稿** |
| 11 | 技术可行性审查 | `design/motion_tech_plan.md` | 用 Web 3D/GSAP/复杂 HTML 动效但无审查 → **禁止 render** |
| 12 | 分镜 + 画面清单 | 对齐节拍表 + 形式策略 + 视觉语言 + B-roll；任何 `template:` 须有 `reuse_reason/visual_difference/risk` | 无节拍表/形式竞争/形式策略/视觉语言/视觉原创门 → **禁止分镜** |
| 13 | 声音方案 | `audio_plan.yaml` | 视频必跑；无方案 → **禁止 publish** |
| 14 | 流水线出片 | `pipeline/*` | — |
| 15 | 发布包 | 三平台文案 + 成品 | `templates/publish_三平台.md` |
| 16 | 验收 | `pipeline/CHECKLIST.md` + `gate_check.py` | 不过则退回对应工种 |
| 17 | 投后复盘 | `post_publish_retro` + `evolution_overlay` | 48h/7d actual 反哺下条 |

带货 / 出镜 / 图文轮播在标准流程上有分支 — 见 `CLAUDE.md` 形态对照。

### 2.3 工种组织（Layer 2）

| 层 | 工种 | 何时跑 |
|----|------|--------|
| 理解 4 | 选题深挖、内核提炼、领域专家、事实校验 | **所有形态** |
| 网络调研 | 网络调研员 | **所有选题** |
| 核心 10 | 编导、记者、纪录片导演、导演、摄像、编剧、视觉、视觉语言策展、剪辑、运营 | **所有形态** |
| 表达/音画 5 | 留存与互动设计、**动画导演（Motion Planner · 单跑不双评）**、形式策略、动效技术导演、声音设计 | **视频**；Web 3D/GSAP/复杂动效按需强制 |
| 增长复盘 1 | 数据复盘官 | **发布后 48h/7d** |
| 带货 4 | 合规、选品、消费者声音、销售脚本 | 带货型 |
| 出镜 2 | 表演指导、造型场景 | 出镜型 |

完整职责表见 `CLAUDE.md` §工种清单。

### 2.4 两道门外发门禁

1. **内容门** — 脚本/洞察过线，才允许 TTS
2. **形式门** — 视觉同质、forecast、CTA 完整；`pre_publish_forecast` pass 才外发

脚本 90+ ≠ 能投。详规：`templates/design/content_form_split_gates.md` · `pipeline/gate_check.py`

### 2.4a Fail-Closed 状态

新选题开工第一步是 `GAP_REPORT.md`，不是直接生成完整生产包。`GAP_REPORT` 仍有 blocking 时，禁止写 `approved`，禁止 TTS / gpt-image / render。

所有 `pass / approved / score >=90` 必须有来源：

```yaml
status: draft_self_generated     # 不具备门禁效力
status: pass_agent_reviewed
status: pass_human_reviewed
status: pass_gate_checked
scorecard_valid: false           # 自生成 scorecard 必须标 false
```

一个模型代替多个工种写出的讨论室和 scorecard，只能是 `draft_self_generated`，不能当作真实互评。

### 2.4b 视频生产硬门：禁止 QA 截图冒充成片

`prototype/qa_shots/`、低保真 HTML 截图、静态 QA 帧只用于证明“画面进入像素”，不得直接拼接为 `douyin/video.mp4`。

写入 canonical 成片路径 `douyin/video.mp4` 前，必须满足：

- 画面来自动态表现层：动态 HTML/GSAP/Canvas/Three 录屏或帧序列、OpenMontage、真实录屏/B-roll/视频生成素材、或正式 render pipeline。
- 配音来自项目生产级 TTS/录音方案，不得用系统 `say` 冒充生产级配音。
- 成片包含字幕、BGM/SFX、动态镜头节奏和逐镜验收。
- `gate_check(pre_render)` 未通过时，任何 mp4 只能作为 `_build/` 临时预览或 `rejected/` 事故归档，不得写成发布候选。

如果达不到这些条件，正确状态是 `blocked`，不是生成一个“长得像视频”的文件。

### 2.5 Git

- **唯一工作分支 `main`** — 克隆后 `git checkout main && git pull origin main`

### 2.6 周发布包流程（`publish/2026-W26/` 等）

单选题走 §2.2；**周批**叠加讨论室与 gate（**禁止直接 render**）：

```
立项（week.yaml / topics_content.yaml）
  → 讨论室 room/ + discussion.md
  → scorecard Phase A（每工种 ≥2 人、≥90 分）
  → gate_check.py --phase approve（内容门）
  → render / week_build.py --render
  → cover_review pass + pre_publish_forecast
  → scorecard Phase B + gate_check 形式门
  → 人工发布 → fetch_platform_metrics → evolution_apply
```

命令链：`.cursor/rules/content-prep-multi-agent.mdc`。`--force` 须登记 `docs/design/GATE_BYPASS_LOG.md`，**禁止外发**。

### 2.7 资产生命周期

项目完结后长期保留的是**设计、实现、代码、结构化数据和复盘依据**；视频、图片、素材、音频等重资产必须归属到具体项目目录，允许按项目清理。

素材来源遵守一条原则：**事实可以生成，但来源不能伪造。**  
`generated_fact` 是合法一等素材来源，可以用 AI 生成虚构但合理的聊天、表格、日报、报价、业务数据样本；但不得声称为真实客户案例、真实后台、真实成交或真实用户原话。详见 `ops/data-policy.yaml` 与 `docs/ASSET_LIFECYCLE.md`。

同理，若没有同平台热门样本，允许形式/留存 Agent 生成 `agent_hypothesis` 作为临时 benchmark 假设，用于指导 0-3s 设计；但它不能冒充真实视频拆解，发布前如有条件应被真实样本替换。

| 长期保留 | 可清理 |
|----------|--------|
| `insights/`、`scripts/`、`design/`、`room/`、`content.yaml`、`storyboard.yaml`、代码、公共模板、`performance.yaml` | `*.mp4`、`*.png`、`*.jpg`、`*.mp3`、`*.wav`、下载 B-roll、渲染帧、`pipeline/**/out/` |

公共能力抽到 `pipeline/`、`templates/`、`assets/*/catalog.yaml` 等长期目录；单项目素材不长期占用公共目录。详规见 `docs/ASSET_LIFECYCLE.md`。

---

## 3. 执行铁律

> 本节细则均服从 [§1.0 北极星](#10-北极星最高优先级--一切决策为此服务)。铁律不是「文件齐不齐」，是「观众会不会划走、会不会互动」。

### 3.1 结果负责制（D04 起）

| # | 铁律 |
|---|------|
| 0 | **北极星贯穿** — 视频看 `completion_3s` + `completion_rate` + 互动；图文看划完 + 收藏/评论。前 3s 须拆同行热门再设计停划 |
| 1 | **不看仓库有什么，只看哪条实现更强** — pipeline/工种/工具不是完成标准；标准是观众停、懂、互动/收藏，发布包能直接外发 |
| 2 | **内容门与形式门分开** — 禁止 catalog 拼盘假 approved |
| 3 | **合规分 ≠ 效果分** — 外发以像素 + `pre_publish_forecast` 为准 |
| 4 | **各环节对最终结果负责** — 禁止讨论室 approved 但成片同质 |
| 5 | **尽一切让内容更好** — 不可「能出片就行」 |
| 6 | **自我进化** — 提标准 → 测 → 更新 Rubric + gate + REJECT_LOG |
| 7 | **形式重做 ≠ 脚本可静默复用** — `form_version` 升版时，须同步评估脚本/叙事；见 [§3.1b](#31b-形式重做时脚本门禁-d02-沉淀) |
| 8 | **形式承诺必须兑现到像素** — format/storyboard 写了 Pexels、B-roll、custom、专属看板等，最终视频里必须真实出现对应素材/模板；禁止用通用 `pipeline/render.py` evidence/newsprint 产物冒充新形式 |
| 9 | **表现形式不可模板化** — 脚本结构可复用，画面表达必须逐条重新设计；首屏、中段机制、CTA 形态不得旧模板换字 |
| 10 | **自生成不等于通过** — 文件齐全但缺真实调研、真实 benchmark、真实互评时，只能标 `draft_self_generated`，不得 pass/approved |
| 11 | **先竞争，后分镜** — 每条内容必须先提出至少 3 个表现方案并说明不选理由；禁止从旧 storyboard 开始改 |

### 3.1b 形式重做时 · 脚本门禁（D02 沉淀）

> 详规：`templates/design/content_form_split_gates.md` §9 · `gate_check.check_form_redo_content_gate()`

**问题：** 用户抱怨「形式千篇一律」时，执行易窄化为只换模板；`script_review` 旧 pass 被当作永久免死金牌，完播主杠杆被边缘化。

| # | 铁律 | 执行 |
|---|------|------|
| 1 | **触发词分流** | 「形式/同质/模板」类抱怨 → discussion **两列**：形式问题 + 叙事/脚本问题；不得只开 form 工单 |
| 2 | **叙事骨架同质 → 双升** | Round 记录「叙事骨架/改造实录模板/近 D{NN}」→ **须 `content_version` +1** 并重写 `script_vo`，不能只升 `form_version` |
| 3 | **数据症状分流** | 7139 播/2 评等 → forecast/discussion **拆列**：3s/视觉 vs 评论/CTA/原话（脚本）；禁止全归因首镜 |
| 4 | **form 领先须声明** | `form_version` 数字 **>** `content_version` 时 → `script_review` 须 `content_redo: true` **或** `content_ab_frozen: true` + 理由；否则 `gate_check` FAIL |
| 5 | **形式 A/B 后第二轮** | W26 等「固定脚本测形式」实验结束后 → 同选题 **允许固定形式、改脚本** 做 content vN+1 |

**验收问句（内容层 · 形式重做时必问）：**

> 关掉声音，中段还像不像 lecture？原话进片了吗？CTA 能勾评论吗？  
> 若形式已换、脚本仍是 vC 压缩版 → **内容门未真正重验**。

### 3.1c 形式承诺兑现门禁（D08 沉淀）

> 详规：`templates/design/content_form_split_gates.md` §11 · `gate_check.check_custom_form_fulfillment()`

**问题：** D08 文档写了 “Pexels B-roll + 私域客户看板 + Agent 分工卡”，但实际用通用 `pipeline/render.py` 输出旧 evidence 窗口卡片和 newspaper 轮播，仍被误标 `ready_to_publish`。

| # | 铁律 | 执行 |
|---|------|------|
| 1 | **不看 format_spec 写了什么，只看最终像素** | render 后须抽关键帧复验；画面不像承诺形式 → `approved_content_blocked_form` |
| 2 | **承诺 Pexels/B-roll 必须真进画面** | storyboard 须引用已下载本地素材；只写搜索词/说明不算 |
| 3 | **承诺 custom/专属看板须有专属模板** | storyboard 至少包含 `dNN_` / `pexels_` / `custom_` 级模板或真实素材 |
| 4 | **通用 evidence/newsprint 不得冒充新形式** | `pipeline/render.py` evidence 卡片、`render_carousel()` newspaper 只能做内部草稿；不得作为形式承诺成品 |
| 5 | **像素失败不得 ready** | `pre_publish_forecast` 标 D/C、blocked_form、通用模板吞掉等 → `gate_check(approve)` FAIL |

### 3.1e 双平台分轨（W26 数据沉淀 · 2026-06-25）

> 数据源：`reports/作品列表.xlsx` · `reports/笔记列表明细表.xlsx` · `publish/2026-W26/performance_data.yaml`

**W26 实测：** 抖音 5 条合计 121 播 / 1 赞 / 0 评；小红书 5 条 539 曝 / 46 观 / 0 藏。跨平台 `video_reuse` 全弱；历史 TOP（1107 播）为 Agent meta，与小老板线人群错位。

| # | 铁律 | 自 W27 起 |
|---|------|-----------|
| 1 | **禁止跨平台 mp4 复用** | `meta.yaml` / `verdict.yaml` 不得出现 `video_reuse`；抖音视频 ≠ 小红书视频 |
| 2 | **分立项、分脚本、分形式** | 同痛点可成对设计，但须独立 `publish/{week}/D*/douyin` 与 `xhs` |
| 3 | **日更分轨** | 每平台 **每天 1 条**（xhs 12:30 · dy 19:30）；同日可成对痛点但须独立脚本/形式 |
| 4 | **平台默认形态** | 抖音：38–45s 叙事视频；小红书：轮播/清单/字段表 |

详规：`publish/2026-W27/week.yaml` · `publish/2026-W27/PLAN.md` · `publish/2026-W26/evolution_brief.yaml` · `templates/publish_双平台.md`

### 3.1d 正向复用协议（D08 重做版沉淀）

> D08 抖音重做后效果明显优于旧版：原因不是“用了某个固定技术”，而是把每一镜的内容任务拆开，并让形式真实服务停划、看懂、互动。

**核心结论：不要设形式优先级；要设镜头任务和兑现检查。**

| 镜头任务 | D08 重做做法 | 以后复用 |
|----------|--------------|----------|
| 停划 | 真实店主/店铺素材作背景 + 大字反常识 Hook | 首 3s 必须同时有场景锚点和一句可懂冲突 |
| 看懂痛点 | 私域消息瀑布：新客、老客、售后、沉默、复购混在一起 | 把抽象痛点变成一个可扫读的工作现场 |
| 看懂方案 | Agent 三件事分拣：分层、提醒、预警 | 把“AI 能做什么”拆成明确工位/职责 |
| 证据感 | 今日待跟进看板：人数、下一步、人工优先 | 仿真看板可以用，但必须声明为解释性画面，不冒充真实后台 |
| 停留变化 | 风险雷达：退款、差评、高价值客户不回 | 中后段必须换一种视觉语法，避免同屏卡片疲劳 |
| 互动 | 四选项 CTA：分层/回访/复购/售后 | 评论问题要让用户能低成本选一个具体答案 |

**实施顺序：**

1. 先写 `retention_beat_sheet`：每段标 `停划 / 看懂 / 证据感 / 情绪 / 互动`。
2. 再写 storyboard：每段必须有不同“画面任务”，不是换色卡片。
3. 再选能力：Pexels、录屏、HTML+GSAP、Three、静帧、真人、P001/P004 都只是候选；谁更能完成该镜头任务就用谁。
4. 素材必须落本地：Pexels/B-roll 不许只写搜索词；要有 `assets/...mp4/png` 或可复现生成物。
5. 专属模板必须存在：storyboard 引用的 `dNN_*.html` / `custom_*.html` 必须真实创建并进最终 mp4。
6. 成片后抽帧复验：至少看首镜、痛点镜、方案镜、证据镜、风险/高潮镜、CTA 镜。
7. 若抽帧发现旧字幕、黑屏、路径丢图、旧模板感，必须返工，不得靠文档解释通过。

**防旧模板回流：**

- 不从“上条视频模板”开始改；从“本条观众要看懂什么”开始设计。
- 旧 pipeline 可用作渲染器，但不能决定画面结构。
- `format_spec` 写了什么不算，`video.mp4` 抽帧看见什么才算。
- 如果某个镜头看起来能替换成任意选题文案仍成立，它就是模板化风险。
- 如果 6 张关键帧像同一个设计系统的卡片轮播，形式门默认不过。

### 3.1a 双人互评（90 分门禁 · 与上表同级）

> 详规：`.cursor/rules/content-outcome-accountability.mdc` · `templates/design/scorecard_enforcement.md`

| 规则 | 说明 |
|------|------|
| 每工种 ≥2 评审 | 不同 `angle`，禁止自评 |
| **≥90 才 pass** | 每位 score ≥90 且 avg ≥90；**89=fail** |
| Phase A + B | 立项 scorecard + 出片前复验 |
| 独立打分 | `review_mode: independent`；禁止同 session 自填 90+ |

未达标：**禁止 render / 禁止 approved**。

### 3.2 留存铁律（音画图文）

1. **清晰直给** — 极短时间内语音+文字+图像抓住眼球；一屏一主信息
2. **图像清晰** — 语义无歧义、画面美观；可识别角色/物件，非抽象圆点
3. **文字可读** — 标题/拟声/CTA 互斥布局；出图后逐张检查遮挡

### 3.2a 视觉路线 · 证据优先（DECISIONS Q9）

- **80% 画面** = 真实截屏/录屏（保留 URL 栏、状态栏等使用痕迹）
- **体裁混搭** — 同一套图文 ≥3 种体裁；禁止多张同一 HTML 结构批量出图
- **禁作主视觉** — 黑金 `build_slides` 直出、统一备忘录 HTML 模版、精美包装帧整段停住
- **AI 生图** — 本路线不作主视觉；chaos 钩子 **必须真实 B-roll**，禁止 AI 替代手机场景
- 无实拍可用 `gen_evidence.py` 仿真体裁（仍须混搭、禁模版感）

### 3.2b 数据叙事（DECISIONS Q4 · `ops/data-policy.yaml`）

| 层 | 用法 |
|----|------|
| **A 真实** | 真实私信/后台/录屏/发布后数据 — 优先 |
| **B 项目真实+区间** | 系统确有其物，效果用区间（「留资个位数」） |
| **C 叙事修饰** | 无精确数时的合理表述，禁可验证假里程碑 |

**项目画面必须真实**；效果数字按 A/B/C，禁止 P 图假后台。

### 3.2c 成功标准（DECISIONS Q6）

- **无硬性 KPI** — `ops/rules.yaml` 阈值为复盘参考，不是过关门槛
- **最强正向信号** — 主动私信；有私信记入 `metrics.notes`

### 3.3 内容硬约束

- 画布 **9:16 · 1080×1920**（`pipeline/screen_dims.py`）
- 视频 **音画硬门**（2026-07-04 更新）：
  - **硬门（必满足）**：配音（VO 全程覆盖 · 前 6s RMS ≥ -25 dB · 禁沉默钉子）+ 字幕
  - **条件件**：BGM 按形态判定 — 密 VO 演示/知识型（VO ≥85% + 无 3s+ 死区）默认无 BGM；稀疏 VO / 出镜 / 情感 / 带货默认要 BGM
  - 外发：有 BGM `*_with_bgm.mp4`；无 BGM `*_no_bgm.mp4` 直接外发
  - 详规：`templates/audio_plan.yaml` bgm.enabled；memory `feedback_dense-vo-no-bgm-default`
- 前 **3s 冲突钩子**：大字 + 演示画面（或真人冲突表情）
- 项目结果先于方法论；业务问题先于技术栈
- **出镜（DECISIONS Q8）** — 数字人仍暂停；真人按形态：

| 形态 | 出镜 |
|------|------|
| 演示型（默认） | ❌ 全屏演示，不出镜 |
| 知识型 | ❌ 默认不出镜；可画中角上半身 |
| 带货型 | ✅ 真人（脸/手/产品）可作主画面 |
| 出镜型 | ✅ 真人为主，演示为辅 |

### 3.4 拒稿级反例（摘要）

- 跳过洞察包写稿 · 无节拍表出分镜 · 发裸片
- 克隆上一条分镜/画面 · catalog 标配三连
- 全片单一渲染场景 · 脚本 90+ 但形式 fail 仍外发
- **形式 vN 重做但 `content_version` 不动、无 `script_review` 声明**（D02 form v4 / content v2）
- 因「默认 pipeline」或「技术更酷」选实现，未按 §4.2 对每镜打分
- 带货跳过合规 · 正文私信导流

完整列表：`CLAUDE.md` 反例 · `docs/design/SCRIPT_REJECT_LOG.md` · `docs/design/FORM_FAIL_LOG.md`

### 3.5 刻意不做（Phase 0–1）

三平台自动发布 · 数字人 · 自研声音克隆 · 爬电商详情 · CMS/数据库

---

## 4. 能力与组织

### 4.1 能力全景

| 能力域 | 路径 / 命令 | 用途 |
|--------|-------------|------|
| **选题输入** | `queue/topics.yaml` | 引擎主输入 |
| **人设与禁词** | `persona/persona.yaml` | 口吻、标签、视频布局 |
| **通用短视频产线** | `pipeline/produce.py --id …` | GitHub 项目 → 三平台 mp4+文案+封面 |
| **周批产线** | `pipeline/week_build.py` · `week_room.py` | W26 等多日批量 |
| **P001 截图风** | `pipeline/render_p001.py` · `gen_evidence.py` | 仿真 UI + 真实截图 B-roll |
| **P002 报纸轮播** | `pipeline/p002_carousel_gen.py` | GPT-image-2 整图 |
| **P004 GSAP 视频** | `pipeline/p004_video/build.py` | HTML 渲染场景 → 帧 → mp4+VO+BGM |
| **P005–P007** | `pipeline/p005_belt_video/` 等 | 带货演示 / 漫画视频 / 漫画图文轮播 |
| **配音** | `pipeline/tts/` | edge / minimax / volcengine |
| **B-roll 库** | `assets/broll/catalog.yaml` | 登记、选型、chaos 真实素材 |
| **形式词汇** | `assets/formats/catalog.yaml` | 分镜观感类型（非 HTML 套用） |
| **视觉语言参考** | `assets/design-md/` · `design/design_language.md` | 从 DESIGN.md 提取本条色板/字体/组件/禁用项 |
| **外发门禁** | `pipeline/gate_check.py` | 内容门+形式门 |
| **投后指标** | `pipeline/fetch_platform_metrics.py` · `import_metrics_48h.py` | 48h 回填 |
| **标准进化** | `pipeline/evolution_apply.py` | 数据驱动 Rubric/gate 更新 |
| **消费者调研** | Agent-Reach CLI | 小红书/B站/Reddit 公开内容 |
| **发布输出** | `publish/` | 文案+清单（`*.png`/`*.mp4` 不入库） |
| **验收** | `pipeline/CHECKLIST.md` | 发布前清单 |

### 4.2 实现方式选型（北极星决策流）

**没有「默认 pipeline」。** 只有「默认决策流程」：先定这一镜的观众行为，再选实现。

#### 流程

```
洞察包 + hook_benchmark（同行怎么停划）
  → retention_beat_sheet（每段：停划 / 看懂 / 互动 主意图）
  → 每一镜：列候选实现 → 五维打分 → 否决项检查
  → 分镜 + audio_plan（音画同拍）
  → pre_publish_forecast（3s/完播/互动区间）→ C/D 禁止外发
  → 渲染（可混用多条 pipeline 于同一成片）
  → 48h 数据 → evolution（改的是「实现」，不是「工具信仰」）
```

#### 每一镜：先标主意图

| 意图 | 观众行为 | 主指标 |
|------|----------|--------|
| **停划** | 拇指停住 | `completion_3s` |
| **看懂** | 不困惑、不中途划走 | `completion_rate` · `avg_watch_s` |
| **互动** | 想评、想收藏、想转发 | 评论率 · 收藏率 |

**未标意图的镜 → 禁止选实现方式。**

#### 候选实现清单（**版本化 · 无默认顺序**）

> **最后同步：2026-07-04** · 每季度或每次新集成入 `integrations/` 时**必须**回顾并更新本清单。
> **本清单是 form_competition 的候选池来源**——不在清单内的能力不得作为方案候选；发现清单遗漏当即回填本节，再回 form_competition。

**原生 pipeline（`pipeline/`）：**
- 真实 B-roll（`pipeline/p004_video/fetch_broll.py` 拉 Pexels CC0）
- P001 截图/录屏（`pipeline/render_p001.py` · `pipeline/gen_evidence.py` HTML 高保真仿真体裁）
- P002 报纸风轮播（`pipeline/p002_carousel_gen.py` · GPT-image-2 整图）
- P004 HTML+GSAP 视频总编排（`pipeline/p004_video/build.py`）
- P005 带货演示（`pipeline/p005_belt_video/`）
- P006/P007 漫画视频/图文（`pipeline/p006_belt_video_comic/` · `pipeline/p007_xhs_engine_comic/`）
- `pipeline/produce.py` 项目演示线
- 真人出镜（Q8 · 按形态激活）

**外部制作插件（`integrations/`）：**
- **OpenMontage**（`integrations/openmontage/` · 已集成 2026-06 · runtime 候选：Remotion / HyperFrames / FFmpeg / undecided · 详见 `templates/design/openmontage_brief.md` 门禁）
- **Grok video**（`integrations/openmontage/openmontage.env.example` · `grok-imagine-video` · 视频生成素材候选）
- **GPT-image-2**（本项目已配 · 报纸风首选之外，也可用于分镜任意需静态生成的画面）
- MiniMax speech-2.8-turbo（`pipeline/tts/gen_speech.py` · 声音层实现）

**Web 3D / 高级动效候选：**
- Three.js（少数镜、非默认）
- Canvas / SVG（覆盖层、打点、翻牌）

**候选池完整性铁律（**form_competition 门禁**）：**
- ❌ 3 个方案**不得同家族**（不能都是 P001 变体 / 都是 P004 变体 / 都是 OpenMontage 变体）
- ❌ 候选池不得**预先缩水**——列候选前必须回来读本清单
- ❌ 发现候选被"默认习惯"排除（例如"就走 P004 吧"），立即打断，回本节重列

**清单本身可能过期。** 出现"我脑子里的默认路线是 X"时立即警觉——是不是清单缺了新能力？回本节校对再决策。

#### 五维打分（1–5，加权求和；最高分 wins）

| 维度 | 权重 | 问什么 |
|------|------|--------|
| 停划力 | 首镜 ×2，其余 ×1 | 0–3s 能否压住信息流？ |
| 看懂速度 | ×2 | 一屏一信息？3s 内能懂？（§3.2 留存铁律） |
| 节奏变化 | ×1 | 支撑 5–8s 一切？中段会不会塌？ |
| 互动钩子 | ×1 | 有没有「想评一句」的钉子？ |
| 信任/证据 | ×1 | Q9：真实画面是否更强？ |
| 交付风险 | ×0.5 | 新管线会不会导致**更差赶工版**？ |

**否决项（不看分数）：** chaos 用 AI 假手机 · 字挡信息 · 带货合规红线 · forecast C/D。

#### 平局时的 tie-breaker

| 情况 | 倾向 |
|------|------|
| 停划/看懂/互动主要靠字与节拍 | GSAP / DOM |
| 同一信息真实界面更有冲击力 | P001 / B-roll（常胜过动效） |
| 必须真 3D 空间，2D 明显假 | Three.js（少数镜，非默认） |
| 轮播收藏动机（清单/漫画故事） | P007 / P002（看本条形态） |
| 带货需摸产品/看脸 | 真人（Q8） |
| 五候选差不多 | **已有管线**（少赶工 = 少毁片） |

整条片可混用：chaos 实拍 + 中段 P001 录屏 + OpenMontage 段 + 末段 GSAP CTA。**`pipeline/p004` 是分镜里若干镜的渲染器之一，不是「视频默认路线」。同理，OpenMontage / P001 / GSAP 也都不是"默认"。**

技术栈细则：`docs/TECH_STACK.md` §画面实现选型。

#### 接到「该用哪种方式？」只问四问

1. 这一镜主意图是停划、看懂还是互动？
2. 真实素材/B-roll 能否更强？（能 → 优先证据，别动效硬撑）
3. 换实现，forecast 里 3s/完播/互动区间会不会上移？
4. 换实现会不会导致赶工烂版？（会 → 用稳管线做好版）

#### D08 复用检查：先定画面任务，不定技术路线

新选题进入视频生产前，必须先写一张“画面任务表”，再选能力：

| 位置 | 必填 | 不合格信号 |
|------|------|------------|
| 首镜 | 场景锚点 + 冲突大字 | 只有抽象背景/只有标题 |
| 痛点镜 | 具体工作现场或具体对象 | 只用概念卡解释 |
| 方案镜 | 方案被拆成动作/职责/流程 | 只写 AI 很强 |
| 证据镜 | 看板、录屏、真实素材、可核验结构 | 假装后台、数字无边界 |
| 变化镜 | 与前一镜不同视觉语法 | 连续同类卡片 |
| CTA | 低成本具体评论动作 | “你怎么看”式空泛问题 |

通过这张表后才允许决定使用 Pexels、GSAP、Three、录屏、真人、P001/P004 等能力。**能力选择的理由必须写成“更有利于哪一个目标”，不能写成“默认用某技术”。**

### 4.3 关键产出格式（非成片套路）

| 类型 | 路径 |
|------|------|
| 洞察包 | `templates/insights/` → 复制到 `publish/{id}/insights/` |
| 节拍 / 音画 | `templates/retention_beat_sheet.md` · `templates/audio_plan.yaml` |
| 工种设计室 | `templates/design/*` · `templates/agent_room/*` |
| 视觉语言约束 | `templates/design/design_language.md` → `publish/{id}/design/design_language.md` |
| 发布文案结构 | `templates/publish_三平台.md` |
| 渲染场景（技术壳） | `pipeline/*/templates/*.html` |

---

## 5. 当前状态

| 项 | 值 |
|----|-----|
| 阶段 | **Phase 0–1** — pipeline 已跑通；**W26 周包** + gate/evolution 在实战 |
| 工作分支 | `main` |
| 内容皮肤 | **按选题激活**（2026-07-04 起取消固定皮肤，详见 §1.3） |
| 每日执行 | `docs/TODO.md` |
| 排期 | `docs/SCHEDULE.md` · `docs/PHASE1_CALENDAR.md` |

---

## 6. 文档地图

| 文档 | 读何时 |
|------|--------|
| **本文 `docs/SYSTEM.md`** | 首次接入 / 大改后对齐全貌 |
| **`.cursor/rules/*.mdc`** | Cursor 自动加载铁律（90 分互评、讨论室、结果负责制） |
| `CLAUDE.md` | Agent 执行：工种、15 步、反例、环境 |
| `docs/DECISIONS.md` | 皮肤层策略辩论结论（Q1–Q8） |
| `templates/README.md` | 产出格式 vs 渲染场景 vs 形式词汇 |
| `pipeline/README.md` | 流水线步骤与 produce.py |
| `pipeline/CHECKLIST.md` | 发布前验收 |
| `docs/TECH_STACK.md` | 工具选型与依赖 |
| `docs/CONVERSION.md` | 私信转化与简介 |
| `docs/TODO.md` | 当天做什么 |
| `docs/design/*_REJECT_LOG.md` | 拒稿案例与进化依据 |
| `templates/design/completion_rate_north_star.md` | 完播与互动北极星细则 |
| `templates/design/content_form_split_gates.md` | 两道门 |
| `templates/design/scorecard_enforcement.md` | 90 分互评门禁 |
| `ops/data-policy.yaml` | 数据叙事 A/B/C |
| `ops/rules.yaml` | 复盘参考阈值（非硬 KPI） |
| `persona/persona.yaml` | 口吻、禁词、视频布局 |
| `legacy/README.md` | 旧案例素材包（降级，非首发默认） |

**已废弃仅留跳转：** `PROJECT.md` · `docs/BLUEPRINT.md` → 指向本文。

---

## 7. 文档维护

**原则：** 改系统行为必须同步改文档；不允许「代码已变、SYSTEM 未变」。

| 变更类型 | 必须更新 |
|----------|----------|
| 宗旨 / 北极星 / 阶段 / 皮肤定位 | 本文 §1、§5 · `docs/DECISIONS.md`（若战略变） |
| 工作流程 / 门禁 | 本文 §2 · `CLAUDE.md` · 相关 `templates/design/*` |
| 铁律 / 验收标准 | 本文 §3 · `CLAUDE.md` · `pipeline/CHECKLIST.md` · `.cursor/rules/` |
| 新增/废弃 pipeline | 本文 §4 · `pipeline/README.md` |
| 形式词汇 | `assets/formats/catalog.yaml` · 本文 §4.1 |
| 拒稿教训 | `docs/design/*_REJECT_LOG.md` · 必要时回写 §3 |
| gate / rubric 逻辑 | `pipeline/gate_check.py` · `templates/design/scorecard_rubric.md` |

**Agent 改代码后：** 若触及上表任一行，在同一 PR/commit 内更新对应文档，并在本文「最后同步」日期改当天。

**删除文档前：** 确认无引用；历史教训并入 REJECT_LOG，不删 fail 登记。
