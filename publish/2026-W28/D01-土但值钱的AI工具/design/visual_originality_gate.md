# 视觉原创门禁 · W28D01

```yaml
status: draft_self_generated
content_id: W28D01
review_source: draft_self_generated
visual_originality_score: null
decision: block_render_until_reviewed
```

## 1. 必答问题

| 问题 | 本条回答 | 不合格信号 |
|------|----------|------------|
| 最近 5 条里，哪几条最容易和本条撞形？ | W27D04 的反差钩子、W26D09 的工具入门、W27D06 的 Agent 卡片都可能撞形。 | 只说“不会撞” |
| 这条和最近 5 条相比，首屏有什么不同？ | 首屏不直接上大字卡，而是“高级 Agent 方案”文件被员工复制动作打断，并出现重复动作计数器。 | 只是换标题 |
| 中段表达方式有什么不同？ | 中段不是卡片清单，而是动作循环计数：复制、整理、判断、输出，每次累加。 | 仍是四卡片 |
| 观众关掉声音，只看画面，还能认出这是新内容吗？ | 能。因为画面主机制是“重复动作计数器”，不是通用讲解卡片。 | 任何 AI 选题都能套 |
| 有没有复用上一条的镜头语法？ | 不复用报价档位、Agent 工种卡、终端工作台、会议纪要结果演示。 | 同样的大字钩子 + 卡片列表 |
| 如果复用组件，复用的是能力还是画面？ | 只复用“字幕/短句/流程节点”能力，不复用上一条构图、节奏和 CTA 样式。 | 复用同一评论框 |

## 2. must_have

- [x] 专属首屏表达：高级 Agent 方案被重复动作计数器打断。
- [x] 专属中段机制：员工一天重复动作计数。
- [x] 专属 CTA 形态：动作输入条，而非固定评论框。
- [x] 不复用上一条分镜骨架：不走“结果钩子 → 证据 → 档位/清单 → 评论框”。
- [x] 不用旧模板换字：每个模板只作为新组件命名，实际构图须围绕计数器机制。

## 3. 模板/组件复用声明

本条 storyboard 若出现 `template:`，必须逐镜写入：

```yaml
reuse_reason: "复用组件能力，而不是旧画面"
visual_difference: "本条的构图/节奏/信息机制差异"
risk: "如果最终像旧模板，怎么返工"
```

## 4. fail 条件

- 如果首屏最终只剩大字标题，fail。
- 如果中段变成四张卡片列表，fail。
- 如果 CTA 仍是固定评论框，fail。
- 如果计数器机制没有进入像素，fail。
- 如果任何镜头 template 缺 `reuse_reason / visual_difference / risk`，fail。

## 5. 通过签字

- 形式策略官：draft_self_generated
- 视觉语言策展师：draft_self_generated
- 动效分镜师：draft_self_generated

未经过独立复评前，不允许 TTS、gpt-image、render。
