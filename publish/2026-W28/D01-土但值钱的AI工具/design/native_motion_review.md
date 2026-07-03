# Native Motion Review · W28D01

```yaml
content_id: W28D01
review_scope: low_fidelity_native_html_motion
review_date: "2026-07-03"
status: prototype_motion_review_pass_with_limits
formal_pre_render_allowed: false
final_render_allowed: false
```

## 结论

原生 HTML/2D 工作流动效路线可以继续作为 W28D01 的表现层方案；当前低保真关键帧已能证明“重复动作计数器”不是只停留在文档里。

但这不是正式动态验收。正式生产仍需录屏或 render 后抽帧，验证计数跳动、口播节奏、字幕、BGM/SFX 和转场。

## 逐镜复验

| 镜头 | 证据 | 结论 | 仍需生产级验证 |
|------|------|------|----------------|
| s1 hook_interrupt | `prototype/qa_shots/s1.png` | pass | 计数器 0→1 的动态跳动和 paper_snap。 |
| s2 示意需求 | `prototype/qa_shots/s2.png` | pass | 便签压住方案的入场顺序。 |
| s3 复制动作 | `prototype/qa_shots/s3.png` | pass-with-risk | 复制选区移动和计数 +1 是否同步。 |
| s4 判断动作 | `prototype/qa_shots/s4.png` | pass-with-risk | 备注扫描是否逐行发生，不能只是静态框。 |
| s5 改写动作 | `prototype/qa_shots/s5.png` | pass-with-risk | 变量词闪动替换是否明显。 |
| s6 冻结反转 | `prototype/qa_shots/s6.png` | pass-with-risk | 冻结命中点和反转句出现节奏。 |
| s7 轨迹拆解 | `prototype/qa_shots/s7.png` | pass-with-risk | 必须从 s6 轨迹连续拆解，不能硬切四节点。 |
| s8 动作 CTA | `prototype/qa_shots/s8.png` | pass | 输入条出现和示例动词浮现。 |

## 已修复的退稿点

- s2 不再像真实用户原话，已改为“示意需求”。
- s3-s5 不再只是页面切换加大数字，已补复制、扫描、变量替换动作层。
- s7 不再是四个筛选条，已改为轨迹拆出四个判断点。
- CTA 与动作输入条一致，改为“每天重复最多的动作”。

## 禁止误用

- 不能用本文件替代 `gate_check(pre_render)`。
- 不能用本文件触发 final TTS / gpt-image / render。
- 不能把低保真截图当成最终发布素材。

## 下一步

1. 如果继续原生路线，做正式动态版并录制 64s preview。
2. 按 `design/dynamic_qa_plan.md` 逐镜抽帧。
3. 通过正式 Phase A scorecards 和 `script_review status: pass` 后，才允许 TTS/render。

