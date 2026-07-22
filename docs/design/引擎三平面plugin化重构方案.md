# 内容生产引擎 · 三平面 Plugin 化重构方案

> **状态:** 提案(草案),待用户确认起手阶段后执行
> **日期:** 2026-07-22
> **决策前提:** 用户已拍板「skill 为主,项目降为使用者」——引擎抽成独立可分发 plugin,`case-study` 逐步降为该 plugin 的一个私有内容使用者。

---

## 1. Context(为什么做)

### 触发
用户在连续几轮对话里指出项目文档「散落一地、感觉乱」,并明确要:**架构简单统一 · 各司其职 · 不会被绕开 · 以后不同项目不同文档不再重新散落**。

### 调研坐实的三个病灶(四份并行调研结论)
1. **质量标准散落 + 重复定义**:光「质量判断机制」就有 **25 个**,散在 CLAUDE.md / SYSTEM.md / `pipeline/gate_check*.py` / `templates/design/` 十几个模板里。「89分=fail」在 4 个文件各写一遍;「五维打分」拆成 3 处。
2. **流程与质量普遍混写**:绝大多数地方「谁先做」和「怎么算过关」缠在同一句话/同一张表格单元格里(如标准动作第5步一句话里塞了流程+质量判据+内容红线)。全项目只有 `WORKFLOW_EXECUTION_LOG.md` 一处刻意做过分工声明。
3. **已经在漂移**:SYSTEM.md §2.2 标题写「15步」表格实际 17 行;脚本流程早改成锦标赛但 SYSTEM.md 表格还留着废弃的「v0/vA/vB」。证明这套散法会自己坏。

### 目标产出
把引擎重构成**三平面清晰分离**、并打包成**单个可分发 Claude Code Plugin**,别人 `/plugin install` 即可用、无需 clone,后续用版本号持续更新。

---

## 2. 目标架构:三平面

用户定义的三平面(控制器 / 能力 / 质量),各司其职,互不混写:

| 平面 | 职责 | 现状载体 | 重构后载体 |
|---|---|---|---|
| **流程(控制器)** | 只写「谁先做、谁后做、依赖什么」,**不写阈值、不写具体能力** | `.claude/workflows/prd_pipeline.js` 的 ROLE_WAVES + CLAUDE.md 标准动作(两者部分重复且混了质量判据) | plugin 的 `workflows/` + 一份纯流程文档;每处「然后检查X」改成「此处适用 QG-XX 门」的指针 |
| **技能(能力池)** | 出图/视频/TTS/代码动画等可插拔能力 | `.agents/skills/` 57 个 SKILL.md(自建 3 + 外部 54) | plugin 只**打包自有 + 确认 MIT** 的;外部技能改「引用 + 安装清单」由用户自装 |
| **质量标准(验收)** | 判「够不够格」,含「提升3档」元规则 | 25 条散落的门 + gate_check*.py + scorecard/forecast | **一份权威质量登记表(单一真相源)**,每道门一个稳定 ID,其余全部按 ID 引用 |

### 质量平面的核心设计:单一登记表 + 提升3档作表头元规则
这是解决用户「锦标赛 vs 提升3档冲突吗」疑问的关键结构:

- **表头 = 元规则区**:铁律8「门禁是地板不是目标 · 抬高3档」定义**一次**,声明它是评判**任何一道门**时的校准镜(不是独立的门)。
- **表体 = 各道门**:QG-SCORECARD-90 / QG-FORECAST-B / QG-PALETTE-NEON / QG-MEDIA-FREEZE / QG-ANTI-MEDIOCRITY / QG-INSIGHT-3FACTS ... 每条**只定义一次**(判定标准 / 阈值 / 应用对象 / 数字还是主观 / 强制点在哪:gate_check.py 函数 or agent 判断 or 人工)。
- **流程平面、gate_check.py、prd_pipeline.js 全部按 ID 引用**,不再各自复述阈值。

→ 「90分门」「forecast分级」是**具体的门**(表体各定义一次);「提升3档」是**套在每道门之上的校准**(表头定义一次)。三者各就各位,不再互相纠缠,也不再多处重复。

---

## 3. 打包形态:单个 Plugin + Marketplace 分发

官方文档结论(claude-code-guide 调研):

