# CLAUDE.md · Claude Code 加载壳

> **所有项目规则在 [`docs/RULES/`](docs/RULES/README.md)(SSOT · 单一事实源)。**
> **本文只声明 Claude Code 特有的加载注册。**
> **规则内容修改一律去 `docs/RULES/`,本文不重复写规则。**
>
> **其他模型接入**:Codex 读 `AGENTS.md`(项目根)· 未来第三个模型见 `docs/RULES/09_MIGRATION_SOP.md`。

---

## Step 1 · 必读顺序

按 `docs/RULES/README.md` 必读顺序读完全部,包括 `docs/RULES/memory/`:

```
docs/RULES/README.md                      索引 · 铁律速查
docs/RULES/00_NORTH_STAR.md               铁律 0 · Audience-First(北极星 · 最高优先级)
docs/RULES/01_IRON_LAWS.md                铁律 1-11
docs/RULES/02_WORKFLOW.md                 4 步 5 拍板点 + 15 步 + 工种 + 强制 Workflow
docs/RULES/03_VISUAL_CREATIVE_GATE.md     视觉创意硬门(20→8-12→概念图)
docs/RULES/04_CONTENT_CONSTRAINTS.md      禁蓝紫 · 禁 AI 味深色 · 密 VO · sfx · palette gate
docs/RULES/05_PIPELINE_CANDIDATES.md      P001-P011 · integrations · 每镜五维打分
docs/RULES/06_SKILL_TRIGGERS.md           skill 触发关键词表(权威规范)
docs/RULES/07_ENVIRONMENT.md              环境配置 · 5 步初始化 · Git
docs/RULES/08_ASSETS_LIFECYCLE.md         素材生命周期
docs/RULES/09_MIGRATION_SOP.md            新模型接入 SOP(装新 skill 也读这个)
docs/RULES/10_MV_ENGINE.md                MV 引擎规范(相机 · 原子 · 缓存 · 求解器)
docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md     新片对话剧本(**用户说做片时按此主导**)
docs/RULES/decisions/DECISIONS.md         战略辩论锁定(Q1-Q11)
docs/RULES/decisions/CONVERSION.md        私信转化路径
docs/RULES/memory/                        40+ 条稳定 feedback / project 规则
docs/RULES/memory/README.md               memory 分类索引
```

---

## Step 2 · Claude Code 特有机制的等价映射

### 2.1 memory 机制

- ⚠️ **稳定项目规则已全部下沉到 `docs/RULES/memory/`**——原 `~/.claude/projects/-Users-wmzuo-Documents-project-case-study/memory/` 只留:
  - SESSION-TEMP(会话临时状态,如调试笔记)
  - PROJECT-STATE(项目当前进度,如 `project_p011-seedance-i2v-candidate`)
  - REFERENCE(外部引用)
- 你的 memory 会自动注入,**但开工前仍须读 `docs/RULES/memory/` 全部**(memory 的自动注入不能替代 SSOT——SSOT 才是所有模型共享的权威)
- **新加稳定规则时**:写到 `docs/RULES/memory/{分类}/{name}.md`,不再写到 `~/.claude/.../memory/`

### 2.2 Skill tool

- `.agents/skills/*/SKILL.md` 靠 frontmatter 触发关键词自动挂载(Skill tool 机制)
- **触发关系的模型无关权威规范**见 `docs/RULES/06_SKILL_TRIGGERS.md`(与 skill frontmatter 冲突以此为准)
- **agent 自主判断挂什么 skill**——用户只描述内容/意图/问题,不指名 skill。禁问"要不要挂 X",详见 memory `feedback_agent-auto-mount-skills`(已下沉到 `docs/RULES/memory/skill_meta/`)

### 2.3 Workflow tool

- `.claude/workflows/prd_pipeline.js` 强制多工种,PRD 定稿后必须调用
- **语义规范**见 `docs/RULES/02_WORKFLOW.md §四 强制走 Workflow`
- 违反(主 LLM 一人兼多工种直接写实现)登记 `docs/design/WORKFLOW_EXECUTION_LOG.md`

### 2.4 Agent() subagent

- 工种协作用独立 `Agent()` 调用,主 LLM 不兼任任何角色
- 并行调用规范:D05 加速要求同批次 tool_use 并行(洞察 4 件 / 设计 3 件 / TTS·UI·broll 三条并行)
- 详见 `docs/RULES/02_WORKFLOW.md §八 D05 加速`

### 2.5 hooks / settings

- `.claude/settings.local.json`
- 权限/hook 变更走 `/config` 或 `update-config` skill,不改本文
- 语义等价规范见 `docs/RULES/09_MIGRATION_SOP.md` 中"Workflow / hooks"一项

---

## 反例(不要这么做)

- ❌ 在本文加规则内容(本文只写加载注册)
- ❌ 在 `~/.claude/.../memory/` 加稳定规则(应写到 `docs/RULES/memory/`)
- ❌ 忽视 `docs/RULES/memory/`,只靠 Claude 自动注入的私有 memory(其他模型看不到)
- ❌ 装新 skill 只装文件不更新 `docs/RULES/06_SKILL_TRIGGERS.md`(下一个人不知道何时触发)
- ❌ 说"这次简单/是 demo/是轻量档"就跳过 `02_WORKFLOW.md §四` 工种协作(`production_tier` 只降验收强度,不减角色数量)

---

## 触发规则:用户说"做片"→ 主导对话

**识别关键词**:「做一支 MV」「新做一个片子」「卡点视频」「音乐动画」「短片」「做个视频」

命中任一,**立即读 `docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md` 全文,先按其「路线分流」判定走线 G(生成式 · conductor 六步 00→05 · 默认)还是线 P(程序化 paperdoll · A→F),再主导对话**——不要等用户问下一步做什么。

**边界铁规**(playbook §边界铁规):
- 只在 `pipeline/voice_room/<片名>/` 下读写文件
- 不改 `pipeline/mv_engine/` 任何文件(要新原子 → 起草 PR 给 owner)
- 不改 `docs/RULES/` 任何规则
- `git push origin main`:2026-08-04 起 main 分支保护已撤、PR 通道已关,直连 main 是当前唯一合并路径;仅在 owner 明确要求时推送

---

## 快速链接

- 每次开工前 4 步:见 `docs/RULES/02_WORKFLOW.md §一 顶层工作模式`
- **新片对话剧本**:`docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md`
- MV 引擎规范:`docs/RULES/10_MV_ENGINE.md`
- 视觉创意硬门:`docs/RULES/03_VISUAL_CREATIVE_GATE.md`
- i2v/t2v prompt 硬门:`docs/RULES/04_CONTENT_CONSTRAINTS.md §15`
- 生成后诊断硬门:`docs/RULES/04_CONTENT_CONSTRAINTS.md §16`
- Skill 触发对照表:`docs/RULES/06_SKILL_TRIGGERS.md`
- 装新模型:`docs/RULES/09_MIGRATION_SOP.md`
- 双层协作模型:`.github/CONTRIBUTING.md`

---

## 备份

- 本文 pre-shell 版本:`archive/CLAUDE_before_shell.md`(52 KB · 已把内容全部搬到 `docs/RULES/`)
