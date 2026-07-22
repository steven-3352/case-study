# 口播脚本标准 · 编剧 + 内核提炼师 + 留存与互动设计师 联合验收

> 工种：**编剧**（`skill/roles/registry.yaml` → `screenwriter`）· 负责维度（owns_dims）：**D19 情绪曲线**（见 `skill/quality/video_19dim_scorecard.md`）
> **禁止** 仅把 P0 信息点串成列表即视为脚本完成——必须对 **VO 听感** 与 **成片口播** 签字。
> **抗平庸机制 canonical 在 `skill/templates/anti_mediocrity_tournament.md`（`QG-ANTI-MEDIOCRITY`）**；本文件是编剧交付的合格/结构标准，与那道「抓不抓人」门并行，两道都要过。
> 对应质量门：**`QG-SCRIPT-QUOTES`**（用户原话 ≥4 条，少于即 fail）· **`QG-ANTI-MEDIOCRITY`**（停划裁判）· **`QG-SCORECARD-90`** + **`QG-REVIEWERS`** + **`QG-NOTES-40`**（双人独立 ≥90、notes ≥40 字）。基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收。

## 必过项

| 项 | 标准 | 不通过示例 | 关联门/维度 |
|----|------|------------|------|
| 场景入戏 | 前 5s 有**谁在哪做什么**，非数字开场 | 「300多个老客户，复购全靠Excel记」 | 停划钩子 |
| 原话/对话 | ≥**4** 句**引号对话**或用户原话转述（来自 topic_brief） | 全篇陈述句排比；**<4 条 fail** | `QG-SCRIPT-QUOTES` |
| 节奏 | 短句+长句交替；禁止 5 句同结构 | 连续「X靠Y」「不是让你…」模板 | D08 |
| 信息落地 | P0 融进叙事，**禁止字段名朗读** | 「购买日、周期、下次触达日、沉默标记」连读 | `QG-INSIGHT-3FACTS` |
| 价值锚 | 全文只出现 1 次，自然嵌入 | 与钩子重复套话 | — |
| 模板去重 | **不得**与上一条同骨架（见下） | 上一条骨架原样复用 | `QG-VISUAL-ORIGINALITY` |
| 角度差异 | 锦标赛竞写的角度**结构明显不同**，非 stub | 某版仅一行敷衍 | `QG-ANTI-MEDIOCRITY` |
| 音画同步 | 句界对齐 storyboard 节拍 | VO 念 field list 时画面在 pain | D06 / D07 |
| 情绪曲线 | 顶点必炸 + 落点必凉/必戳，两锚点单独验收 | 中段一路平读 | D19 |

## 禁止通过的「模板口播骨架」（出现即 reject · 触 `QG-ANTI-MEDIOCRITY`）

```
① 数字钩子一句
② 痛点排比两句
③「不是让你多买/上系统」
④ 字段名连读（购买日、周期…）
⑤「只讲跟进不讲功效」
⑥ 讨论型 CTA
```

与上一条有 **≥3 处** 同序同句式 → **编剧 + 编导** 退稿，不得 render（`QG-VISUAL-ORIGINALITY` 同源约束）。

## 产出物

```
scripts/
├── 竞写多版（不同角度）    # 结构须不同，走 anti_mediocrity_tournament
├── chosen.md               # best-of 合成 + 选用理由 + 未选版本取舍
└── design/script_review.md # pass/reject + 听感验收
```

## 门禁

- `script_review.md` 为 **reject** → 禁止 TTS（`cap-tts`）/ 禁止 render
- 编剧不得自批 pass；须 **留存与互动设计师**（节奏）+ **内核提炼师**（P0/原话）联签
- **双人独立评审 avg ≥ 90**（`QG-SCORECARD-90` + `QG-REVIEWERS` ≥2 不同 angle + `QG-NOTES-40` notes ≥40 字）
- render 后 **编导** 听 VO 与 mp4 对齐复验 + Phase B scorecard 重评
- storyboard / 动效大版本变更 → 强制编剧 scorecard 重评
- **禁止** 为卡成片时长压缩叙事；应加长 VO/片长或改分镜

## 竞写角度最低形态（走 `anti_mediocrity_tournament.md` 的 N 角度并行）

> canonical 机制见 `skill/templates/anti_mediocrity_tournament.md`（`QG-ANTI-MEDIOCRITY`）：N 个**不同角度**独立并行竞写 → 停划裁判判平不平庸（默认毙）→ 逐拍 best-of 合成。下表是「角度必须真不同」的参考形态，不是固定三版流水。

| 角度示例 | 主形态 |
|----|--------|
| 故事/场景向 | 故事/场景/纪录片向 |
| 数据/反差向 | 数据/反差/punch 向 |
| 单场景深挖向 | 单场景或单原话深挖 |

任两版 ≥3 处同序同句式 → reject。任一版一行 stub → reject（`QG-ANTI-MEDIOCRITY`）。

## 反例登记

见项目历史脚本拒稿记录（历史成品参考）。
