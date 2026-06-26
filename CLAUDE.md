# CLAUDE.md — AI 小系统获客引擎 · 项目规则

> **首读：** [docs/SYSTEM.md](docs/SYSTEM.md)（§1.0 北极星 · 宗旨 · 工作方式 · 铁律 · 能力全景 · 文档维护）
>
> 本文：Agent **执行细则**（工种、14 步、环境、反例）。与 SYSTEM 同步维护，勿在两处写不同规则。

## 项目概览（摘要）

- **引擎：** `queue/topics.yaml` 选题 → 多 Agent 编排 → `pipeline/` 出片 → `publish/` 发布包
- **当前皮肤：** 小老板烦事 → 能跑的小系统（可换，非系统边界）
- **辩论锁定：** `docs/DECISIONS.md` · **无标准内容模板：** `templates/README.md`

## 环境配置

```bash
# 复制 .env 模板填入 key
cp .env.example .env

# Python 依赖
pip install openai pillow python-dotenv edge-tts requests

# 系统依赖
# macOS + Python 3 + ffmpeg + Google Chrome + 剪映

# 调研工具(可选,装好后 Agent 自动识别)
# 让 Claude 跑: 帮我安装 Agent Reach：https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
# 用途:小红书/B站/Reddit 公开内容调研(消费者声音),不用于商品/电商详情爬取
```

## Git 与分支

- **唯一工作分支：`main`** — 日常开发、提交、推送均在 `main` 上完成。
- 不创建日期分支或长期 feature 分支；小改动直接 commit，大改动可在本地 short-lived 分支做完后 **merge 回 `main` 并删除**。
- 克隆后默认：`git checkout main && git pull origin main`

## 统一画布规格

- 全局 9:16 → 1080×1920（图文 + 视频统一）
- 常量定义：`pipeline/screen_dims.py`（CANVAS_W/H, VIDEO_W/H, IPHONE_W/H）

## 流水线入口

| 路线 | 脚本 | 用途 |
|------|------|------|
| P001 真实截图风 | `pipeline/render_p001.py --all` | 仿真 B-roll + 三平台视频/图文 |
| P001 仿真素材 | `pipeline/gen_evidence.py` | Chrome 渲 HTML 出 9:16 满铺帧 |
| P002 报纸风出图 | `pipeline/p002_carousel_gen.py` | GPT-image-2 整版报纸风轮播 |
| P004 视频总编排 | `pipeline/p004_video/build.py` | HTML+GSAP 渲染场景 → PNG → mp4 + VO + BGM + 字幕 |
| TTS 配音 | `pipeline/tts/gen_speech.py --script <path>` | `config.yaml` provider: edge / minimax / volcengine |
| 调研工具 | `agent-reach`(独立 CLI) | 小红书/B站/Reddit 公开内容拉取(消费者声音研究员用) |

## GPT-image-2 API（报纸风首选）

- 中转：tonbirds（`GPT_IMAGE_BASE_URL=https://us.tonbirds.com/v1`）
- 尺寸：1024×1536 原生 → 升采样 1080×1620
- 单张耗时 60-130s，需 4 次重试 + 5s 退避
- 中文标题渲染质量高，正文长段落约 5% 乱码（可接受）
- 不适合：精确文字排版、可编辑版面、品牌 logo

## GSAP Skills（项目已安装 · `.agents/skills/` · 8 个）

gsap-core / gsap-timeline / gsap-scrolltrigger / gsap-plugins / gsap-performance / gsap-utils / gsap-react / gsap-frameworks

来源：https://github.com/greensock/gsap-skills.git · 索引见 `.agents/skills/gsap-llms.txt`

适用场景：
- 项目演示落地页 / 长滚动案例页
- 交互式作品集 / Before-After 对比
- 网页动效 → 录屏当 B-roll
- 报纸风不适合时 HTML+GSAP 拼版面再截图（**为本条写场景**，非套旧文件）

## 无标准内容模板（用语）

- **工种产出格式** → `templates/`（洞察、节拍、音画等文档结构）
- **渲染场景** → `pipeline/*/templates/*.html`（截帧用画布；每条可新建或重写）
- **形式词汇** → `assets/formats/catalog.yaml`（观感类型，不是指定 `.html` 文件名）

