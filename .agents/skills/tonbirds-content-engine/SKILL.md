---
name: tonbirds-content-engine
description: |
  **Tonbirds Content Engine · 内容制作引擎 · 完整工作流编排**
  
  覆盖"选题 → 洞察 → 脚本 → 分镜确认 → 制作 → 验收 → 交付"全链路。
  
  本 skill 解决了原 22 agent workflow 的核心缺陷：把"长期知识资产维护"（A层）
  和"单条选题制作"（B层）混在一起，导致每条选题重复挖掘可复用的领域/受众/原话知识。
  
  触发场景：
  - 用户说"帮我做一条 XX" / "这条选题怎么做" / "走一遍流程"
  - 用户给了选题方向/素材/需求
  - 用户说"研究一下 XX 领域/受众/形式"（A层触发）
  
  **两轨并存：**
  - A层（库维护） = 用户手动触发·一次挖清楚·入库复用
  - B层（单条制作） = 每条选题跑一遍·从库取材·不重挖
platforms:
  - claude-code
  - cursor
---

# Tonbirds Content Engine · 内容制作引擎

> **Version:** 2.0 · 2026-07-22  
> **重构原因：** v3 语音厅 workflow 走查发现 22 agent 混淆了"长期资产维护"和"单次制作"两类活动，导致每条选题从零重造可复用知识。见 `docs/design/WORKFLOW_EXECUTION_LOG.md` + `library/README.md`。

---

## 0 · 两轨架构总览

```
┌─────────────────────────────────────────────────────────┐
│  A层 · 库维护轨（低频·用户手动触发·入 library/）           │
│                                                         │
│  A-DR1 领域研究员  A-DR2 原话档案员  A-DR3 形式观察员      │
│  A-DR4 受众研究员  A-DR5 视觉语言库  A-DR6 动效技术档案员   │
│  A-DR7 亚文化词典员                                       │
└─────────────────────────────────────────────────────────┘
                         ↓ 查库 · 缺项报告
┌─────────────────────────────────────────────────────────┐
│  B层 · 单条制作轨（每条选题跑一遍 · 从库取材）              │
│                                                         │
│  B1编导 → B2选题深挖 → B3内核 → B4叙事弧线 →             │
│  B5留存节拍 → B6编剧 → B7形式策略 → B8视觉语言 →         │
│                                                         │
│  ⭐ 大白话分镜硬门（用户确认每个分镜画面+动效）             │
│                                                         │
│  B9动画导演 → B10导演摄像 → B11动效技术 → B12声音 →      │
│  制作(prd_pipeline) → B13独立验收 → B14预测 → B15运营    │
└─────────────────────────────────────────────────────────┘
```

**库取材协议（B层每个 agent 开工前）：**
1. 查 `library/` 是否已有所需领域/受众/原话/形式/视觉知识
2. 有 → 直接引用 · 不重挖
3. 没有 → **报告缺项** · 等用户拍板"是补库（触发A层）还是靠常识往下"

---

## 一、A层 · 库维护员触发协议

### 触发规则（铁律）

**仅用户手动命令触发** · B层制作遇缺项时报告但不自动起：

| 用户说什么 | 触发哪个A层agent | 入哪个库目录 |
|---|---|---|
| "帮我研究一下 XX 领域/产品/生态" | A-DR1 领域研究员 | `library/domains/` |
| "扒一批 XX 主题的用户原话/吐槽" | A-DR2 原话档案员 | `library/quotes/<domain>/` |
| "补一下 XX 形式家族/现存做法" | A-DR3 形式观察员 | `library/formats/` |
| "分析一下 XX 受众/人群画像" | A-DR4 受众研究员 | `library/audiences/` |
| "整理 XX 视觉符号/token/禁用清单" | A-DR5 视觉语言库维护员 | `library/visual_language/` |
| "扩展 XX 动效技术/可行性/踩坑" | A-DR6 动效技术档案员 | `library/motion_tech/` |
| "整理 XX 亚文化梗/雷区/圈层词典" | A-DR7 亚文化词典员 | `library/subcultures/` |

