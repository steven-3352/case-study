# CLAUDE.md — AI 内容自动化生产引擎 · Claude Code 特定执行细则

> **首读：** [docs/SYSTEM.md](docs/SYSTEM.md)（§1.0 北极星 · 宗旨 · 工作方式 · 铁律 · 能力全景 · 文档维护）
>
> 本文：Claude Code **特定执行细则**（工种、15 步、环境、反例）。与 SYSTEM 同步维护，勿在两处写不同规则。
>
> **其他模型/agent（Codex / Aider / Cline / Cursor / 其他）：** 首读 [AGENTS.md](AGENTS.md) 拿到跨模型铁律 0 + 分工指路；工种/15 步/反例同样适用本文。

## 项目概览（摘要）

- **引擎：** `queue/topics.yaml` 选题 → 多 Agent 编排 → `pipeline/` 出片 → `publish/` 发布包
- **内容皮肤：** **按选题激活**（2026-07-04 起取消固定皮肤；受众开放到「任何对 AI 工具/AI 应用感兴趣者」；每条选题在 `insights/topic_brief.md` 的 `skin:` 段声明自己的受众/人设锚/话术方向）
- **辩论锁定：** `docs/DECISIONS.md` · **无标准内容模板：** `templates/README.md`

## 环境配置

**首次接手项目 · 5 步初始化**(按操作系统区分):

### 1. Python 3.9+

```bash
# macOS(自带 python3 · 或用 brew install python@3.11)
python3 --version   # 应 ≥ 3.9

# Linux(Ubuntu/Debian)
sudo apt install python3.11 python3.11-venv   # 或 3.9+ 任一

# Windows
# 从 https://www.python.org/downloads/ 下 3.11.x · 装时勾 "Add to PATH"
```

