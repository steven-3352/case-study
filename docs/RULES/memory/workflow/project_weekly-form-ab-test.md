---
name: weekly-form-ab-test
description: 每周 D01-D07 形式差异化 A/B · 三维判据 · 玩法 B 同主题簇不同形 · 归因表反哺下周
metadata: 
  node_type: memory
  type: project
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**事实:** 2026-07-20 用户拍板固化"周维度形式差异化 A/B"规则,写入 `CLAUDE.md` 顶层工作模式的"周维度"小节 + 建 `docs/design/weekly_form_ab_test_TEMPLATE.md` 供每周复用。项目以周为节奏(D01-D07),每周制作 7 天素材时**每天用一种"完全不同"的表现形式**,让形式本身成为可归因变量。

### 三维判据(每两日至少 2 维不同)

- **① 渲染家族**:P001 / P002 / P004 / P005 / P006 / P007 / P011 Seedance / grok i2v / 真人出镜 / 真实 B-roll / 未来新集成
- **② 视觉语汇**(源自 57 skill):cinematic / 3d-cgi / cartoon / comic / 报纸风 / vibe motion / fashion lookbook / food ASMR / 病毒钩子 / 电商 / 房产漫游 / MV / 品牌故事 / SaaS 动效 等
- **③ 形态类型**:演示型 / 知识型 / 带货型 / 出镜型 / 图文轮播

**判据**:两日之间至少 2 维不同 · 一周三维都有变化 · 每日至少 1 条命中 57 skill 里未用过的能力(强制探索防闲置)。伪多样(如"P004 电影 vs P004 vibe motion"只换视觉语汇不换家族)→ 退回 agent 重排。

### 玩法 B(拍板走这个)

- **B · 同主题簇不同形** — 一周同 1 大主题(如"AI 工具批处理")下拆 7 个子选题 · 每子选题一种不同形式
- 拒绝玩法 A(同题重复观众疲劳)· 拒绝玩法 C(变量太多归因失效)
- 归因逻辑:同主题簇内比较,形式差异贡献占主导

### 周维度多 2 个操作(不占用户 5 拍板点)

- **周一开工前**:agent 出 7 天形式分配单 → 用户抽验 1 次
- **周日/次周一**:agent 数据回填 + 形式排名 → 生成 `weekly_form_ab_test_W{NN}.md` → 用户看结论(不改)

单条仍走 4 步 5 拍板点([[project_user-agent-4step-workflow]])——周维度是**跨条约束**,不改单条流程。

**Why:** 用户 2026-07-20 提出——不然容易"就走 P004 吧"心智固化([[feedback_no-default-tech-stack]]),57 个 skill 也会闲置。走 A/B 测试后,数据回填直接反哺下周,呼应 [[feedback_audience-first]] 完播北极星的闭环学习。我评审提出 3 个必答判据(何为"完全不同" / 同题 vs 不同题 / 归因记录框架),用户认可我建议的方案(三维 2 维不同 + 玩法 B + 每周归因表)。

**How to apply:**
- **周一开工前**:先看上周 `weekly_form_ab_test_W{NN-1}.md` 的"⑥ 保/弃/组合"→ 基于此定本周 7 天分配单
- **每日走 4 步 5 拍板点**:选题/前期/制作/交付+复盘 · 单条不受周维度干扰
- **周日/次周一 agent 自动**:
  1. 从 `pipeline/fetch_platform_metrics.py` 拉数据回填
  2. 计算完播 3s / 完播率 / 收藏率 / 评论率 · 排名
  3. 归因判断(排除主题差异 · 形式差异贡献占主导)
  4. 生成 `weekly_form_ab_test_W{NN}.md`
  5. 反哺 `queue/topics.yaml` 下周批 + `evolution_overlay.md`
- **违反判据**:
  - ❌ 7 天里 3 天以上用同一 P00X 渲染家族 → 伪多样,退 agent 重排
  - ❌ 无 `weekly_form_ab_test_W{NN}.md` → 违反本条,数据学不到 · 每条视频从零脑暴
  - ❌ 混玩法(部分同题部分不同题)→ 归因失效,退回选题定稿
- **模板路径**:`docs/design/weekly_form_ab_test_TEMPLATE.md`
- **相关**:[[project_user-agent-4step-workflow]](周维度嵌在 4 步框架里)· [[feedback_audience-first]](数据回填反哺是北极星闭环)· [[feedback_no-default-tech-stack]](防默认心智)· [[visual-form-inspiration-library]](形式候选池)· [[feedback_delta-docs-only]](单条 delta 文档不冲突,周表是跨条汇总)
