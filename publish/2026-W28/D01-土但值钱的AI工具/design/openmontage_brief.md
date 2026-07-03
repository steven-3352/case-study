# OpenMontage 制作 brief · W28D01

## 0. 启用判断

```yaml
enabled: false
content_id: W28D01
platform: douyin
target_duration_s: 60-70
recommended_pipeline: native_2d_workflow_motion
render_runtime: undecided
budget_usd: 0
budget_mode: cap
target_metric: completion_3s
decision: disabled
```

### 判断结论

- 是否启用 OpenMontage：否
- 一句话理由：D01 是曝光周定调选题，核心靠钩子和判断框架，当前原生 2D 工作流动效足够。
- 服务的北极星指标：3s 停留、评论流程名。
- 为什么当前项目原生路线够用：画面只需要“老板误区 + 重复流程 + 四问题筛选器”，不需要复杂视频合成。
- 什么时候再启用：若 D01 中段完播差，但钩子有效，可用 OpenMontage 增强流程演示。

### 禁止理由自检

- [x] 不是因为“更酷 / 更电影感 / 更高级”而启用。
- [x] 没有启用，不会改写 chosen script。
- [x] 当前内容适合原生 2D / 轮播路线。

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | `meta.yaml` | ready | 仅作后续参考 |
| chosen script | `scripts/chosen.md` | ready | 不改写 |
| retention_beat_sheet | `retention_beat_sheet.md` | ready | 不改写 |
| form_strategy | `design/form_strategy.md` | ready | 不改写 |
| design_language | `design/design_language.md` | ready | 不改写 |

## 2. 不可改内容

- 核心选题：真正值钱的 AI 工具，都很土。
- 价值锚：AI 真正落地，是从少掉一段重复工作开始。
- 事实边界：不承诺降本、省人、替代岗位。
- 禁用表达：私信/扣1/一定/最/唯一。
- CTA：评论区写一个耗人流程。

## 3. 制作导演签字

- OpenMontage 制作导演：pass_disabled
- 编导采纳：pass
- 下一步：走当前项目原生路线
