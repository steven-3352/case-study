# D01 发布记录 · 美甲撞档

## 今日发布（首测 · 决定 W26 后续形式）

| 平台 | 形式 | 定时 | 素材 | content_id |
|------|------|------|------|------------|
| 抖音 | F2 | 19:30 | `douyin/video.mp4` + `cover.png` | T009-DY |
| 小红书 | F1 | 12:30（可选） | `xhs/video.mp4` + `cover.png` | T009-XHS |

建议：**先主投抖音 F2**，小红书可同日或等 48h 抖音数据后再发。

## 发布前 3 项

- [ ] 标题/正文从 `douyin/publish.md` 复制（勿改硬广词）
- [ ] 封面用 `douyin/cover.png`（v3 light_split）
- [ ] 发布后记实际发布时间 → `ops/metrics.csv` 的 `publish_date`

## 明天回填（48h · 决定后续形式用）

填 `ops/metrics.csv` 行 **T009-DY**（必填）：

| 字段 | 用途 |
|------|------|
| exposure_48h | 曝光 |
| completion_rate_48h | 完播率（片长 ~73s，重点看） |
| likes_48h / comments_48h / saves_48h | 互动 |
| notes | 私信大意、高赞评论类型（「我也撞档」「能帮忙做吗」等） |

## 形式决策参考（48h 后）

| 信号 | 后续倾向 |
|------|----------|
| 完播 ≥35% + 评论有场景共鸣 | F2 继续，D02–D07 可混 F3/F4 对照 |
| 完播低、3s 跳出高 | 加强 hook 段 / 压片长到 45–50s |
| 私信/评论问「能不能做」 | 转化有效，内容保持「改造实录+小流程」 |
| 只有赞无评论 | CTA 或钩子再 sharpen |

回填后把 `meta.yaml` 的 `status` 改为 `published`，`verdict` 写入 metrics。
