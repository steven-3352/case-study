# 02 · 工作流程 · 4 步 5 拍板点 + 15 步 + 工种

> **顶层视角**(用户看的 4 步 5 拍板点)与 **agent 视角**(15 步)是**同一流程的两个层次**,不冲突。
> agent 跑 15 步,只在 5 个点回来找用户。

---

## 一、顶层工作模式(4 步 5 拍板点 · 用户视角)

**全流程只有 5 个用户拍板点,其余 agent 自主。**

### 4 步框架

| # | 步骤 | agent 自主(子步 · 并行/串行) | 👤 用户拍板 |
|---|------|--------------------------|------------|
| **1** | **选题** | ① 翻 `material/` 真实内容原矿(优先) → ② agent 扩展 N 条候选(3-5)· 每条声明 skin/受众/形态/钩子 | **① 定选题方向 · ② 拍板 1 条定稿** |
| **2** | **前期规划** | ① 洞察包 4 件(选题深挖师+内核提炼师+领域专家+事实校验员)+ 网络调研员 → ② 留存节拍(视频必跑) → ③ 脚本锦标赛 N 版并行 + 停划裁判(anti-mediocrity) → ③′ **视觉创意锦标赛**(矩阵机械出 20 → 独立评审默认毙 → 存活 8-12 出概念图) → **👤 停** → ④ 形式策略会(五维打分)→ ⑤ 视觉语言 + 分镜 + 技术可行性 + 声音方案(agent 并行) → **👤 抽验** | **③ 拍板脚本终稿 + 看图选视觉创意 · ④ 抽验 1 次(不逐个)** |
| **3** | **制作** | ① 出图/出片 → ② TTS + 字幕烧录 + SFX → ③ **gate_check_media / palette 硬门**(fail-closed) → ④ **生成后单镜诊断内环**(`i2v-video-diagnose` · 3 次救不活升级换路线) → ⑤ 三平台适配(抖音 / xhs) → ⑥ `pre_publish_forecast` ≥ B | **无**(除非诊断 3 次仍崩,agent 会请示是否换路线/撤镜) |
| **4** | **交付 + 复盘** | ① agent 生成三平台发布包 → **👤 停** → ② 数据复盘官 48h/7d 数据回填 → ③ `post_publish_retro.md` + 反哺下条 `evolution_overlay.md` | **⑤ 外发**(用户手动发到抖音/xhs) |

### 5 个用户拍板点(不多不少)

1. **选题方向** — 步骤 1 起点,你给方向
2. **选题定稿** — 步骤 1 末,从 agent 扩展的 N 条里拍板 1 条
3. **脚本终稿 + 看图选视觉创意** — 步骤 2 中段,脚本锦标赛 + 视觉创意锦标赛后一次拍完
4. **抽验** — 步骤 2 末,agent 并行产出后你看一眼(不逐个审)
5. **外发** — 步骤 4 中段,你手动发到平台

**除此以外 agent 自主**:洞察包、留存节拍、脚本 N 版竞写、形式打分、视觉语言、分镜、技术可行、声音、制作全流程、gate 门禁、生成后诊断、三平台适配、投后数据回填。

### 闭环规则(不许无限循环)

| 环节 fail | 回退到 | 上限 |
|---|---|---|
| 洞察包不合格(<3 关键信息 / 无原话) | 退记者 / 内核提炼师 | 2 轮 |
| 脚本被停划裁判判平庸 | 退脚本锦标赛加锐度 | 2 轮 |
| **视觉创意全军覆没**(20 个矩阵产出无一存活 / 用户 8-12 张全不想看) | **换矩阵轴**(换跨域源、换反差类型)重跑 20 个,不是在原 20 个里挑矮子 | 2 轮 · 2 轮仍全灭 → 退选题 |
| 形式策略 forecast fail(<B) | 退形式策略官换 route | 2 轮 |
| 单镜生成崩(幻觉/角色/相机/AI 味) | `i2v-video-diagnose` 4 步走 · 只改 1-2 变量 | **3 次救不活升级换实现**(换模型/撤镜/换 B-roll) |
| 三平台适配失败 | 退剪辑 / 平台文案 | 1 轮 |
| 投后 48h 差评(AI 味重/看不懂) | 反哺下条 `evolution_overlay` · 不救本条 | — |