**禁止**：从上一条克隆分镜/画面、catalog 标配三连、同场景占全片大部分时长。详见 `templates/README.md`。

---

## 核心工作流程：新选题多工种协作模式

每次出现新选题（`queue/topics.yaml` 新增、口头抛一个场景、或给某项目做内容落地），**必须**先按多工种协作跑一遍，不能直跳 prompt 写作或剪辑。

> 本节即引擎的 **多 Agent 专业化编排层**（对应 BLUEPRINT Layer 2）：采料与各工种产出在此完成，再汇入 `pipeline/` 流水线出片。

### 工种清单

> **理解层 4**（所有形态必跑）+ **核心 9** + **表达/音画层 4**（视频必跑/按需激活）+ **增长复盘层 1** + 扩展工种（按形态激活）

#### 理解层 4 工种（所有形态必跑 · 洞察包）

| 工种 | 职责 | 输出 |
|------|------|------|
| **选题深挖师** | 拆透选题：谁、场景、烦什么、要什么结果 | `insights/topic_brief.md` |
| **内核提炼师** | 从调研中抽 3–5 条不可删关键信息 + 1 句价值锚 | `insights/core_message.md` |
| **领域专家** | 项目：业务逻辑/流程；带货：品类决策链、竞品差异 | `insights/domain_notes.md` |
| **事实校验员** | 核对数据、SKU、引用；标红不可写 | `insights/fact_check.md` |

产出格式见 `templates/insights/`。**门禁：** 洞察包未完成 → 禁止编剧写稿。

#### 网络调研层（所有选题必跑 · 2026-06 起）

| 工种 | 职责 | 输出 |
|------|------|------|
| **网络调研员** | 搜公开内容（行业文/案例/社区），提炼痛点与可引用转述 | `insights/external_references.md` |

**门禁：** 无 external_references（≥3 URL、≥2 网络原话）→ 禁止洞察包定稿。前期宁可多讨论，不可跳过调研。

#### 核心 9 工种（所有形态都跑）

| 工种 | 职责 | 输出 |
|------|------|------|
| **编导（总导）** | 选题是否符合主线、四形态拆分 | 选题立项单：钩子 + 形态分工 + 验收标准 |
| **记者** | 真实性、数据、证据链 | 调研笔记：小老板原话、痛点佐证、数据点 |
| **纪录片导演** | 故事弧线、改造前后对比 | 叙事大纲：起承转合 + 情绪锚点 |
| **导演（执行）** | 镜头语言、节奏、信息密度 | 分镜表：画面/口播/字幕/时长（出镜型含机位） |
| **摄像/视觉** | 画面可拍性、构图、可复用素材 | 画面清单：B-roll 列表、截图需求 |
| **编剧** | 钩子、逐字稿、字幕节奏 | v0/vA/vB 三版脚本 + 前 3s 大字钩子 |
| **视觉设计** | 版面、色彩、品牌一致性；**封面 mock 验收** | 视觉路线 + `design/cover_brief.md` + `design/cover_review.md` |
| **剪辑** | 时长卡控、三平台规格 | 剪辑说明：抖音 45-60s / 小红书 ≤60s / 视频号 60-90s |
| **运营/增长** | 分发策略、私信转化承接 | 三平台文案 + 评论区埋点 + 私信路径 |

#### 表达/音画层 4 工种（视频形态必跑/按需激活）

| 工种 | 职责 | 输出 |
|------|------|------|
| **留存与互动设计师** | 完播节拍、形式切换、互动 CTA | `retention_beat_sheet.md` |
| **形式策略官 / 视觉策略官** | 在脚本期比较每个关键镜头的多种表达方式，按数据杠杆选择实拍、2D UI、GSAP、Three/Web 3D、截图或字幕 | `design/form_strategy.md` |
| **动效技术导演 / Web 3D 技术导演** | 对高级动效、GSAP、Three/Web 3D、HTML 截帧做可行性、资产、性能、导出风险审查 | `design/motion_tech_plan.md` |
| **声音设计师** | 配音、BGM 情绪、字幕方案 | `audio_plan.yaml` |

