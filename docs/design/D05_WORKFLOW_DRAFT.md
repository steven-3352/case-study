# D05 workflow · draft for user review

> 用途：D05 开工前的流程 + 规范草稿 · 用户 review 后确认再启动 D05 实际执行
>
> 只写与 D04 及 SYSTEM.md 的 **delta**（不复述 15 步、10 合并 agent 结构 · 引 CLAUDE.md 段号）
>
> **状态：** DRAFT · 待用户确认 · **未确认前不启动 D05**

---

## 1. 收纳的 D04 教训（5 个必改）

| # | D04 出问题 | D05 改法 | 落地位置 |
|---|-----------|---------|---------|
| 1 | 前 3s 沉默钉子 · 无 VO 无 sfx · 3s 完播率崩 | **VO 从 0s 覆盖**（禁 s1_silence 段设计） | audio_plan.yaml + pipeline_config.yaml |
| 2 | 视频号浪费一份 mp4 + 一份发布文案 | **只出 douyin + xhs 两平台** | pipeline_config.yaml.platforms（DEFAULT 已删 weixin） |
| 3 | xhs 默认沿用抖音 mp4 · 漏 7 页图文轮播（verdict 有写但没做） | **xhs 形态由形式策略官定** · video vs 7 页轮播 二选一 | design/form_strategy.md "xhs 形态判定" 段 |
| 4 | agent 未在交付前听 vo.mp3 前 5s 波形 · 形式监控盲区 | **交付前必听 vo 前 5s + 全片** · 波形 or 转文本核对 | Agent 自查项（无门禁工具化，靠 checklist） |
| 5 | 8k+ 字文档冗长 · 复述框架内容 | **delta-docs 硬字数上限**（memory feedback_delta-docs-only） | 每份文档 `wc -c` 超即回炉 |

## 2. 流程（15 步 / 10 合并 agent · delta only）

流程本身**沿用 CLAUDE.md 定义**（15 步 + 10 合并 agent · 见 CLAUDE.md 「核心工作流程」段）。D05 的 delta：

### 2.1 加速三件套（memory feedback_d05-parallel-agents / feedback_delta-docs-only / lib code gates）

- **A · Agent 并行化**：三批次同批次 tool_use
  - 批 1（洞察 4 件套）：topic_brief · reporter_notes · external_references · core_message + fact_check — **同批 3 min**
  - 批 2（设计 3 件套）：design_language · form_competition · form_strategy 起草 — **同批 10 min**
  - 批 3（TTS + UI + broll）：TTS 合成 · gen_ui 出 PNG · fetch_broll 拉 Pexels — **同批 5 min**
  - **不并行**：编剧+ vB 双评 · 形式策略官双评 · pipeline TTS→preview→platforms 三步（严格串行）
- **B · Delta 文档硬字数上限**（memory feedback_delta-docs-only）
  - topic_brief ≤2.5k · reporter_notes ≤4k · design_language ≤5k · form_strategy ≤8k · motion_storyboard ≤8k
  - `wc -c <file>` 超即回炉 · 不允许"这份重要所以多写点"
- **C · Config-driven pipeline 三道硬门**（已入 lib · D04 已验证）
  - TTS estimate_duration + 60s cap · 90% warn / 97% fail
  - config lint · overlay/UI PNG 冗余（headline ≥80pt · text ≥6 字落 img scene）
  - CTA ship gate · sum(scene.total_dur) ≥ seg_total - 0.5s
  - scene realign 自动建议

### 2.2 时间预算（D04 2h45min → D05 目标 60min）

| 阶段 | D04 用时 | D05 目标 | 加速手段 |
|-----|---------|---------|---------|
| 选题 + 立项 | 5min | 5min | — |
| 洞察 4 件套 | 25min | 3min | A 并行 + B delta |
| 留存节拍表 | 10min | 5min | B delta |
| 编剧 v0/vA/vB + 双评 | 40min | 25min | vB 双评保留（硬约束）· 减复述 |
| 设计 3 件套 | 30min | 10min | A 并行 + B delta |
| 形式策略官 + 双评 | 20min | 15min | 保留 |
| 动画导演单跑 | 15min | 5min | B delta |
| storyboard + audio_plan | 15min | 5min | B delta + 引 form_strategy 段号 |
| gen_ui + broll + TTS | 20min | 5min | A 并行 |
| pipeline vo + preview + platforms | 15min | 15min | 串行（无法压） |
| 运营 + 发布包 | 10min | 5min | 双平台减一半 |
| **合计** | **165min** | **≈60min** | — |

