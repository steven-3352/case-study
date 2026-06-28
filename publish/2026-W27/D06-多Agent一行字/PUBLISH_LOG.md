# 发布日志 · W27D06 + W27X06

> 交付时间: 2026-06-28 · 自动化产线 `deliver_w27d06.py`

## W27D06 抖音

- [x] `douyin/video_with_bgm.mp4` (45.7s)
- [x] `douyin/cover.png`
- [x] `douyin/publish.md`
- [ ] 人工发布 2026-07-04 19:30
- [ ] 48h 回填 metrics

## W27X06 小红书

- [x] `xhs/page_01..08.png`
- [x] `xhs/publish.md`
- [x] demo: `pipeline/demo_tools/quote_draft/index.html`
- [ ] 人工发布 2026-07-04 12:30
- [ ] 48h 回填 metrics

## 命令复现

```bash
python3 pipeline/p004_video/gen_vo_d06.py
python3 pipeline/p004_video/build.py --storyboard pipeline/p004_video/storyboard_d06.yaml \
  --vo pipeline/p004_video/out/audio/vo_d06.mp3 --subtitle-template d06_subtitles.html \
  --bgm "assets/audio/hook_pack_01/我爱的女孩叫丫头-最终版本.mp3"
python3 pipeline/p004_video/gen_xhs_d06.py
open pipeline/demo_tools/quote_draft/index.html
```