依据:memory `project_user-agent-4step-workflow` · `feedback_autonomous-data-driven` · `feedback_full-autonomy-no-confirm` · `feedback_d05-parallel-agents`

---

## 二、周维度 · 形式差异化 A/B(每周制作套此规则)

项目以周为节奏(D01-D07),每周批量出 7 天素材时,**每天用一种"完全不同"的表现形式**,让形式本身成为可归因的变量。

### "完全不同"的三维判据(至少 2 维不同才算)

| 维度 | 候选来源 |
|---|---|
| **① 渲染家族** | P001 截图 · P002 报纸风 · P004 GSAP · P005 带货 · P006 漫画视频 · P007 漫画图文 · P011 Seedance i2v · grok i2v · 真人出镜 · 真实 B-roll · 其他新集成 |
| **② 视觉语汇**(见 `06_SKILL_TRIGGERS.md`) | cinematic · 3d-cgi · cartoon · comic · 报纸风 · vibe motion · fashion lookbook · food ASMR · 病毒钩子 · 电商 · 房产漫游 · MV · 品牌故事 · SaaS 动效 等 |
| **③ 形态类型** | 演示型 · 知识型 · 带货型 · 出镜型 · 图文轮播 |

**判据:每天在这 3 维中至少 2 维和其他 6 天不同**。伪多样(如"周一 P004 电影感 · 周二 P004 vibe motion"只换视觉语汇不换家族)→ 退回 agent 重排。

### 玩法(2026-07-20 拍板走 B)

**B · 同主题簇不同形** — 一周同 1 大主题下 7 个子选题(如"AI 工具批处理"下拆 Excel/图片/视频/文字/邮件/日程/文件)· 每子选题一种不同形式

- 拒绝 A(同题重复观众疲劳)
- 拒绝 C(变量太多归因失效)

### 周维度 agent 自主操作(不占用户 5 拍板点)

| 时点 | agent 自主 | 👤 用户 |
|---|---|---|
| **周一开工前** | agent 拆主题簇 · 从 `assets/formats/catalog.yaml` + skill 库 · 按 3 维出 7 天形式分配单 · 每日声明 skin/受众 | 抽验分配单 1 次 |
| **周日/次周一** | agent 数据回填 → 形式排名 → 生成 `docs/design/weekly_form_ab_test_W{NN}.md` + 下周 evolution 建议 | 看结论(不改) |

**周归因表**(每周新建 · 模板 `docs/design/weekly_form_ab_test_TEMPLATE.md`):
- 7 天 × 3 维形式分配 · 每日 skin/子选题
- 48h/7d 完播 3s · 完播率 · 收藏率 · 评论率 数据回填
- 周末形式排名 · 保/弃/组合更新 · 反哺下周 `evolution_overlay`

**每周单条仍走 4 步 5 拍板点**——周维度是**跨条约束**,不改变单条流程。

依据:memory `project_weekly-form-ab-test`

---

## 三、15 步标准动作(agent 视角)

