# Prototype QA · W28D01

```yaml
content_id: W28D01
qa_scope: low_fidelity_html_prototype
qa_date: "2026-07-03"
status: prototype_visual_qa_pass_with_limits
final_render_allowed: false
pre_render_gate: still_blocked
```

## 验证结论

低保真 HTML 原型可以继续作为 W28D01 的表现层试点依据，但不能作为最终成片通过依据。

本轮只确认：核心视觉机制已经进入像素，不再只是文档字段；正式生产仍需 Phase B 复验、正式素材/字幕/配音/BGM/动效技术验收。

## 已实际修复

1. 首镜客户消息弹窗在截图模式下因子动画未完成而几乎不可见，已改为 `?shot=s1` 静态 QA 时强制可见。
2. 右上角计数器在 9:16 截图中被裁切，已缩小并移动到安全区。
3. 原型画布默认贴左渲染，避免 Chrome headless 截图时因居中画布造成右侧裁切。
4. 原型支持 `?shot=s1` 到 `?shot=s8` 的关键帧 QA 模式，便于后续逐镜复核。
5. 计数器不再全程固定为 1；原型运行时按阶段切换为重复动作/重复判断/重复改写/归零。
6. s3-s5 已补复制选区、扫备注光标、变量替换轨迹，避免计数器脱离动作。
7. s7 已从四个筛选条改为轨迹线拆解四个判断点，并补充截图证据。

## 像素检查

| 项目 | 结论 | 说明 |
|------|------|------|
| 0-3s 不是纯大字 | pass | 截图可见《高级 AI Agent 方案》、客户消息弹窗、计数器和大字 hook 同屏。 |
| 计数器安全区 | pass | `重复动作 1` 已完整显示在右上角。 |
| source 标注 | pass | 顶部显示 `示意 · generated_fact / synthetic_visual`。 |
| s1 打断机制 | pass | 方案文件被客户消息弹窗打断，符合“高级方案被现实工作打断”。 |
| s3 复制动作 | prototype-pass-with-risk | 截图可见复制选区、复制路径、光标和计数 4；生产级仍需验证计数跳动节奏。 |
| s4 判断动作 | prototype-pass-with-risk | 截图可见备注扫描、高亮行、光标和计数 7；生产级仍需验证逐行判断节奏。 |
| s5 改写动作 | prototype-pass-with-risk | 截图可见变量替换轨迹、光标和计数 10；生产级仍需验证变量闪动。 |
| s6 冻结反转 | prototype-pass | HTML 已包含轨迹、计数器、反转句，正式成片仍需验证冻结节奏。 |
| s7 四问题来源 | prototype-pass-with-risk | 已从四个筛选条改为轨迹拆成四个判断点；生产级仍需验证动态转场。 |
| s8 CTA | pass-for-prototype | CTA 是动作输入条，不是固定评论框。 |

## 保留限制

- 不能把本 QA 解释为最终 render 通过。
- 不能进入正式发布态；`gate_check(pre_render)` 仍失败是正确状态。
- 生产级版本必须补：逐镜截图/视频验收、字幕、BGM、配音、表现层复核、Phase B agent 互评。

## QA 证据

- s1 首镜打断：[s1.png](./qa_shots/s1.png)
- s2 示意需求：[s2.png](./qa_shots/s2.png)
- s3 复制动作：[s3.png](./qa_shots/s3.png)
- s4 判断动作：[s4.png](./qa_shots/s4.png)
- s5 改写动作：[s5.png](./qa_shots/s5.png)
- s6 冻结反转：[s6.png](./qa_shots/s6.png)
- s7 轨迹拆解：[s7.png](./qa_shots/s7.png)
- s8 动作 CTA：[s8.png](./qa_shots/s8.png)
