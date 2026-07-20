# 开工前自查清单 · 偷懒拦截清单

> 与 `anti_perfunctory_gates.md` 同级，但**在它之前**用：那份文件是产出后的门禁校验（scorecard/gate_check），这份是**动笔前 / 定稿前**的主动自查，目的是不靠用户事后抓包发现问题。
>
> 来源：memory `feedback_self-audit-before-finalizing`（T040 教训：同一机制性问题在单条 session 里重复出现 5 次）+ `docs/design/SCRIPT_REJECT_LOG.md` + `docs/design/FORM_FAIL_LOG.md` + `docs/DECISIONS.md` 真实案例。**不是空喊口号，每条都能追溯到具体出处。**

## Part A · 开工前自查（每次切换工种/步骤，动笔前过一遍）

任何一个工种开始产出前，先问自己 5 个问题：

1. **是否在拿姊妹条/上一条当模板参照？** 克隆分镜、画面、骨架、文案句式都算——哪怕只是"看一眼上条怎么写的"也要警惕会不会抄了不该抄的结构。
2. **"撞形检查"是不是只碰了一下旧文件夹就算过了？** 真的要核对 catalog 占比、视觉家族、专属模板计数，不是打开文件夹扫一眼没有一模一样的文件名就算通过。
3. **是否把 P0 核心内容悄悄降级成"轻量版"？** 轻量生产模式只砍重复功（模板复用/只重评<90/默认单轮），不砍质量门；核心脚本/核心卖点不能因为赶进度被简化。
4. **视觉/创作类主观选择，是不是默认选了"最省事/最像 AI 默认"的那个？** 默认暗色开发者工具风、默认 catalog 三连拼盘、默认单一表达方式——这些"看起来理所当然"的选择恰恰最容易踩雷（详见 Part C 视觉条目）。
5. **同一条规则要写两处（CLAUDE.md + memory）时，两处是否一致？** 如果只改了一处，另一处是不是已经过期成了错误信息源？

## Part B · 定稿前自查（任何"定稿 / 最终采用 / pass / approved"动作前）

打上"定稿""pass""approved"标签之前，再过一遍：

- 本 session 里用户已经明确说过的约束，这次产出有没有可能违反？
- 相关 memory（尤其"防 default"型规则，如禁 AI 味视觉、禁霓虹色）有没有过一遍？
- `docs/DECISIONS.md` Q1–Q11 锁定项有没有踩线？
- 这是不是一个"我觉得理所当然但其实是默认省事"的选择？

**核心原则：** 不要等用户发现——被发现之前自己先挑出来。

## Part C · 偷懒拦截清单（按本系统 15 步分阶段 · 前置版）

> 按 `CLAUDE.md` 标准动作 v2 的真实步骤组织，不套用其他内容赛道的产线划分。每条都是已经发生过、被打回的真实案例，看到同类信号 = 偷懒，立即停下重做，不要等到 FAIL_LOG 事后登记。

### 洞察包（步骤 3 · 理解层 4 工种 + 网络调研）

- 关键信息 < 3 条仍往下走 → 退回内核提炼师
- 无用户原话 / 无场景细节 → 退回记者
- `external_references.md` 不足 3 条 URL 或 2 条网络原话 → 洞察包不能定稿
- `topic_brief.md` 缺 `skin:` 段（audience/persona_anchor/hook_scene 等）→ 不能定稿（`docs/DECISIONS.md` Q10）

### 脚本锦标赛（步骤 5 · 编剧）

来源：`docs/design/SCRIPT_REJECT_LOG.md` 2026-06-24 / 2026-06-16 两条真实记录

- 5 句同结构陈述句，无场景无对话，像在念改造方案 bullet（"念 PPT"）
- 沿用上一条的句式骨架（如「不是让你多买系统」同结构复用）→ 模板克隆
- vA / vB / v0 各只写 1 行占位 → 三版讨论造假，不是真竞写
- 口播里的数字和 P0 洞察卡数据打架（如口播「300 多个」 vs 洞察卡「312」）
- topic_brief 里的用户原话没有实际进片，只是背景参考
- gate 合规、scorecard 92.5，但字段连读、同骨架仍然过 → scorecard 放水，微扣 notes 不改稿；用户原话："各位 agent 都尽力了吗？难道就能做出这样的水平？"

### 视觉路线 / 形式策略 / 视觉语言（步骤 6–9）

来源：`docs/design/FORM_FAIL_LOG.md` W26D04/D06/D07/D02/D08 真实记录 + `docs/DECISIONS.md` 禁 AI 味段

- 专属模板 < 3 种、excel/wechat 卡片各用 2 次充数 → catalog 占比超 35%
- VO 时长与成片时长对不上，CTA 被裁尾
- 无平台表现分析师 `pre_publish_forecast.md`，或 forecast 未过 go/no-go 仍继续
- P004 沿用暗色族只换皮 → 与上条同质（W26D06/D07 两次同类教训）
- storyboard / format_spec 承诺 Pexels/custom/专属私域看板，但实际执行走通用 `pipeline/render.py`（W26D08）→ **"文档承诺不算，最终关键帧看见才算"**
- 视觉语言默认选"暗色画布 + 克制 accent + Linear/Vercel/Cursor 式开发者工具美学" → 撞项目自己的禁 AI 味红线（`CLAUDE.md` 内容硬约束段）
- 视觉方向候选没有包含至少一个浅色方案，暗色变成了唯一默认起点

### 评审 / 互评（贯穿全程）

来源：`docs/design/FORM_FAIL_LOG.md` W26D02 真实记录

- 同一 session 内批量填完 9 个工种 × 2 位 reviewer 的 scorecard，notes 只在两个模板间轮换 → 假互评
- `reviewer_agent_id` 缺失但 scorecard 仍标 PASS
- cover 帧的 mtime 早于 video.mp4 的 mtime → 旧封面充数
- `hook_benchmark.md` 初版缺真实 URL（无法验证是否真的做过同行拆解）

---

**维护规则：** 每次往 `SCRIPT_REJECT_LOG.md` 或 `FORM_FAIL_LOG.md` 新增一条教训时，同步判断这条教训是不是一个会重复出现的模式——是就在 Part C 对应阶段补一条前置信号。把"事后登记"和"事前自查"绑成同一个闭环，避免这份清单写完就过期、成为摆设。
