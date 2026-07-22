# 封面设计标准 · 视觉设计 Agent 产出

> 工种：**视觉设计** + **导演** 联合验收（`skill/roles/registry.yaml` → `visual-designer` + `exec-director`）
> **禁止** 仅定 hook 文案即视为封面完成——必须对 **渲染产出 PNG** 签字。
> 负责维度（owns_dims）：**D04 包装 · D09 排版与图形 · D15 视线引导**（见 `skill/quality/video_19dim_scorecard.md`；基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收）
> 对应质量门：**`QG-PALETTE-NEON`**（配色/禁霓虹）· **`QG-VISUAL-ORIGINALITY`**（不套旧封面模板）· **`QG-PRD-ACCEPTANCE`**。

## 必过项（抖音/小红书封面）

| 项 | 标准 | 不通过示例 | 维度 |
|----|------|------------|------|
| 场景感 | 有证据画面：聊天截图/表格/门店语境/真实模糊底图 | 纯黑金渐变 + 大字（无场景） | D04 |
| 信息层次 | 一屏一钩子；主标题 ≤2 行；副标题 1 行 | 上中下三段全是 slogan，中间大面积空黑 | D09 |
| 配色 | 跟板块一致；本地生活宜亮/暖/实拍感，忌「黑金 PPT」；`QG-PALETTE-NEON` 通过 | 暗底径向渐变 + 金色 pill kicker | D10 |
| 高亮 | mark 关键词自然嵌入句中，忌黄块切字、括号感 | 「约了**两个人**」只高亮末两字 | D09 |
| 可读性 | 小屏缩略 1:1 仍可读；对比度 ≥4.5:1 | 暗底 + 细金边 kicker 糊成一团 | D09 / D17 |
| 形式对齐 | 强钩子 ≠ 纯 typography；宜叠 chat/metric 角标 | 强钩子却用默认无图回落 | D04 |
| **抖音原生** | **成片定格帧或全屏大字冲击** | 分屏 + 桌面窗口 mock 幻灯片感 | D16 |
| **动效** | 抖音成片 mp4 · 小红书生成漫画帧 | 静态 PNG / PPT 分屏 / Ken Burns slideshow | D01 / D02 |

## 抖音封面专用（平台原生策划签字）

| 优先 | 类型 | 何时用 |
|------|------|--------|
| 1 | 成片定格帧 | 有成片视频 — 封面 = 视频某一帧（默认取 punch 镜） |
| 2 | 全屏大字冲击 | 成片未出前 — 全屏纯底大字，与成片 punch 首镜一致 |
| ❌ | 分屏 / 桌面窗口 mock | **禁止用于抖音** — 分屏幻灯片感，平台与用户均违和 |

## 产出物

```
design/
├── cover_brief.md      # 视觉设计：构图、配色、必现元素
├── cover_review.md     # 对渲染产出的 pass/reject + 修改清单
└── cover_reference/    # 可选：参考截图或 mood
```

## 门禁

- `cover_review.md` 为 **reject** → 封面状态 `blocked`，不可标 ready
- 渲染前置校验：**抖音禁止分屏/桌面窗口 mock**；无版式且无 panel/bg → 拒绝渲染
- 视觉设计签字前 **必须打开 PNG** 对照 brief，不得仅审 hook 文案（`QG-PRD-ACCEPTANCE`：验收者只看结果是否达标）
- 配色须过 `QG-PALETTE-NEON`；封面与最近作品不同质须过 `QG-VISUAL-ORIGINALITY`

## 反例登记

见项目历史封面拒稿记录（历史成品参考）。
