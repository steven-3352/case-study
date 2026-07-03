# 生产前 Preflight · W28D01

```yaml
content_id: W28D01
status: production_preparation_blocked_before_formal_pre_render
date: "2026-07-03"
can_continue: production_preparation_only
tts_allowed: false
image_generation_allowed: false
final_render_allowed: false
```

## 当前判断

W28D01 可以进入“生产前准备的补齐环节”，但不能进入正式 `pre_render`、最终 TTS、图片生成、视频 render 或发布。

原因不是“文件没写完”，而是正式门禁仍要求独立复评和完整 Phase A scorecards。当前已有的 scorecard 是 `draft_self_generated`，不能算通过。

## 可以继续做

| 任务 | 负责项目 | 说明 |
|------|----------|------|
| 生产口播压缩 | case-study | 以 `scripts/production_cut.md` 作为后续 TTS 候选输入。 |
| UI 动效实现 | case-study 原生表现层 | 当前路线是 2D 工作流计数器，不启用 OpenMontage。 |
| 字幕样式实现 | case-study | 遵守 `audio_plan.yaml` 和 `dynamic_qa_plan.md`。 |
| BGM/SFX 选型 | case-study | 只做计划和素材候选，不生成最终混音。 |
| 逐镜 QA 准备 | case-study | 使用 `?shot=s1..s8` 或后续 render frame 做证据。 |

## 暂时不能做

| 禁止项 | 原因 |
|--------|------|
| 最终 TTS | `design/script_review.md` 仍不是 pass。 |
| gpt-image / 视频生成 | `gate_check(pre_render)` 仍失败。 |
| final render | Phase A scorecards 缺失且当前 scorecard 无效。 |
| approved / publish | 没有 post_render Phase B 和平台表现分析。 |
| 静态截图拼成 `douyin/video.mp4` | 已发生一次失败；`prototype/qa_shots` 只能做 QA 证据，不能冒充成片。 |

## 硬阻塞

1. `scorecards_index.yaml` 仍是 `scorecard_valid: false`，且缺 `required_roles_phase_a`。
2. 多个 Phase A 必需工种 scorecard 缺失。
3. 已有 scorecard 的 reviewer 不符合真实互评要求。
4. `script_review.md` 仍是 `draft_self_generated`，不是 `status: pass`。
5. s3-s7 仍需逐镜动态验收，特别是计数同步和 s7 轨迹拆解。
6. 生产级 mp4 必须来自动态表现层和生产级 TTS；禁止再用静态 QA 截图 + 系统 `say` 生成 canonical `douyin/video.mp4`。

## 生产级路线

推荐继续原生 2D 工作流动效路线，不启用 OpenMontage。

理由：

- 本条核心不是电影感或真实视频合成，而是“重复动作计数器”这个可视化机制。
- OpenMontage 会增加表现层成本，但不能自动解决独立复评和脚本门禁。
- 若后续发现中段视觉弱，再把 s3-s7 单独交给 OpenMontage 做增强版流程演示。