**风险**：编剧 vB 双评 + 形式策略官双评 = 40min · 占 D05 总时长 2/3 · 若 vB 首轮 <90 需 round 2 → 时长可能拉到 90min

## 3. 规范（delta only · 与 CLAUDE.md 差异）

### 3.1 新规（D05 起硬约束）

- **VO 从 0s 覆盖**（memory feedback_dense-vo-no-dead-air）· 禁 s1_silence 段设计 · 前 6s 波形必查
- **双平台 only**（memory feedback_dual-platform-only）· pipeline_config.yaml.platforms 禁写 weixin
- **xhs 形态由形式策略官定** · form_strategy 必带 "xhs 形态判定" 段（video vs 7 页轮播）
- **delta 文档硬字数上限**（memory feedback_delta-docs-only）
- **Agent 并行化三批次**（memory feedback_d05-parallel-agents）· 单条同批 tool_use ≥ 3

### 3.2 保留规则（沿用 D04）

- **10 合并 agent 工作流**（DECISIONS Q12）· 编剧+ / 形式策略官 双评 · 其余单跑
- **动画导演单跑不双评**（DECISIONS Q11）
- **audience-first**（memory feedback_audience-first）· 内容共鸣 + 强观赏性 + 强内容
- **openmontage_brief 每条必跑**（DECISIONS Q10）
- **TTS 前置估算门**（memory tts-estimate-duration-pre-synth）· audio_plan 写完必跑 · ≥30% 溢出 fail
- **active_roles 用户拍板**（memory feedback_user-picks-active-agents）· 每条开工前列候选清单

### 3.3 用户 confirm 点（务必勾选）

**A · 加速三件套是否全启用？**
- [ ] A 并行化（洞察 4 / 设计 3 / TTS·UI·broll 三条同批 tool_use）
- [ ] B delta 文档字数上限（超即回炉）
- [ ] C pipeline 三道硬门（已入 lib · 自动生效）

**B · 双平台形式**
- [ ] 抖音视频（默认）
- [ ] 小红书 · 由形式策略官在 form_strategy 段判定视频 or 7 页轮播（不预设）

**C · D04 5 教训是否全收纳？**
- [ ] 教训 1：VO 从 0s 覆盖（禁沉默钉子）
- [ ] 教训 2：只出双平台
- [ ] 教训 3：xhs 形态由形式策略官定
- [ ] 教训 4：交付前必听 vo 前 5s + 全片
- [ ] 教训 5：delta 文档硬字数上限

**D · D05 选题**
- 用户提供 D05 选题（title + 受众 skin + 主推平台 + P0-P3 关键信息条数）
- 或从 `queue/topics.yaml` 里指定 topic_id
- 或从 D04 迭代方向（如"AI 帮想视频选题"的 v2 · 换受众 skin：家居→美妆/母婴/数码）

**E · active_roles 勾选**（用户 review D05 选题后我列候选清单）

## 4. 时间承诺

- 用户 review 本 draft + confirm A/B/C/D/E → **5 min**
- Agent 起步 D05（选题 → 洞察 → 脚本 → 设计 → pipeline → 发布包）→ **60 min**（若无 vB round 2）
- Agent 交付 D05 → **≤90 min 总**（含 review confirm 时间）

## 5. 需用户确认的一个关键决策

> **P1 sfx-mixer 是否需要在 D05 前落地？**

- 现状：#66 sfx-catalog / #67 sfx-mixer / #68 bgm-catalog / #69 sfx-fetcher / #70 sfx-search-helper 全 pending
- 影响：D05 若走密 VO 演示型（默认无 BGM · sfx 也 off）→ **不需 sfx-mixer**
- 影响：D05 若走**情感型 / 出镜型 / 稀疏 VO** → 需 sfx + BGM · 缺 sfx-mixer 无法上音效层
- 用户可选：
  - [ ] 先跑 D05 · P1 sfx tasks 挂起（默认走密 VO 演示型 · 无 BGM 无 sfx · 与 D04 A-fix 版一致）
  - [ ] 先落 P1 sfx-catalog + sfx-mixer（#66 + #67）· D05 起支持 sfx 层 · Agent 预计 30-45 min

---

**Agent 等你确认。以下动作我不启动直到收到 confirm：**
- 起草 D05 选题（若未提供）
- 打开 D05 洞察 4 件套
- 任何 D05 目录下的 file 创建

**Agent 已在做的（本 doc 外 · 用户此前批准）：**
- P1 sfx-catalog（#66）· 因 memory feedback_sfx-layer-required 已定义清单 · 落成 assets/sfx/catalog.yaml
