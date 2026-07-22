# 视觉语言约束 · design_language

> 工种：**视觉语言策展师**（`skill/roles/registry.yaml` → `visual-language-curator`）· 在 `form_strategy` 后、`storyboard` 前完成
> 目的：把成熟视觉系统转成**本条内容可执行的画面约束**，不是照抄品牌。
> 负责维度（owns_dims）：**D04 包装 · D09 排版与图形 · D10 色彩与影调**（见 `skill/quality/video_19dim_scorecard.md`；基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收）
> 对应质量门：**`QG-PALETTE-NEON`**（禁霓虹/蓝紫占比 ≤5%）· **`QG-VISUAL-ORIGINALITY`**（视觉原创）· **`QG-PRD-ACCEPTANCE`**。

## 0. 入口必读（开工前打勾）

> 流程与门位见 `skill/docs/PROCESS.md`；不过清单不得开工

- [ ] **流程 refs**：`skill/docs/PROCESS.md` 波次表（W8 视觉语言策展师）
- [ ] **质量 refs**：`skill/quality/quality_registry.md`（`QG-PALETTE-NEON` · `QG-VISUAL-ORIGINALITY` · `QG-RAISE-3`）
- [ ] **维度 refs**：`skill/quality/video_19dim_scorecard.md` D04/D09/D10 的「提升 3 档目标」与「常见踩雷」列（AI 默认深色画布 + 冷蓝配色 = AI 视觉套路）
- [ ] **template refs**：本节点已完成 `topic_brief.md` skin.tone_direction · `form_competition.md`（推荐方案）· form_strategy
- [ ] **历史成品参考**：同主题最近 1 条 `design_language.md` 实读（防复用 token）

**触发词打断**：「用老色板」「霓虹紫其实挺好看的」「上条 token 抄一下」

> **禁 AI 味深色开发者风（硬规则）**：起稿默认不得选「自造深色画布 + 克制 accent + 暗色高对比开发者美学」这套气质——它本身已是生成式 AI 内容的高频套路，触 D04/D10 踩雷 + `QG-PALETTE-NEON` 同源约束。**候选方向必须含 ≥1 个浅色/白底方案**，除非画面本身就是真实截屏且该 app 原生深色 UI（真实使用痕迹，非设计选择，允许保留）。

## 0-a. 本条定位

- content_id:
- 平台 / 形态:
- 观众行为目标: 停划 / 看懂 / 收藏 / 评论
- 参考来源:
  - 成熟视觉系统 / DESIGN 参考:
  - 选择理由:
  - 不照抄声明:

## 1. 视觉关键词

用 3–5 个词描述本条画面气质，必须能指导取舍。

- 关键词 1:
- 关键词 2:
- 关键词 3:

## 2. Token 提取

### 色板（`QG-PALETTE-NEON`：蓝紫像素 HSL H∈[240°,290°] 占比 >5% → fail；真截屏系统色例外）

| 角色 | 色值 | 用途 | 禁用 |
|------|------|------|------|
| canvas | | 背景 / 主画布 | |
| surface | | 卡片 / 面板 | |
| ink | | 标题 / 正文 | |
| muted | | 辅助信息 | |
| accent | | 只用于关键焦点 | |
| danger / contrast | | 冲突提示 | |

### 字体与层级（D09：字体层级对比 ≥3× 大小/粗细差）

| 层级 | 字号 / 字重 | 行高 | 用途 | 单屏上限 |
|------|-------------|------|------|----------|
| display | | | 封面 / 首镜大字 | |
| headline | | | 每页主标题 | |
| body | | | 解释文本 | |
| caption | | | 标签 / 来源 / 注释 | |
| mono / data | | | 数据 / 字段 / 代码 | |

### 形状与间距

- 圆角:
- 边框:
- 阴影 / 深度:
- 留白密度:
- 卡片最大层级:

## 3. 组件规则

| 组件 | 应该怎么画 | 不该怎么画 |
|------|------------|------------|
| 封面标题 | | |
| 信息卡片 | | |
| 表格 / 字段表 | | |
| 对比块 | | |
| CTA | | |
| 标签 / badge | | |

## 4. 逐镜 / 逐页应用

| 镜 / 页 | 主意图 | 使用的视觉 token / 组件 | 焦点路径（D15） | 禁止项 |
|---------|--------|--------------------------|----------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## 5. Do / Don't

### Do

- 
- 
- 

### Don't

- 
- 
- 

## 6. 像素验收清单

- [ ] 参考来源已本地化，不出现直接品牌冒充或照抄 logo / 文案。
- [ ] 色板在最终 HTML / PNG 中兑现，accent 没有泛滥（`QG-PALETTE-NEON` 通过）。
- [ ] 字体层级稳定，移动端 / 1080 宽画布文字不挤、不溢出（D09）。
- [ ] 每页 / 每镜只有一个主要视觉焦点（D15）。
- [ ] 组件规则进入 storyboard 或 HTML 模板，不只停留在描述。
- [ ] 与上一条 approved 内容首屏观感不同（`QG-VISUAL-ORIGINALITY`）。
- [ ] 候选方向含 ≥1 浅色方案，未把自造深色画布当默认（D04/D10）。
