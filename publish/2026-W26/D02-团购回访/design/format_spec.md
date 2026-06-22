# 形式规格 · D02 v3

> status: **specced** · 待 render（2026-06-22）
> 工种: 形式选型师 + 动效分镜师 + 漫画分镜师 + 平台原生策划

## 问题诊断（v2 为何像 D01）

| 问题 | 根因 |
|------|------|
| 观众审美疲劳 | 全周走同一 `render.py` evidence slideshow |
| 数据预期偏低 | 单模板 HTML 卡片 + Ken Burns，无动效层次、无故事 |
| 专家未生效 | 纪录片导演/动效分镜师/形式选型师未产出；讨论室只改文案未改 pipeline |

## v3 选型（与 D01 彻底错开）

### 抖音 · `p004_gsap`

- **catalog:** chaos_broll → punch_black ×2 → pain_stack ×3 → before_after → cta
- **禁止:** chat, table, flow pill, terminal「团购助手」, metric 卡片
- **storyboard:** `projects/W26D02/storyboard.yaml`
- **第一感:** 真实 busy 镜头 → 黑底砸字 → 灯泡痛点堆叠 → 红绿对比改造

### 小红书 · `p007_comic`（待建 storyboard_carousel）

- **delivery:** 仅轮播 6–8 张，**删除 video.mp4**
- **catalog:** comic_4panel — 老板/前台/团购客四格故事 + 字段清单
- **第一感:** 漫画叙事，不是报纸纯文字也不是口播短视频

## 需激活的专家（v2 未跑）

| 工种 | v3 产出 |
|------|---------|
| **形式选型师** | 本文件 + `assets/formats/week_W26_matrix.yaml` |
| **平台原生策划** | 抖音/channels 用 GSAP；小红书纯漫画轮播 |
| **动效分镜师** | `projects/W26D02/storyboard.yaml` |
| **漫画分镜师** | `projects/W26D02/storyboard_carousel.yaml`（待写） |
| **纪录片导演** | 故事线：晚高峰 chaos → 三连断点 → 对比反转（非改造实录口播） |
| **声音设计师** | `audio_plan.yaml` 按 scene start_at 对齐 |

## 渲染命令（v3）

```bash
# 抖音 P004
python3 pipeline/p004_video/build.py --storyboard projects/W26D02/storyboard.yaml

# 小红书漫画（storyboard 就绪后）
python3 pipeline/p007_xhs_engine_comic/capture_carousel.py --storyboard projects/W26D02/storyboard_carousel.yaml

# 同步到 publish 周目录
```

## 签字

- [x] 形式选型师（v3 spec）
- [ ] 动效分镜师（P004 render pass）
- [ ] 漫画分镜师（P007 render pass）
- [ ] 视觉设计（封面跟 pipeline 重出）
