---
name: feedback_delta-docs-only
description: "工种文档只写\"本条与上条/SYSTEM/DESIGN 的 delta\"，不复述框架内容；设字数硬上限"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# Delta 文档规则（2026-07-05 落地）

**Why:** D04 topic_brief 8k · design_language 27k · form_strategy 22k · reporter_notes 16k — 用户反馈慢 · 大量字数是复述 SYSTEM.md/DESIGN.md/catalog 已有内容 · 属"完成心态"（多写不算多干活）· 真正影响下游的信息量约 1/4

**How to apply:** 每个工种产出前先想"本条 vs 上条/SYSTEM/DESIGN 差异是什么" · 只写差异 · 引用 SYSTEM/DESIGN 段号不要 copy · 达到硬字数上限强制截稿

## 字数硬上限（D05 起 · 超即回炉）

| 文档 | 上限 | 只写什么 |
|------|------|---------|
| `insights/topic_brief.md` | 2500 字 | 本条 skin/受众/1 句价值锚/3-5 条关键信息 · 不复述"AI 内容自动化"这类框架话 |
| `insights/reporter_notes.md` | 4000 字 | 3-5 条真实原话 + 场景细节 · 不复述调研方法论 |
| `insights/external_references.md` | 3000 字 | ≥3 URL + ≥2 网络原话 + 引用 delta · 不复述"网络调研规则" |
| `insights/domain_notes.md` | 3000 字 | 本条特殊领域细节 · 通用业务逻辑引 SYSTEM 章节号 |
| `insights/core_message.md` | 1500 字 | 3-5 条不可删信息 + 1 句价值锚 · 就这些 |
| `insights/fact_check.md` | 2000 字 | 每条数据/引用逐条核验表 · 表格形式即可 |
| `retention_beat_sheet.md` | 5000 字 | 逐段完播预测 + 形式切换点 + CTA 埋点 · 不复述留存理论 |
| `design/design_language.md` | 5000 字 | 本条 token/字号/组件表 · 引 DESIGN.md 段号不 copy |
| `design/form_competition.md` | 6000 字 | 每 scene ≥3 候选打分表 · 打分即可不写"候选实现是什么" |
| `design/form_strategy.md` | 8000 字 | 每 scene 选中方案 + 数据杠杆 + 制作成本 · 6 硬门自检表 |
| `design/motion_storyboard.md` | 8000 字 | 逐秒 9 字段表 · 就是表格 |
| `design/openmontage_brief.md` | 3000 字 | enabled/disabled/blocked 判定 + 理由 · 不复述 OpenMontage 介绍 |
| `design/pre_publish_forecast.md` | 4000 字 | 三平台 forecast + 数据杠杆逐项打分 |
| `audio_plan.yaml` | 无 | yaml 结构化 · 无字数限制但禁 comment 长于 2 行 |

## 该 copy 的地方（延续 D04 golden）

- `insights/reporter_notes.md` 真实原话逐字 · 不可摘要
- `design/form_strategy.md` 6 硬门自检项目名 · 不可改字（gate_check 依赖）
- `room/scorecards/*.yaml` scorecard 字段结构 · 不可自造

## 该压的地方

- 每份文档开头"背景/概览/流程说明"这类复述性开场 → 一句话或删
- "为什么要这么做"这类元讨论 → 引 SYSTEM/DECISIONS 段号
- 表格/清单能替代散文的 → 用表格
- 每条候选/每个 scene 都重写通用规则 → 只写本条差异

## 反例（不要这么做）

- ❌ topic_brief 里花 2k 字复述"我们做 AI 内容自动化" · 引 SYSTEM 段号 3 行
- ❌ design_language 27k 字里 20k 是 DESIGN.md 已有的色板/字体理论 · 只需列本条 delta token 表
- ❌ form_strategy 每个 scene 都重写"形式选型 6 硬门是什么" · 6 硬门自检表放开头一次即可

## 上限如何强制

D05 起 · 每份文档产出后立即 `wc -c <file>` · 超上限 → 回炉压缩 · 不允许"这份重要所以多写点"

参考 memory：[[feedback_d05-parallel-agents]] · [[feedback_audience-first]]
