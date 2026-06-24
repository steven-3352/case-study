# 口播脚本反例登记

> 用户/编剧/留存设计师判定 **不可外发** 的脚本，记录根因，避免复现。

---

## 2026-06-24 · W26D04 · script vA / script_vo.md v2

**文件：** `projects/W26D04/script_vo.md` · `scripts/vA.md`  
**判定：** ❌ **不可 pass**（用户原话：「脚本水平太差，这种水平直接 pass 不允许产出」）

### 问题（听感级）

1. **念 PPT** — 5 句同结构陈述，无场景、无对话，像在读改造方案 bullet
2. **模板克隆 D03** — 「不是让你多买系统」→「不是让你多买系统」同骨架；字段连读同 D03 三表
3. **数字打架** — 口播「300多个」与 P0「312」并存；VO 后补「Excel打开都怕」与 vA 不一致
4. **vB/v0 占位** — vB 一行「要科学管理」、v0 一行「复购很重要」→ **三版讨论造假**
5. **音画脱节** — 字段罗列时 storyboard 已在 compare/pain，听感像 late VO 贴 PPT
6. **零原话** — topic_brief 5 条用户原话 **未进片**

### 根因链

```
6/16 vA 五句 bullet 定稿后未随 v3 分镜/动效重做
  → script_vo 从 vA 机械扩写
  → 无 script_review 门禁
  → TTS + P004 直接 build
  → 用户听 mp4 判定脚本不合格
```

### 应改为

- 场景+对话入戏；P0 融叙事；**script_review pass** 后再 TTS
- 见 `scripts/vC.md` · `script_vo.md` v3

---

## 2026-06-16 · W26D04 · script vD v5 · gate PASS 但内容未尽力

**文件：** `scripts/vD.md` v5 · `room/scorecards/编剧.yaml` avg 92.5  
**判定：** ❌ **gate 合规 ≠ 内容合格**（用户：「各位 agent 都尽力了吗？难道就能做出这样的水平？」）

### 问题（实质级）

1. **原话打卡** — 5/5 原话贴进陈述句，小刘无动作
2. **P0 漏 dramatize** — topic_brief「触达无模板」从未进片
3. **禁止项命中仍 pass** — 字段连读 + D03 同骨架仍给 92.5
4. **三版造假** — vA/vB 各 3 句 stub
5. **scorecard 放水** — 微扣 notes 不改稿

### 应改为

- v6 见 `scripts/vD.md` · 编剧 scorecard 重评 ≥90 后再 TTS/render

---
