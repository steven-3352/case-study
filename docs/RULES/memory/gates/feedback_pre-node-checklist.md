---
name: feedback_pre-node-checklist
description: 每个节点执行前必须过一遍「入口必读清单」(SYSTEM/template/memory/姊妹条/能力清单 5 类)；不过清单不得开工；含触发关键词表 + 违反登记
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

case-study 项目：**每个节点执行前必须过一遍「入口必读清单」**，不过清单不得开工。这是防止"默认习惯跳过约束"的元规则。

**Why:** 2026-07-04 W28 累计 3 次违反——
- W28D02 生产阶段：跳过 `openmontage_brief.md` 判断（把 P001/P004 当默认路径）
- W28D02 form_competition：3 方案都在 P001 家族（SYSTEM §4.2 候选清单跳过）
- **W28D03 规划阶段（本次）：用户问「D03 该怎么做」，agent 把它当聊天问题回答，凭 D02 复用清单直给 D03 路径，没先对 CLAUDE.md 15 步 + 铁律 + templates/README 逐条核对，漏了 8 条规范（纪录片导演/轻量模式/五维打分/两道门/hook_benchmark/gate_check/pre_publish_forecast/图文轮播分支）。用户点名："又出现漏掉规范？"**

**共同根因：** "规划/提议/该怎么做"类问题被当成"聊天"回答（skim），而不是"节点开工"信号（checklist 对表）。规则存在 ≠ 执行。必须**触发词表 + 违反登记**双管齐下。

**通用「入口必读清单」结构（每个节点开工前过一遍）：**

```yaml
pre_node_checklist:
  system_refs: []      # 相关 SYSTEM 章节（§X.Y 具体到号）
  template_refs: []    # 本节点 template 的关键章节
  memory_refs: []      # 相关 feedback/project memory（feedback_XXX 具体到名）
  sibling_refs: []     # 姊妹条最近 1-2 条同节点产出的实际路径
  capability_refs: []  # 相关 pipeline/ + integrations/ 能力清单
```

**How to apply:**

### 触发时机

每次进入以下节点前 **强制** 过一遍：

- 洞察包 4 件套（topic_brief · core_message · domain_notes · fact_check）
- external_references / hook_benchmark
- retention_beat_sheet
- 编剧脚本（v0/vA/vB）
- **form_competition**（本条错误的重灾区，必须最严格）
- form_strategy / design_language / visual_originality_gate
- **openmontage_brief**（每条必跑判断，无论 enabled/disabled）
- motion_tech_plan（如用 Web 3D/GSAP/复杂动效）
- storyboard.yaml
- audio_plan.yaml
- 三平台发布文案

### 触发信号（用户话术识别 · 2026-07-04 W28D03 教训补）

**显性触发词**（用户话里出现即触发）：

| 类型 | 关键词 | 触发的清单类型 |
|------|--------|----------------|
| 节点开工 | `开始 / 开始执行 / 开工 / 该怎么做 / 怎么跑 / 帮我出 <template>` | 5 类全过 |
| 规划提议 | `路径 / 规划 / 全景 / 全流程 / 有无遗漏 / 该做什么` | 5 类全过（**这一类最容易漏**） |
| 选题引用 | `D0X / W28D0X / <slug>` 首次出现且当前节点未开工 | 5 类全过 |
| 姊妹条对比 | `参考 D0X / 沿用 D0X / 复用 D0X` | 5 类 + 姊妹条**实读文件** |
| 门禁类 | `gate / 门禁 / 验收 / 合规 / forecast` | 5 类 + `pipeline/gate_check*.py` 实读 |

**隐性触发（agent 自觉抓）：**

- 用户问一个**规划/路径/该怎么做**问题（不是"帮我写一行代码"这种点状问题）→ 必触发
- 用户第一次提到**当前会话没做过的产物 / 节点**（哪怕只是"看看"）→ 必触发
- Agent 自己**想给一个"看起来完整的方案"**（超过 3 步的路径）→ 必触发
- Agent 心里已经有"我觉得应该 X"的答案 → **警报**，先触发再回答（默认心智固化的信号）

**反触发（不用过 5 类的场景）：**

- 单点 bug 修（"这里报错，看下"）
- 已明确节点内的小操作（"把字号从 42 改到 50"）
- 事实性查询（"D02 时长多少"）
- 用户明说"直接干，不用对表"（罕见，需用户明说）

### 起手动作（触发信号出现后的第 1 步）

**不是回答，是打开 5 类清单。** 顺序：

1. `Read CLAUDE.md` — 找相关段（标准动作 v2 / 铁律 / 反例 / 形态分支）
2. `Read docs/SYSTEM.md` — §1.0 北极星 · §4.2 五维打分（若涉实现选型）· §3.3 音画硬门（若涉视频）
3. `Read templates/README.md` — 三类东西区分 + 正确流程
4. `Read templates/<相关 template>` — 顶部「## 0. 入口必读」块打勾
5. `Read publish/<最近同类姊妹条>/insights/topic_brief.md 等` — 具体实读文件
6. `Read ~/.claude/projects/*/memory/MEMORY.md` + 相关 memory 条 — 关键词 grep
7. `ls pipeline/ + ls integrations/` — 能力清单实查
8. **对表完成前不产出任何"路径/方案"提议**。可以先输出："触发 pre_node_checklist，正在过 5 类清单…"

