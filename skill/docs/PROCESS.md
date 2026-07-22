# 内容生产流程文档（控制器视角）

> **原则：本文只写「谁先做、谁后做、依赖什么」。所有「怎么算过关」一律引用 `quality/quality_registry.md` 的 `QG-*` ID，不在此复述阈值。角色定义与波次以 `roles/registry.yaml` 为单一事实源，本文的波次表是它的人类可读镜像。**

---

## 1. 顶层模型：蓝图即合约（一次确认）

新选题进来时，用户用**大白话**描述想要的效果（可多主题一起），引擎自主设计脚本/风格/画面/分镜/每镜用哪几维，**只在最前面让用户确认一次**，之后无人值守跑完，交付可发布内容 + `publish.md`。

**为什么拆成两个 workflow（关键约束）**：harness 不能让一个 workflow 跑到一半停下等用户输入。所以：

```
用户大白话 brief（1 个或多个）
  │
  ▼
① workflows/blueprint.js  ── 预生产（理解→脚本→风格→形式→分镜，止于 wave 10）
  │   产出：逐分镜大白话蓝图 + 每镜用哪几维 + batched_choices（集中的待拍板点，带推荐）
  │   ★ 绝不写盘、绝不自动续跑制作 —— 这个硬停就是"只确认一次"的结构保证
  ▼
👤 用户【唯一确认点】：接受推荐，或调整 batched_choices 的编号
  │
  ▼
② workflows/prd_pipeline.js（+ 制作）── 无人值守跑完 waves 1-13 + 出片 + 门禁 + 诊断 + 适配
  │   交付：可发布内容 + publish.md
  ▼
👤 外发（用户手动发平台）→ 48h/7d 数据回填 → 复盘反哺下条
```

**「无人值守」的准确含义**：制作段里机器门（`QG-MEDIA-*`/`QG-PALETTE-NEON`/`QG-MOTION-FREEZE`…）、质量门、闭环上限**照常运行**——那是流程自身的自动校验，**不算人工干预**。只有当闭环预算耗尽（诊断 3 次仍救不活等）才把控制权交还用户，而**不是**发残次品。用户不参与每道门的逐个审阅。

---

## 2. 两个 workflow 的职责边界

| workflow | 阶段 | 跑哪些 wave | 产出 | 是否续跑 |
|---|---|---|---|---|
| `blueprint.js` | 预生产 | wave 1–10（止于分镜） | 人类可读蓝图 + batched_choices（**返回**，不写盘） | ❌ 硬停，交还用户确认 |
| `prd_pipeline.js` | 生产编排 | wave 1–13（全波次） | 结构化子 PRD + 独立验收 + 汇总复核 | 下接出片/门禁/适配 |

- 两个 workflow **各内嵌一份 `ROLE_REGISTRY` 镜像**（沙箱无 fs，无法运行时读 `registry.json`）；`workflows/validate.js` 校验两份镜像逐字段 == `registry.json`，防双写漂移。
- 激活集合由**代码确定性推导**（`activateRoles()` 按形态 + registry 的 `activation` 字段），agent 只补"每个角色的输入切片理由"。结构性杜绝"tier 减角色""实现者自兼角色"两类事故。

---

## 3. 角色波次（以 registry.yaml 为准）

各波次内角色**并行**；波与波之间保留依赖顺序——后一波拿到前面所有波次的产出摘要。`blueprint.js` 只跑到 **W10（分镜）** 为止。

| 波次 | 角色（video 全量时） | 关键门（QG-ID） |
|---|---|---|
| W1 | 编导 | `QG-PRD-ACCEPTANCE` |
| W2 | 记者 · 纪录片导演 · 网络调研员〔+带货：选品/商品分析师 · 消费者声音研究员〕 | `QG-EXTERNAL-REFS` |
| W3 | 选题深挖师 · 内核提炼师 · 领域专家 · 事实校验员 | `QG-INSIGHT-3FACTS` |
| W4 | 留存与互动设计师 | `QG-ATTENTION` · `QG-REVIEWERS` |
| W5 | 编剧〔+带货：销售脚本师 · 合规审核〕 | `QG-ANTI-MEDIOCRITY` · `QG-SCRIPT-QUOTES`〔`QG-COMPLIANCE`〕 |
| W6 | 动画导演（翻译层，单跑不设打分门） | `QG-MOTION-CREATIVE` · `QG-MOTION-FREEZE` |
| W7 | 形式策略官 | `QG-FORM-COMPETITION` · `QG-FIVE-DIM` · `QG-FORECAST` · `QG-REVIEWERS` |
| W8 | 视觉设计 · 视觉语言策展师 | `QG-PALETTE-NEON` · `QG-VISUAL-ORIGINALITY` |
| W9 | 动效技术导演（用 GSAP/Web3D/复杂动效时） | `QG-MOTION-FREEZE` · `QG-REVIEWERS` |
| **W10** | 导演 · 摄像/视觉〔+出镜：演员表演指导 · 造型/服装/场景〕 | `QG-PRD-ACCEPTANCE` ← **blueprint 止步于此** |
| W11 | 声音设计师 | `QG-MEDIA-HEAD-RMS` · `QG-REVIEWERS` |
| W12 | 剪辑 | `QG-MEDIA-BLACK` · `QG-MEDIA-SILENCE` · `QG-DELIVERY` |
| W13 | 运营/增长 | `QG-PRD-ACCEPTANCE` |
| 发布后 | 数据复盘官（`wave: post`，不在生产波次，外发后单独触发） | `QG-FORECAST` |