- **形态 = 单个 Plugin**(不是散 skill,skill 无法单独分发;也不是多 plugin,依赖管理复杂)。一个 plugin 可同时装 skills + agents + workflows + docs。
- **分发 = GitHub 直链 `/plugin install <url>` 或私人 marketplace**,版本号管理 + `/plugin update` 持续更新,无需 clone。
- **「通用引擎 + 私有配置」分层**正是官方推荐:plugin 放通用能力,用户项目放私有内容/凭证。

### 待官方确认的不确定点(不当既定事实)
- plugin.json 的 `dependencies` 自动安装、`entrypoint` 字段 —— claude-code-guide 自己标了「需确认官方是否支持」。
- workflow 脚本进 plugin 后的调用入口(直接 Workflow 工具 vs 包一个 orchestrator agent)—— 执行前需实测。

---

## 4. 分发边界(可分发 vs 私有)

### ✅ 进分发包(content-engine-plugin)
```
content-engine-plugin/
├── .claude-plugin/plugin.json          # 新建(分发骨架从零搭)
├── workflows/
│   └── prd_pipeline.js                 # 抽掉本项目专有角色措辞
├── skills/                             # 只放自有 + 确认 MIT
│   ├── i2v-video-prompt/               # 自建,需参数化(剥离本项目铁律为可配置)
│   ├── i2v-video-diagnose/             # 自建,同上
│   ├── (可选) gsap-*/                  # MIT,补 LICENSE 全文后可打包
│   ├── (可选) ai-image-prompts-skill/  # MIT,带 LICENSE,可打包
│   └── (可选) higgsfield/              # 主包 MIT
├── quality/
│   └── quality_registry.md             # 【核心新建】单一质量登记表 + 提升3档表头
├── templates/                          # ~27 个通用方法论模板
│   ├── design/*.md
│   └── insights/*.md
├── skills-manifest.json                # 外部技能「引用+安装来源」清单(video-form/higgsfield-* 由用户自装)
├── docs/
│   ├── PROCESS.md                      # 纯流程文档(15步/波次,无阈值)
│   ├── CAPABILITY_INDEX.md             # 技能能力索引(指向自装的外部 skill)
│   └── README.md
└── LICENSE
```

### 🔒 留在使用者项目(case-study 降级后只剩这些)
- `queue/topics.yaml`(选题库)、`material/`、`publish/`、`projects/`(全部产出/原矿)
- `.env` / `.env.example`(Tonbird 商业主线所在,全部 `*.tonbirds.com` 中转)
- `.claude/settings.local.json`、`config/mcporter.json`(本机配置,给 `.example`)
- `templates/design/performance_data.yaml`、`platform_metrics_import.example.json`(本项目实测数据)
- CLAUDE.md/AGENTS.md 的**项目专属段落**(环境配置、tonbirds、北极星具体指标、刻意不做、`feedback_*`、P/W 项目号)
- `pipeline/` 下具体项目实例(`p004_video`/`p005_*`/`w30d0x_*`/`assemble_*`)

### 🚨 licensing 硬约束(执行前必须先清)
- **`video-form-*`(15)绝不进包** —— 无 license/来源/author,放进去=法律风险。改为 `skills-manifest.json` 里的「用户自装」条目,但需先查清它们本身能不能合法被引用/来源是哪。
- **`higgsfield-*` 子包(30)** —— 只靠 parent 推定 MIT,子目录无独立 LICENSE。**默认也走「引用+自装」,不直接打包**,除非确认主包 MIT 覆盖子目录。
- **gsap-*(8)** —— MIT 但无随附 LICENSE 全文;若打包需从 `greensock/gsap-skills` 补 LICENSE。
- 结论:**分发包尽量只含自有 + 明确带 LICENSE 的 skill;其余一律「引用+安装清单」**,既合法又轻,还强化了「技能=可插拔」的架构。
- **用户已拍板(2026-07-22):自有 skill 直接打包;别人的 skill 一律「引用 + 用户自己确认安装」,不替用户打包。** → video-form-* / higgsfield-* 子包的授权问题因此转为用户侧,分发包本身不承担。

### 4b. 技能平面封装目标(用户 2026-07-22 指定 · 必做)
四类核心能力现为散落的 `pipeline/` Python 脚本,须封装成自洽、可分发的能力单元(每个 = 一个 SKILL.md + 所包脚本 + 参数化配置 + 剥离本项目路径/env 依赖):