### 2. 虚拟环境 + Python 依赖(强烈建议隔离)

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Windows(PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Post-install(playwright 装浏览器 · 所有系统)

```bash
playwright install chromium
```

### 4. 系统依赖(不通过 pip · 按 OS 装)

| 依赖 | 用途 | macOS | Linux(Debian/Ubuntu) | Windows |
|---|---|---|---|---|
| **ffmpeg**(基础版) | 音视频合成 | `brew install ffmpeg` | `sudo apt install ffmpeg` | 从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下 · 加 PATH |
| **ffmpeg-full**(含 libass) | 字幕烧录必需(见 [feedback_pipeline-burn-subs](feedback_pipeline-burn-subs.md)) | `brew install ffmpeg-full` · 路径 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` | apt 自带 ffmpeg 通常已含 libass | gyan.dev 的 "full" build 已含 |
| **Google Chrome** | P001 pipeline HTML 截图渲染 | 官网下载 | apt install google-chrome-stable | 官网下载 |
| **git** | 版本控制 | 系统自带或 `brew install git` | apt install git | Git for Windows |
| **剪映**(可选) | 人肉后剪辅助 | 仅 macOS · App Store 下 | ❌ 无 Linux 版 | 有 Windows 版但项目未验证 |

### 5. 复制 .env 模板填 API keys

```bash
cp .env.example .env   # macOS/Linux
copy .env.example .env # Windows PowerShell
# 然后打开 .env 填入 GPT_IMAGE_API_KEY / TTS_API_KEY / GROK_API_KEY / SEEDANCE_API_KEY 等
```

### 可选:调研工具 · agent-reach

```bash
# 让 Claude 跑: 帮我安装 Agent Reach:https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
# 用途:小红书/B站/Reddit 公开内容调研(消费者声音),不用于商品/电商详情爬取
```

**验证初始化成功:**
```bash
python3 -c "import openai, PIL, dotenv, edge_tts, playwright, pydantic, requests, yaml; print('OK')"
```


## Git 与分支

- **唯一工作分支：`main`** — 日常开发、提交、推送均在 `main` 上完成。
- 不创建日期分支或长期 feature 分支；小改动直接 commit，大改动可在本地 short-lived 分支做完后 **merge 回 `main` 并删除**。
- 克隆后默认：`git checkout main && git pull origin main`

## 统一画布规格

- 全局 9:16 → 1080×1920（图文 + 视频统一）
- 常量定义：`pipeline/screen_dims.py`（CANVAS_W/H, VIDEO_W/H, IPHONE_W/H）

## 候选实现清单（无默认顺序 · 每次分镜必查完整版）

> **本表只列常用入口，完整版看 `docs/SYSTEM.md §4.2 候选实现清单`。**
> ⚠️ **禁止把本表任一条当"默认路线"**——每一镜必须按 SYSTEM §4.2 五维打分；出现"就走 P004 吧"这类念头立即回 SYSTEM §4.2 校对。

### 原生 pipeline（`pipeline/`）

| 候选之一 | 脚本 | 用途 |
|------|------|------|
| P001 真实截图风 | `pipeline/render_p001.py --all` | 仿真 B-roll + 三平台视频/图文 |
| P001 仿真素材 | `pipeline/gen_evidence.py` | Chrome 渲 HTML 出 9:16 满铺帧 |
| P002 报纸风出图 | `pipeline/p002_carousel_gen.py` | GPT-image-2 整版报纸风轮播 |
| P004 HTML+GSAP 视频 | `pipeline/p004_video/build.py` | HTML+GSAP 渲染场景 → PNG → mp4 + VO + BGM + 字幕 |
| P005/P006/P007 | `pipeline/p005_belt_video/` 等 | 带货 / 漫画视频 / 漫画图文 |
| 真实 B-roll | `pipeline/p004_video/fetch_broll.py` | 拉 Pexels CC0 免费商用素材 |
| TTS 配音 | `pipeline/tts/gen_speech.py --script <path>` | `config.yaml` provider: edge / minimax / volcengine |
| 调研工具 | `agent-reach`(独立 CLI) | 小红书/B站/Reddit 公开内容拉取(消费者声音研究员用) |

### 外部制作插件（`integrations/`）· 与原生 pipeline 同级候选

| 候选之一 | 位置 | 用途 | 门禁 |
|------|------|------|------|
| **OpenMontage** | `integrations/openmontage/` | 视频合成 runtime（Remotion / HyperFrames / FFmpeg / undecided） | **每条必跑** `design/openmontage_brief.md` 判断 enabled/disabled/blocked，未跑不得进 storyboard |
| Grok video | `integrations/openmontage/openmontage.env.example` · `grok-imagine-video` | 视频生成素材候选 | 走 OpenMontage brief |
| GPT-image-2 | 直接 API | 报纸风外，也可用于任意需静态生成的画面 | 走 form_competition 打分 |

**候选池完整性铁律：** 3 个方案不得同家族（不能都是 P001 变体或都是 P004 变体）；发现候选被"默认习惯"排除立即打断，回 SYSTEM §4.2 重列。

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

## 顶层工作模式(2026-07-20 立 · 用户与 agent 4 步分工)

**用户视角的宏观流程 4 步 · 每步内嵌子步 · 全流程只有 5 个用户拍板点,其余 agent 自主。**
本节是"外壳",内嵌详细执行参考下一节 `核心工作流程:新选题多工种协作模式`(agent 视角的 15 步)。

### 4 步框架

| # | 步骤 | agent 自主(子步 · 并行/串行) | 👤 用户拍板 |
|---|------|--------------------------|------------|
| **1** | **选题** | ① 翻 `material/` 真实内容原矿(优先) → ② agent 扩展 N 条候选(3-5)· 每条声明 skin/受众/形态/钩子 | **① 定选题方向 · ② 拍板 1 条定稿** |
| **2** | **前期规划** | ① 洞察包 4 件(选题深挖师+内核提炼师+领域专家+事实校验员)+ 网络调研员 → ② 留存节拍(视频必跑) → ③ 脚本锦标赛 N 版并行 + 停划裁判(anti-mediocrity) → **👤 停** → ④ 形式策略会(五维打分)→ ⑤ 视觉语言 + 分镜 + 技术可行性 + 声音方案(agent 并行) → **👤 抽验** | **③ 拍板脚本终稿 + 形态大方向 · ④ 抽验 1 次(不逐个)** |
| **3** | **制作** | ① 出图/出片 → ② TTS + 字幕烧录 + SFX → ③ **gate_check_media / palette 硬门**(fail-closed) → ④ **生成后单镜诊断内环**(`i2v-video-diagnose` · 3 次救不活升级换路线) → ⑤ 三平台适配(抖音 / xhs) → ⑥ `pre_publish_forecast` ≥ B | **无**(除非诊断 3 次仍崩,agent 会请示是否换路线/撤镜) |
| **4** | **交付 + 复盘** | ① agent 生成三平台发布包 → **👤 停** → ② 数据复盘官 48h/7d 数据回填 → ③ `post_publish_retro.md` + 反哺下条 `evolution_overlay.md` | **⑤ 外发**(用户手动发到抖音/xhs) |

### 5 个用户拍板点(不多不少)

1. **选题方向** — 步骤 1 起点,你给方向
2. **选题定稿** — 步骤 1 末,从 agent 扩展的 N 条里拍板 1 条
3. **脚本终稿 + 形态大方向** — 步骤 2 中段,锦标赛后拍板
4. **抽验** — 步骤 2 末,agent 并行产出后你看一眼(不逐个审)
5. **外发** — 步骤 4 中段,你手动发到平台

**除此以外 agent 自主**:洞察包、留存节拍、脚本 N 版竞写、形式打分、视觉语言、分镜、技术可行、声音、制作全流程、gate 门禁、生成后诊断、三平台适配、投后数据回填。

### 闭环规则(不许无限循环)

| 环节 fail | 回退到 | 上限 |
|---|---|---|
| 洞察包不合格(<3 关键信息 / 无原话) | 退记者 / 内核提炼师 | 2 轮 |
| 脚本被停划裁判判平庸 | 退脚本锦标赛加锐度 | 2 轮 |
| 形式策略 forecast fail(<B) | 退形式策略官换 route | 2 轮 |
| 单镜生成崩(幻觉/角色/相机/AI 味) | `i2v-video-diagnose` 4 步走 · 只改 1-2 变量 | **3 次救不活升级换实现**(换模型/撤镜/换 B-roll) |
| 三平台适配失败 | 退剪辑 / 平台文案 | 1 轮 |
| 投后 48h 差评(AI 味重/看不懂) | 反哺下条 `evolution_overlay` · 不救本条 | — |

### 与其他章节的关系

- 本节 = **用户看的顶层**(4 步 · 5 拍板点)
- 下一节 `新选题多工种协作模式` = **agent 看的实操**(15 步 · 22 工种)
- 两节**不冲突,是同一流程的两个视角** — agent 跑 15 步,只在 5 个点回来找用户
- 违反本节铁律(如让用户拍 5 个以上点、跳过闭环上限)→ 违反 [feedback_autonomous-data-driven](feedback_autonomous-data-driven.md) + [feedback_d05-parallel-agents](feedback_d05-parallel-agents.md)

### 周维度 · 形式差异化 A/B(2026-07-20 立 · 每周制作套此规则)

项目以周为节奏(D01-D07),每周批量出 7 天素材时,**每天用一种"完全不同"的表现形式**,让形式本身成为可归因的变量,数据回填后学习哪种更受欢迎。

**"完全不同"的三维判据(至少 2 维不同才算,防伪多样):**

| 维度 | 候选来源 |
|---|---|
| **① 渲染家族** | P001 截图 · P002 报纸风 · P004 GSAP · P005 带货 · P006 漫画视频 · P007 漫画图文 · P011 Seedance i2v · grok i2v · 真人出镜 · 真实 B-roll · 其他新集成 |
| **② 视觉语汇**(见 57 skill) | cinematic · 3d-cgi · cartoon · comic · 报纸风 · vibe motion · fashion lookbook · food ASMR · 病毒钩子 · 电商 · 房产漫游 · MV · 品牌故事 · SaaS 动效 等 |
| **③ 形态类型** | 演示型 · 知识型 · 带货型 · 出镜型 · 图文轮播 |

**判据:每天在这 3 维中至少 2 维和其他 6 天不同**。伪多样(如"周一 P004 电影感 · 周二 P004 vibe motion"只换视觉语汇不换家族)→ 退回 agent 重排。

**玩法(2026-07-20 拍板走 B):**
- **B · 同主题簇不同形** — 一周同 1 大主题下 7 个子选题(如"AI 工具批处理"下拆 Excel/图片/视频/文字/邮件/日程/文件)· 每子选题一种不同形式
- 拒绝 A(同题重复观众疲劳)· 拒绝 C(变量太多归因失效)

**周维度多的 2 个 agent 自主操作(不占用户 5 拍板点):**

| 时点 | agent 自主 | 👤 用户 |
|---|---|---|
| **周一开工前** | agent 拆主题簇 · 从 `assets/formats/catalog.yaml` + 57 skill 库 · 按 3 维出 7 天形式分配单 · 每日声明 skin/受众 | 抽验分配单 1 次(如需调整) |
| **周日/次周一** | agent 数据回填 → 形式排名 → 生成 `docs/design/weekly_form_ab_test_W{NN}.md` + 下周 evolution 建议 | 看结论(不改) |

**周归因表**(每周新建 · 模板 `docs/design/weekly_form_ab_test_TEMPLATE.md`):
- 7 天 × 3 维形式分配 · 每日 skin/子选题
- 48h/7d 完播 3s · 完播率 · 收藏率 · 评论率 数据回填
- 周末形式排名 · 保/弃/组合更新 · 反哺下周 `evolution_overlay`

**每周单条仍走 4 步 5 拍板点**——周维度是**跨条约束**,不改变单条流程。

---

## 核心工作流程：新选题多工种协作模式

每次出现新选题（`queue/topics.yaml` 新增、口头抛一个场景、或给某项目做内容落地），**必须**先按多工种协作跑一遍，不能直跳 prompt 写作或剪辑。

> 本节即引擎的 **多 Agent 专业化编排层**（对应 BLUEPRINT Layer 2）：采料与各工种产出在此完成，再汇入 `pipeline/` 流水线出片。

### 强制走 Workflow（2026-07-21 立 · 语音厅测试片 PPT 事故后新增）

**PRD 定稿后进入执行阶段，必须调用 `.claude/workflows/prd_pipeline.js`（`Workflow({scriptPath})`），不得由主 LLM 一人身兼多个工种从需求直接写到实现代码。**

事故链：主 LLM 自己兼任"动画导演"角色，跳过工种协作直接写 ffmpeg 代码，把效果名（Ken Burns/parallax）当成"已实现"的凭证，没有产出任何独立、可核验的"这镜该有什么感觉"陈述，也没有独立验收——渲染结果人物位移不到画面宽 4%，肉眼判断为静止（PPT 感）。详见 `docs/design/WORKFLOW_EXECUTION_LOG.md` 首条记录。

**"测试/demo/轻量"性质不构成跳过工种流程的理由**——`production_tier`（探索/轻量/全量，见 `templates/design/lightweight_production_mode.md`）只影响验收强度（独立评审人数、是否走脚本锦标赛），**不影响该激活哪些角色**。角色是否参与由 CLAUDE.md 形态对照表决定，不由主 LLM 临场判断"这次可以自己兼"。

- **开工前**：`prd_pipeline.js` Phase 0 强制读 `docs/design/WORKFLOW_EXECUTION_LOG.md` 最近 5 条的 `carry_forward`
- **角色执行**：每个被激活角色必须由独立 `agent()` 调用产出，用 `templates/design/subagent_prd_schema.md` 定义的 schema 结构化返回，核心字段 `perceptual_goal.observable_metric` 禁止写效果名术语，必须是可观察量级
- **独立验收**：验收者与产出者是不同的 `agent()` 调用，不锦标赛、不打分排名，二元 pass/fail
- **交付后**：主 LLM 回读所有子 PRD 推理栏，把这次协作过程本身的错误（不是内容对错）登记进 `docs/design/WORKFLOW_EXECUTION_LOG.md`

### 工种清单

> **理解层 4**（所有形态必跑）+ **核心 10** + **表达/音画层 4**（视频必跑/按需激活）+ **增长复盘层 1** + 扩展工种（按形态激活）

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

#### 核心 10 工种（所有形态都跑）

| 工种 | 职责 | 输出 |
|------|------|------|
| **编导（总导）** | 选题是否符合主线、四形态拆分 | 选题立项单：钩子 + 形态分工 + 验收标准 |
| **记者** | 真实性、数据、证据链 | 调研笔记：小老板原话、痛点佐证、数据点 |
| **纪录片导演** | 故事弧线、改造前后对比 | 叙事大纲：起承转合 + 情绪锚点 |
| **导演（执行）** | 镜头语言、节奏、信息密度 | 分镜表：画面/口播/字幕/时长（出镜型含机位） |
| **摄像/视觉** | 画面可拍性、构图、可复用素材 | 画面清单：B-roll 列表、截图需求 |
| **编剧** | 钩子、逐字稿、字幕节奏 | N 角度锦标赛竞写 + 停划裁判 best-of（`anti_mediocrity_tournament.md`）+ 前 3s 大字钩子 |
| **视觉设计** | 版面、色彩、品牌一致性；**封面 mock 验收** | 视觉路线 + `design/cover_brief.md` + `design/cover_review.md` |
| **视觉语言策展师** | 读取 DESIGN.md / 成熟视觉系统，萃取本条可执行的色板、字体、组件、禁用项；把审美口径落成约束 | `design/design_language.md` |
| **剪辑** | 时长卡控、三平台规格 | 剪辑说明：抖音 45-60s / 小红书 ≤60s / 视频号 60-90s |
| **运营/增长** | 分发策略、私信转化承接 | 三平台文案 + 评论区埋点 + 私信路径 |

#### 表达/音画层 5 工种（视频形态必跑/按需激活）

| 工种 | 职责 | 输出 | 是否双评 |
|------|------|------|------|
| **留存与互动设计师** | 完播节拍、形式切换、互动 CTA | `retention_beat_sheet.md` | 是（≥90 门） |
| **动画导演 / Motion Planner** 🆕 | 判定风格（WaytoAGI / 七七 / Vibe Motion / 混合），输出**逐秒分镜**（9 字段：时间/旁白/内容类型/画面主体/动画动作/镜头运动/屏幕文字/素材需求/推荐实现方式/设计目的），每 2-4 秒必须有明确视觉变化 | `design/motion_storyboard.md` | **否（单跑 · 2026-07-04 起）** |
| **形式策略官 / 视觉策略官** | 在脚本期比较每个关键镜头的多种表达方式，按数据杠杆选择实拍、2D UI、GSAP、Three/Web 3D、截图或字幕 | `design/form_strategy.md` | 是（≥90 门） |
| **动效技术导演 / Web 3D 技术导演** | 对高级动效、GSAP、Three/Web 3D、HTML 截帧做可行性、资产、性能、导出风险审查；接住动画导演的逐秒分镜，拆成 Remotion / Manim / Three.js 组件任务清单 | `design/motion_tech_plan.md` | 是（≥90 门） |
| **声音设计师** | 配音、BGM 情绪、字幕方案 | `audio_plan.yaml` | 是（≥90 门） |

产出格式见 `templates/retention_beat_sheet.md`、`templates/design/motion_storyboard.md`、`templates/audio_plan.yaml`。

**门禁：**
- 无留存节拍表 → 禁止出分镜
- 视频形态无 `motion_storyboard.md`（含风格判定 + 逐秒分镜）→ **禁止**进入形式策略会
- 视频/强互动图文无 `form_strategy` → 禁止定 storyboard
- 使用 Web 3D/GSAP/复杂 HTML 动效但无 `motion_tech_plan` → 禁止 render
- 无音画方案 → 禁止进 publish

**动画导演单跑说明**：2026-07-04 起决定，动画导演走 draft_self_generated 直接生效，不做双 agent 90 分互评。原因：本岗是"翻译层"（把已定的脚本 + 留存节拍翻译成逐秒画面），错了下游形式策略官/动效技术导演/声音设计师会拦，无需自建打分门。详见 `docs/DECISIONS.md` Q11。

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
| **演示型**（默认） | 理解 4 + 核心 10 + 表达/音画 4（视频）+ 增长复盘 1（发布后） | AI 改造小老板系统、案例复盘 |
| **知识型** | 理解 4 + 核心 10 + 表达/音画 4（视频）+ 增长复盘 1（发布后） | 拆解、方法论、教程 |
| **带货型** | 理解 4 + 核心 10 + 表达/音画 4 + 带货 4 + 增长复盘 1（发布后） | 商品种草、对比测评 |
| **出镜型**（可叠加） | 当前形态 + 出镜 2 | 任何形态切真人出镜版本 |
| **图文轮播** | 理解 4 + 核心 10（无声音设计师；图内大字替代字幕） | 6–8 张小红书轮播 |

### 生产模式（轻量 / 全量 · 2026-06-26 固化）

**单条 ≤60s 视频/轮播默认走「轻量模式」**，详规：`templates/design/lightweight_production_mode.md`。

- **轻量只砍重复功，不砍质量门**：两道门 fail-closed、36 张 scorecard 双人独立 ≥90、注意力硬门、真实性红线、音画三件套——一个不少。
- **精简点**：①同形态 fork 已有 `dNN_` 模板不从零搭；②第 2 轮互评只重评上轮 <90 的工种（best-of-2），不全员重跑；③默认 1 轮、挑出硬伤才开第 2 轮，最多 2 轮取最好往下继续；④洞察/文档可串行直写，只有渲染/独立互评/真联网调研才派 agent；⑤需用户拍板的决策攒成一次问。
- **升回全量**：带货 / 出镜 / 形式 A/B 周 / 投后要求重做 / 新形态首条（无模板）/ 选题强争议 / 用户点名。

### 生产效率顺序（所有视频强制 · 2026-07-19）

- 可实验的核心 claim 先做 Stage 0 evidence spike；结论不成立先换命题，禁止让完整脚本/分镜陪着返工。
- 派 reviewer 前先建 `角色 × content_version × form_version × Phase` 覆盖矩阵；禁止用无计划的追加任务代替完整覆盖。
- 正式 TTS 前先做 provider/voice/emotion 单句小样；生产 `strict_provider: true`，失败即停，不回退其他音色。
- 动画以真实 VO timing 为唯一时基，并做 1.0×/1.5× 镜头压力测试；禁止沿用 40s/43s 等名义时长硬拉终片。
- frame/audio/cache/concat 的可写路径按 `content_id/scene_id` 隔离；并行项目不得共享输出目录。
- Phase B 前先跑机器 QC；冻结 >4.00s、黑帧、异常静音、规格或音轨失败直接返工。
- Phase B scorecard 与 forecast 必须记录终片 SHA-256；MP4 变化即失效并重审。
- 优先逐场景增量重渲。任何小改触发全片渲染，都要登记为 pipeline 技术债，不能当作正常成本。

详见 `docs/SYSTEM.md` §2.4c 与 `docs/postmortems/2026-W30-D01-D02-production-latency.md`。

### 标准动作（v2）

1. **立项** — 编导确认选题进 `queue/topics.yaml`；**立项前先翻 `material/`(真实内容原矿),优先从真材料提炼钩子/弧线,不从零脑暴;`material/` 没料才允许新脑暴**；**同时须在 `projects/{id}/content.yaml` 声明 `production_tier`（探索/轻量/全量，判据见 `templates/design/lightweight_production_mode.md` §2）**，未命中全量触发条件默认写 `explore`
2. **并行深挖** — 记者 + 纪录片导演；带货型加消费者声音 + 选品
3. **洞察包** — 选题深挖师 + 内核提炼师 + 领域专家 + 事实校验员 → `insights/` 四件套
4. **留存设计** — 留存与互动设计师 → `retention_beat_sheet.md`（视频/强互动图文）
5. **脚本锦标赛** — 编剧走**抗平庸锦标赛**：N 个**不同角度**独立并行竞写 → **停划裁判**判"平不平庸"（默认毙，除非有别人写不出的东西）→ 逐拍 best-of 合成（**只能引用洞察卡 P0/P1，不得新增卖点**）。机制与打分表见 `templates/design/anti_mediocrity_tournament.md`（替代易造假的 v0/vA/vB 三版，见 `SCRIPT_REJECT_LOG` 三版造假教训）。**按赌注分级（判据见 `templates/design/lightweight_production_mode.md`）**：边角料 = 探索档默认一稿过；核心脚本 = 命中全量触发条件（带货/出镜/A-B 实验周/投后重做/新形态首条/强争议/用户点名）时才上全锦标赛。
6. **视觉路线** — 视觉设计定 P001 / P002 / 新路线；形式选型见 `assets/formats/catalog.yaml`（≥3 种）
7. **形式策略会** — 形式策略官逐镜比较表达方案，声明数据杠杆、理解成本、制作成本、技术风险 → `design/form_strategy.md`
8. **视觉语言约束** — 视觉语言策展师从 DESIGN.md / 成熟视觉系统中萃取本条 token、组件、Do/Don't 与逐镜应用 → `design/design_language.md`
9. **技术可行性审查** — 使用 Web 3D / GSAP / 复杂 HTML 动效 / 重资产 B-roll 时，动效技术导演给实现路线 → `design/motion_tech_plan.md`
10. **分镜 + 画面清单** — 导演 + 摄像对齐节拍表、形式策略、视觉语言约束与 `assets/broll/catalog.yaml`
11. **声音方案** — 声音设计师 → `audio_plan.yaml`（视频必跑）
12. **剪辑/出图** — 进入对应 `pipeline/` 脚本
13. **发布包** — 运营三平台文案 + `templates/publish_三平台.md`
14. **验收** — `pipeline/CHECKLIST.md`，不过回到对应工种返工
15. **投后复盘** — 数据复盘官回填 48h/7d actual，形成 `post_publish_retro` 与下条 `evolution_overlay`

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

0. **北极星 · Audience-First, Not Pipeline-First** — 做出用户愿意看完、且互动高的内容；三要素：**内容共鸣**（命中真实情绪/场景）+ **强观赏性**（每 2-4s 视觉变化、首屏停划、音画同步 · **声音密度 ≥ 画面变化密度**：每次画面切换/关键金句/CTA 必配 sfx 或 VO 变化，"画面是骨架、声音是灵魂"）+ **强内容**（信息密度真材实料、可复现方法）。视频看 `completion_3s` + `completion_rate` + 评论/收藏；图文看划完 + 收藏/评论。前 3s 须拆同行热门设计停划。

   **反例（工程完成心态 · 全部不算交付达标）**：pipeline 跑通了 / 15 步走完了 / 所有工种产出齐了 / render 无报错 / 发布包三平台文案齐了。**唯一交付判据**：`pre_publish_forecast` ≥ B + 投后观众数据达标。

   详规：`docs/SYSTEM.md` §1.0 · `templates/design/completion_rate_north_star.md`

1. **不看仓库有什么，只看哪条实现更强** — pipeline/场景文件/工种名单不是完成标准；标准是观众会不会停、懂、互动/收藏，以及发布包能否直接外发。实现选型：`docs/SYSTEM.md` §4.2
2. **内容门与形式门分开** — 脚本 90+ 允许 TTS；**形式**（视觉同质、分析师 forecast、CTA 完整）pass 才允许外发。禁止 catalog 拼盘假 approved。
3. **合规分 vs 效果分** — scorecard 纸面 90+ ≠ 能投；外发以像素 + `pre_publish_forecast` 为准。差距 >5 归档 `form_audit`。
4. **各环节专家对最终结果负责** — 禁止「讨论室 approved + render 跑通」但成片与上条同质。
5. **尽一切可能让内容更好** — 宁可多一轮讨论、换 route、重写 storyboard，不可「能出片就行」。
6. **自我进化** — 提高标准 → 多轮测试 → 更新 Rubric + `gate_check` + REJECT_LOG。详规：`templates/design/system_evolution.md`
   - 任何"定稿/最终采用/pass/approved"判断前，先过 `templates/design/pre_work_self_audit_checklist.md`——不靠用户事后抓包发现问题
7. **形式为数据假设服务** — 每个高级视觉镜头必须声明服务 `completion_3s` / `completion_rate` / 理解 / 收藏 / 评论中的哪一项；不能声明数据杠杆的形式，不进入成片。

**核心文档：**
- 完播北极星：`templates/design/completion_rate_north_star.md` · `templates/insights/hook_benchmark.md`
- 铁律：`.cursor/rules/content-outcome-accountability.mdc` · `.cursor/rules/content-prep-multi-agent.mdc`
- 两道门：`templates/design/content_form_split_gates.md`
- 门禁：`pipeline/gate_check.py` · `templates/design/anti_perfunctory_gates.md`（判合格/应付）· `templates/design/anti_mediocrity_tournament.md`（判平庸/抓人 · 停划裁判）· `pipeline/gate_check_media.py`（成片 ffprobe 体检）
- fail 登记：`docs/design/FORM_FAIL_LOG.md` · `docs/design/SCRIPT_REJECT_LOG.md`
- 投后进化：`pipeline/fetch_platform_metrics.py` · `pipeline/evolution_apply.py`

### 反例（不要这么做）

- ❌ 选题一来直接跳进 `p002_carousel_gen.py` 写 prompt
- ❌ 跳过洞察包直接写脚本 → 内容敷衍、卖点虚假
- ❌ 只用编剧视角，跳过记者 → 没真实感
- ❌ 无留存节拍表就出分镜 → 中段拖沓、完播差
- ❌ 发裸片（无 BGM / 无字幕）→ 违反音画硬门槛
- ❌ 跳过视觉设计 → 所有选题都出报纸风
- ❌ 跳过视觉语言策展 → 只说“高级/像产品/更干净”，没有色板、字体层级、组件、禁用项和逐镜应用
- ❌ 全片单一渲染场景或同质画面 → 观赏性差、用户划走
- ❌ 从上一条克隆分镜/画面（模板克隆）→ 见 `SCRIPT_REJECT_LOG.md`
- ❌ 用形式库 catalog 拼盘代替本条分镜设计 → 平台表现分析师退稿
- ❌ 工种产出混成一份不可分辨的文档
- ❌ 带货选题跳过合规审核 → 一夜封号
- ❌ 把「选品分析」塞给编剧/记者糊弄过去 → 不懂 SKU 的卖点提炼是假卖点
- ❌ 脚本 90+ 但形式 catalog 拼盘仍外发 → **平台表现分析师 + 编导** 退稿（D04 v10 教训）
- ❌ 无 `pre_publish_forecast` 或形式 forecast fail 仍 approve
- ❌ 因「P004 是默认视频线」或「Three 更酷」选实现 → 须按 SYSTEM §4.2 对每一镜打分
- ❌ 主 LLM 自己兼任动画导演/摄像等工种直接写实现代码，跳过 `prd_pipeline` Workflow → 效果名（Ken Burns/parallax）被当成"已实现"凭证，实际渲染肉眼不可见（PPT 感）；见 `docs/design/WORKFLOW_EXECUTION_LOG.md` 首条
- ❌ 把「这是测试/demo/轻量档」当成跳过工种协作的理由 → `production_tier` 只降验收强度，不减角色数量

---

## 内容硬约束（来自 DECISIONS.md）

### 留存铁律（音画图文通用 · 2026-06-21）

1. **清晰直给** — 极短时间内，用语音、文字、图像同时抓住眼球；一张图/一屏只传达一个主信息。
2. **图像清晰** — 语义无歧义，画面美观；禁止用抽象图标糊弄可识别的角色/物体（工种用卡通头像，输入输出用具体物件）。
3. **文字可读** — 所有大字完整可见，标题 / 拟声 / CTA 互斥布局，出图后逐张目视检查叠层遮挡。

### 禁霓虹色（2026-06-27 W27D04 教训 · 详 DECISIONS.md Q9）

| 类别 | 禁用 hex/token | 改用 |
|---|---|---|
| Dracula 紫 | `#bd93f9` / `var(--purple)` | — 直接删,不替代 |
| Dracula 粉 | `#ff79c6` / `var(--pink)` | — 直接删,不替代 |
| Dracula 青 | `#8be9fd` / `var(--blue)` | 真截屏自带的系统蓝(iOS/微信),不新造蓝 token |
| 暖红→冷蓝渐变 | `linear-gradient(*,#2a0e0e,#0a0e14)` 一类 | 纯黑 `#000` 或 `#0a0e14` 单色 |
| 偏粉红 | `#ff5252` / `#ff7e7e` | 血红 `#e53935` / `#c0392b` |

**自动兜底:** `python3 pipeline/gate_check_palette.py <png>` 检测主色域 HSL H=240~290(蓝紫)占比 >5% 直接 fail-closed。pre_publish 必过。
**允许:** 真截屏自带的系统色(iOS 蓝、微信绿 #95ec69、淘宝橙等) —— 这是真实痕迹不是色板。

### 禁"AI 味"深色开发者工具风(2026-07-16 T040 教训 · 硬规则,任何时候不得出现)

视觉语言策展师起稿时**默认选"暗色画布 + 克制accent + Linear/Vercel/Cursor 式开发者工具美学"**——这套气质本身已经是生成式 AI/AI 工具类内容的高频默认套路,构成"AI 味"信号,不因为"克制/证据感/开发者质感"这类理由豁免。

| 禁用 | 说明 |
|---|---|
| 自造深色画布作默认起点(如 `#0a0e14`/`#141922` 一类自定深色 canvas) | 不得作为视觉方向的默认选择 |
| Linear/Vercel/Cursor 式"暗色高对比+克制accent"整套气质 | 同上,过度常见、一眼 AI 套壳感 |
| 冷色调(蓝/青灰)为主的背景基底 | 与禁霓虹色表的蓝紫占比铁律同源,但这条更早介入——从"选方向"这一步就排除,不等到出图后靠 gate_check 兜底 |

**改用:** 浅色/白底为主的画布起手,除非画面内容本身**就是真实截屏、且该 app 恰好原生深色 UI**(那是真实使用痕迹,不是设计选择,允许保留)。

**自动兜底:** 视觉语言策展师起稿前列的候选方向必须包含至少一个浅色方案,不得让"暗色"成为唯一默认起点;每条视觉语言约束定稿前自查一遍本表。

### 接手项目第一动作(调用通用服务前)

调 TTS / GPT-image / LLM / 向量等共享服务前 **必做** 三件事:
1. `cat .env.example` —— 看每条服务的中转地址范例,对照 `.env` 看凭证 + URL 是否齐全(尤其云雾中转的 `/minimax` `/openai-v1` 一类前缀,容易漏写)
2. `grep -r "<服务名>" publish/2026-W*/ pipeline/p004_video/_d*_*_config.yaml` —— 找最近一条跑通的姊妹脚本,直接抄它的 config
3. 4xx/5xx 不能直接降级 fallback —— 先核对 URL 拼写,再查凭证,最后才考虑切 provider

### i2v / t2v 视频 prompt 硬门(2026-07-20 立)

**任何**要给视频模型写 prompt(不管是 grok-imagine-video / Seedance 2.0 / Kling / Runway / Luma / Wan / HunyuanVideo / Veo / 未接入的新模型)之前,**必读** `.agents/skills/i2v-video-prompt/SKILL.md` + 按形态挂载 `.agents/skills/video-form-{X}/`(15 个子 skill · 电影/3D/漫画/打斗/日漫/SaaS/电商/360/MV/病毒钩子/品牌/时尚/美食/房产)+ 需要时挂载 `.agents/skills/higgsfield-{X}/`(30 个 · MCSLA 元公式生态 · MIT · 相机/soul/facs/motion/models 等)。

**skill 挂哪个、什么时候挂,由 agent 自主判断**——用户只描述内容/意图/问题,不指名 skill。详见 memory `feedback_agent-auto-mount-skills`(场景 → skill 组合矩阵)。禁问"要不要挂 X",禁让用户点单,禁说"你可以说'用 XX skill'"。

- **触发场景**:分镜 storyboard 出现"video/motion prompt"字段 · 调用 `pipeline/gen_video_frames.py` 或 `pipeline/p011_seedance_i2v/gen_video.py` 或任何 `gen_*_motion.py` · 用户说"生成一段视频/一段 i2v/一段动效"
- **必带落地**:2s 钩子公式 + 精确镜头运动语句(ft/s + 时长)+ 灯光 K 值 + 人物 anchor + NEGATIVES 段(禁蓝紫/禁 AI 味深色/禁 face morphing/温馨场景禁冷渲染)
- **skill 优先级**:i2v-video-prompt(项目铁律)→ video-form-{形态}(形态公式)→ higgsfield-{X}(具体子能力 · 元公式)—— 后者遇 cyberpunk/cool-blue/dark-canvas 一律以本项目铁律替代
- **平台耦合子 skill 忽略**:`higgsfield-apps/workspaces/recall/stack` 假设你在 Higgsfield workspace 工作,项目不订阅 Higgsfield 平台,忽略即可
- **违反后果**:视为反 AI 味 / 禁蓝紫 / 反 template-clone 铁律未过,pre_publish gate fail,登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`

### i2v / t2v 视频生成后诊断硬门(2026-07-20 立)

视频**生成后**(mp4 已下载但你或用户觉得不满意时),**必读** `.agents/skills/i2v-video-diagnose/SKILL.md`。此前项目诊断力量集中在①事前 gate_check 门禁 和 ②投后 evolution_apply/post_publish_retro,**中间"这条镜为什么崩、怎么最小代价救"的层缺失**——本 skill 补齐。

- **触发场景**:视频生成完效果不满意 · 幻觉/伪影/角色崩/动作不自然/AI 味重/相机运动看不出/palette gate fail · 用户说"这段不对/重生/改一下/为什么这么僵"
- **必带落地**:4 步动作(扫描 → 7 类归因 → minimal-edit 只改 1-2 变量 → 登记 VIDEO_ITERATE_LOG)· 3 次救不活升级换路线(换模型/换实现/撤镜)
- **违反后果**:瞎改 prompt 无限迭代 = 违反 D05 加速铁律 · 该 skill 强制"3 次上限 + 只改 1-2 变量"

依据:memory `feedback_pre-node-checklist` · `feedback_no-neon-palette` · `feedback_no-ai-visual-dark-canvas` · `feedback_camera-motion-vs-i2v-ceiling` · `feedback_anti-ai-visual` · `feedback_skill-vs-template-distinction`

- 9:16 → 1080×1920 统一画布（图文 + 视频）
- **视频音画硬门槛**（2026-07-04 起 · BGM 由硬门下调为条件件）：
  - **硬门（必满足）**：配音（VO 全程覆盖，前 6s RMS ≥ -25 dB，禁沉默钉子）+ 字幕叠主画面
  - **条件件（按形态判定）**：BGM
    - 密 VO 演示/知识型（VO 覆盖 ≥85% + 无 3s+ 死区）→ **默认无 BGM**（参考 WaytoAGI / 七七 / 浙大猫学长）
    - 稀疏 VO / 出镜型 / 情感叙事型 / 带货型 → **默认要 BGM**
  - 外发命名：有 BGM → `*_with_bgm.mp4`；无 BGM → `*_no_bgm.mp4` 直接外发（不再是"预览件"）
  - 依据：memory `feedback_dense-vo-no-bgm-default` · `feedback_dense-vo-no-dead-air`
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
