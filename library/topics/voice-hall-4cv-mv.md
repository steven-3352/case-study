---
name: voice-hall-4cv-mv
type: topic
last_updated: 2026-07-22
source_projects:
  - publish/语音厅 (v1 · 2026-07-21)
  - publish/语音厅 (v2 · 2026-07-21)
  - publish/语音厅 (v3 · 2026-07-22)
tags: [topic, voice-hall, cv-group, mv, illustration, douyin]
reuse_scope: 同类选题参考（语音厅推广 + CV 群像 + 同人 MV）· 附三次教训不可绕过
freshness_horizon: never
---

# 选题 · 语音厅 4 CV 群像 MV（明月天涯）

## 选题简介

**语音厅平台 + 4 位 CV 并列群像 + 明月天涯导唱 WAV（53s）+ 抖音 9:16 竖屏**  
定位：语音厅平台通指推广 · 软 CTA · 只留情绪气氛 · 不做硬导流  
物料：cy / 诺兰 / 轩珩 / 中里毅2 四张静态立绘 PNG + 明月天涯导唱 WAV（53.08s）

---

## 三次迭代历史（教训库 · 不可绕过）

### v1 · 2026-07-21 · 9 镜 · PPT 感事故

**用什么做的：** P004 HTML+GSAP + ffmpeg zoompan  
**出了什么问题：**
- 主 LLM 自己兼任动画导演 · 跳过多工种协作流程
- zoompan 参数写了 Ken Burns / parallax 效果名 · 实际人物位移 <4% 屏宽 · 肉眼判静止（PPT 感）
- 无独立验收 · 自己写代码自己看一眼说"还行"

**根本原因：** 效果名字被当"已实现"凭证 · 感知目标从未独立存在

**修复：** 新建 `prd_pipeline.js` + `subagent_prd_schema.md` + `WORKFLOW_EXECUTION_LOG.md` + 独立运镜验收 `qa_motion.py`

**对未来同类选题的约束：**
- **动画导演必须独立子 agent 调用** · 主 LLM 不得兼任
- **perceptual_goal.observable_metric 必须写可抽帧量级** · 禁效果名/术语
- **独立验收进程**（验收者 ≠ 产出者）是必要条件

---

### v1 复跑 · 2026-07-21 · 9 镜 · 复跑仍微颤

**用什么做的：** 同 v1 · 添加了独立 observable_metric + 独立验收 `qa_motion.py`  
**出了什么问题：**
- 独立验收机制已建 · 但 s0 实测首末位移仅 16px（0.8% 屏高）
- 实现层技术直觉错了：plate 低 zoom（~1.1x）下竖向位移物理上只有 ~60px · 到不了 190px 底线

**修复：** 
- `dy ≈ H × (z_avg - 1) × py_sweep` 经验式反解 zoom 参数
- zoompan 单帧输入改为 `-i + d=n`（禁 `-loop 1 -t + d=1` 掉帧）
- 全 9 镜重标运镜参数 · s0=213px/20pt · 副歌镜 AND 双过

**对未来同类选题的约束：**
- **observable_metric 是必要不充分条件** · 真正兜底的是"独立抽帧量化验收 + 二元底线"
- **zoompan 必须先用经验式反解参数** · 禁拍脑袋写参数后等验收退回
- **低 zoom（<1.15x）+ 小 plate 的物理上限是设计陷阱** · 要位移就得抬 zoom 或加大 plate

---

### v2 · 2026-07-21 · 22 单元 · 三差评"运镜小/转场慢/形式单一"

**用什么做的：** render_mv2.py · 22 单元 · 8 种运镜 · 7 种转场 · 9 种版式  
**出了什么问题（用户三差评）：**
- ①运镜幅度太小基本在微微颤抖 · 要更明显+多种运镜不单一
- ②转场节奏慢还是像 PPT 且单一
- ③从始至终表现形式单一

**根本原因：**
- v1 复跑独立验收只验了"单镜位移量级" · 没验"跨镜手法多样性"
- 9 镜全部用同一种缓推运镜 + 同一种叠化转场 + 同一种单人全屏版式
- 逐镜合格但连起来看单调如 PPT

**修复：**
- `qa_motion2.py` 加"手法多样性"硬约束层：运镜去重 ≥6 · 转场去重 ≥5 · 版式去重 ≥5 · 相邻不重复 · 无单一手法过半 ≤11/22
- 22 单元 · 8 种运镜（punch/scan/whip/snap/rise/dutch/pullback/shake）· 7 种转场 · 9 种视觉版式

**对未来同类选题的约束：**
- **"逐镜合格 ≠ 整片不单调"** — 单镜位移验收是必要条件 · 跨镜多样性是另一层
- **独立验收器必须同时含"单镜量级" + "跨镜多样性"两层** · 缺一层就会出现 v2 那种情况
- **多样性层至少含**：运镜/转场/版式三维去重下限 + 相邻不重复 + 无单一手法过半
- zoom 跨度作杠杆时注意浮点：1.50-1.10 在 float 下 = 39.9999 < 40 · 定"≥40pt"硬阈值要么留容差要么直接抬到 44pt

---

### v3 · 2026-07-22 · workflow 走查

**做了什么：** 走查 22 agent workflow 流程 · A1-A10 完成  
**发现的架构问题（用户诊断）：** 
- 22 agent 混淆了"低频高复用的长期知识资产"和"单次制作产出"两种活动
- A2 选题深挖师 / A5 领域专家 / A7 网络调研员 这类角色产出的受众/原话/领域知识 · 每条选题从零重造 · 实际可以复用
- 导致每条选题洞察包工作量大 · 且深度有限（因时间不足只能浅挖）

