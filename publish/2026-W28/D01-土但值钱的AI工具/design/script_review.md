# 脚本审查 · W28D01

```yaml
status: draft_self_generated
content_id: W28D01
review_source: draft_self_generated
decision: block_tts_until_real_review
```

> 对象：`scripts/chosen.md`  
> 说明：这是单 Agent 草稿审查，不具备内容门通过效力。

## 草稿判断

当前脚本方向可继续打磨，但不能标记为 pass：

- 钩子有明确冲突：“很多老板做 AI 的第一步就错了。”
- 场景有具体动作：复制消息、整理表格、判断跟进、改写回复。
- CTA 没有使用私信/扣1。

## 仍需补齐

| 阻塞项 | 原因 | 下一步 |
|--------|------|--------|
| 原话来源不足 | 当前四句是归纳，不是可追溯原话 | 补真实评论/客户沟通原话 |
| hook benchmark 不足 | 缺 2 条同平台短视频拆解 | 补抖音/小红书同类视频前 3 秒 |
| 未独立复评 | 当前没有真实 reviewer | 补独立 Agent/人类复评 |

## 不允许

- 不允许 TTS。
- 不允许 render。
- 不允许在 `room/verdict.yaml` 写 pass/approved。
