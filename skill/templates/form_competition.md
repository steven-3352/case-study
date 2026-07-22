# 表现形式竞争 · form_competition

> 工种：**形式策略官**（`skill/roles/registry.yaml` → `form-strategist`；协作：纪录片导演 + 动画导演）
> 位置：`design/form_competition.md`
> 时机：`form_strategy` 之前，`storyboard` 之前。
> 目的：阻止"默认套模板"。每条内容必须先竞争至少 3 个表现方案且跨 ≥2 家族，再允许进入分镜。
> 对应质量门：**`QG-FORM-COMPETITION`**（≥3 方案且跨 ≥2 家族）· **`QG-FORM-EXCLUSIVE`**（专属视觉隐喻 ≥3 种）· **`QG-FIVE-DIM`**（实现方式五维打分）。基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收。
> 负责维度（owns_dims）：**D03 特效 · D05 转场**（见 `skill/quality/video_19dim_scorecard.md`）。

## 0. 入口必读（开工前打勾 · **本节点错误重灾区，必须最严格**）

> 流程与门位见 `skill/docs/PROCESS.md`；不过清单不得开工
> 教训：3 方案全在同一渲染家族（如都是截图变体），跳过跨家族竞争，属候选池预先缩水

- [ ] **流程 refs**：`skill/docs/PROCESS.md` 波次表（W9 形式策略官 · 定分镜前门位）
- [ ] **质量 refs**：`skill/quality/quality_registry.md`（`QG-FORM-COMPETITION` · `QG-FORM-EXCLUSIVE` · `QG-FIVE-DIM` · `QG-RAISE-3`）
- [ ] **维度 refs**：`skill/quality/video_19dim_scorecard.md` D03/D05 的「提升 3 档目标」列
- [ ] **template refs**：本文件 §3 候选池完整性自查 · `skill/templates/design_language.md` · `skill/templates/motion_storyboard.md`（本岗提供第 1 方案）
- [ ] **历史成品参考**：同主题最近 1-2 条已存在的 `form_competition.md` 实读，防撞形
- [ ] **能力清单 refs**：浏览 `skill/` 内全部 `cap-*` 能力目录 + `skills-manifest.json` 各跑一次；确认没有可用能力被漏

**触发词打断**（出现即回 §3 候选池完整性 + `QG-FIVE-DIM` 五维打分）：
- 「就走某条默认渲染线吧」/「用现成模板拼一个」
- 「拉素材 + 配音 + HTML 仿真 + 合成拼一个」（未跨家族对比）
- 「某某合成 runtime 太重了不适合本条」（不跑合成 runtime brief 就下结论 = 门禁绕过）
- 「3 方案都用同一家族的变体也行」

## 1. 结论

```yaml
status: draft | pass | fail
content_id:
review_source: agent_reviewed | human_reviewed
decision: proceed_to_form_strategy | rewrite_competition | block_storyboard
recommended_route:
```

## 1b. 本条视觉命题

> 一句话说明这条内容"画面到底要让观众看见什么"，不能写成抽象风格词。

- 视觉命题：
- 本条最重要的观众反应：
- 本条最不能出现的旧模板感：

## 2. 最近 5 条撞形检查

| 近作 | 主要首屏 | 中段机制 | CTA 形态 | 本条如何避开 |
|------|----------|----------|----------|--------------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

## 3. 候选池完整性自查（**门禁 · 早于列方案** · `QG-FORM-COMPETITION`）

> **每次列方案前必读 `skill/` 内全部 `cap-*` 能力目录 + `skills-manifest.json`。** 能力清单随新集成更新。

### 3.1 候选池来源确认

```yaml
capabilities_reviewed_date:            # 浏览 cap-* / skills-manifest.json 的日期
candidates_considered:
  native_render: []                    # 渲染 pipeline / 截帧脚本家族（HTML 截帧、信息图、报纸风、带货、漫画等）
  generative: []                       # 生成式能力（cap-image-gen 文生图/图生图 · cap-video-i2v 图生视频）
  raw_materials: []                    # 真实 B-roll（cap-stock-footage）/ 真人出镜 / 屏幕录制 / GSAP / Three.js
```

