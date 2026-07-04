# 表现形式竞争 · form_competition

> 工种：形式策略官 + 平台原生策划 + 纪录片导演 + 动效分镜师  
> 位置：`design/form_competition.md`  
> 时机：`form_strategy.md` 之前，`storyboard.yaml` 之前。  
> 目的：阻止“默认套模板”。每条内容必须先竞争至少 3 个表现方案，再允许进入分镜。

## 0. 入口必读（开工前打勾 · **本节点错误重灾区，必须最严格**）

> memory 元规则：[[feedback_pre-node-checklist]] · 不过清单不得开工
> 教训：2026-07-04 W28D02 form_competition 3 方案都在 P001 家族，跳过了 OpenMontage，属候选池预先缩水

- [ ] **SYSTEM refs**：`docs/SYSTEM.md` **§4.2 候选实现清单（最新版）** · §2.4b 生产 whitelist · §3.1e 双平台分轨 · §4.2 五维打分
- [ ] **template refs**：本文件 §3 候选池完整性自查 · `templates/design/openmontage_brief.md`（**必须已跑**，decision 明确）· `templates/design/design_language.md`
- [ ] **memory refs**：**`feedback_no-default-tech-stack`（触发词打断）** · `feedback_pre-node-checklist`（本条元规则）· `feedback_anti-ai-visual`
- [ ] **姊妹条 refs**：同周最近 1-2 条 `publish/{week}/D0X/design/form_competition.md` + `design/openmontage_brief.md` 实读
- [ ] **能力清单 refs**：`ls integrations/` + `ls pipeline/` 各跑一次；确认没有新集成能力被漏
- [ ] **openmontage_brief 已跑**：`design/openmontage_brief.md` decision 字段 = enabled | disabled | blocked（不是 pending）

**触发词打断**（出现即回 SYSTEM §4.2）：
- 「就走 P004 吧」/「就走 P001 吧」/「用 GSAP 拼一个」
- 「fetch_broll + gen_speech + HTML 仿真 + ffmpeg 拼一个」
- 「OpenMontage 太重了不适合本条」（不跑 openmontage_brief 就写这句 = 门禁绕过）
- 「3 方案都用 P001 家族的变体也行」

## 1. 结论

```yaml
status: draft | pass | fail
content_id:
review_source: agent_reviewed | human_reviewed
decision: proceed_to_form_strategy | rewrite_competition | block_storyboard
recommended_route:
```

## 1. 本条视觉命题

> 一句话说明这条内容“画面到底要让观众看见什么”，不能写成抽象风格词。

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

## 3. 候选池完整性自查（**门禁 · 早于列方案**）

> **每次列方案前必读 `docs/SYSTEM.md §4.2 候选实现清单`。** 清单版本化，每季度/新集成入 `integrations/` 时会更新。

### 3.1 候选池来源确认

```yaml
system_ref_version_read: 2026-07-04   # 读的 SYSTEM §4.2 最后同步日期
candidates_considered:
  native_pipeline: []                 # 从 pipeline/ 考虑的（P001/P002/P004/P005-P007/produce）
  integrations: []                    # 从 integrations/ 考虑的（OpenMontage/Grok video/GPT-image-2）
  raw_materials: []                   # 真实 B-roll / 真人出镜 / 屏幕录制 / GSAP / Three
```

**候选池完整性铁律：**
- [ ] 未把 P001/P004 当"默认路线"
- [ ] `integrations/` 全目录已至少浏览一遍
- [ ] 3 个方案**不得同家族**（不能都是 P001 变体 / 都是 P004 变体 / 都是 OpenMontage 变体）
- [ ] 未跑 `openmontage_brief.md` 前不得写"OpenMontage 不适合"这类结论
- [ ] 候选池遗漏当即回填 SYSTEM §4.2 清单，再回本节

### 3.2 openmontage_brief 判断（**强制前置**）

> 无论最终启用与否，都必须先跑一遍 `design/openmontage_brief.md` 得到 enabled/disabled/blocked 明确 decision，作为本条候选池讨论的输入。

```yaml
openmontage_brief_status: pending | pass | blocked   # 未 pass/blocked → 本文件不得进 form_strategy
openmontage_decision: enabled | disabled | blocked
openmontage_disabled_reason:                          # disabled 时必填一句理由
```

## 4. 三个候选表现方案（跨家族强制）

**至少 3 个方案且必须来自至少 2 个不同家族**（如：1 个原生 pipeline + 1 个 integrations + 1 个混合，或类似组合）。

### 方案 A

- 名称：
- **实现家族：** `pipeline` / `integrations` / `raw`  # 声明来自哪个家族
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
- **实现家族：** `pipeline` / `integrations` / `raw`
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
- **实现家族：** `pipeline` / `integrations` / `raw`
- 核心画面机制：
- 首屏：
- 中段：
- CTA：
- 服务指标：3s 停留 / 完播 / 理解 / 收藏 / 评论
- 优点：
- 风险：
- 制作成本：

**跨家族自查：**
- [ ] 至少覆盖 2 个不同家族（`pipeline` + `integrations` 或 `pipeline` + `raw` 或 `integrations` + `raw`）
- [ ] 3 个方案的"核心画面机制"实质不同（不是同一路线的参数变体）

## 5. 选择与不选择

### 推荐方案

- 推荐：
- 为什么最能服务北极星：
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
- [ ] 3 个方案覆盖 ≥2 个不同家族（`pipeline` / `integrations` / `raw`）。
- [ ] 有明确推荐方案。
- [ ] 写清楚不选其他方案原因。
- [ ] 写清楚与最近 5 条的差异。
- [ ] 明确禁止旧 storyboard 改字。
- [ ] **`openmontage_brief.md` 已跑，decision 明确（enabled/disabled/blocked）。**
- [ ] **候选池完整性自查 §3 五条全过。**

任一项未完成：`status: fail`，禁止进入 storyboard。