**默认关闭的触发：**
- ❌ 定期/定时自动扫库
- ❌ B层制作遇缺项自动反射触发A层
- ❌ material/ 新增文件驱动库更新

### A-DR1 · 领域研究员

**职责：** 挖指定领域的业务逻辑地图 · 竞品定位 · 用户行为链 · 氪金/转化机制

**产出格式：** `library/domains/<slug>.md`（frontmatter + 业务地图 + 竞品 + 用户行为链 + 制作层启示）

**IO：**
- 输入：领域名/平台名/产品名（用户指定）
- 输出：可复用领域知识库文件
- 不做：具体选题的立项 · 受众细化 · 原话采集（那是A-DR2/A-DR4）

### A-DR2 · 原话档案员

**职责：** 跨平台采集真实用户原话（知乎/微博/小红书/B站/贴吧/App Store）· 按 tag 分类 · 标 [一手]/[二手]

**产出格式：** `library/quotes/<domain>/<topic-tag>.md`

**IO：**
- 输入：话题关键词 + 目标平台 + 想覆盖的受众层
- 输出：原话库文件（每条含 URL + 上下文 + 可用性评估）
- 硬门：**每条必有 URL** · 拿不到 URL = 诚实标"抓不到" · 禁编原话
- 不做：内核提炼 · 字幕引用决策（那是B3内核提炼师）

### A-DR3 · 形式观察员

**职责：** 挖指定内容类型的现存做法家族 + 代表案例 + 表达上限 + 抖音/B站数据基线

**产出格式：** `library/formats/<slug>.md`

**IO：**
- 输入：内容形式关键词（如"CV MV" / "知识型短视频" / "带货种草"）
- 输出：形式家族库文件（每个家族含代表案例 URL + 表达上限 + 与不同选题距离）
- 不做：本条选题的形式决策（那是B7形式策略官）

### A-DR4 · 受众研究员

**职责：** 为指定受众类型建立可复用画像 · 含场景/姿势/抓手关键词/心理位移原型/禁触发词

**产出格式：** `library/audiences/<slug>.md`

**IO：**
- 输入：受众类型描述（如"都市青年深夜声音消费者"）
- 输出：可复用受众画像库文件
- 不做：本条选题的三层受众权重配比（那是B2选题深挖师）

### A-DR5 · 视觉语言库维护员

**职责：** 维护跨平台通用视觉符号候选池 + 平台专属禁用清单

**产出格式：** `library/visual_language/<slug>.md`

**IO：**
- 输入：主题/赛道/产品类别
- 输出：可用符号 + 禁用元素 + 使用建议（每个含"是什么/业务环节/建议用在哪段"三要素）
- 不做：具体选题的视觉色板/字体（那是B8视觉语言策展师）

### A-DR6 · 动效技术档案员

**职责：** 维护动效技术家族对照 + 踩坑记录 + 独立验收工具

**产出格式：** `library/motion_tech/<slug>.md`

**IO：**
- 输入：技术场景（如"静态立绘动起来"）
- 输出：技术家族对比 + 选型决策树 + 历史踩坑记录 + 验收工具路径
- 不做：具体选题的技术选型（那是B11动效技术导演）

### A-DR7 · 亚文化词典员

**职责：** 维护圈层梗/雷区字典 · 供编剧/运营避雷

**产出格式：** `library/subcultures/<slug>.md`

**IO：**
- 输入：圈层名称（如"CV 声控粉"/ "游戏速通圈"）
- 输出：可用梗 + 崩粉雷 + 每条含 MV/文案里"用/不用"建议
- freshness_horizon 90d（圈层快速演进）

---

## 二、B层 · 单条制作工作流

### 2.0 · 开工前必做：查库三步

**每条选题 B1 编导开工前，主 LLM 必须完成：**

```
Step 1 · 查 library/topics/ 是否有同类选题教训
  → 有 → 读 topics/<slug>.md 的"三次迭代历史"段
  → 没有 → 进 Step 2

Step 2 · 查 library/domains/ + library/audiences/ + library/formats/
  → 按选题标签匹配（如"语音社交 + CV + MV + 抖音"）
  → 列出"已有" vs "缺项"清单

Step 3 · 报告缺项 + 等用户拍板
  → "以下知识库缺项：[XX受众画像未建 / XX领域知识未挖]"
  → "是先补库（需 15-30 分钟）还是靠常识直接做？"
  → 等用户决策再进 B1
```

