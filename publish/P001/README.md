# P001 · 海外品牌邮件获客 · 三平台发布包

> content_id: P001 · 状态: **可发布** · 画面：全屏演示 + 口播 + 硬字幕 · 无人物出镜

## 直接上传的文件

| 平台 | 视频（MP4） | 图文（PNG 按序上传） |
|------|-------------|----------------------|
| 抖音 | `douyin/video.mp4`（40s） | `douyin/carousel/01.png`–`06.png` |
| 小红书 | `xhs/video.mp4`（55s） | `xhs/carousel_story/01–07.png` · `xhs/carousel_howto/01–08.png` |
| 视频号 | `channels/video.mp4`（63s） | `channels/carousel/01.png`–`06.png` |

文案（标题/正文/标签）见各平台 `publish.md`。

## 重新渲染

```bash
python3 pipeline/render_p001.py --all          # 视频 + 全部图文
python3 pipeline/render_p001.py --video douyin # 仅某平台视频
python3 pipeline/render_p001.py --carousel xhs-story
```

中间文件在 `_tmp/`，不是发布物。

## 发布顺序建议

1. 小红书图文 A（故事踩坑）→ 测收藏
2. 抖音视频 → 测完播
3. 小红书干货图文 B → 测收藏
4. 视频号复盘视频 → 测分享

## 发布后

`ops/metrics.csv` 填一行 · content_id = P001-douyin / P001-xhs-story 等
