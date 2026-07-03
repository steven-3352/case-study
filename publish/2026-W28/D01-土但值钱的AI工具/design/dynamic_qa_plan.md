# 逐镜动态 QA 计划 · W28D01

```yaml
content_id: W28D01
qa_scope: production_pre_render_dynamic_plan
status: draft_self_generated
final_render_allowed: false
```

## 目标

把低保真原型推进到生产级前，先定义“看什么算通过”。本文件不是通过证明，是后续生产验收清单。

## 必验关键帧

| 时间点 | 镜头 | 必须看到 | 失败即退回 |
|--------|------|----------|------------|
| 1.2s | s1 | 方案文件、客户弹窗、计数器同屏 | 只剩大字 hook |
| 3.5s | s2 | 示意需求便签压住方案文件，并明确不冒充真实原话 | 四条问题像真实用户原话 |
| 17s | s3 | 复制动作和计数变化有关联 | 数字自己跳 |
| 27s | s4 | 备注列高亮，计数器变成重复判断 | 仍是复制动作重复 |
| 38s | s5 | 变量词替换明显 | 普通聊天截图 |
| 45s | s6 | 重复轨迹、计数器 10、反转句同屏 | 纯黑底金句 |
| 53s | s7 | 轨迹拆成高频/重复/输入/结果四个判断点；低保真证据见 `prototype/qa_shots/s7.png` | 独立四卡片清单 |
| 60s | s8 | 动作输入条成为主焦点 | 固定评论框 |

## 字幕验收

- 每屏字幕不超过 14 个汉字为主，必要时两行。
- 字幕不得遮挡计数器、表格字段、轨迹线、CTA 输入槽。
- `generated_fact / synthetic_visual` 示意标注至少在开头可见。

## 动效验收

- 计数器至少 5 次有效变化：1 / 4 / 7 / 10 / 0。
- 动效节奏必须跟口播含义同步，不追求炫技。
- s7 必须保留“轨迹拆解”，不能回退到四个独立筛选卡。

## 产出物要求

正式生产后必须补：

- `prototype/qa_shots/` 已有 8 个低保真关键帧；正式生产后需补 `douyin/qa_frames/`。
- 30-64s 全片预览视频。
- `design/openmontage_review.md` 或 `design/native_motion_review.md`，说明表现层兑现情况。
- render 后 Phase B scorecards，不得复用本文件当 pass。
