---
name: claude-model-evaluation-and-cost
type: domain
last_updated: 2026-07-25
source_projects:
  - publish/2026-W30/D08-Claude-Opus-5实测 (T046 · 2026-07-25)
tags: [claude, opus, fable, sonnet, model-evaluation, api-pricing, budget]
reuse_scope: Claude 模型新品拆解、能力/价格比较、API 预算与任务路由内容
freshness_horizon: event-driven
---

# Claude 模型评测与成本决策

## 摘要

Opus 5 是 Opus tier 的高能力日用档：官方称接近更高层级的 Fable 5，API 单价正好一半；但它仍显著贵于 Sonnet 5。能力、价格、订阅额度和 effort 必须分开比较。

## 核心地图

- Opus 5：$5/百万输入 token、$25/百万输出 token；适合高失败成本的代码、架构、深度分析。
- Fable 5：Mythos-class；$10/$50；适合极限质量、长自治、最难知识工作。
- Sonnet 5：2026-08-31 前促销 $2/$10，之后 $3/$15；适合高量、低风险与生产规模化。
- 成本不只由单价决定，还受上下文、输出长度、重试、缓存、effort、Fast mode 与 usage credits 影响。

## 评测口径

- Artificial Analysis GDPval-AA v2 是独立盲评，覆盖 220 个职业任务；当前记录 Opus 5 max 1861、Fable 5 含 fallback 1747、Sonnet 5 max 1603。
- Anthropic 官方公告的 Frontier-Bench、CursorBench、ARC-AGI 3、AutomationBench、OSWorld 结果属于厂商自测，必须明确标注来源与条件。
- Pydantic AI 的公开 PR 记录了实时 API 参数探针：关闭 thinking 时 Opus 5 对 xhigh/max 返回 400；Fast mode 无组织配额时返回 429。这是兼容性/配额证据，不是综合能力榜。

## 制作启示

先按失败成本路由模型，再谈“哪个最强”：高风险关键步骤用 Opus，批量低风险默认 Sonnet，只有确有极限质量或长自治需求才升级 Fable。每条内容必须写清测试版本、effort、fallback 和价格单位。
