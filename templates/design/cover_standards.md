# 封面设计标准 · 视觉设计 Agent 产出

> 工种：**视觉设计** + **导演** 联合验收  
> **禁止** 仅定 hook 文案即视为封面完成——必须对 **render 产出 PNG** 签字。

## 必过项（抖音/小红书封面）

| 项 | 标准 | 不通过示例 |
|----|------|------------|
| 场景感 | 有证据画面：聊天截图/表格/门店语境/真实模糊底图 | 纯黑金渐变 + 大字（无场景） |
| 信息层次 | 一屏一钩子；主标题 ≤2 行；副标题 1 行 | 上中下三段全是 slogan，中间大面积空黑 |
| 配色 | 跟板块一致；本地生活宜亮/暖/实拍感，忌「黑金 PPT」 | `#0c0a06` 径向渐变 + 金色 pill kicker |
| 高亮 | mark 关键词自然嵌入句中，忌黄块切字、括号感 | 「约了**两个人**」只高亮末两字 |
| 可读性 | 小屏缩略 1:1 仍可读；对比度 ≥4.5:1 | 暗底 + 细金边 kicker 糊成一团 |
| 形式对齐 | F2 强钩子 ≠ 纯 typography；宜叠 chat/metric 角标 | F2 却用默认 `cover_png` 无图回落 |

## 产出物

```
publish/{week}/Dxx-*/design/
├── cover_brief.md      # 视觉设计：构图、配色、必现元素
├── cover_review.md     # 对 render 产出的 pass/reject + 修改清单
└── cover_reference/    # 可选：参考截图或 mood
```

## 门禁

- `cover_review.md` 为 **reject** → `meta.yaml` 封面状态 `blocked`，不可标 ready
- `render.py` 默认回落渐变 **不得** 直接外发，须换 `cover.shot_ref` / `coverbg/` / 证据卡片合成

## 反例登记

见 `docs/design/COVER_REJECT_LOG.md`
