# W28D01 · production_cut · 64s 对齐稿

```yaml
content_id: W28D01
source_script: scripts/chosen.md
status: draft_self_generated
review_source: production_alignment_only
tts_allowed: false
target_duration_s: 64
paired_storyboard: design/storyboard.yaml
```

> 用途：把 `chosen.md` 压成与当前 8 镜 storyboard / audio_plan 对齐的生产口播候选稿。  
> 限制：这不是 script_review pass，不允许直接 TTS / render。

## 生产口播

很多老板做 AI 的第一步就错了。

我通常会把这类需求概括成几种情况：

想用 AI，但不知道从哪开始。

一上来就想做复杂 Agent。

买了工具，最后还是没人用。

员工每天还在复制消息和整理表格。

问题其实已经写在这些动作里了。

很多人一上来就想做一个很高级的 Agent。

但公司里真正值钱的 AI 工具，往往土得要命。

比如员工每天早上，把客户消息复制到表格。

中午，按备注判断谁该跟进。

下午，把差不多的回复改几个字发出去。

这不是员工勤奋。

这是流程没有被产品化。

所以企业做 AI，第一步不是问能不能做一个很厉害的系统。

先问四件事：

高频吗？

重复吗？

输入明确吗？

结果明确吗？

如果这四个问题都答得上来，一个很土的小工具，反而可能比复杂 Agent 更值得先做。

AI 真正落地，往往不是从酷开始。

是从少掉一段重复工作开始。

评论区写一个你公司每天重复最多的动作，我帮你判断它值不值得 AI 化。

## 相对 chosen 的删改

| 删除 / 压缩 | 原因 |
|-------------|------|
| 四句需求的引号 | 避免 generated_fact 被误听成真实用户原话。 |
| “晚上，再整理一遍日报” | storyboard 没有日报镜头，保留会造成音画不同步。 |
| “自动分类客户 / 生成报价草稿 / 推到销售面前”三例 | 当前 s8 聚焦评论动作输入条，不做功能清单页。 |