| 步 | 动作 | 产出 | 门禁 |
|----|------|------|------|
| 1 | **立项** | 编导确认进 `queue/topics.yaml`;**先翻 `material/` 真实原矿**,`material/` 没料才新脑暴;**须在 `projects/{id}/content.yaml` 声明 `production_tier`**(探索/轻量/全量) | — |
| 2 | **并行调研** | 记者笔记 + 网络调研 | ≥3 URL、≥2 网络原话 |
| 3 | **洞察包** | `insights/` 四件套(topic_brief / core_message / domain_notes / fact_check) + `external_references.md` | 未完成 → **禁止写稿** |
| 4 | **留存设计** | `retention_beat_sheet.md`(每段标 停划/看懂/证据感/情绪/互动) | 视频/强互动图文必跑 |
| 5 | **脚本锦标赛** | **抗平庸锦标赛**:N 个不同角度独立并行竞写 → **停划裁判**判平不平庸(默认毙,除非有别人写不出的东西)→ 逐拍 best-of 合成(只能引用洞察 P0/P1,不得新增卖点) | 无 anti-mediocrity 记录 → reject;三版 stub → reject |
| 6 | **视觉路线** | **先过 03_VISUAL_CREATIVE_GATE.md**(矩阵 20 → 独立评审毙到 8-12 → 概念图 → 用户二元勾选)· 拿到选中的创意后视觉设计才定 P001/P002/新路线 | 视觉创意硬门未过 → **禁定视觉路线、禁进形式策略会** |
| 7 | **形式策略会** | 形式策略官逐镜比较表达方案,声明数据杠杆、理解成本、制作成本、技术风险 → `design/form_strategy.md`(输入是**已选定的视觉创意**,不是从零挑形式) | 少于 3 个候选方案 / 未写不选原因 / 未比近 5 条 → **禁 storyboard** |
| 8 | **视觉语言约束** | 视觉语言策展师从 DESIGN.md / 成熟视觉系统萃取本条 token、组件、Do/Don't、逐镜应用 → `design/design_language.md` | 无色板/字体/组件/禁用项/逐镜应用 → **禁 storyboard 定稿** |
| 9 | **视觉原创门** | `design/visual_originality_gate.md` | 不能证明首屏/中段/CTA 与近作不同 → **禁 storyboard 定稿** |
| 10 | **技术可行性审查** | 使用 Web 3D / GSAP / 复杂 HTML 动效 / 重资产 B-roll 时 → `design/motion_tech_plan.md` | 触发但无审查 → **禁 render** |
| 11 | **分镜 + 画面清单** | 导演 + 摄像对齐节拍表 + 形式策略 + 视觉语言 + B-roll;任何 `template:` 须有 `reuse_reason/visual_difference/risk` | 无节拍表/形式竞争/形式策略/视觉语言/视觉原创门 → **禁分镜** |
| 12 | **声音方案** | `audio_plan.yaml` | 视频必跑;无方案 → **禁 publish** |
| 13 | **剪辑/出片** | 进入对应 `pipeline/` 脚本(见 `05_PIPELINE_CANDIDATES.md`) | 缺 gate_check(pre_render) PASS → 禁 render |
| 14 | **发布包** | 运营三平台文案 + `templates/publish_双平台.md`(视频号 2026-07-05 起停做) | — |
| 15 | **验收** | `pipeline/CHECKLIST.md` + `gate_check.py --phase approve`;不过则退回对应工种 | 不过 = blocked |
| 16 | **投后复盘** | 数据复盘官回填 48h/7d actual → `post_publish_retro` + 下条 `evolution_overlay` | 差评触发反哺下条(不救本条) |

### 大白话分镜硬门(制作开始前必过)

B9 动画导演 + B10 导演摄像完成后,用户会逐 beat **用大白话**告诉你:

> "Beat X:画面里是谁 · 什么景别 · 背景什么 · 动效是什么"

**禁止**写效果名("Ken Burns" / "parallax"),**只写可观察描述**。用户 pass 每个 beat 之后才进入渲染。

---

## 四、强制走 Workflow(2026-07-21 立 · 语音厅测试片 PPT 事故后新增)

**PRD 定稿后进入执行阶段,必须调用 `.claude/workflows/prd_pipeline.js`(`Workflow({scriptPath})`),不得由主 LLM 一人身兼多个工种从需求直接写到实现代码。**

事故链:主 LLM 自己兼任"动画导演"角色,跳过工种协作直接写 ffmpeg 代码,把效果名(Ken Burns/parallax)当成"已实现"的凭证,没有产出任何独立、可核验的"这镜该有什么感觉"陈述,也没有独立验收——渲染结果人物位移不到画面宽 4%,肉眼判断为静止(PPT 感)。详见 `docs/design/WORKFLOW_EXECUTION_LOG.md` 首条记录。

