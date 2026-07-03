# Production Review · W28D01

```yaml
content_id: W28D01
review_date: "2026-07-03"
review_type: readonly_subagent_preflight
status: production_preparation_only
formal_pre_render_allowed: false
final_render_allowed: false
```

## 复验结论

三位只读 reviewer 的共识：

- 可以继续做生产前准备的补齐环节。
- 不允许进入正式 `pre_render`。
- 不允许 final TTS / final gpt-image / final render / approved。

## Reviewer 摘要

| reviewer | 角色视角 | 分数 | 结论 |
|----------|----------|------|------|
| Ptolemy | 编剧 + 留存与互动设计师 | 76 | 创意方向成立，但 benchmark 缺失、generated_fact 表达边界、s7 生产级动效未验证。 |
| Pascal | 视觉语言策展师 + 动效设计师 | 62 | s7 明显过弱，计数器机制还停在说明层，不能进入正式生产前准备。 |
| Lovelace | 编导 + 生产技术导演 | 62 | 可以进入生产前准备补齐环节，但正式 pre_render / final render 仍 blocked。 |

## 已采纳修改

1. `scripts/chosen.md` 去掉四句需求的引号，避免 generated_fact 被误听成真实原话。
2. 新增 `scripts/production_cut.md`，作为 64s storyboard 对齐候选稿。
3. `audio_plan.yaml` 指向 `scripts/production_cut.md`，仍明确 `tts_allowed: false`。
4. `prototype/index.html` 的 s2 改为“示意需求”，并写明“不冒充真实用户原话”。
5. `prototype/index.html` 的 s3-s5 补复制选区、扫备注光标、变量替换轨迹，让计数器绑定动作。
6. `prototype/index.html` 的 s7 从四个筛选条改为“轨迹拆成四个判断点”。
7. CTA 从“耗人流程”收窄为“每天重复最多的动作”，降低评论门槛并匹配动作输入条。
8. 已补 s1-s8 低保真关键帧证据到 `prototype/qa_shots/`。

## 未解决风险

- 真实同平台 benchmark 仍缺失，但按当前系统规则可用 agent_hypothesis 继续推进低保真和生产准备。
- 正式 Phase A scorecards 仍缺失，不能通过 `gate_check(pre_render)`。
- s3-s5 已补低保真动作层，但生产级仍需验证计数跳动和口播同步。
- s7 已在低保真层修正，但生产级仍需验证从 s6 到 s7 的动态转场。

## 下一步

1. 补 `design/native_motion_review.md`，把 s1-s8 低保真关键帧逐项验收。
2. 若要进入正式生产，实现动态版并按 `design/dynamic_qa_plan.md` 做录屏验收。
3. 若要进入正式 pre_render，必须补齐真实独立 Phase A scorecards 和 `script_review status: pass`。
