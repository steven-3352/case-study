# 系统说明 · Agent / 人类首读

> **任何模型接入本仓库，先读本文。** 执行细则见 `CLAUDE.md`；辩论锁定见 `docs/DECISIONS.md`。
>
> 最后同步：**2026-06-21** · 维护规则见 [§7 文档维护](#7-文档维护)

---

## 1. 系统宗旨

### 1.0 北极星（最高优先级 · 一切决策为此服务）

**本系统的最大价值：做出用户愿意看完、且互动高的内容。**

| 载体 | 「看完」 | 「互动高」 |
|------|----------|------------|
| **视频** | `completion_3s` · `completion_rate` · `avg_watch_s` | 评论率 · 收藏率 · 讨论型 CTA 效果 |
| **图文轮播** | 划完全部张 · 停留点不塌 | 收藏动机 · 评论争议点/共鸣点 |

**第二条铁律：所有决定都以北极星为中心。** 工种、pipeline、技术栈、讨论室打分、是否 render、选 GSAP 还是实拍——唯一合法问题是：**会不会让观众多停几秒、多看懂一点、更愿意评一句/收藏？**

| 层次 | 含义 | 与北极星的关系 |
|------|------|----------------|
| **意义** | 用内容证明「烦事能变成能跑的小系统」，等私信转化 | 观众须**先看完、愿意聊** |
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
| **内容皮肤** | 对外讲什么故事、什么人设、什么垂直 | **可换**（当前：小老板烦事 → 能跑的小系统） |

换一批选题 / 行业 / 形态，**同一套引擎仍应跑通**。

### 1.3 当前内容皮肤（账号，非系统边界）

- 不是 AI 教程号，不是经验分享号
- 对外一句：**我用 AI 把小老板每天烦、重复、没人管的事，做成能跑的小系统**
- 转化：**等私信**（正文不导流）· 见 `docs/CONVERSION.md`
- 辩论锁定策略见 `docs/DECISIONS.md`

### 1.4 无标准内容模板

**没有可套用的「标准成片模板」。** 每条内容从洞察包与分镜单独设计；禁止克隆上一条画面、catalog 拼盘交差。用语见 `templates/README.md`。

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

### 2.2 新选题标准流程（11 步 · v2）

| 步 | 动作 | 产出 | 门禁 |
|----|------|------|------|
| 1 | 立项 | 进 `queue/topics.yaml` | — |
| 2 | 并行调研 | 记者笔记 + 网络调研 | ≥3 URL、≥2 网络原话 |
| 3 | **洞察包** | `insights/` 四件套 + external_references | 未完成 → **禁止写稿** |
| 4 | 留存设计 | `retention_beat_sheet.md` | 视频/强互动图文必跑 |
| 5 | 脚本三版 | v0/vA/vB（仅引用洞察 P0/P1） | — |
| 6 | 视觉路线 | 形式词汇 ≥3 种观感；封面 brief | 非套旧渲染场景 |
| 7 | 分镜 + 画面清单 | 对齐节拍表 + B-roll | 无节拍表 → **禁止分镜** |
| 8 | 声音方案 | `audio_plan.yaml` | 视频必跑；无方案 → **禁止 publish** |
| 9 | 流水线出片 | `pipeline/*` | — |
| 10 | 发布包 | 三平台文案 + 成品 | `templates/publish_三平台.md` |
| 11 | 验收 | `pipeline/CHECKLIST.md` + `gate_check.py` | 不过则退回对应工种 |

带货 / 出镜 / 图文轮播在标准流程上有分支 — 见 `CLAUDE.md` 形态对照。

### 2.3 工种组织（Layer 2）

| 层 | 工种 | 何时跑 |
|----|------|--------|
| 理解 4 | 选题深挖、内核提炼、领域专家、事实校验 | **所有形态** |
| 网络调研 | 网络调研员 | **所有选题** |
| 核心 9 | 编导、记者、纪录片导演、导演、摄像、编剧、视觉、剪辑、运营 | **所有形态** |
| 音画 2 | 留存与互动设计、声音设计 | **视频** |
| 带货 4 | 合规、选品、消费者声音、销售脚本 | 带货型 |
| 出镜 2 | 表演指导、造型场景 | 出镜型 |

完整职责表见 `CLAUDE.md` §工种清单。

### 2.4 两道门外发门禁

1. **内容门** — 脚本/洞察过线，才允许 TTS
2. **形式门** — 视觉同质、forecast、CTA 完整；`pre_publish_forecast` pass 才外发

脚本 90+ ≠ 能投。详规：`templates/design/content_form_split_gates.md` · `pipeline/gate_check.py`

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
- 视频 **音画三件套**：配音 + BGM + 字幕；外发默认 `*_with_bgm.mp4`
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

#### 候选实现（举例，非默认顺序）

真实 B-roll · P001 截图/录屏 · HTML+GSAP · Three.js · P002/P007 整图轮播 · 真人出镜（Q8）· `produce.py` 项目演示

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

整条片可混用：chaos 实拍 + 中段 P001 录屏 + 末段 GSAP CTA。**`pipeline/p004` 是分镜里若干镜的渲染器之一，不是「视频默认路线」。**

技术栈细则：`docs/TECH_STACK.md` §画面实现选型。

#### 接到「该用哪种方式？」只问四问

1. 这一镜主意图是停划、看懂还是互动？
2. 真实素材/B-roll 能否更强？（能 → 优先证据，别动效硬撑）
3. 换实现，forecast 里 3s/完播/互动区间会不会上移？
4. 换实现会不会导致赶工烂版？（会 → 用稳管线做好版）

### 4.3 关键产出格式（非成片套路）

| 类型 | 路径 |
|------|------|
| 洞察包 | `templates/insights/` → 复制到 `publish/{id}/insights/` |
| 节拍 / 音画 | `templates/retention_beat_sheet.md` · `templates/audio_plan.yaml` |
| 工种设计室 | `templates/design/*` · `templates/agent_room/*` |
| 发布文案结构 | `templates/publish_三平台.md` |
| 渲染场景（技术壳） | `pipeline/*/templates/*.html` |

---

## 5. 当前状态

| 项 | 值 |
|----|-----|
| 阶段 | **Phase 0–1** — pipeline 已跑通；**W26 周包** + gate/evolution 在实战 |
| 工作分支 | `main` |
| 内容皮肤 | 小老板 + 小系统（获客向） |
| 每日执行 | `docs/TODO.md` |
| 排期 | `docs/SCHEDULE.md` · `docs/PHASE1_CALENDAR.md` |

---

## 6. 文档地图

| 文档 | 读何时 |
|------|--------|
| **本文 `docs/SYSTEM.md`** | 首次接入 / 大改后对齐全貌 |
| **`.cursor/rules/*.mdc`** | Cursor 自动加载铁律（90 分互评、讨论室、结果负责制） |
| `CLAUDE.md` | Agent 执行：工种、11 步、反例、环境 |
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
