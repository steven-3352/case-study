---
name: feedback_d05-parallel-agents
description: D05 起产线加速方案 A · 洞察 4 件 / 设计 3 件 / TTS·UI·broll 三条 · Agent 并行发射不再串行
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# D05+ 产线并行化规则（2026-07-05 落地）

**Why:** D04 全流程串行耗时 2h45min · 用户明确反馈"2 小时也慢" · 42 件产物 AI 单件 30s-2min · 串行是主要瓶颈非 AI 慢

**How to apply:** 每条新内容开工时按下面三批 batch 并行发射 Agent 调用 · 同批次多个 Agent 塞在同一条 assistant message 里（多个 tool_use block），不要一条 message 只发一个

## 批次 1 · 理解层（并行 4 件 · 9min → 3min）

发射时同批次 tool_use：
- 记者+ → `insights/reporter_notes.md` + `insights/external_references.md` + `insights/fact_check.md` + `insights/core_message.md` + `insights/topic_brief.md`（同一 Agent 一次出 5 件 · 因为都是理解层内互相依赖）

如果拆分：4 个并行 Agent
- Agent-A: external_references（网络调研 · 独立 · 最先起飞）
- Agent-B: topic_brief + reporter_notes（互相依赖 · 同一 Agent）
- Agent-C: domain_notes（领域专家）
- Agent-D: core_message + fact_check（等 A/B 出稿后跑 · 二段批次）

## 批次 2 · 设计层（并行 3 件 · 24min → 10min）

编剧 vB pass 后发射：
- Agent-E: design_language.md（视觉语言策展 · 独立）
- Agent-F: openmontage_brief.md + form_competition.md（形式选型 · 同一 Agent）
- Agent-G: motion_storyboard.md（动画导演 · 依赖 vB + retention_beat · 单跑不双评）

设计层结束后：
- form_strategy.md 走 Agent() 新 session 双评（硬性约束 · 不能省）

## 批次 3 · 音画+素材（并行 3 条 · 15min → 5min）

storyboard.yaml 定版后发射：
- Agent-H: audio_plan.yaml + TTS 前置估算（同 Agent · 前后依赖）
- Agent-I: UI PNG 生成（gen_ui_wXXdYY.py · 独立）
- Agent-J: Pexels broll 拉取（fetch_broll.py · 独立）

## 硬性约束（不能并行的地方）

1. **编剧+ 双评**：vB v1 → scorecard → 如 fail 走 v2 → scorecard round 2 · 必须串行 · 每轮独立 session
2. **形式策略官双评**：form_strategy.md → 双 reviewer 独立 session
3. **TTS 合成 → preview → platforms**：pipeline 三步物理串行

## 反例（不要这么做）

- ❌ 洞察包 5 件一件一件写 · 每件等前件完成才起下件（D04 教训）
- ❌ 设计层 design_language / openmontage / form_competition 依次跑 · 三件其实独立
- ❌ TTS 估算跑完等结果才生成 UI PNG · 两条独立
- ❌ 一条 assistant message 只发一个 Agent tool_use · 浪费并发能力

## 预期效果

D05 目标 60min（含 [[feedback_delta-docs-only]] B + [[tts-estimate-duration-pre-synth]] C 硬门）· D04 从 2h45min 压缩 ~65%

参考 memory：[[feedback_delta-docs-only]] · [[tts-estimate-duration-pre-synth]] · [[feedback_user-picks-active-agents]]