产出格式见 `templates/retention_beat_sheet.md`、`templates/audio_plan.yaml`。**门禁：** 无留存节拍表 → 禁止出分镜；视频/强互动图文无 `form_strategy` → 禁止定 storyboard；使用 Web 3D/GSAP/复杂 HTML 动效但无 `motion_tech_plan` → 禁止 render；无音画方案 → 禁止进 publish。

#### 增长复盘层 1 工种（发布后必跑）

| 工种 | 职责 | 输出 |
|------|------|------|
| **数据复盘官 / 增长复盘官** | 48h/7d 对比 forecast 与 actual，判定问题来自选题、钩子、脚本、形式、CTA、平台文案或发布时间，并反哺下条 | `design/post_publish_retro.md` + `evolution_overlay.md` |

#### 带货扩展 4 工种（带货型选题激活）

| 工种 | 职责 | 输出 |
|------|------|------|
| **合规审核** | 广告法、绝对化用语、医美/食品/化妆品红线、平台社区规则 | 合规清单 + 改写建议（红区逐句标注） |
| **选品/商品分析师** | 商品 SKU 拆解、卖点、价位、目标人群、竞品对照 | 选品卡：核心卖点 + 不卖点 + 适合人群 + 价位锚 |
| **消费者声音研究员** | 走 Agent-Reach 挖小红书/B 站真实槽点和决策路径 | 消费者声音报告：高频痛点 + 争议词 + 原话引用 5-10 条 |
| **销售脚本师** | 卖货话术、痛点放大、对比、限时福利、口播 CTA | 卖货逐字稿（与"编剧"叙事区分） |

#### 出镜扩展 2 工种（出镜型选题激活，可与带货型叠加）

| 工种 | 职责 | 输出 |
|------|------|------|
| **演员/出镜表演指导** | 真人出镜：口语化重写、表情/手势/眼神、节奏、机位建议 | 表演说明：情绪点 + 机位号 + 默背要点 |
| **造型/服装/场景** | 穿搭、布景、品牌一致性、灯光色温 | 拍摄清单：服装 / 道具 / 场景 / 灯光 |

### 形态对照

不是每条选题都跑全扩展工种。按形态激活：

| 形态 | 激活工种 | 典型选题 |
|------|----------|-----------|
| **演示型**（默认） | 理解 4 + 核心 9 + 表达/音画 4（视频）+ 增长复盘 1（发布后） | AI 改造小老板系统、案例复盘 |
| **知识型** | 理解 4 + 核心 9 + 表达/音画 4（视频）+ 增长复盘 1（发布后） | 拆解、方法论、教程 |
| **带货型** | 理解 4 + 核心 9 + 表达/音画 4 + 带货 4 + 增长复盘 1（发布后） | 商品种草、对比测评 |
| **出镜型**（可叠加） | 当前形态 + 出镜 2 | 任何形态切真人出镜版本 |
| **图文轮播** | 理解 4 + 核心 9（无声音设计师；图内大字替代字幕） | 6–8 张小红书轮播 |

### 生产模式（轻量 / 全量 · 2026-06-26 固化）

**单条 ≤60s 视频/轮播默认走「轻量模式」**，详规：`templates/design/lightweight_production_mode.md`。

- **轻量只砍重复功，不砍质量门**：两道门 fail-closed、36 张 scorecard 双人独立 ≥90、注意力硬门、真实性红线、音画三件套——一个不少。
- **精简点**：①同形态 fork 已有 `dNN_` 模板不从零搭；②第 2 轮互评只重评上轮 <90 的工种（best-of-2），不全员重跑；③默认 1 轮、挑出硬伤才开第 2 轮，最多 2 轮取最好往下继续；④洞察/文档可串行直写，只有渲染/独立互评/真联网调研才派 agent；⑤需用户拍板的决策攒成一次问。
- **升回全量**：带货 / 出镜 / 形式 A/B 周 / 投后要求重做 / 新形态首条（无模板）/ 选题强争议 / 用户点名。

### 标准动作（v2）

