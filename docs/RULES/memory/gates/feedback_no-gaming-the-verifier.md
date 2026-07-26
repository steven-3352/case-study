---
name: no-gaming-the-verifier
description: "禁止用「改验收器的输入」来过门——给非主体挂 bbox、把主体清空、改 motion-track 记录方式,都比 fail 更糟;门只接受\"东西真的变了\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d04dbe9-0eca-4173-920a-35df529e7925
---

**过不了门时,只准改被测的东西,不准改喂给门的数据。**

**Why:** 门是代理指标,它测的是「画面真的动了没有」;一旦通过改记录方式让门读不到/读错,门还亮绿灯,但它已经不在测量画面了。这比 fail 更糟——fail 是信号,假 pass 是把信号永久静音,而且是静默的,后面没人会再发现。两次实例的诚实解法都在手边,成本还更低,说明这不是"没办法只好绕",是**绕比想更省事**。

**How to apply:** 任何提案里出现"让 gate 读不到 X / 给 Y 补一条记录 / 换个字段口径",默认驳回,回去改画面本身。

R9 冻结门(`pipeline/gate_check_motion.py`)已实测出现两次(2026-07-26 语音厅《明月天涯》):

| # | 提案 | 为什么是作弊 | 诚实解法 |
|---|---|---|---|
| 1 | 把 `scan_bar` 的 y_frac 当"合成主体"中心写进 motion.json | 门量的是立绘构图变化,不是光效位置。光条动 ≠ 主体动 | 段内真切一刀镜(多 shot_id 本来就 PASS) |
| 2 | 空拍那一拍设 `doll=""` + `bbox=None`,触发"主体缺席"分支不判冻结 | 靠让门读不到主体来过门。且画面上空拍并非无主体,清空这一拍就从"音乐让开"变成"画面掉了" | 独立 Shot 保留即可,多 shot_id 已 PASS |

裁定全文:`publish/语音厅/design/storyboard_sample_22465_29780.md` 裁定 2;撤销标注在 `publish/语音厅/design/motion_tech_plan.md` §10 第 5 条。

与 [[feedback_gate-floor-not-target]] 是一对:那条管"别把地板当目标",这条管"别伪造地板"。同一个病根——把 gate 当成要应付的对象,而不是要测量的事实。
