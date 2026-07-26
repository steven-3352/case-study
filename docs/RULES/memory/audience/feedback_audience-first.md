---
name: audience-first-not-pipeline-first
description: "交付评判基准是观众成果（内容共鸣/强观赏性/强内容），不是工程产出（pipeline 跑通/15 步齐/render 无报错/发布包齐）。触发时刻：任何\"完成\"判定的语义节点。"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# Audience-First, Not Pipeline-First

**规则**：交付达标的唯一评判基准是**观众成果**（**内容共鸣** · **强观赏性** · **强内容**），不是**工程产出**（pipeline 跑通 · 15 步走完 · 所有工种产出齐 · render 无报错 · 发布包三平台文案齐）。

**Why**：项目已多次出现「工种全齐 · pipeline 跑通 · 但成片与上条同质 / catalog 拼盘 / 无观赏性 / 无共鸣」的假交付（详见 `docs/design/SCRIPT_REJECT_LOG.md` · `FORM_FAIL_LOG.md`）。铁律 4「各环节专家对最终结果负责」明确要求：完成的是**结果**不是**流程**。用户 2026-07-04 明确点破：**「项目核心是创作好的内容，不是完成工程化的任务。」** 一切规范/模板/工种/pipeline 都是**手段**，创作出观众愿意看完且愿意互动的好内容是**目的**。

## 三要素定义（对内容的正向标准）

| 要素 | 含义 | 判定方法 |
|---|---|---|
| **内容共鸣** | 命中真实情绪/场景 · 观众愿意在评论里接话 | ①钉子场景是**真的**（有网络原话/一手素材支撑） ②情绪表达是**具体的**（不是"焦虑""内卷"这类空词） ③是否能激发评论区互动 |
| **强观赏性** | 视觉每 2-4s 变化 · 首屏停划 · 音画同步 | ①同行热门 3s 停划设计已拆解 ②每一镜有明确视觉变化 ③单场景占比 ≤35% ④catalog 拼盘 ≤35% |
| **强内容** | 信息密度真材实料 · 可复现的方法/prompt/清单 | ①有 ≥1 可复制粘贴的产物（prompt / checklist / 时间线） ②不空喊口号（禁「轻松掌握」「秒变」类） ③不概念糊弄（禁 LLM/Prompt Engineering 术语堆砌） |

## How to apply

### 1. 任何"完成"判定时刻的自查三问

触发时机：Task 打勾前 · Write 完文件后 · 脚本终稿声明 · render 出 mp4 · 发布包齐 · Task #XX completed 声明。

**自查三问**：
- 观众看到会不会**共鸣**？（场景是真的吗？情绪是具体命中的吗？）
- 画面**观赏性**够吗？（每 2-4s 有变化吗？首屏停划吗？音画同步吗？）
- 内容**真材实料**吗？（有可复现的方法/prompt/清单？还是空喊/概念糊弄）

**任何一问答不上"是" → 状态仍是 `draft`，未 done。**

### 2. 唯一交付判据

`pre_publish_forecast` 评级 ≥ **B** + 投后观众数据（3s 完播 / 完播率 / 互动 / 收藏）达标。评级 C/D 或无 forecast 一律 `blocked`。

### 3. 反例识别（出现这些心态立即打断 · 回到自查三问）

- ❌「pipeline 跑通了就发」
- ❌「15 步走完了就 ship」
- ❌「所有工种产出齐了就 done」
- ❌「render 没报错就 approve」
- ❌「三平台文案齐了就 ready」
- ❌「Task #XX completed」但没确认下游用没用、观众看没看
- ❌「domain_notes.md 已 Write = 领域专家环节完成」（真正完成 = 该产出在下游被用到并推高观众数据）

### 4. 正向表达（写文档/规范/汇报时的默认措辞）

- ✅「本条 3s 完播预测 X% · 达 `pre_publish_forecast` B 级 · 可外发」
- ✅「共鸣：钉子场景来自 X 平台 Y 条网络原话；观赏性：每 3s 变化 + catalog 占比 28%；强内容：3 段 prompt 可复制粘贴」
- ❌「pipeline 已跑通 · 发布包齐 · 可外发」
- ❌「15 步完成 · Task closed」

## 关联

- [[pre-node-checklist]] · 新节点起手 5 类清单实读
- [[autonomous-data-driven]] · 用户只出选题和数据，其他自己拍板
- [[no-default-tech-stack]] · pipeline 存量不代表选型正确，看哪条更强
- [[dense-vo-no-bgm-default]] · 音画硬门是观赏性子集，不是工程勾选项