1. **立项** — 编导确认选题进 `queue/topics.yaml`
2. **并行深挖** — 记者 + 纪录片导演；带货型加消费者声音 + 选品
3. **洞察包** — 选题深挖师 + 内核提炼师 + 领域专家 + 事实校验员 → `insights/` 四件套
4. **留存设计** — 留存与互动设计师 → `retention_beat_sheet.md`（视频/强互动图文）
5. **脚本三版** — 编剧产出 v0/vA/vB（**只能引用洞察卡 P0/P1，不得新增卖点**）
6. **视觉路线** — 视觉设计定 P001 / P002 / 新路线；形式选型见 `assets/formats/catalog.yaml`（≥3 种）
7. **形式策略会** — 形式策略官逐镜比较表达方案，声明数据杠杆、理解成本、制作成本、技术风险 → `design/form_strategy.md`
8. **技术可行性审查** — 使用 Web 3D / GSAP / 复杂 HTML 动效 / 重资产 B-roll 时，动效技术导演给实现路线 → `design/motion_tech_plan.md`
9. **分镜 + 画面清单** — 导演 + 摄像对齐节拍表、形式策略与 `assets/broll/catalog.yaml`
10. **声音方案** — 声音设计师 → `audio_plan.yaml`（视频必跑）
11. **剪辑/出图** — 进入对应 `pipeline/` 脚本
12. **发布包** — 运营三平台文案 + `templates/publish_三平台.md`
13. **验收** — `pipeline/CHECKLIST.md`，不过回到对应工种返工
14. **投后复盘** — 数据复盘官回填 48h/7d actual，形成 `post_publish_retro` 与下条 `evolution_overlay`

### 形态分支（在标准动作上插入）

- **带货型** — 步骤 2 后插入选品分析；步骤 3 前合规预审；步骤 5 销售脚本师主导叙事钩子；步骤 10 前再过合规
- **出镜型** — 步骤 6 后追加演员表演说明 + 造型清单；步骤 9 分镜含机位号；步骤 11 增加录制
- **图文轮播** — 跳过步骤 8；步骤 4 留存表改为「每张停留点 + 收藏动机」

### 洞察包门禁（反敷衍）

- 关键信息 < 3 条 → 退回内核提炼师
- 无用户原话 / 无场景细节 → 退回记者
- 编剧稿出现洞察卡没有的卖点 → 退回事实校验员
- 带货无选品卡 → 禁止进销售脚本

### 规则

- 允许某个工种声明"本选题不输出"，但必须显式说明原因
- 可由 Claude 串行扮演各工种，也可调 Agent 工具并行
- 每个工种产出独立、可审阅的段落，不合并成"四不像"
- Phase 0 全人工串行；Phase 2+ 半自动后 Agent 并行

### 铁律 · 结果负责制（2026-06 起 · D04 升级）

0. **北极星** — 做出用户愿意看完、且互动高的内容；视频看 `completion_3s` + `completion_rate` + 评论/收藏；图文看划完 + 收藏/评论。前 3s 须拆同行热门设计停划。详规：`docs/SYSTEM.md` §1.0 · `templates/design/completion_rate_north_star.md`

1. **不看仓库有什么，只看哪条实现更强** — pipeline/场景文件/工种名单不是完成标准；标准是观众会不会停、懂、互动/收藏，以及发布包能否直接外发。实现选型：`docs/SYSTEM.md` §4.2
2. **内容门与形式门分开** — 脚本 90+ 允许 TTS；**形式**（视觉同质、分析师 forecast、CTA 完整）pass 才允许外发。禁止 catalog 拼盘假 approved。
3. **合规分 vs 效果分** — scorecard 纸面 90+ ≠ 能投；外发以像素 + `pre_publish_forecast` 为准。差距 >5 归档 `form_audit`。
4. **各环节专家对最终结果负责** — 禁止「讨论室 approved + render 跑通」但成片与上条同质。
5. **尽一切可能让内容更好** — 宁可多一轮讨论、换 route、重写 storyboard，不可「能出片就行」。
6. **自我进化** — 提高标准 → 多轮测试 → 更新 Rubric + `gate_check` + REJECT_LOG。详规：`templates/design/system_evolution.md`
7. **形式为数据假设服务** — 每个高级视觉镜头必须声明服务 `completion_3s` / `completion_rate` / 理解 / 收藏 / 评论中的哪一项；不能声明数据杠杆的形式，不进入成片。

