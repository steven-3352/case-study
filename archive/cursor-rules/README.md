# archive/cursor-rules/ · 归档说明

> **2026-07-26 归档**——本项目当前只支持 Claude Code + Codex 两个模型(见 `docs/RULES/09_MIGRATION_SOP.md`)。
> **不再使用 Cursor** → 4 个 mdc 文件迁到本目录归档,不再作为 alwaysApply 规则源。

---

## 内容与归宿

| 归档文件 | 内容主题 | 已合并到 |
|---|---|---|
| `audience-first.mdc` | 铁律 0 · Audience-First | `docs/RULES/00_NORTH_STAR.md` |
| `content-outcome-accountability.mdc` | 结果负责制 + 双人互评 + 动效铁律 + 口播铁律 + 多 Agent 审核 + 各工种责任表 + 禁止行为大表 | `docs/RULES/01_IRON_LAWS.md` |
| `content-prep-multi-agent.mdc` | 内容前期多 Agent 讨论定稿 + 必跑工种表 + 命令 | `docs/RULES/02_WORKFLOW.md` |
| `platform-same-video-delivery.mdc` | 抖音/小红书同素材策略(**已废弃 · 2026-07-05 起停做视频号 + 双平台各自出**) | `docs/RULES/04_CONTENT_CONSTRAINTS.md §18`(引用 memory `feedback_dual-platform-only`) |

**修改内容**:一律去 `docs/RULES/` 对应文件。本归档目录只作原始参考,不再作为 alwaysApply 规则源。

---

## 如需重启 Cursor 支持

按 `docs/RULES/09_MIGRATION_SOP.md` 建立 Cursor 加载壳(可以是 `.cursor/rules/loader.mdc` 或 `.cursorrules`),声明:
- **规则加载**:`.cursor/rules/*.mdc alwaysApply` → 只写一个 loader.mdc,内容指向 `docs/RULES/README.md`
- **memory 等价**:Cursor 的 notepads / project rules
- **Skill 触发等价**:`docs/RULES/06_SKILL_TRIGGERS.md` 手动查
- **subagent / workflow 等价**:Cursor 的 Composer / Chat / Rules for AI

**不要**把本目录的 4 个 mdc 恢复回 `.cursor/rules/`——那会重新引入"规则多处漂移"的老问题。