| 能力 | 现有实现 | 封装后能力 skill(暂名) |
|---|---|---|
| **做图** | `pipeline/p002_carousel_gen.py`(GPT-image-2 报纸风)+ 直连 API 通用出图 + `ai-image-prompts-skill` | `cap-image-gen`(provider 可配:GPT-image-2 / 其他) |
| **视频** | `pipeline/p004_video/build.py`(HTML+GSAP)+ `p011_seedance_i2v/gen_video.py`(Seedance)+ grok i2v + `i2v-video-prompt`/`i2v-video-diagnose` skill | `cap-video-gen`(家族可选:GSAP渲染 / i2v模型) |
| **TTS** | `pipeline/tts/gen_speech.py`(provider: edge / minimax / volcengine) | `cap-tts`(provider 可配) |
| **免费素材库** | `pipeline/p004_video/fetch_broll.py`(Pexels CC0) | `cap-stock-footage`(source 可配:Pexels / 其他 CC0 库) |

封装原则:能力 skill 只暴露「输入→输出 + provider/参数」,不含本项目选题/skin/路径;凭证走 env,给 `.example`。这四个属自有能力,**直接打包进分发包**。

---

## 5. 迁移阶段(低风险优先 · 分阶段,每阶段可独立验收)

> 因涉及 537 行 CLAUDE.md / 618 行 SYSTEM.md / 1425 行 gate_check.py + 活跃生产,严禁一次性大爆改。分阶段,每阶段结束项目仍可正常生产。

### Phase 1 — 质量平面单一化(纯新增 + 文档,风险最低,价值最高)
1. 新建 `quality/quality_registry.md`:把 25 条门全迁进去给 ID,表头写「提升3档」元规则。
2. CLAUDE.md / SYSTEM.md / templates 里的**重复阈值定义**改成按 ID 引用(如「见 QG-SCORECARD-90」),消除「89分=fail」四处重复。
3. 顺手修漂移 bug:SYSTEM.md §2.2「15步/17行」对齐、删废弃的「v0/vA/vB」。
- **不改任何代码行为**,gate_check.py 照常跑。

### Phase 2 — 流程平面提纯(把质量判据从流程描述里抽走)
1. CLAUDE.md 标准动作 / prd_pipeline.js 的 prompt 里,把「怎么算过关」替换成「适用 QG-XX 门」的指针,流程只留「谁先做、依赖什么」。
2. 消除 CLAUDE.md 标准动作与 prd_pipeline waves 的重复(定一个为真相源,另一个引用)。

### Phase 3 — 技能平面梳理 + 安装清单
1. 补全 `skills-manifest.json`:所有外部 skill 的来源 URL + license 状态。
2. 查清 video-form-* / higgsfield-* 子包的真实来源与授权(卡住分发的关键)。
3. 自建 skill(i2v-*)参数化:把写死的本项目铁律抽成可配置项。

### Phase 4 — 抽壳成 Plugin(结构搭建)
1. 建 `.claude-plugin/plugin.json` + plugin 目录骨架,把 Phase 1-3 产物按分发边界搬进去。
2. 实测:workflow 进 plugin 的调用入口、外部 skill 自装流程。
3. 本地 `/plugin install` 自测跑通一条完整选题。

### Phase 5 — case-study 降级为使用者
1. 项目内引擎内容替换为「装 plugin + 私有覆盖层」。
2. CLAUDE.md 拆成:通用部分进 plugin,项目部分留下作使用者配置。

### Phase 6 — 发布 + 更新机制
1. 建 marketplace.json,发 GitHub。
2. 版本号 + release 流程,验证 `/plugin update`。

---

## 6. 验证

- **Phase 1-2**:项目照常能跑一条选题到 pre_publish_forecast,gate_check*.py 全绿;人工核对「任一质量标准只在 registry 定义一次」。
- **Phase 4**:在一个干净空目录 `/plugin install` 本地包,能拉起 prd_pipeline 编排、能引用到质量 registry。
- **Phase 5**:case-study 删掉本地引擎副本后,靠装上的 plugin 仍能完整生产。
- **licensing**:分发包内每个打包的 skill 都有可追溯 LICENSE;video-form-*/higgsfield-* 子包若未确认授权,必须只在 manifest 里「引用」而非打包。

---

## 7. 待用户拍板的起手点
- 从 **Phase 1(质量登记表)** 起手最稳(纯新增、立刻解决「散落/重复」主诉、不碰代码);还是要先做别的。
- 分发包名字 / marketplace 归属(个人 GitHub or 组织)。
- video-form-* 的来源用户是否知情(卡分发,可能需要用户提供来源)。