**核心文档：**
- 完播北极星：`templates/design/completion_rate_north_star.md` · `templates/insights/hook_benchmark.md`
- 铁律：`.cursor/rules/content-outcome-accountability.mdc` · `.cursor/rules/content-prep-multi-agent.mdc`
- 两道门：`templates/design/content_form_split_gates.md`
- 门禁：`pipeline/gate_check.py` · `templates/design/anti_perfunctory_gates.md`
- fail 登记：`docs/design/FORM_FAIL_LOG.md` · `docs/design/SCRIPT_REJECT_LOG.md`
- 投后进化：`pipeline/fetch_platform_metrics.py` · `pipeline/evolution_apply.py`

### 反例（不要这么做）

- ❌ 选题一来直接跳进 `p002_carousel_gen.py` 写 prompt
- ❌ 跳过洞察包直接写脚本 → 内容敷衍、卖点虚假
- ❌ 只用编剧视角，跳过记者 → 没真实感
- ❌ 无留存节拍表就出分镜 → 中段拖沓、完播差
- ❌ 发裸片（无 BGM / 无字幕）→ 违反音画硬门槛
- ❌ 跳过视觉设计 → 所有选题都出报纸风
- ❌ 全片单一渲染场景或同质画面 → 观赏性差、用户划走
- ❌ 从上一条克隆分镜/画面（模板克隆）→ 见 `SCRIPT_REJECT_LOG.md`
- ❌ 用形式库 catalog 拼盘代替本条分镜设计 → 平台表现分析师退稿
- ❌ 工种产出混成一份不可分辨的文档
- ❌ 带货选题跳过合规审核 → 一夜封号
- ❌ 把「选品分析」塞给编剧/记者糊弄过去 → 不懂 SKU 的卖点提炼是假卖点
- ❌ 脚本 90+ 但形式 catalog 拼盘仍外发 → **平台表现分析师 + 编导** 退稿（D04 v10 教训）
- ❌ 无 `pre_publish_forecast` 或形式 forecast fail 仍 approve
- ❌ 因「P004 是默认视频线」或「Three 更酷」选实现 → 须按 SYSTEM §4.2 对每一镜打分

---

## 内容硬约束（来自 DECISIONS.md）

### 留存铁律（音画图文通用 · 2026-06-21）

1. **清晰直给** — 极短时间内，用语音、文字、图像同时抓住眼球；一张图/一屏只传达一个主信息。
2. **图像清晰** — 语义无歧义，画面美观；禁止用抽象图标糊弄可识别的角色/物体（工种用卡通头像，输入输出用具体物件）。
3. **文字可读** — 所有大字完整可见，标题 / 拟声 / CTA 互斥布局，出图后逐张目视检查叠层遮挡。

- 9:16 → 1080×1920 统一画布（图文 + 视频）
- **视频音画三件套（硬门槛）**：配音 + BGM + 字幕叠主画面；外发默认 `*_with_bgm.mp4`
- 口播：Edge TTS 或 MiniMax（见 `audio_plan.yaml`）
- 前 3s 冲突钩子：大字字幕 + 演示画面（演示/知识型），或真人冲突表情（出镜型）
- 项目结果先于方法论，业务问题先于技术栈
- 出镜按形态决定：演示型/知识型默认全屏演示不出镜；带货型/出镜型可走真人出镜（数字人仍暂停，见下方）

## 刻意不做（Phase 0–1）

- ❌ 三平台自动发布（API 风控）
- ❌ 数字人（资产保留备查，详见 DECISIONS Q7/Q8；真人出镜已于 2026-06-20 解锁）
- ❌ 自研声音克隆
- ❌ 爬商品/电商详情页（淘宝/京东/拼多多/抖店）— Agent-Reach 读公开社交内容（小红书/B 站评论作消费者调研）不算爬虫，是允许的例外
- ❌ CMS / 数据库
