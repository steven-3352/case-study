# AGENTS.md · Codex 加载壳

> **所有项目规则在 [`docs/RULES/`](docs/RULES/README.md)(SSOT · 单一事实源)。**
> **本文只声明 Codex 特有的加载注册。Codex 无 memory / 无 Skill 自动挂载 / 无 Workflow tool / 无并行 subagent,以下 5 项能力全部要人肉模拟。**
> **规则内容修改一律去 `docs/RULES/`,本文不重复写规则。**
>
> **其他模型接入**:Claude Code 读 `CLAUDE.md`(项目根)· 未来第三个模型见 `docs/RULES/09_MIGRATION_SOP.md`。

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

## Step 2 · Codex 特有机制的等价映射(Codex 无原生对应,须人肉模拟)

### 2.1 memory 等价

- Codex **无内置 memory 机制**
- **开工前必须显式 read `docs/RULES/memory/` 全部**(相当于 Claude Code 里 memory 自动注入)
- 新加稳定规则时,直接写到 `docs/RULES/memory/{分类}/{name}.md`——不需要维护单独的 Codex-private memory 目录

### 2.2 Skill 触发等价

- Codex **无 skill 自动挂载**
- **开工前查 `docs/RULES/06_SKILL_TRIGGERS.md`**,根据用户描述文本匹配"触发场景"关键词后,**主动 `read` 对应 `.agents/skills/{skill}/SKILL.md`**
- **用户不用指名 skill · Codex 自己按本表匹配**——禁问"要不要挂 X"、禁让用户点单
- 常见组合速查见 `06_SKILL_TRIGGERS.md §场景 → skill 组合矩阵`

### 2.3 多工种 Workflow 等价

- Codex **无 Workflow tool** · `.claude/workflows/prd_pipeline.js` 只 Claude Code 能跑
- **按 `docs/RULES/02_WORKFLOW.md §四 强制走 Workflow` 章节手动执行 phase 0-2**:
  - Phase 0:读 `docs/design/WORKFLOW_EXECUTION_LOG.md` 最近 5 条的 `carry_forward`
  - 每个被激活角色**独立会话产出结构化 markdown**(schema 见 `templates/design/subagent_prd_schema.md`),核心字段 `perceptual_goal.observable_metric` **禁写效果名术语**(禁 Ken Burns / parallax 等),必须是可观察量级
  - 验收者与产出者是**不同的会话**,二元 pass/fail
  - 交付后主 LLM 回读所有子 PRD,把协作过程错误登记 `docs/design/WORKFLOW_EXECUTION_LOG.md`
- 每个工种独立产出 markdown,**不合并成"四不像"**

### 2.4 subagent 等价

- Codex **无并行 subagent**
- **串行方案**——每角色一次独立会话,主 LLM 不主动兼任任何角色
- 洞察 4 件 / 设计 3 件 / TTS·UI·broll 三条:**一个一个来**(会比 Claude 慢,但铁律"独立子 agent 调用"仍必须遵守)

### 2.5 hooks 等价

- Codex **无 hooks**
- CLAUDE.md 里靠 hook 保证的事(如 pre-node-checklist),Codex **在每个节点开工前手动跑一遍 checklist**
- 关键 checklist:
  - `docs/RULES/memory/gates/feedback_pre-node-checklist.md` — 每节点入口必读清单
  - `docs/RULES/01_IRON_LAWS.md §8` — 门禁抬高 3 档反问
  - `docs/RULES/03_VISUAL_CREATIVE_GATE.md` — 创意不过关禁进执行层

---

## 反例(不要这么做)

- ❌ 在本文加规则内容(本文只写加载注册)
- ❌ 靠 Claude Code 私有 memory(`~/.claude/.../memory/`)—— Codex 看不到,那是 Claude 的私区
- ❌ 一次会话里 Codex 自己兼任多个工种直接写代码(违反 `02_WORKFLOW.md §四` 强制走 Workflow · 一个 PPT 感事故触发的铁律)
- ❌ 说"没有 Skill tool 就不用查 skill 触发表"—— `06_SKILL_TRIGGERS.md` 是**权威规范**,Codex 必须手动查
- ❌ 装新 skill 只装文件不更新 `docs/RULES/06_SKILL_TRIGGERS.md`(下一个人不知道何时触发)
- ❌ 说"这次简单/是 demo/是轻量档"就跳过工种协作(`production_tier` 只降验收强度,不减角色数量)

---

## 触发规则:用户说"做片"→ 主导对话

**识别关键词**:「做一支 MV」「新做一个片子」「卡点视频」「音乐动画」「短片」「做个视频」

命中任一,**立即读 `docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md` 全文,按 6 阶段(A→B→C→D→E→F)主导对话**——不要等用户问下一步做什么。剧本里写清楚了每阶段要问什么、要跑什么命令、什么时候停下来让用户确认。

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

- 本文 pre-shell 版本:`archive/AGENTS_before_shell.md`(7 KB · 已把内容全部搬到 `docs/RULES/`)
