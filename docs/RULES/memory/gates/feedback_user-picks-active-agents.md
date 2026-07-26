---
name: user-picks-active-agents
description: 每条选题的 active_roles 由用户拍板；我只提前给候选清单（名称·职能·作用·必选/建议/可选/不激活）；双评必新 session
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# active_roles 拍板机制（2026-07-05 决定）

**规则：** 每条选题开工前，我列候选清单让用户勾选；用户拍板后锁定 `active_roles` 写进 `topic_brief.md`；后续所有产出只由 active_roles 内的角色写。

**Why：**
- 同 session 单人扮多角色 = self-bias（D03 room/scorecards 事实上把双评降成自演）
- 不是每条选题都要全套 20+ 工种；同职能族能力相近的 agent 应合并成最全的一个
- CLAUDE.md P1 简化门禁的设计初衷是"不同 session 讨论"，不是同 session 自演

**How to apply（每条选题开工前）：**

1. 我先按 CLAUDE.md 全套工种列候选清单（21 项：理解 7 + 核心 8 + 表达音画 5 + 复盘 1 + 扩展），每条标注：
   - 名称 · 职能 · 对本条选题的**具体作用** · **门禁级别**（必选 / 建议 / 可选 / 不激活）
   - 相同职能族给合并建议
2. **给推荐合并版 10 个**（默认演示型/知识型主结构 · 2026-07-05 确定）：
   1. 编导
   2. **记者+**（记者 + 内核提炼师 + 领域专家 + 网络调研员）
   3. **编剧+**（编剧 + 纪录片导演 + 导演执行）
   4. **视觉设计+**（视觉设计 + 视觉语言策展师 + 摄像/视觉）
   5. 剪辑
   6. **运营+**（运营/增长 + 事实校验员合规）
   7. 留存与互动设计师
   8. 动画导演
   9. 形式策略官（+ 动效技术导演 · 用高级动效才叠加）
   10. 声音设计师
   带货型 +4 / 出镜型 +2 / 复盘官步 15 才启
3. 用户勾选 → 写进 `topic_brief.md` 的 `active_roles:` 段
4. 开跑，只按 active_roles 产出文档
5. **scorecard 双评只在两处跑，且必须 `Agent()` 起新 session 子 agent**：
   - **编剧+**（vB 稿 · 按编剧 rubric 打分）
   - **形式策略官**（form_strategy · 按平台表现分析师 rubric 打分）
   - 其他步骤**不跑双评**（省略了；同职能已合并单人产出）
   - SC <90 或用户点名 → 起第二轮，另起 agent
   - 本 session 内自扮 reviewer 打分 = self-bias，不算数

**反例：**
- 不询问 active_roles 就直接开跑 → 违反本约定
- scorecard 在本 session 内自扮 reviewer 打分 → self-bias，等于没跑双评
- 同职能族全跑（编剧+内核提炼+事实校验各写一份文档）→ 无意义拆分

**相关 memory：** [[feedback_multi-role-collab]] [[feedback_autonomous-data-driven]]
