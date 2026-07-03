# GAP_REPORT · W28D01

```yaml
content_id: W28D01
status: production_preparation_only
review_source: pass_agent_reviewed_for_prototype
scorecard_valid: prototype_only
prototype_allowed: true
final_render_allowed: false
allowed_next_step:
  - 用 agent_hypothesis 替代缺失 benchmark
  - 用 generated_fact 替代缺失原话
  - 补真实多 Agent / 人类复评
  - 做生产前准备补齐
  - 复评表现形式竞争
  - 复评视觉原创门
  - 复评素材策略
not_allowed:
  - final TTS
  - final gpt-image
  - final render
  - approved
```

## 为什么降级

W28D01 已允许用 `agent_hypothesis` 替代缺失的同平台 benchmark，用 `generated_fact` 替代缺失的真实原话。低保真 HTML 样机首镜已完成像素 QA，生产前只读复验已完成。当前仍不能进入最终制作，因为正式 Phase A scorecard、script_review pass、逐镜动态验收和 render 后 Phase B 复验都没完成。

## Blocking

| 阻塞项 | 当前证据 | 需要补什么 | 完成后谁复核 |
|--------|----------|------------|--------------|
| 正式 Phase A scorecard 未完成 | `scorecards_index.yaml` 仍为 `scorecard_valid: false` | 补齐全工种独立互评 | 编导 |
| script_review 未通过 | `design/script_review.md` 仍为草稿 | 基于 `scripts/production_cut.md` 做正式复评 | 编剧 + 留存 |
| 逐镜动态验收未完成 | 首镜已截图，s3-s7 仍未逐镜验收 | 按 `design/dynamic_qa_plan.md` 抽帧/录屏 | 编导 + 动效设计师 |
| Phase B 复验未完成 | 尚无正式 mp4 | render 后做听片、字幕、BGM、封面、平台预估 | 编导 + 视觉语言策展师 |

## Optional Calibration

| 可选校准项 | 当前替代方式 | 说明 |
|------------|--------------|------|
| 同平台短视频 benchmark ≥2 | `agent_hypothesis` | 没有样本也可以推进；后续拿到样本再校准 |
| 真实网络原话 ≥2 | `generated_fact` | 可用于脚本和画面，但不得冒充真实用户原话 |

## 允许做

- 补真实样本校准（可选）
- 打开低保真样机
- 做 motion_wow 像素验收
- 基于样机修正 storyboard / prototype

## 禁止做

- 不允许最终 TTS
- 不允许最终 gpt-image
- 不允许最终 render
- 允许低保真 HTML/动效样机
- 不允许写 `approved`
- 不允许把现有 scorecard 当作 pass
