---
name: project_audience-open-skin-per-topic
description: case-study 项目 2026-07-04 起取消固定皮肤（原「小老板+小系统」），受众开放，皮肤按每条选题激活
metadata: 
  node_type: memory
  type: project
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

case-study 项目自 **2026-07-04** 起：**取消固定内容皮肤**（原「小老板烦事 → 能跑的小系统」已归档为历史皮肤），改为「**开放选题 · 选题定皮肤**」。

**Why:** 历史皮肤把选题池窄化到「实体店老板 + 小系统改造」单一垂直，导致选题窄、视觉/话术套模板、阻碍尝试非案例形态（工具评测、方法论、观察、新品拆解等）。开放后同一套引擎可承载任意 AI 主题，每条内容对**自己声明的目标受众**负责。

**How to apply:**

- **受众开放** — 任何对 AI 工具/AI 应用感兴趣的人都可能是受众；不再默认「实体店老板」
- **皮肤按选题激活** — 每条新选题必须在 `insights/topic_brief.md` 顶部 `skin:` 段声明本条的：
  - `audience`（具体人群+场景，不写"泛 AI 爱好者"）
  - `persona_anchor`（这条我是谁）
  - `tone_direction`（口吻/关键词/禁词）
  - `hook_scene`（钉子场景）
  - `landing_intent`（转化落点）
  - `format_leaning`（形态倾向）
  - `differ_from_last`（与近 2 条差异）
- **皮肤不跨条继承** — D07 的 skin 不许 D08 直接套；每条重写
- **`persona/persona.yaml` 仅作默认参考** — 其中 openings/catchphrases/closings 里带「小老板」的条目已标注为「历史皮肤，非通用」，未声明 skin 时才兜底
- **不变的部分**（与皮肤无关，始终生效）：
  - 转化仍是**等私信**（Q3），正文不导流
  - 数据规范 A/B/C（Q4）
  - 无硬性 KPI（Q6）
  - 视觉路线：证据优先、禁霓虹色、禁 AI 味（Q9）
  - 17 步流程、两道门、90 分双人互评、fail-closed
  - 出镜按形态（Q8 更新版）
- **旧内容不回填** — 2026-07-04 前已在生产管线的选题（如 W28D01）沿用原皮肤跑完；此日期后新建选题必须写 `skin:`

**同步改动的文档：**
- `docs/SYSTEM.md` §1.1 §1.2 §1.3 §5（新增 §1.3 "皮肤按选题激活"）
- `CLAUDE.md` 顶部「内容皮肤」说明
- `docs/DECISIONS.md` 顶部 disclaimer + 新增 Q10 + Q1/Q2/Q5 标注归档
- `queue/topics.yaml` direction 字段
- `persona/persona.yaml` 顶部 disclaimer + role 中性化 + openings/catchphrases 标注历史条目
- `docs/CONVERSION.md` 主页简介模板（通用版 + 历史皮肤版并列）
- `templates/insights/topic_brief.md` 顶部新增 `skin:` 必填段

**关联：** [[feedback_multi-role-collab]]（多工种协作）、[[feedback_anti-ai-visual]]（反 AI 味）、[[feedback_autonomous-data-driven]]（自主推进）。

**反例（不要这么做）：**
- ❌ 假设「实体店老板」是默认受众
- ❌ 用 persona.yaml 的旧 openings/closings 里带「小老板」的句子做新皮肤的话术
- ❌ 把 D07 的 skin 直接套用到 D08，只改具体产品名/工具名
- ❌ 认为「取消固定皮肤 = 不需要皮肤」（每条仍要在 topic_brief.skin 声明）
