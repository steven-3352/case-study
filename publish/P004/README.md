# P004 · K1 · 实体店老板 · 项目介绍片 · 交付清单

> 选题 ID: T008 · 制作日期: 2026-06-21 · 状态: ready_with_caveats(可发)

## 一句话

实体店老板的微信群消息地狱 → 小系统替你回 → 这条视频本身就是它做的。

## 编排层交付（v2 标准）

| 类型 | 路径 |
|------|------|
| 洞察包 | `publish/P004/insights/`（topic_brief · core_message · domain_notes · fact_check） |
| 留存节拍表 | `publish/P004/retention_beat_sheet.md` |
| 声音方案 | `publish/P004/audio_plan.yaml` |
| 形式库参考 | `assets/formats/catalog.yaml` |

## 主交付物

| 类型 | 路径 | 规格 |
|------|------|------|
| **视频(推荐)** | `pipeline/p004_video/out/final/p004_K1_with_bgm.mp4` | 1080×1920 · 38s · 含 ambient drone BGM · 2.6 MB |
| 视频(裸) | `pipeline/p004_video/out/final/p004_K1.mp4` | 同上,无 BGM,如需自配可用 |
| 小红书封面 | `publish/P004/cover_xhs.png` | 1080×1440 · 884 KB · 「又是这个/问八百遍」 |
| chaos 帧(无字幕) | `publish/P004/cover_chaos.png` | 1080×1440 · 备用底图 |
| 三平台文案 | `publish/P004/publish_三平台.md` | 抖音 / 小红书 / 视频号 |
| **小红书漫画轮播** | `publish/P004/xhs_carousel_引擎升级_漫画版.md` | 8 张 · `pipeline/p007_xhs_engine_comic/out/carousel/` |
| 验收记录 | `publish/P004/CHECKLIST_verdict.md` | 86% 通过 · 2 处 caveat |

## 制作链溯源

| 环节 | 路径 |
|------|------|
| 洞察包 | `publish/P004/insights/` |
| 留存节拍 | `publish/P004/retention_beat_sheet.md` |
| 声音方案 | `publish/P004/audio_plan.yaml` |
| 定稿脚本 | `pipeline/p004_video/script_k1_v2.md` |
| 字幕(SRT) | `pipeline/p004_video/sub_k1.srt` |
| 字幕层渲染 | `pipeline/p004_video/templates/_subtitles.html` |
| 分镜配置 | `pipeline/p004_video/storyboard.yaml` |
| chaos 源素材 | `assets/broll/raw/shop_owner_phone__7669201.mp4` (Pexels) |
| 配音(裸) | `pipeline/p004_video/out/audio/vo_k1_v2.mp3` (32.1s) |
| 配音(已加 1s 前置静默) | `pipeline/p004_video/out/audio/vo_k1_v2_padded.mp3` (33.1s) |

## 反差钩子结构(0-3s)

```
0.0-1.0s  chaos broll · 实体店主刷手机消息
1.0-1.7s  punch1 黑底「又是这个」
1.7-3.0s  punch2 黑底「问八百遍」
```

## 数据反馈触发的下一步

发布后 48h / 7d 填 `ops/metrics.csv` 中 T008-DY / T008-XHS / T008-WX 三行,然后:

```bash
python3 ops/analyze_metrics.py --topic T008
```

会按 `ops/rules.yaml` 阈值自动给 verdict 和推荐动作(R03 完播低 / R04 干货形态 / R05 故事形态 / R06 私信)。

Claude 按数据决定:

| 信号 | 触发动作 |
|------|----------|
| 抖音完播 < 25% | 钩子重做(换钉子场景:报价/库存/排班) |
| 抖音完播 ≥ 35% + 评论问"还有吗" | 扩长版 K2(加具体场景案例) |
| 抖音完播 25-35% + 互动 < 1% | CTA 重做 |
| 视频号完播 < 30% | 视频号专版加招呼语 + 案例 |
| 任意平台私信 ≥ 3 条 | 同模板继续 K2/K3/K4 跑队列 |
| 私信 = 0 但其他正常 | 主页定位/简介承接重写 |

## 重新出片命令(如需迭代)

```bash
# 全片重出(默认参数:用 vo_k1_v2_padded.mp3)
python3 pipeline/p004_video/build.py

# 只改钩子文案,跳过截帧(快)
# 改 storyboard.yaml 的 01b_punch1.data.big 后:
python3 pipeline/p004_video/capture_frames.py --scene 01b_punch1
python3 pipeline/p004_video/build.py --skip-capture

# 重录 VO(API 烧钱,谨慎)
python3 pipeline/tts/gen_speech_minimax.py \
  --script pipeline/p004_video/script_k1_v2.md \
  -o pipeline/p004_video/out/audio/vo_k1_v3.mp3
```

## 三个 caveat(发布前知晓即可,不阻塞)

1. **38s 短于抖音/视频号下限规范** · 不阻塞,数据反馈再决定是否扩长
2. **未做路人测试** · 建议发前找 1-2 个开店朋友看前 10s
3. ~~无 BGM~~ · 已修复。外发用 `p004_K1_with_bgm.mp4`；见 `audio_plan.yaml`

## P1 待办（留存表已标）

- [ ] storyboard 02–08 场景视觉重做（对齐实体店文案 + ≥3 种形式）

详见 `CHECKLIST_verdict.md`
