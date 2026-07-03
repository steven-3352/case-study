# 视觉原创门禁 · visual_originality_gate

> 工种：形式策略官 + 视觉语言策展师 + 动效分镜师  
> 位置：`design/visual_originality_gate.md`  
> 时机：`form_strategy.md` 之后、`storyboard.yaml` 定稿之前。  
> 核心原则：**脚本结构可以复用，表现形式不能模板化。模板只能约束判断流程，不能决定画面长什么样。**

## 0. 结论

```yaml
status: draft | pass | fail
content_id:
review_source: agent_reviewed | human_reviewed
visual_originality_score:
decision: proceed_to_storyboard | rewrite_form_strategy | block_render
```

## 1. 必答问题

| 问题 | 本条回答 | 不合格信号 |
|------|----------|------------|
| 最近 5 条里，哪几条最容易和本条撞形？ | | 答不出最近作品 |
| 这条和最近 5 条相比，首屏有什么不同？ | | 只是换标题/换颜色 |
| 中段表达方式有什么不同？ | | 仍是卡片堆叠/清单轮播 |
| 观众关掉声音，只看画面，还能认出这是新内容吗？ | | 画面可替换任意选题 |
| 有没有复用上一条的镜头语法？ | | 同样的大字钩子 + 四卡片 + 评论框 |
| 如果复用组件，复用的是能力还是画面？ | | 复用构图、节奏、CTA 样式 |

## 2. must_have

- [ ] 专属首屏表达：首屏画面不是旧模板换字。
- [ ] 专属中段机制：中段有本条专属的信息机制或视觉隐喻。
- [ ] 专属 CTA 形态：结尾互动不是固定评论框换字。
- [ ] 不复用上一条分镜骨架：镜头顺序和信息节奏不与最近作品同构。
- [ ] 不用旧模板换字：任何模板/组件复用都声明复用的是能力，不是画面。

## 3. 模板/组件复用声明

只要 `storyboard.yaml` 出现 `template: xxx.html`，该镜头必须同时包含：

```yaml
reuse_reason: "为什么需要复用这个组件能力"
visual_difference: "本条与旧用法在构图/节奏/信息机制上的差异"
risk: "如果最终像旧模板，如何返工"
```

示例：

```yaml
template: w28d03_copy_counter.html
reuse_reason: "复用计数器组件能力，用于表现复制粘贴次数累积"
visual_difference: "本条是员工一天循环计数，不是上一条四项筛选器"
risk: "若呈现为普通数字卡片，退回动效分镜重做"
```

## 4. fail 条件

以下任一项成立，必须 fail：

- 首屏只是旧模板换文案。
- 中段仍是同一套卡片堆叠，只改标题。
- CTA 固定为同一评论框样式，无本条专属互动形态。
- 画面关掉声音后不能区分具体选题。
- storyboard 复用 `template` 但没有 `reuse_reason / visual_difference / risk`。
- form_strategy 的推荐理由是“沿用上一条 / 为了快 / 默认用 / 更酷”。

## 5. 通过签字

- 形式策略官：pass / fail
- 视觉语言策展师：pass / fail
- 动效分镜师：pass / fail

未通过时，不允许 storyboard 定稿，不允许 TTS、gpt-image、render。