**候选池完整性铁律：**
- [ ] 未把任何一个渲染家族当"默认路线"
- [ ] `skill/` 全部 `cap-*` 能力目录已至少浏览一遍
- [ ] 3 个方案**不得同家族**（不能都是截图变体 / 都是 GSAP 变体 / 都是同一合成 runtime 变体）
- [ ] 未跑「视频合成 runtime brief」前不得写"某合成 runtime 不适合"这类结论
- [ ] 候选池遗漏当即回填 `cap-*` / `skills-manifest.json` 清单，再回本节

### 3.2 视频合成 runtime brief 判断（**强制前置**）

> 若本条可能用到外部视频合成 runtime（如 Remotion / 帧序列合成 / FFmpeg 编排 / 未定），无论最终启用与否，都必须先跑一遍合成 runtime brief 得到 enabled/disabled/blocked 明确 decision，作为本条候选池讨论的输入。无相关能力则标 `n/a`。

```yaml
composition_runtime_brief_status: pending | pass | blocked | n/a   # 未 pass/blocked/n_a → 本文件不得进 form_strategy
composition_runtime_decision: enabled | disabled | blocked | n/a
composition_runtime_disabled_reason:                               # disabled 时必填一句理由
```

## 4. 三个候选表现方案（跨家族强制 · `QG-FORM-COMPETITION`）

**至少 3 个方案且必须来自至少 2 个不同家族**（如：1 个原生渲染 + 1 个生成式 + 1 个真实素材，或类似组合）。

### 方案 A

- 名称：
- **实现家族：** `native_render` / `generative` / `raw`  # 声明来自哪个家族
- 核心画面机制：
- 首屏：
- 中段：
- CTA：
- 服务指标：3s 停留 / 完播 / 理解 / 收藏 / 评论
- 优点：
- 风险：
- 制作成本：

### 方案 B

- 名称：
- **实现家族：** `native_render` / `generative` / `raw`
- 核心画面机制：
- 首屏：
- 中段：
- CTA：
- 服务指标：3s 停留 / 完播 / 理解 / 收藏 / 评论
- 优点：
- 风险：
- 制作成本：

### 方案 C

- 名称：
- **实现家族：** `native_render` / `generative` / `raw`
- 核心画面机制：
- 首屏：
- 中段：
- CTA：
- 服务指标：3s 停留 / 完播 / 理解 / 收藏 / 评论
- 优点：
- 风险：
- 制作成本：

**跨家族自查：**
- [ ] 至少覆盖 2 个不同家族（`native_render` + `generative` 或 `native_render` + `raw` 或 `generative` + `raw`）
- [ ] 3 个方案的"核心画面机制"实质不同（不是同一路线的参数变体）
- [ ] 专属视觉隐喻 ≥3 种（`QG-FORM-EXCLUSIVE`）

## 5. 选择与不选择（五维打分 · `QG-FIVE-DIM`）

> 每一镜实现选型走五维加权打分（停划×2 / 看懂×2 / 节奏×1 / 互动×1 / 证据×1 / 交付风险×0.5），加权最高分 wins；否决项不看分。

### 推荐方案

- 推荐：
- 为什么最能服务北极星（完播/理解/收藏/评论）：
- 与最近 5 条最大差异：
- 需要放弃什么：

### 不选其他方案原因

| 方案 | 不选原因 | 是否可作为后续备选 |
|------|----------|--------------------|
| A | | |
| B | | |
| C | | |

## 6. 禁止从旧 storyboard 开始改

- [ ] 本条不是复制上一条 storyboard 后改字。
- [ ] 本条不是旧模板换标题、换颜色、换字幕。
- [ ] 若复用组件，只复用能力，不复用画面骨架。
- [ ] 分镜将从本条视觉命题生成，而不是从旧镜头顺序生成。

## 7. 进入 form_strategy 的条件

- [ ] 至少 3 个候选方案完整。
- [ ] 3 个方案覆盖 ≥2 个不同家族（`native_render` / `generative` / `raw`）（`QG-FORM-COMPETITION`）。
- [ ] 专属视觉隐喻 ≥3 种（`QG-FORM-EXCLUSIVE`）。
- [ ] 有明确推荐方案（五维打分 `QG-FIVE-DIM`）。
- [ ] 写清楚不选其他方案原因。
- [ ] 写清楚与最近 5 条的差异。
- [ ] 明确禁止旧 storyboard 改字。
- [ ] 视频合成 runtime brief 已跑，decision 明确（enabled/disabled/blocked/n_a）。
- [ ] 候选池完整性自查 §3 全过。

任一项未完成：`status: fail`，禁止进入 storyboard。