### 执行动作

1. **打开 template** — 每个 template 顶部有「## 0. 入口必读」块，跟着做
2. **就地打勾** — 5 类清单每项要么读了打勾，要么显式声明"不适用+理由"
3. **姊妹条实读** — 不是"我知道 W28D01 用了什么"就够，而是要**具体打开** `publish/2026-W28/D01-*/design/openmontage_brief.md` 读一遍
4. **能力清单实查** — 每次都 `ls integrations/` + `ls pipeline/`，防止新集成漏掉
5. **memory 实查** — 每次都 `cat ~/.claude/projects/*/memory/MEMORY.md` 看看有没有相关条目

### 反例（跳过清单 = 错误）

- ❌ "我记得 SYSTEM §4.2 大概说什么" → 必须实读最新版本（清单本身可能被别人更新过）
- ❌ "W27D06 我上次看过了" → 每条 sibling_refs 都要**当前节点相关**的实读
- ❌ "跳过入口必读没关系，我知道该做什么" → 这句话本身就是错误信号
- ❌ 只读 template 说明，不读 SYSTEM refs → 半读
- ❌ 只读 SYSTEM，不查 memory → 半读
- ❌ **"这只是聊天回答，不算开工"** → 规划/提议问题**必须**触发（W28D03 教训）
- ❌ **凭上一条经验（如 D02）复用清单直给下一条** → 起点错误：mental model 起点应是 CLAUDE.md 规范，不是上一条实操
- ❌ **CLAUDE.md 挂在 systemPrompt 里就当"读过了"** → skim ≠ checklist 对表

### 违反后果 · 登记流程（2026-07-04 补）

**违反信号识别（agent 自查）：**

- 用户说"你确定按规范做吗 / 你按 XX 规范了吗 / 又漏了 / 又出现"
- 用户列出"你漏了 X 个规范"
- Agent 事后发现"其实我没对 CLAUDE.md 逐条核对"

**违反后立即执行 3 步（不能"下次注意"式回避）：**

1. **停下当前工作** — 不继续原方向输出
2. **根因分析** — 讲清 3 个层面：
   - **流程层**：具体漏了哪几条规范（引用 CLAUDE.md 段号）
   - **认知层**：为什么会漏（默认心智固化？边界识别错？skim 而非 checklist？）
   - **机制层**：怎么让下次不再犯（哪条 memory 要强化？哪个 template 顶部块要加？）
3. **登记 log** — 写到 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`（若不存在则新建），字段：
   ```yaml
   - date: YYYY-MM-DD
     node: D0X-<slug> · <节点名 如 "规划路径提议">
     missed:
       - <规范段号 + 具体漏点>
     root_cause: [flow | cognition | mechanism]
     detected_by: user | self
     fix: <memory/template 强化的具体改动>
   ```

**目的：** miss_log 是自我进化材料 —— 每月一盘"哪类规范最常漏"，据此升级 template 顶部块 / memory / gate_check。**不登记不放过。**

### 与 3 层清理机制的关系（2026-07-04 补）

- **L1 SYSTEM §4.2 候选清单版本化** → 让 `system_refs` 读到的是最新清单
- **L2 表述纠正**（CLAUDE.md/README.md/catalog.yaml） → 让 `template_refs` 不含"默认路径"暗示
- **L3 门禁前置**（form_competition §3 候选池自查 + openmontage_brief 前置） → 让 form_competition 节点的清单**结构化打勾**
- **L4 本 memory** → 定义**通用元规则**（本条）
- **L5 template 顶部块**（2026-07-04 中等版落地） → 让 template 打开的第一眼就是「入口必读」
- **L6 触发词表 + 违反登记**（2026-07-04 W28D03 补） → 让「规划/提议」类问题也强制触发清单，违反有登记有分析

### 边界（什么不做）

- ❌ 不搞 hook 自动化（成本高、维护累；靠 template 头部块就够）
- ❌ 不搞 gate_check.py 强制记录"已读 XX"（机械化过头，拖慢产线）
- ❌ 不把清单变长（每 template 顶部块保持 10-20 行、可扫读）

### 与 [[feedback_autonomous-data-driven]] 的边界

- 自主推进 = **工种执行内自主拍板**
- 入口必读 = **进节点前必查约束**
- 两者不冲突：自主推进的前提是**已经过完入口必读清单**

### 与 [[feedback_read-env-example-first]] 的关系

后者是"接手项目第一动作"（一次性），本条是"每个节点执行前动作"（重复性）。前者是本条的一个特例（"启动"节点的入口必读）。

**关联 memory：**
- [[feedback_no-default-tech-stack]] — 本条是它的执行机制
- [[feedback_read-env-example-first]] — 本条是它的通用化
- [[feedback_autonomous-data-driven]] — 本条明确了自主的边界
- [[feedback_multi-role-collab]] — 每个工种/节点都受本条约束