**"测试/demo/轻量"性质不构成跳过工种流程的理由**——`production_tier`(探索/轻量/全量,见 `templates/design/lightweight_production_mode.md`)只影响验收强度(独立评审人数、是否走脚本锦标赛),**不影响该激活哪些角色**。角色是否参与由本文形态对照表决定,不由主 LLM 临场判断"这次可以自己兼"。

### 硬要求

| 阶段 | 硬要求 |
|---|---|
| **开工前** | `prd_pipeline.js` Phase 0 强制读 `docs/design/WORKFLOW_EXECUTION_LOG.md` 最近 5 条的 `carry_forward` |
| **角色执行** | 每个被激活角色必须由独立 `agent()` 调用产出,用 `templates/design/subagent_prd_schema.md` 定义的 schema 结构化返回,核心字段 `perceptual_goal.observable_metric` **禁止写效果名术语**,必须是可观察量级 |
| **独立验收** | 验收者与产出者是不同的 `agent()` 调用,不锦标赛、不打分排名,二元 pass/fail |
| **交付后** | 主 LLM 回读所有子 PRD 推理栏,把这次协作过程本身的错误(不是内容对错)登记进 `docs/design/WORKFLOW_EXECUTION_LOG.md` |

### 模型无关等价

- **Claude Code**:调 `.claude/workflows/prd_pipeline.js`(Workflow tool)
- **Codex / 其他模型**:手动按本节 4 项硬要求执行——每个角色一次独立会话产出结构化 markdown,验收者另开一次会话给 pass/fail;详见 `09_MIGRATION_SOP.md`

---

## 五、工种清单

**分层**:理解层 4(必跑)+ 网络调研层 1(必跑)+ 核心 10(必跑)+ 表达/音画层 5(视频必跑/按需激活)+ 增长复盘层 1(发布后必跑)+ 扩展工种(按形态激活)

### 理解层 4 工种(所有形态必跑 · 洞察包)

| 工种 | 职责 | 输出 |
|------|------|------|
| **选题深挖师** | 拆透选题:谁、场景、烦什么、要什么结果 | `insights/topic_brief.md` |
| **内核提炼师** | 从调研中抽 3–5 条不可删关键信息 + 1 句价值锚 | `insights/core_message.md` |
| **领域专家** | 项目:业务逻辑/流程;带货:品类决策链、竞品差异 | `insights/domain_notes.md` |
| **事实校验员** | 核对数据、SKU、引用;标红不可写 | `insights/fact_check.md` |

**门禁:** 洞察包未完成 → 禁止编剧写稿。

### 网络调研层(所有选题必跑)

| 工种 | 职责 | 输出 |
|------|------|------|
| **网络调研员** | 搜公开内容(行业文/案例/社区),提炼痛点与可引用转述 | `insights/external_references.md` + **`insights/hook_benchmark.md`**(≥2 条同行前 3 秒:人设/镜头/音乐) |

**门禁:** 无 external_references(≥3 URL、≥2 网络原话)/ 无 hook_benchmark → 禁止洞察包定稿。前期宁可多讨论,不可跳过调研。

### 核心 10 工种(所有形态都跑)

| 工种 | 职责 | 输出 |
|------|------|------|
| **编导(总导)** | 选题是否符合主线、四形态拆分 | 选题立项单:钩子 + 形态分工 + 验收标准 |
| **记者** | 真实性、数据、证据链 | 调研笔记:小老板原话、痛点佐证、数据点 |
| **纪录片导演** | 故事弧线、改造前后对比 | 叙事大纲:起承转合 + 情绪锚点 |
| **导演(执行)** | 镜头语言、节奏、信息密度 | 分镜表:画面/口播/字幕/时长(出镜型含机位) |
| **摄像/视觉** | 画面可拍性、构图、可复用素材 | 画面清单:B-roll 列表、截图需求 |
| **编剧** | 钩子、逐字稿、字幕节奏 | **N 角度锦标赛竞写 + 停划裁判 best-of**(`anti_mediocrity_tournament.md`)+ 前 3s 大字钩子 |
| **视觉设计** | 版面、色彩、品牌一致性;**封面 mock 验收** | 视觉路线 + `design/cover_brief.md` + `design/cover_review.md` |
| **视觉语言策展师** | 读取 DESIGN.md / 成熟视觉系统,萃取本条可执行的色板、字体、组件、禁用项;把审美口径落成约束 | `design/design_language.md` |
| **剪辑** | 时长卡控、平台规格 | 剪辑说明:抖音 45-60s / 小红书 ≤60s |
| **运营/增长** | 分发策略、私信转化承接 | 双平台文案 + 评论区埋点 + 私信路径 |

