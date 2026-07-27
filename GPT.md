# GPT.md · ChatGPT / GPT-4 加载壳

> **所有项目规则在 [`docs/RULES/`](docs/RULES/README.md)（SSOT · 单一事实源）。**
> **本文只声明 ChatGPT / GPT-4 特有的加载注册。**
> **规则内容修改一律去 `docs/RULES/`，本文不重复写规则。**
>
> **其他模型接入**：Claude Code 读 `CLAUDE.md` · Codex 读 `AGENTS.md` · 其他模型见 `docs/RULES/09_MIGRATION_SOP.md`。

---

## 使用方式

ChatGPT 没有自动读取项目文件的机制。使用本项目时，**在每次新对话开始时**将本文件内容粘贴进 system prompt，或在 ChatGPT Projects 的「Instructions」里填入本文件内容。

---

## Step 1 · 必读顺序

开工前，请让 GPT 读取以下文件（用文件上传或复制粘贴）：

```
docs/RULES/README.md                      索引 · 铁律速查
docs/RULES/00_NORTH_STAR.md               铁律 0 · Audience-First（北极星）
docs/RULES/01_IRON_LAWS.md                铁律 1-11
docs/RULES/02_WORKFLOW.md                 4 步 5 拍板点 + 工种
docs/RULES/10_MV_ENGINE.md               MV 引擎规范（相机模型 · 原子准入 · 帧缓存）
docs/RULES/memory/README.md               稳定反馈 / 项目规则索引
```

其余文件按需读取（具体见 `docs/RULES/README.md` 必读顺序）。

---

## Step 2 · ChatGPT 特有机制等价映射

| # | 能力 | Claude Code 现状 | ChatGPT 等价做法 |
|---|------|-----------------|-----------------|
| 1 | 规则自动加载 | 项目根 `CLAUDE.md` 自动读 | 手动上传或粘贴本文件进 system prompt |
| 2 | memory 持久化 | `~/.claude/projects/.../memory/` 自动注入 | 用 ChatGPT Projects「Instructions」保存；稳定规则以 `docs/RULES/memory/` 为准 |
| 3 | Skill 自动挂载 | Skill tool 关键词自动匹配 | 无自动挂载；开工前查 `docs/RULES/06_SKILL_TRIGGERS.md`，按用户描述匹配关键词后主动读相关文档 |
| 4 | Workflow hooks | `.claude/workflows/prd_pipeline.js` | 无；手动按 `02_WORKFLOW.md §四 强制走 Workflow` 执行 phase 0-2 checklist |
| 5 | 并行 subagent | `Agent(subagent_type=...)` | 无并行；串行方案，每角色一次调用 |

---

## Step 3 · 工作边界

**ChatGPT 可以帮你做的**：
- 在 `pipeline/voice_room/<你的片名>/` 里做新片内容（palette、shots.yaml、layouts.py）
- 调用 `mv_engine` 库（读文档、写调用代码）
- 讨论分镜参数、运镜逻辑、色板选择
- 读 `docs/RULES/` 回答项目规则类问题

**ChatGPT 不应自主修改的**（须提 PR 等 owner 审核）：
- `pipeline/mv_engine/` 下的任何文件
- `docs/RULES/` 下的任何规则
- `pipeline/mv_engine/atoms/lock.json`（原子锁文件）

---

## Step 4 · 原子准入提醒

如果 GPT 建议新增或修改原子（`mv_engine/atoms/`），必须满足：
1. 不带默认颜色
2. 纯函数（无 I/O，无模块级全局）
3. 声明 `touches_alpha: bool`
4. 补 `lock.py` case 并更新 `lock.json`

满足条件后提 PR，由 owner（@steven-3352）审核合并。

---

## 快速链接

- 引擎规范：`docs/RULES/10_MV_ENGINE.md`
- 新片模板：`templates/mv/tech_plan.template.md`
- 贡献指南：`.github/CONTRIBUTING.md`
- 迁移 SOP（其他模型接入）：`docs/RULES/09_MIGRATION_SOP.md`