**重构方案（2026-07-22 用户拍板）：**
- 建立 `library/` 作为长期资产库（低频改变 · 高复用度）
- A 层库维护员（约 7 个）独立触发 · 仅用户手动命令
- B 层制作 workflow（约 12-14 个 agent）从库取材 · 不重挖
- v3 洞察包产出全部提炼入库（见下方"本条入库产出"）

**对未来同类选题的约束（+对 workflow 的永久改变）：**
- **开工前先查库**（`library/` 是否已有所需领域/受众/原话/形式家族）
- **库没有 = 报告缺项 + 等用户拍板是否补库**（不自动重挖）
- **22 agent 重构为 A 层库维护 + B 层制作两轨** · B 层制作 agent 数从 22 精简为约 12-14

---

## 本条入库产出（从 v3 洞察包抽出 · 可复用）

| 库文件 | 路径 | 内容摘要 |
|---|---|---|
| 领域知识 | `library/domains/voice-social.md` | 语音社交跨平台业务地图 + 4 家竞品 + 氪金三层 |
| 受众 · 外圈 | `library/audiences/voice-social-listener.md` | 都市青年深夜声音消费者画像 |
| 受众 · 中圈 | `library/audiences/cv-fandom-core.md` | CV 声控核心粉画像 |
| 受众 · 内圈 | `library/audiences/voice-hall-churned.md` | 语音厅弃坑玩家画像 |
| 原话 · CV 稀缺 | `library/quotes/voice-social/cv-scarcity.md` | 1 条一手知乎原话 · CV 一听钟情 |
| 原话 · 深夜陪伴 | `library/quotes/voice-social/night-companion.md` | 2 条（1 一手 App Store + 1 二手） |
| 原话 · 尬聊疲态 | `library/quotes/voice-social/awkward-fatigue.md` | 1 条二手 · 尬场机制 |
| 原话 · 弃坑氪金 | `library/quotes/voice-social/churn-anti-monetization.md` | 3 条二手 · 付费墙/变味/贡献榜 |
| 亚文化字典 | `library/subcultures/cv-fandom-lexicon.md` | CV 圈 7 梗 5 雷 |
| 视觉符号 | `library/visual_language/voice-social-symbols.md` | 10 通用符号 + 7 禁用元素 |
| 动效技术 | `library/motion_tech/candidate_families.md` | 8 动态元素 + 5 技术家族 + v1/v2 踩坑记录 |
| 形式家族 | `library/formats/cv-mv-families.md` | CV MV 3 类现存做法 |
| 钩子公式 | `library/formats/douyin-hooks.md` | 抖音前 3s 3 类钩子 + 转场基线 |
| 方法论 | `library/methodology/quote-validation.md` | 合成原话 vs 真原话验证协议 |
| 方法论 | `library/methodology/core-extraction.md` | 3-5 条不可删关键信息提炼协议 |

---

## 本条未入库产出（本条独有 · 换选题不复用）

以下产出保留在 `publish/语音厅/` · 是本条 v3 施工文档：

| 文件 | 内容 |
|---|---|
| `design/project_brief.md` | A1 编导立项单 · 本条 4 OM + 用户 6 字段拍板 |
| `insights/topic_brief.md` | A2 选题深挖师 · 三层受众 40/40/20 + 三场景 + 5 痛点 + 4 心理位移 |
| `insights/external_references.md` | A7 网络调研员 · 7 条真原话 + 4 家竞品 + 3 类 MV 家族 |
| `insights/domain_notes.md` | A5 领域专家 · 4 CV 业务位猜想 + 符号字典（含本条 4 CV 专属信息） |
| `insights/core_message.md` | A4 内核提炼师 · 5 条不可删 + 价值锚 14 字 |
| `insights/narrative_arc.md` | A8 纪录片导演 · 4 段结构 + 5 情绪锚点 + 4 CV 叙事功能 + 4 反 v2 硬约束 |
| `design/retention_beat_sheet.md` | A9 留存节拍 · 24 beat · 22.0s 副歌爆点 · 48.0s 软 CTA |
| `design/anti_mediocrity_tournament.md` | A10 编剧 · 24 beat 逐 beat 字幕 · 价值锚 14 字 |
| `insights/A3_A6_role_skip_decision.md` | A3 合并/A6 空跑决策存档 |
| `insights/fact_check.md` | A6 事实校验员空跑声明 |
| `design/WORKFLOW_EXECUTION_LOG.md`（项目层） | v1/v2/v3 三条执行错误登记 |
| `qa_motion.py` / `qa_motion2.py` | 独立运镜验收器（v1 复跑/v2 沉淀 · 可复用工具资产） |

---

## 下次处理同类选题时的起手动作

1. **先查库**：`library/audiences/`（三层受众是否齐）+ `library/quotes/voice-social/`（相关原话是否充足）+ `library/domains/voice-social.md`（领域知识是否更新）
2. **原话库不够 → 起 A-DR2 舆情/原话档案员补挖** · 等用户拍板
3. **领域知识过期（90d）→ 起 A-DR1 领域研究员重扒**
4. **B 层制作 workflow 从 22 精简为约 12-14** · 参考 v3 workflow 走查结论
5. **所有静态立绘选题必带 `library/motion_tech/candidate_families.md`**（zoompan 天花板 + i2v 幻觉风险 + qa_motion2 验收）