### 2.1 · B层 14个制作 agent 序列

**核心原则：** 每个 agent 必须独立 `Agent()` 调用 · 主 LLM 不兼任任何角色（v1 PPT 事故铁律）

| # | Agent（工种） | 读哪些库文件 | 产出 | 用户停点 |
|---|---|---|---|---|
| **B1** | 编导（总导） | `domains/` · `topics/` | `design/project_brief.md` | ✅ |
| **B2** | 选题深挖师（本条 skin） | `audiences/<>` · `quotes/<>` | `insights/topic_brief.md` | ✅ |
| **B3** | 内核提炼师 | `methodology/quote-validation.md` · `methodology/core-extraction.md` | `insights/core_message.md` | ✅ |
| **B4** | 纪录片导演 | `formats/<>` · 上游 A2/A3 洞察包 | `insights/narrative_arc.md` | ✅ |
| **B5** | 留存节拍设计师 | `formats/douyin-hooks.md` | `design/retention_beat_sheet.md` | ✅ |
| **B6** | 编剧（锦标赛或一稿） | `quotes/<>` · `subcultures/<>` | `design/anti_mediocrity_tournament.md` | ✅ 拍板脚本 |
| **B7** | 形式策略官 | `formats/` · `motion_tech/` | `design/form_strategy.md` | ✅ 拍板形态 |
| **B8** | 视觉语言策展师 | `visual_language/` | `design/design_language.md` | — 并行 |
| **B9** | 动画导演 · Motion Planner | `motion_tech/` | `design/motion_storyboard.md` | — 并行 |
| **B10** | 导演 + 摄像 | 上游全部洞察包 | `design/storyboard.md` + `design/shot_list.md` | — 并行 |
| **B11** | 动效技术导演 | `motion_tech/<>` | `design/motion_tech_plan.md` | — 并行 |
| **B12** | 声音设计师 | — | `design/audio_plan.yaml` | — 并行 |
| — | **⭐ 大白话分镜硬门** | — | 主 LLM 逐 beat 大白话总结 | **✅ 用户逐 beat 过** |
| — | 制作（prd_pipeline.js） | `design/` 全部 | 帧/音画/字幕/合成 | — 自动 |
| **B13** | 独立验收 | `motion_tech/` 的验收工具路径 | qa_motion2 + gate_check 报告 | ✅ |
| **B14** | 平台表现分析师 | — | `design/pre_publish_forecast.md`（≥B才外发） | ✅ |
| **B15** | 运营（平台文案） | `subcultures/` · `formats/` | `publish/douyin_copy.md` | ✅ 外发 |

**B8/B9/B10/B11/B12 并行：** 五个 agent 可一批启动 · 每个产出仍独立贴给用户过（不合并展示）。

**B层精简点（vs 原22个）：**
- A2 受众深挖 → 库已有 → B2 只做"本条 skin" · 不重挖通用受众（省40分钟）
- A5 领域专家 → 库已有 → B7/B11 直接引用（省30分钟）
- A7 网络调研员 → 库已有 → B3 直接引用原话（省45分钟）
- A3 记者 + A6 事实校验员 → 库已覆盖 · 仅需 B3 引用验证

**总用时目标：** 洞察包 20min + 设计包 30min + 分镜确认 15min + 制作 60min = **约 2h**（vs v2 的 2h45min）

---

## 三、⭐ 大白话分镜硬门（用户必过 · 制作开始前）

### 位置

**B9 动画导演 + B10 导演摄像 完成后 · 制作（prd_pipeline）开始前**

这是本次重构新增的硬门，原因：
- v1 PPT 事故 = 分镜都写完了但用户从来没看到"画面长什么样"
- v2 三差评 = 分镜通过了 22 个 agent 链条但用户到成片才看到"单调如 PPT"
- 解法 = 在制作前用大白话让用户脑子里有画面 · 确认后再开始渲染

