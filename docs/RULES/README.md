# docs/RULES/ · 项目规则单一事实源 (SSOT)

> **本目录是所有项目规则的唯一权威。**
> `CLAUDE.md` / `AGENTS.md` / `~/.claude/.../memory/` / `.agents/skills/*/SKILL.md` 都指向这里。
> **修改规则一律改本目录,不要改薄壳文件。**

---

## 谁应该读什么

| 身份 | 入口 | 必读顺序 |
|---|---|---|
| **Claude Code** | 项目根 `CLAUDE.md`(薄壳)→ 本 README → 全部 `docs/RULES/*.md` | 见下方"必读顺序" |
| **Codex** | 项目根 `AGENTS.md`(薄壳)→ 本 README → 全部 `docs/RULES/*.md` | 同上 |
| **其他模型**(第三次接入起) | `docs/RULES/09_MIGRATION_SOP.md`——按 SOP 建自己的薄壳 | SOP Step 1 就是读全 RULES |

---

## 必读顺序

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
09_MIGRATION_SOP.md           新模型接入 SOP(5 项能力等价映射)
decisions/DECISIONS.md        战略辩论锁定(Q1-Q11)
decisions/CONVERSION.md       私信转化路径
memory/                       从 memory 下沉的 40+ 条稳定规则(feedback / project)
memory/README.md              memory 分类索引
```

---

## 铁律速查(0-11 编号稳定,老引用继续有效)

| # | 铁律 | 章节 |
|---|---|---|
| 0 | Audience-First, Not Pipeline-First | `00_NORTH_STAR.md` |
| 1 | 不看仓库有什么,看哪条实现更强 | `01_IRON_LAWS.md §1` |
| 2 | 内容门 + 形式门分开 fail-closed | `01_IRON_LAWS.md §2` |
| 3 | 合规分 vs 效果分 | `01_IRON_LAWS.md §3` |
| 4 | 各环节专家对最终结果负责 | `01_IRON_LAWS.md §4` |
| 5 | 尽一切可能让内容更好 | `01_IRON_LAWS.md §5` |
| 6 | 自我进化 | `01_IRON_LAWS.md §6` |
| 7 | 形式为数据假设服务 | `01_IRON_LAWS.md §7` |
| 8 | 门禁是地板不是目标 · 抬高 3 档 | `01_IRON_LAWS.md §8` |
| 9 | 创意决定上限 · 打磨只是防守 | `01_IRON_LAWS.md §9` |
| 10 | `draft_self_generated` 无门禁效力 | `01_IRON_LAWS.md §10` |
| 11 | 数据 A/B/C 分级 | `01_IRON_LAWS.md §11` |

---

## 修改规则的正确做法

**不要**:
- ❌ 在 `CLAUDE.md` / `AGENTS.md` 薄壳里加规则(它们只写加载注册,不写规则)
- ❌ 在 `~/.claude/.../memory/` 里加稳定规则(memory 只留会话临时状态)
- ❌ 在 `.agents/skills/*/SKILL.md` 里加跨 skill 的项目铁律(skill 只写本 skill 方法论)

**应该**:
- ✅ 找到规则对应的 `docs/RULES/{topic}.md` 或 `docs/RULES/memory/{category}/*.md`
- ✅ 就地修改;若规则确属新主题,新建文件并在本 README 索引里登记
- ✅ 修改后 grep 一遍薄壳(`CLAUDE.md` / `AGENTS.md`),确认没有旧规则遗留

---

## Source Map(此目录内容的原始来源)

| 目标文件 | 原始来源 |
|---|---|
| `00_NORTH_STAR.md` | 原 `CLAUDE.md §铁律 0` + `AGENTS.md 开头` + `docs/SYSTEM.md §1.0` + `.cursor/rules/audience-first.mdc` + memory `feedback_audience-first.md` |
| `01_IRON_LAWS.md` | 原 `CLAUDE.md §铁律 R0-R9` + `docs/SYSTEM.md §3.1` + `.cursor/rules/content-outcome-accountability.mdc` + 4 条 memory 铁律级 feedback |
| `02_WORKFLOW.md` | 原 `CLAUDE.md §顶层工作模式 + §核心工作流程` + `docs/SYSTEM.md §2` + `.cursor/rules/content-prep-multi-agent.mdc` + 多条 memory workflow 类 |
| `03_VISUAL_CREATIVE_GATE.md` | 原 `CLAUDE.md §视觉创意硬门` + `docs/design/COLLAB_REFORM_DRAFT.md` |
| `04_CONTENT_CONSTRAINTS.md` | 原 `CLAUDE.md §内容硬约束` + 多条 memory palette/visual 类 |
| `05_PIPELINE_CANDIDATES.md` | 原 `CLAUDE.md §候选实现清单` + `docs/SYSTEM.md §4.2` |
| `06_SKILL_TRIGGERS.md` | **新写** · 覆盖 45 个 skill |
| `07_ENVIRONMENT.md` | 原 `CLAUDE.md §环境配置 + §Git` |
| `08_ASSETS_LIFECYCLE.md` | 原 `docs/ASSET_LIFECYCLE.md` 全文 |
| `09_MIGRATION_SOP.md` | **新写** |

原始文件处理见 `archive/README.md`。
