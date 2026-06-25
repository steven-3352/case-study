# 真实互评 · 执行规范（工具 enforcement）

> **形式互评 = 同 Agent 填两个 yaml 分数。** 以下由 `gate_check.py` fail-closed 校验。

## 1. 物理隔离（必须）

| 步骤 | 产出者 Agent | 评审 Agent |
|------|-------------|-----------|
| 1 | 写脚本/动效/分镜 | **不得**写同工种 scorecard |
| 2 | 将 `{工种}.yaml` 设为 `pass: false` | — |
| 3 | — | **独立** Task / subagent · `readonly: true` · 只读 artifact + rubric |
| 4 | — | 第二位评审 · **不同** subagent · **不同** angle |
| 5 | 汇总 avg | discussion.md 记录 Round；`|分差|>5` 须写交锋 |

## 2. scorecard 必填字段（每位 reviewer）

```yaml
reviewers:
  - reviewer_id: 纪录片导演      # 真实工种名，禁止「编剧审校-A」「子 Agent」
    review_mode: independent      # 必填，缺则 gate FAIL
    reviewer_agent_id: task-abc12345  # post_render/approve 必填 · 独立 Task 会话 ID
    reviewed_at: "2026-06-25"
    angle: 叙事与场景
    score: 93
    verdict: pass                 # 须与 score 一致：≥90→pass，<90→fail
    notes: |
      场景入戏 22/25：有开表停顿 +1。
      扣(-7)：改法段仍 lecture 感 → 改成「表标红三行」可见结果。
      改法：删「做了件很笨的事」，换一行结果句。
scorecard_phase: pre_render       # Phase B 工种须 post_render
```

## 3. gate_check 验什么（假互评直接 FAIL）

| 检查 | 说明 |
|------|------|
| `review_mode: independent` | 缺 = 未隔离 |
| `reviewer_agent_id` | post_render/approve 必填；格式 `task-*`/`agent-*`/`subagent-*`（≥8 字符） |
| 批量互评检测 | 同一 `reviewer_agent_id` 出现在 >3 个评审位 → FAIL |
| `scorecard_phase` | Phase B 工种（动效/编剧/视觉/留存/编导）须 `post_render` |
| 禁止假分身 | `审校` / `子 Agent` / `-甲` / 工种名出现在 reviewer_id |
| notes ≥40 字 | pass 时每位 reviewer |
| 扣分项 | score<100 须含 `扣(-N)` 或 `-N` |
| 禁止套话微扣 | 仅「微扣(-7)：可再具体」= FAIL |
| notes 不得完全相同 | 疑似复制 |
| verdict 与 score 一致 | 93 分不得标 fail |
| 级联作废 | script→v6 后产出层 scorecard 仍 pass v5 = FAIL |
| 洞察层豁免 | `insights/*` 不强制 artifact_version=content_version |

## 4. 89 分规则

**89 = fail。** 须改产出 → `optimization_round +1` → **新** 独立 Agent 重评，不得在原 notes 上改分。

## 5. 反模式登记

见 `docs/design/SCRIPT_REJECT_LOG.md` · `docs/design/FORM_FAIL_LOG.md`

| 案例 | 教训 |
|------|------|
| D04 v5 假 92.5 | 独立 Agent readonly · notes 实质 |
| D04 v10 形式纸面 92 / 效果 ~81 | 内容/形式两道门 · 分析师 · visual gate |
| D02 v4 批量 scorecard ~92 / spirit fail | agent_id 硬校验 · 独立 Task 重写 · cover mtime |

## 6. 合规分 vs 效果分

- **外发以效果分为准**（像素 + forecast），不以 scorecard 纸面分为准
- 差距 >5 → `room/form_audit_{v}.yaml` + `FORM_FAIL_LOG.md`
- forecast 形式 fail → `gate_check(approve)` 硬失败