### 表达/音画层 5 工种(视频形态必跑/按需激活)

| 工种 | 职责 | 输出 | 是否双评 |
|------|------|------|------|
| **留存与互动设计师** | 完播节拍、形式切换、互动 CTA | `retention_beat_sheet.md` | 是(≥90 门) |
| **动画导演 / Motion Planner** | 判定风格(WaytoAGI / 七七 / Vibe Motion / 混合),输出**逐秒分镜**(9 字段:时间/旁白/内容类型/画面主体/动画动作/镜头运动/屏幕文字/素材需求/推荐实现方式/设计目的),每 2-4 秒必须有明确视觉变化 | `design/motion_storyboard.md` | **否(单跑 · 2026-07-04 起)** |
| **形式策略官 / 视觉策略官** | 在脚本期比较每个关键镜头的多种表达方式,按数据杠杆选择实拍、2D UI、GSAP、Three/Web 3D、截图或字幕 | `design/form_strategy.md` | 是(≥90 门) |
| **动效技术导演 / Web 3D 技术导演** | 对高级动效、GSAP、Three/Web 3D、HTML 截帧做可行性、资产、性能、导出风险审查;接住动画导演的逐秒分镜,拆成 Remotion / Manim / Three.js 组件任务清单 | `design/motion_tech_plan.md` | 是(≥90 门) |
| **声音设计师** | 配音、BGM 情绪、字幕方案 | `audio_plan.yaml` | 是(≥90 门) |

**门禁:**
- 无《视觉创意硬门》产出(20→8-12 概念图 + 用户勾选)→ **禁定视觉路线、禁进形式策略会**(fail-closed · 铁律 9)
- 无留存节拍表 → 禁出分镜
- 视频形态无 `motion_storyboard.md`(含风格判定 + 逐秒分镜)→ **禁进形式策略会**
- 视频/强互动图文无 `form_strategy` → 禁定 storyboard
- 使用 Web 3D/GSAP/复杂 HTML 动效但无 `motion_tech_plan` → 禁 render
- 无音画方案 → 禁进 publish

**动画导演单跑说明**:2026-07-04 起决定,动画导演走 `draft_self_generated` 直接生效,不做双 agent 90 分互评。原因:本岗是"翻译层"(把已定的脚本 + 留存节拍翻译成逐秒画面),错了下游形式策略官/动效技术导演/声音设计师会拦,无需自建打分门。详见 `decisions/DECISIONS.md` Q11。

### 增长复盘层 1 工种(发布后必跑)

| 工种 | 职责 | 输出 |
|------|------|------|
| **数据复盘官 / 增长复盘官** | 48h/7d 对比 forecast 与 actual,判定问题来自选题、钩子、脚本、形式、CTA、平台文案或发布时间,并反哺下条 | `design/post_publish_retro.md` + `evolution_overlay.md` |

### 带货扩展 4 工种(带货型选题激活)

| 工种 | 职责 | 输出 |
|------|------|------|
| **合规审核** | 广告法、绝对化用语、医美/食品/化妆品红线、平台社区规则 | 合规清单 + 改写建议(红区逐句标注) |
| **选品/商品分析师** | 商品 SKU 拆解、卖点、价位、目标人群、竞品对照 | 选品卡 |
| **消费者声音研究员** | 走 Agent-Reach 挖小红书/B 站真实槽点和决策路径 | 消费者声音报告:高频痛点 + 争议词 + 原话引用 5-10 条 |
| **销售脚本师** | 卖货话术、痛点放大、对比、限时福利、口播 CTA | 卖货逐字稿(与"编剧"叙事区分) |

