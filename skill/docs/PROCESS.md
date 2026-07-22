# 内容生产流程文档(控制器视角)

> **原则:本文只写「谁先做、谁后做、依赖什么」。所有「怎么算过关」一律引用 `quality/quality_registry.md` 的 `QG-*` ID,不在此复述阈值。**

---

## 1. 触发条件

用户给出内容主题/选题方向后,按下面流程跑。全程只有 **5 个用户拍板点**,其余 agent 自主。

---

## 2. 流程总览(4 步 · 5 拍板点)

| 步 | 阶段 | agent 自主 | 👤 用户拍板 |
|---|---|---|---|
| 1 | 选题 | 翻 material/ → 扩展 3-5 条候选 | ① 方向 ② 定稿 |
| 2 | 前期规划 | 洞察包 → 留存节拍 → 脚本锦标赛 → 形式策略+视觉+分镜+声音 | ③ 脚本+形态 ④ 抽验 |
| 3 | 制作 | 出图/出片 → TTS+字幕 → gate → 诊断 → 三平台适配 → `QG-FORECAST` ≥B | 无(除非诊断 3 次仍崩) |
| 4 | 交付+复盘 | 发布包 → 数据回填 → retro → evolution | ⑤ 外发 |

---

## 3. 角色波次(工种执行顺序)

各波次内角色可并行;波与波之间保留粗粒度依赖顺序——后一波拿到前面所有波次产出摘要。

| 波次 | 角色 | 关键门(引用 QG-ID) | 门位 |
|---|---|---|---|
| W1 | 网络调研员 | `QG-EXTERNAL-REFS`(≥3 URL+≥2 原话) | 洞察包定稿前 |
| W2 | 选题深挖师 | — | — |
| W3 | 内核提炼师 · 领域专家 · 事实校验员 | `QG-INSIGHT-3FACTS` | 洞察包完成前 |
| W4 | 编导 | — | — |
| W5 | 记者 · 纪录片导演 | `QG-INSIGHT-3FACTS` 退回触发 | — |
| W6 | 留存与互动设计师 | `QG-SCORECARD-90`(双评) | Phase B |
| W7 | 编剧 | `QG-ANTI-MEDIOCRITY` · `QG-SCRIPT-QUOTES` | 锦标赛后 |
| W8 | 视觉设计 · 视觉语言策展师 | `QG-VISUAL-ORIGINALITY` · `QG-SCORECARD-90` | Phase B |
| W9 | 形式策略官 | `QG-FIVE-DIM` · `QG-FORM-COMPETITION` · `QG-SCORECARD-90` | 定分镜前 |
| W10 | 动画导演 | 单跑(翻译层,不设打分门) | — |
| W11 | 动效技术导演 · 声音设计师 | `QG-SCORECARD-90`(双评) | Phase B |
| W12 | 导演(执行) · 摄像/视觉 | `QG-FIVE-DIM` 实现选型 | 出镜/复杂动效时 |
| W13 | 剪辑 · 运营/增长 | `QG-TWO-GATES` · `QG-FORECAST` ≥B | 外发前 |

**扩展波次(按形态激活):**
- 带货型:W3 后插入合规审核/选品/消费者声音研究员;W7 后插入销售脚本师(`QG-COMPLIANCE`)
- 出镜型:W8 后追加演员表演指导+造型

---

## 4. 制作流程门(引用 QG-ID,不复述阈值)

```
PRD 定稿
  → Workflow: prd_pipeline.js(Phase 0-4 强制 · 每角色独立 agent · 验收 QG-PRD-ACCEPTANCE)
  → 出图/出片(调用 cap-* 能力 skill)
  → TTS(cap-tts)  ← 视频硬门:VO 全程覆盖 · 前 6s 见 QG-MEDIA-HEAD-RMS
  → 字幕叠帧
  → gate_check_palette(QG-PALETTE-NEON) · gate_check_media(QG-MEDIA-*) · gate_check(QG-MOTION-FREEZE / QG-FORM-*)
  → 生成后单镜诊断(QG-I2V-DIAGNOSE · 3 次上限)
  → 三平台适配
  → pre_publish_forecast(QG-FORECAST ≥B · 不达标禁发)
  → 外发(用户手动)
  → 48h/7d 数据回填 → QG-DELIVERY 最终判据
```

---

## 5. 闭环上限(防无限循环)

见 `QG-LOOP-LIMITS`。任何环节 fail → 按下表回退,**不超过上限即升级换路线**:

| 环节 fail | 回退 | 上限(QG-LOOP-LIMITS) |
|---|---|---|
| 洞察包不合格 | 退记者/内核提炼师 | 2 轮 |
| 脚本被判平庸 | 退锦标赛加锐度 | 2 轮 |
| 形式 forecast fail | 退形式策略官换 route | 2 轮 |
| 单镜生成崩 | QG-I2V-DIAGNOSE 诊断 | 3 次救不活升级 |
| 三平台适配失败 | 退剪辑/文案 | 1 轮 |

---

## 6. 生产档位(只影响验收强度,不减角色数)

| 档位 | 触发 | reviewer 数 | 锦标赛 |
|---|---|---|---|
| 探索 | 默认(未命中全量) | 1 | 一稿过 |
| 轻量 | ≤60s 且非全量触发 | 2 独立 | 视情况 |
| 全量 | 带货/出镜/A-B周/投后重做/新形态首条/强争议/用户点名 | 2 独立 | 全锦标赛 |

---

*本文档是流程控制器的定义文档。质量阈值见 `quality/quality_registry.md`;能力 skill 见各 `cap-*` 目录;外部技能见 `skills-manifest.json`。*
