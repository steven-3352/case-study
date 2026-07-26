---
name: user-agent-4step-workflow
description: case-study 顶层工作模式 4 步框架 · 5 个用户拍板点 · 其余 agent 自主 · CLAUDE.md 已立
metadata: 
  node_type: memory
  type: project
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**事实:** 2026-07-20 用户拍板固化项目顶层工作模式为 4 步框架,写入 `CLAUDE.md` "顶层工作模式" 章节(在 "核心工作流程:新选题多工种协作模式" 15 步之前作为外壳)。4 步 = **选题 → 前期规划 → 制作 → 交付+复盘**;每步内嵌子步(agent 自主);全流程**只有 5 个用户拍板点**。

### 5 个用户拍板点(全流程唯一 · 不多不少)

1. **选题方向** — 步骤 1 起点
2. **选题定稿** — 从 agent 扩展的 3-5 条候选里拍板 1 条
3. **脚本终稿 + 形态大方向** — 锦标赛停划裁判后
4. **抽验** — 前期规划末尾(视觉/分镜/声音等)看一眼,不逐个
5. **外发** — 用户手动发到抖音 / xhs

### agent 自主段(用户不参与)

洞察包 4 件 + 网络调研 · 留存节拍 · 脚本 N 版竞写 · 形式打分 · 视觉语言 · 分镜 · 技术可行 · 声音 · 制作全流程(出图/出片/TTS/字幕/SFX)· gate 门禁(media/palette)· 生成后诊断(i2v-video-diagnose)· 三平台适配 · 投后 48h/7d 数据回填 · `post_publish_retro` · `evolution_overlay` 反哺下条。

### 闭环规则(反无限循环)

- 洞察包/脚本/形式 fail → 退对应工种 · **2 轮上限**
- 单镜生成崩 → `i2v-video-diagnose` 4 步 minimal-edit · **3 次救不活升级换实现**(换模型/撤镜/换 B-roll)
- 三平台适配 fail → 退剪辑 · 1 轮
- 投后 48h 差评 → 反哺下条 `evolution_overlay`,不救本条

**Why:** 用户 2026-07-20 提出粗略 4 步(选题/材料脚本分镜形式/制作/验收),我评审指出粒度太粗 + 缺 4 环节(选题挖矿前置 · 15 步顺序铁律 · 生成后诊断 · 投后复盘)+ 5 个拍板点边界不清。用户认可优化版,固化。本框架**不与 15 步冲突**,是同流程两视角:用户看 4 步 5 拍板点,agent 跑 15 步 22 工种,只在 5 个点回找用户。

**How to apply:**
- 收到新选题 → agent **不问用户"要不要跑洞察包/脚本锦标赛/形式打分"**——那些是 agent 自主段,静默跑
- 每次跑到用户拍板点(1-5)才停下等用户 · 其他时候直接产出下一子步
- 违反判据:
  - ❌ agent 跑到子步(如脚本 N 版竞写)时问用户"你希望走 A/B/C 哪种钩子?" → 违反本条,应自主并行 N 版让停划裁判判优,再交定稿
  - ❌ 用户被要求参与"每个子步都确认" → 违反 [[feedback_autonomous-data-driven]] + [[feedback_d05-parallel-agents]]
  - ❌ 制作跑通就算过 → 违反 [[feedback_audience-first]] 铁律 0;必须过 `pre_publish_forecast` ≥ B 才交付
  - ❌ 投后不做数据回填 → 违反本框架步骤 4;每条必写 `post_publish_retro.md`
- **相关**:[[feedback_autonomous-data-driven]](本框架子条实现)· [[feedback_d05-parallel-agents]](60min 目标依赖 agent 并行 · 用户少介入)· [[feedback_user-picks-active-agents]](开工前 active_roles 用户勾选,是**步骤 2 之前**的一次性动作,不冲突)· [[feedback_multi-role-collab]](15 步详细流程)· [[feedback_audience-first]](交付判据)· [[project_i2v-video-diagnose-skill]](步骤 3 内环)· [[feedback_agent-auto-mount-skills]](步骤 3 中 agent 自主挂 skill)