### 主 LLM 的总结格式（每 beat 一行）

```
【Beat X · Y.Y-Z.Zs · A8 段 X】
画面：[谁 · 什么景别（全身/半身/特写/群像）· 背景是什么 · 表情/姿势]
动效：[具体动作描述 · 大白话 · 禁写效果名]
转场：[下一 beat 怎么切（白闪/叠化/硬切/滑入）]
服务：[服务哪层受众 + 哪条内核]
```

**大白话规则（禁 / 必）：**

| 禁止（效果名） | 必须（可观察描述） |
|---|---|
| "Ken Burns 缓推" | "相机在 4 秒内从人物腰部慢慢推到胸口·位移约 30%屏高" |
| "parallax 视差" | "前景立绘向右移 · 背景向左移 · 3 秒内各移动约 15%屏宽" |
| "zoompan 效果" | "画面整体放大 · 从 1.0x 到 1.3x · 人物从画面 40% 大变为 52% 大" |
| "情绪叙事氛围" | "暖光从左上角射入 · 落在轩珩手上的竹叶往右飘 · 每 2 秒转 1 圈" |
| "有生命感" | "cy 的白色披风在右侧风吹方向微抖 · 幅度约 5 度左右" |
| "炫酷转场" | "白色光条从左向右扫过全屏 · 0.3 秒内扫完 · 切到下一个人物" |

### 用户确认协议

- 主 LLM 把全部 beat 大白话一次性贴出（不分批）
- 用户看完后：
  - **"pass"** → 进制作
  - **"beat X 改 XX"** → 主 LLM 修改对应 beat 的 motion_storyboard · 重新贴那一 beat 让用户再过
  - **"全部重做"** → B9/B10 退回重跑（占用 1 次闭环上限）
- **闭环上限：2 轮**（修 2 次仍不过 → 用户上升决策是换路线还是降低预期）

---

## 四、用户5个拍板点（B层）

全流程只有这 5 个必须等用户拍板的地方 · 其他 agent 自主：

| # | 拍板时机 | 拍什么 | 触发下一步 |
|---|---|---|---|
| **①** | 开工前 | 选题方向 + 形态大方向 | 进 B1 编导 |
| **②** | B2 完成后 | 选题定稿 + 本条 skin（受众层、CTA、授权） | 进 B3-B4 |
| **③** | B6 完成后 | 脚本终稿 + 形态方向（编剧/形式策略官结论） | 进 B7-B12 并行 |
| **④** | 大白话分镜硬门 | 逐 beat 确认画面+动效（视频选题必做） | 进制作 |
| **⑤** | B14 完成后 | 外发拍板（forecast ≥ B + 文案审核） | 人工发布 |

**除此以外 agent 自主**：洞察/叙事弧线/节拍/视觉语言/分镜/技术方案/声音/制作/验收/预测

---

## 五、门禁系统（fail-closed）

### 内容门

| 门禁 | 条件 | 操作 |
|---|---|---|
| 洞察包门禁 | 无 external_references（≥3 URL + ≥2 原话）| 禁进内核提炼 |
| 原话验证门禁 | 无合成原话 vs 真原话验证清单 | 禁进编剧 |
| 无 motion_storyboard | 视频形态无 motion_storyboard.md | 禁进形式策略会 |
| 无 form_strategy | 视频/强互动图文无 form_strategy | 禁定 storyboard |
| 无音画方案 | 无 audio_plan.yaml | 禁进 publish |

### 制作门（自动工具）

| 工具 | 门禁逻辑 |
|---|---|
| `pipeline/gate_check_media.py` | 黑帧/死区/前6s RMS · fail-closed |
| `pipeline/gate_check_palette.py` | 主色域蓝紫 HSL H=240~290 占比 >5% · fail |
| `qa_motion2.py`（语音厅项目沉淀） | 单镜位移 ≥10%屏高 + 跨镜多样性双层硬约束 |

### 大白话分镜硬门

- **用户未 pass → 制作不启动**（无论 prd_pipeline 多急）
- 主 LLM 自己判断"分镜看起来行"不算通过 · 必须用户明确 pass