### 出镜扩展 2 工种(出镜型选题激活,可与带货型叠加)

| 工种 | 职责 | 输出 |
|------|------|------|
| **演员/出镜表演指导** | 真人出镜:口语化重写、表情/手势/眼神、节奏、机位建议 | 表演说明:情绪点 + 机位号 + 默背要点 |
| **造型/服装/场景** | 穿搭、布景、品牌一致性、灯光色温 | 拍摄清单:服装 / 道具 / 场景 / 灯光 |

### `active_roles` 用户拍板(2026-06 起)

每条选题开工前,agent 列**候选清单**(名称·职能·作用·必选/建议/可选)让用户勾选;scorecard 双评必新 session。依据:memory `feedback_user-picks-active-agents`。

---

## 六、形态对照

不是每条选题都跑全扩展工种。按形态激活:

| 形态 | 激活工种 | 典型选题 |
|------|----------|-----------|
| **演示型**(默认) | 理解 4 + 核心 10 + 表达/音画 5(视频)+ 增长复盘 1(发布后) | AI 改造小老板系统、案例复盘 |
| **知识型** | 理解 4 + 核心 10 + 表达/音画 5(视频)+ 增长复盘 1 | 拆解、方法论、教程 |
| **带货型** | 理解 4 + 核心 10 + 表达/音画 5 + 带货 4 + 增长复盘 1 | 商品种草、对比测评 |
| **出镜型**(可叠加) | 当前形态 + 出镜 2 | 任何形态切真人出镜版本 |
| **图文轮播** | 理解 4 + 核心 10(无声音设计师;图内大字替代字幕) | 6–8 张小红书轮播 |

---

## 七、生产模式(轻量 / 全量 / 探索 · 2026-06-26 固化)

**单条 ≤60s 视频/轮播默认走「轻量模式」**,详规:`templates/design/lightweight_production_mode.md`。

- **轻量只砍重复功,不砍质量门**:两道门 fail-closed、36 张 scorecard 双人独立 ≥90、注意力硬门、真实性红线、音画三件套——一个不少
- **精简点**:
  1. 同形态 fork 已有 `dNN_` 模板不从零搭
  2. 第 2 轮互评只重评上轮 <90 的工种(best-of-2),不全员重跑
  3. 默认 1 轮、挑出硬伤才开第 2 轮,最多 2 轮取最好往下继续
  4. 洞察/文档可串行直写,只有渲染/独立互评/真联网调研才派 agent
  5. 需用户拍板的决策攒成一次问
- **升回全量**:带货 / 出镜 / 形式 A/B 周 / 投后要求重做 / 新形态首条(无模板)/ 选题强争议 / 用户点名

**production_tier 只影响验收强度,不减角色数量。** 强制走 workflow(§四)不受本节影响。

依据:memory `feedback_delta-docs-only`

---

## 八、生产效率硬门(所有视频强制 · 2026-07-19)

**效率问题必须通过顺序和自动门禁解决,不得靠操作者记住教训。** 完整案例见 `docs/postmortems/2026-W30-D01-D02-production-latency.md`。