**形态激活**（`registry.yaml` 的 `formats` 段）：
- 演示型/知识型：always + video_only 角色
- 带货型：加带货扩展 4（合规审核/选品/消费者声音/销售脚本师）
- 出镜型：加出镜扩展 2（可叠加在任意形态上）
- 图文轮播：跳过声音设计师/动画导演/动效技术导演

**19 维是设计输入**：每个角色的 `owns_dims` 在开工时连同该维「提升 3 档目标」注入其 prompt——角色一动手就知道自己负责设计哪几维、按什么标准做，不是事后打分。详见 `quality/video_19dim_scorecard.md`「本表是设计输入」节。

---

## 4. 制作流程门（引用 QG-ID，不复述阈值）

```
蓝图确认 → prd_pipeline.js（Phase 0-4 · 每角色独立 agent · 验收 QG-PRD-ACCEPTANCE）
  → 出图/出片（调用 cap-* 能力 skill）
  → TTS（cap-tts）           ← 视频硬门：VO 全程覆盖 · 前 6s 见 QG-MEDIA-HEAD-RMS
  → 字幕叠帧
  → 色板门 QG-PALETTE-NEON · 成片体检 QG-MEDIA-* · 冻帧 QG-MOTION-FREEZE · 形式 QG-FORM-*
  → 生成后单镜诊断（QG-I2V-DIAGNOSE · 3 次上限）
  → 三平台适配
  → 投前预测 QG-FORECAST（≥B 才允许外发，C/D 禁发）
  → 外发（用户手动）
  → 48h/7d 数据回填 → QG-DELIVERY 最终判据
```

> QG-RAISE-3 元规则贯穿全程：任何门的阈值都是**地板**不是目标。"我觉得这能过"的感觉本身 = 标准定低了的信号，强制抬高 3 档再验收。

---

## 5. 闭环上限（防无限循环）

见 `QG-LOOP-LIMITS`。任何环节 fail → 按下表回退，**不超过上限即升级换路线/交还用户**：

| 环节 fail | 回退 | 上限（QG-LOOP-LIMITS） |
|---|---|---|
| 洞察包不合格 | 退记者/内核提炼师 | 2 轮 |
| 脚本被判平庸 | 退锦标赛加锐度 | 2 轮 |
| 形式 forecast fail | 退形式策略官换 route | 2 轮 |
| 单镜生成崩 | QG-I2V-DIAGNOSE 诊断 | 3 次救不活升级 |
| 三平台适配失败 | 退剪辑/文案 | 1 轮 |

预算耗尽 = 无人值守段结束、把问题交还用户的**唯一**触发条件（不是每道门都停下问）。

---

## 6. 生产档位（只影响验收强度，不减角色数）

| 档位 | 触发 | reviewer 数 | 锦标赛 |
|---|---|---|---|
| 探索 | 默认（未命中全量） | 1 | 一稿过 |
| 轻量 | ≤60s 且非全量触发 | 2 独立 | 视情况 |
| 全量 | 带货/出镜/A-B周/投后重做/新形态首条/强争议/用户点名 | 2 独立 | 全锦标赛 |

档位由 `production_tier`（explore/lightweight/full）传入，**只调验收强度**，激活哪些角色由 registry + 形态决定，与档位无关。

---

*本文档是流程控制器的定义文档。角色/波次单一事实源 = `roles/registry.yaml`；质量阈值 = `quality/quality_registry.md`；19 维设计输入 = `quality/video_19dim_scorecard.md`；能力 skill 见各 `cap-*` 目录；外部技能见 `skills-manifest.json`。*
