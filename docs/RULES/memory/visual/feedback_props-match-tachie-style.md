---
name: props-match-tachie-style
description: "片中道具/场景资产必须与立绘同一画风；生图要线稿必须把 LINE ART 写成主诉求，只写 \"illustration not a photograph\" 会得到三维产品渲染"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d04dbe9-0eca-4173-920a-35df529e7925
---

同一部片里的**道具、场景、器物资产必须画成和立绘同一套画风**，不能一边是插画人物一边是实拍/写实渲染的物件。

**Why:** 用户 2026-07-26 在《明月天涯》创意 A 直接指示「打印机用跟立绘一样的风格」。原方案给扫描仪写的是纪录片式微距实拍（prompt 里甚至明确写 `NOT an illustration`），实拍机器配插画人物会两层皮——观众第一眼看到的就是两套资产被硬凑在一起，这本身就是"AI 拼贴感"的来源，比任何禁用色表都更早暴露。

**How to apply:** 任何为某条片生成道具/背景/器物时，先看主体资产（立绘）是什么画风，再让新资产去对齐它，而不是各自挑各自"最好看"的风格。

## 生图落地：想要立绘风，必须把线稿写成主诉求

第一版 prompt 写了 "high-end otome-game character-art illustration / crisp thin dark line art / NOT a photograph, NOT a 3D render"——**仍然拿回柔和三维产品渲染**（无线稿、无块面，像 Apple 产品图）。

立绘的**识别特征是线稿**，不是"精致"。所以：

| | 写法 |
|---|---|
| ❌ 不够 | 把画风词埋在一串形容词里，靠 `NOT a photograph` 排除 |
| ✅ 有效 | `MOST IMPORTANT: clean crisp dark ink LINE ART defines every edge, seam and contour, drawn with confident varying-weight strokes` + 颜色部分单独写 `cel shading: flat base tones with a few clear shadow shapes` |

否定项也要跟着补具体：`NOT a 3D render, NOT a product render, NOT product photography, NOT a soft vector gradient illustration, NOT flat minimal vector art`——只否定 photograph，模型会滑到"三维渲染"这个中间态。

**分档**：只有**道具本体**要线稿；光效/瑕疵叠加底板（漏光、灯管衰减、CCD 行噪、浮尘）画线稿没有意义，那一档给"手绘感干净渐变"即可。落地见 `pipeline/gen_scanner_plates.py` 的 `STYLE_PROP` / `STYLE_PLATE` 双档 + `Plate.lineart` 开关。

相关：[[feedback_anti-ai-visual]] · [[feedback_no-cheap-procedural-background]]（那条管"背景不许现搓"，这条管"资产之间画风要统一"）
