# 09 · 新模型接入 SOP

> **本文是"如何让第三个 AI 编码模型(如 Gemini / Roo / Cline / Cursor 等)接入本项目"的机械 SOP。**
> **目前项目直接支持 Claude Code + Codex(见项目根 `CLAUDE.md` / `AGENTS.md` 薄壳)。第三个模型接入时,按本 SOP 建立自己的薄壳,项目从此支持你的模型。**

---

## 核心理念

**不预先适配所有模型。** 每个新模型接入时,由该模型自己按本 SOP 改造一次,产出:
1. 自己的项目入口薄壳(如 `<YOUR_MODEL>.md` 或该模型约定的入口文件)
2. 5 项模型特有能力的等价映射声明

**规则/铁律/工种/skill 触发表**始终来自 `docs/RULES/`(SSOT),新模型只需要声明"我这边怎么执行 SSOT 里定义的机制"。

---

## Step 1 · 通读 `docs/RULES/`

按 [README.md 必读顺序](README.md#必读顺序) 读完全部 `.md`,**包括 `docs/RULES/memory/` 全部**。

**顺序**:
```
00_NORTH_STAR.md              铁律 0 · Audience-First(北极星 · 最高优先级)
01_IRON_LAWS.md               铁律 1-11(全项目行为规范)
02_WORKFLOW.md                4 步 5 拍板点 + 15 步 + 工种清单 + 强制 Workflow
03_VISUAL_CREATIVE_GATE.md    视觉创意硬门(20→8-12→概念图 · 层级次序)
04_CONTENT_CONSTRAINTS.md     内容硬约束(禁蓝紫 / 禁 AI 味深色 / 密 VO / sfx / gate)
05_PIPELINE_CANDIDATES.md     P001-P011 · integrations · 每镜五维打分
06_SKILL_TRIGGERS.md          skill 触发关键词表(模型无关等价规范)
07_ENVIRONMENT.md             环境配置 · 5 步初始化 · Git
08_ASSETS_LIFECYCLE.md        素材生命周期
09_MIGRATION_SOP.md           本文
decisions/DECISIONS.md        战略辩论锁定(Q1-Q11)
decisions/CONVERSION.md       私信转化路径
memory/                       ~40 条稳定 feedback / project 规则
memory/README.md              memory 分类索引
```

---

## Step 2 · 建立你的加载壳

**在项目根建 `<YOUR_MODEL>.md`**——用该模型约定的入口文件名(如 `.gemini/config.md` / `.roo/rules.md` / 或者就用模型名 `GEMINI.md` / `CLINE.md`)。

### 格式模板(抄 `CLAUDE.md` 或 `AGENTS.md`)

```markdown
# <YOUR_MODEL>.md · <模型名> 加载壳

> **所有项目规则在 `docs/RULES/`(SSOT · 单一事实源)。**
> **本文只声明 <模型名> 特有的加载注册。**
> **规则内容修改一律去 `docs/RULES/`,本文不重复写规则。**

## Step 1 · 必读顺序
按 `docs/RULES/README.md` 必读顺序读完全部,包括 `docs/RULES/memory/`

## Step 2 · <模型名> 特有机制的等价映射
(按下方 Step 3 · 必答 5 项填写)
```

---

## Step 3 · 逐项声明模型特有能力的等价映射

**必答 5 项**——每项写清"你的模型有 → 用什么机制;没有 → 手动做什么等价":

| # | 能力 | Claude Code 现状(参照) | Codex 现状(参照) | 你的模型 |
|---|---|---|---|---|
| **1** | **规则自动加载** | 项目根 `CLAUDE.md` 自动读 | 项目根 `AGENTS.md` 自动读 | 声明你的入口文件名(如 `GEMINI.md` / `.roo/rules.md`) |
| **2** | **memory 持久化** | `~/.claude/projects/.../memory/` 自动注入 | 无内置 memory · **每次开工必读 `docs/RULES/memory/` 全部** | 有 → 声明存哪读哪;无 → 声明每次开工必读 `docs/RULES/memory/` |
| **3** | **Skill 自动挂载** | Skill tool 靠 `.agents/skills/*/SKILL.md` frontmatter 关键词自动匹配 | 无自动挂载 · **开工前查 `06_SKILL_TRIGGERS.md`,匹配用户描述关键词后主动 read** | 有 → 声明触发机制;无 → 声明查 `06_SKILL_TRIGGERS.md` 后主动 read |
| **4** | **Workflow / hooks** | `.claude/workflows/prd_pipeline.js`(Workflow tool)+ `settings.local.json` hooks | 无 · **按 `02_WORKFLOW.md §四 强制走 Workflow` 手动执行 phase 0-2** | 有 → 声明脚本位置;无 → 声明手动跑 `02_WORKFLOW.md §四` checklist |
| **5** | **并行 subagent** | `Agent(subagent_type=...)` 并行调用 | 无并行 · **串行方案 · 每角色一次调用** | 有 → 声明语义;无 → 声明串行方案 · 每角色一次调用 |

### 5 项详细说明

#### 1. 规则自动加载

**问的是**:你的模型有没有"每次会话开始自动读某个 markdown 文件"的机制?

- **Claude Code**:项目根 `CLAUDE.md` 自动加载
- **Codex**:项目根 `AGENTS.md` 自动加载
- **Cursor**:`.cursor/rules/*.mdc` 带 `alwaysApply: true` 会自动加载
- **Gemini CLI / Roo / Cline**:各自约定不同,查文档

**如果你的模型没有自动加载机制**:在你的加载壳文档里明写"用户每次会话开始前须复制本文档全文进 prompt",或在项目 README.md 加一条"接入本模型请先复制 `<YOUR_MODEL>.md`"。

#### 2. memory 持久化

**问的是**:你的模型有没有"会话之间持久记住偏好/反馈/上下文"的机制?

- **Claude Code**:`~/.claude/projects/.../memory/{名字}.md` 自动注入
- **Codex**:无内置 memory · 每次会话独立
- **Cursor**:`.cursor/` 目录 + `notepads` 机制
- **持久 IDE 类**(Continue / Roo):各自有 personal notes / context 机制

**关键动作**:
- **有 memory 机制**:声明写在哪、读在哪。同时**声明"稳定规则仍以 `docs/RULES/memory/` 为准"**,你的私有 memory 只存会话级临时状态。
- **无 memory 机制**:在你的加载壳明写"每次开工必须显式 read `docs/RULES/memory/` 全部"(相当于 Claude memory 自动注入)。

#### 3. Skill 自动挂载

**问的是**:你的模型有没有"根据用户描述文本自动匹配并挂载专业 skill 文档"的机制?

- **Claude Code**:Skill tool + frontmatter 关键词
- **Codex / 其他**:一般没有

**关键动作**:
- **有 skill 挂载机制**:声明触发机制(frontmatter 字段名 / 匹配算法 / 触发时机)。同时**声明"与 `06_SKILL_TRIGGERS.md` 冲突以本表为准"**——skill 挂对靠自动机制,但**权威规范来自本项目 SSOT**。
- **无 skill 挂载机制**:在你的加载壳明写"开工前根据用户描述,在 `06_SKILL_TRIGGERS.md` 匹配触发关键词后,主动 `read` 对应 skill 文件"。**用户不用指名 skill,你自己按本表匹配。**

#### 4. Workflow / hooks

**问的是**:你的模型有没有"在特定生命周期节点强制执行某段代码/检查"的机制?

- **Claude Code**:Workflow tool(`.claude/workflows/*.js`) + hooks(`.claude/settings.local.json`)
- **Codex**:无原生 workflow / hook
- **其他**:各自不同

**关键动作**:
- **有 workflow/hook 机制**:声明脚本位置和触发时机。当前项目的 `.claude/workflows/prd_pipeline.js` **只 Claude Code 能用**;其他模型如果有对应机制,可写一个自己的 workflow 脚本放在 `.<yourmodel>/workflows/`。
- **无 workflow/hook 机制**:在你的加载壳明写"在每个节点开工前**手动跑一遍** `02_WORKFLOW.md §四 强制走 Workflow` checklist"。特别是:
  - 每个被激活角色必须由独立会话/调用产出结构化 markdown
  - 验收者与产出者是不同的会话
  - 主 LLM 不主动兼任任何角色

#### 5. 并行 subagent

**问的是**:你的模型有没有"同一时刻并行调用多个独立子会话/子 agent"的机制?

- **Claude Code**:`Agent(subagent_type=...)` 可同一消息发多个并行
- **Codex**:无原生并行,只能串行
- **其他**:各自不同

**关键动作**:
- **有并行 subagent**:声明语义(如 subagent 类型、并行上限、cost implications)。
- **无并行**:声明**串行方案**——洞察 4 件 / 设计 3 件 / 独立评审 / 讨论室工种,一个一个来。**用户等待时间会更长**,但铁律"独立子 agent 调用"仍必须遵守——**每角色一次独立会话,主 LLM 不兼任**。

---

## Step 4 · 提交 PR

### 必备内容

1. **新加载壳文件**(项目根 `<YOUR_MODEL>.md` 或该模型约定的入口文件)
2. **本文档更新**:在下方"已接入模型注册表"添加一行

### 特殊情况处理

**若发现某铁律在你的模型下语义不成立**(如某模型无法执行"独立子 agent 调用",串行方案有本质区别),**不改主文**——在 `docs/RULES/{冲突章节}.md` 结尾加一节:

```markdown
## 平台注释 · <你的模型名>
- <说明为什么本铁律在你的模型下有特殊语义>
- <你的模型下的等价执行方式>
```

**让下一个人可以直接抄。**

---

## Step 5 · Skill 触发表同步(装新 skill 时)

若新模型接入过程中,发现要装新 skill 到 `.agents/skills/` 下,除装 skill 外**必须同步更新 `06_SKILL_TRIGGERS.md`**:
1. 在合适分类下加一行:触发关键词 + skill 路径 + 与其他 skill 的组合关系
2. 若属新范畴,新增一节
3. 若与项目铁律冲突,加"平台注释"说明

---

## 已接入模型注册表

| 模型 | 加载壳文件 | 入口机制 | memory | skill | workflow | subagent |
|---|---|---|---|---|---|---|
| **Claude Code** | `CLAUDE.md` | 自动加载项目根 | `~/.claude/.../memory/` 自动注入 | Skill tool + frontmatter | Workflow tool `.claude/workflows/` | `Agent(subagent_type=...)` 并行 |
| **Codex** | `AGENTS.md` | 自动加载项目根 | 无(必须显式 read `docs/RULES/memory/`) | 无(必须查 `06_SKILL_TRIGGERS.md` 主动 read) | 无(手动跑 `02_WORKFLOW.md §四` checklist) | 无(串行 · 每角色一次调用) |

---

## 反例(不要这么做)

- ❌ 把新模型的 memory 或规则**写到项目根**(应写到 `docs/RULES/` 或你自己的 memory 目录)
- ❌ 因你的模型没有某能力,就在薄壳里**放宽项目铁律**(应改成手动执行的等价方案,铁律不动)
- ❌ 装新 skill 时**只装文件、不更新 `06_SKILL_TRIGGERS.md`**(下一个人不知道何时触发 = skill 永久沉睡)
- ❌ 在你的加载壳里**复制 docs/RULES/ 内容**(应只写加载注册,规则内容单一来源)
- ❌ **绕过 `docs/RULES/memory/`,直接读 Claude Code 私有 memory**(那不在项目仓库里,你的模型看不到)

---

## Source Map

- 新写
- 参考:`CLAUDE.md`(现有 Claude Code 加载机制)· `AGENTS.md`(现有 Codex 加载机制)