1. **Stage 0 evidence spike** — 凡核心卖点可实验验证,先做最小真实 A/B,保存输入/输出/模型/参数/时间/哈希和 claim boundary。命题未成立,禁止写完整脚本、分镜或启动付费生产
2. **审核覆盖矩阵先于派工** — 先列 `角色 × content_version × form_version × Phase`,再派独立 reviewer;多任务不等于覆盖完整
3. **TTS capability dry-run** — 每个 provider/voice/emotion 组合先生成 5–10s 小样。生产配置必须 `strict_provider: true`,供应商失败**不得静默换音色**继续
4. **真实 timing 驱动动画** — 先生成最终 VO timing,再生成 runtime storyboard;名义脚本时长不得作为渲染时长。每镜做 1.0×/1.5× 压力测试
5. **并行产物隔离** — 所有 frame/audio/cache/concat 临时路径必须含 `content_id`;逐场景路径还须含 `scene_id`,禁跨项目共享可写目录
6. **机器 QC 先于 Phase B** — 终片先过规格、黑帧、静音、字幕/音轨和 `freezedetect`。连续像素冻结 >4.00s 直接 fail
7. **评审绑定终片字节** — Phase B 输入必须记录 canonical MP4 SHA-256;成片变化即自动作废旧 Phase B scorecard 和 forecast
8. **增量构建优先** — 场景模板、data、duration、共享资源未变时复用帧缓存;小改不得默认全片重渲。缓存未实现的 pipeline 记为 P0 技术债

### D05 加速 · Agent 并行化

洞察 4 件 / 设计 3 件 / TTS·UI·broll 三条同批次 tool_use 并行 · D04 2h45min 教训 · 目标 60min。

**独立 subagent 调用规范:**
- 每个工种独立 `Agent()` 调用(Claude Code)/ 每角色独立会话(Codex)
- 主 LLM 不主动兼任任何角色(§四强制走 Workflow)
- 需要并行的工种(如洞察 4 件、设计 3 件)一批次并行发起

依据:memory `feedback_d05-parallel-agents` · `feedback_delta-docs-only`

---

## 九、周批发布流程

单选题走 §三;**周批**叠加讨论室与 gate(**禁止直接 render**):

```
立项(week.yaml / topics_content.yaml)
  → 讨论室 room/ + discussion.md
  → scorecard Phase A(每工种 ≥2 人、≥90 分)
  → gate_check.py --phase approve(内容门)
  → render / week_build.py --render
  → cover_review pass + pre_publish_forecast
  → scorecard Phase B + gate_check 形式门
  → 人工发布 → fetch_platform_metrics → evolution_apply
```

`--force` 须登记 `docs/design/GATE_BYPASS_LOG.md`,**禁止外发**。

### 命令

```bash
python3 pipeline/week_room.py                        # 展开讨论室产物
python3 pipeline/gate_check.py --all --phase approve # 铁律 fail-closed
python3 pipeline/evolution_apply.py --week publish/2026-W26   # 投后
python3 pipeline/fetch_platform_metrics.py --login douyin     # 首次扫码
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04 # 拉账号数据
python3 pipeline/evolution_apply.py --id W26D05 --check       # 下条开工前
python3 pipeline/week_build.py                       # 仅 approved
python3 pipeline/week_build.py --render
```

---

## 十、五层架构(参考)

```
Layer 0  你           定选题 + 方向(queue/topics.yaml)
Layer 1  选题引擎      读 metrics + 规则推荐选题(Phase 2+)
Layer 2  多 Agent 编排  工种并行 → 脚本/分镜/合规/文案
Layer 3  生产流水线     脚本 → 画面 → 配音 → 拼接 → 导出
Layer 4  发布采集       人工发布 → 48h/7d 指标
Layer 5  反馈修正       rules.yaml → 周报 → 下批选题/标准进化
```

---

## Source Map

- 原 `CLAUDE.md §顶层工作模式`(4 步 5 拍板点)
- 原 `CLAUDE.md §核心工作流程`(15 步 + 强制 Workflow + 工种清单 + 形态对照 + 生产模式 + 生产效率顺序)
- 原 `CLAUDE.md §周维度形式差异化 A/B`
- 原 `docs/SYSTEM.md §2`(全部 2.1 - 2.7)
- 原 `.cursor/rules/content-prep-multi-agent.mdc` 全文
- 原 memory:`feedback_multi-role-collab` · `feedback_autonomous-data-driven` · `feedback_full-autonomy-no-confirm` · `feedback_user-picks-active-agents` · `project_user-agent-4step-workflow` · `project_weekly-form-ab-test` · `feedback_d05-parallel-agents` · `feedback_delta-docs-only` · `feedback_dual-platform-only`