---

## 六、闭环上限表

| 环节 fail | 回退到 | 上限 |
|---|---|---|
| 洞察包不合格 | 退相应工种 | 2 轮 |
| 脚本被停划裁判判平庸 | 退编剧加锐度 | 2 轮 |
| 大白话分镜用户要求修改 | B9/B10 局部修改 | 2 轮 |
| 单镜生成崩（幻觉/AI味）| `i2v-video-diagnose` 4步走 | **3次救不活 → 换路线** |
| 独立验收 fail | 修改对应参数重渲 | 2 轮 |
| forecast fail | 退形式策略官换 route | 2 轮 |

---

## 七、library/ 查库快查表

在选题开工前，按以下表检索 `library/` 是否已覆盖所需知识：

| 选题类型 | 必查库文件 |
|---|---|
| 语音厅/语音社交 | `domains/voice-social.md` · `audiences/voice-social-listener.md` · `cv-fandom-core.md` · `voice-hall-churned.md` · `quotes/voice-social/*.md` |
| CV/立绘/同人MV | `subcultures/cv-fandom-lexicon.md` · `formats/cv-mv-families.md` · `motion_tech/candidate_families.md` · `visual_language/voice-social-symbols.md` |
| 抖音短视频通用 | `formats/douyin-hooks.md` |
| 静态立绘动起来 | `motion_tech/candidate_families.md`（含 v1/v2 zoompan 踩坑 + i2v 选型） |
| 通用方法论 | `methodology/quote-validation.md` · `methodology/core-extraction.md` |

**库文件缺项 = 报告缺项** · 不自动补 · 等用户拍板。

---

## 八、production_tier 对 B层的影响

| 档位 | 判据 | B层精简点 |
|---|---|---|
| **explore** | 小实验/demo/无外发要求 | 洞察包可串行 · B6一稿过 · B13独立验收1人 |
| **lightweight**（默认） | 单条 ≤60s · 无事实claim · 非新形态 | B6一稿过 · B13独立验收1人 · B7-B12并行组 |
| **full** | 带货/出镜/新形态首条/A/B实验周/用户点名 | B6走锦标赛N≥3 · B13独立验收≥2人 · 所有角色不砍 |

**不因档位变化的：**
- 主 LLM 不兼任任何角色（三档都禁）
- 大白话分镜硬门（视频选题三档都走）
- observable_metric 强制可量化（三档都要）
- 独立验收进程（验收者 ≠ 产出者）

---

## 九、与现有项目文件的关系

| 文件/目录 | 角色 | 关系 |
|---|---|---|
| `library/` | 长期资产库（A层维护） | B层开工前查库 |
| `publish/<project>/` | 单条制作产出（B层输出） | 不入库 · 本条独有 |
| `templates/` | 通用文档格式模板 | B层 agent 产出时参照 |
| `.claude/memory/` | 用户偏好 · 反馈记忆 | 全流程遵守 |
| `docs/design/WORKFLOW_EXECUTION_LOG.md` | 多角色协作执行错误登记 | B22（数据复盘官）交付后必写 |
| `docs/postmortems/` | 架构/技术事故复盘 | 架构级问题登记在此 |
| `queue/topics.yaml` | 待做选题运行队列 | B1 编导立项时同步更新 |

---

## 十、反例（禁止做的事）

- ❌ 主 LLM 兼任任何 B层角色（PPT 事故铁律）
- ❌ B层遇知识缺项时自动重挖（应报告 + 等用户）
- ❌ 大白话分镜硬门跳过（无论是否"测试/demo/轻量"）
- ❌ 制作前"用户没看过任何分镜"就开始渲染
- ❌ 大白话里写效果名术语（"Ken Burns" / "parallax" / "有生命感"）
- ❌ 把合成原话当真原话引入内核（见 `methodology/quote-validation.md`）
- ❌ 因"P004 是默认视频线"选实现路线（须按 SYSTEM §4.2 逐镜打分）
- ❌ 忽略 freshness_horizon 过期的库文件（过期 = 报告可能过时 · 不是禁用）
