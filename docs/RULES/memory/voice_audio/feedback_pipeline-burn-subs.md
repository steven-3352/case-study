---
name: feedback_pipeline-burn-subs
description: VO 字幕必须 pipeline 自动烧进 mp4，不该甩给剪映智能识别 — 我们手上有精确 seg_timing，用 ffmpeg-full+libass 一键搞定
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

**规则：** VO 主字幕**必须**在 pipeline 从 `seg_timing_*.json` 自动生成 SRT/ASS 并烧进 mp4，**不得**在剪映交接单里让用户跑"智能字幕→识别声音"。

**Why：** W28D02 v2 交接单让用户去剪映跑智能字幕，用户反问「字幕不是自动生成吗？为什么还要我操作？」——他是对的：
- VO 是我们自己合成的（MiniMax），每段的精确 start/dur/text 已经躺在 `seg_timing_w28d02.json` 里
- 剪映"智能识别"是重新做一遍语音识别，多此一举 + 还可能识别错要校对
- 让用户手操 = 破坏"pipeline 自动化"的定位，直接违背用户明说的期望

**How to apply：**
- 每条视频出 `gen_subs_*.py`（或复用 `pipeline/p004_video/gen_subs_w28d02.py` 为模板），从 `seg_timing_*.json` 读 8-N 段自动生成：
  - `vo_*.srt` — 通用字幕，剪映/PR/DaVinci 兼容
  - `vo_*.ass` — 带内嵌样式（PingFang SC 42pt 白 &Hf0f5f5& / 描边 &H000000& 粗 3 / Alignment 2 底居中 / MarginV 200）
  - `preview_no_bgm_subs_v*.mp4` — 已烧字幕的最终外发件
- 长段自动拆多 cue：`_greedy_pack(_tokenize(text), max_chars=17)`；`split_into_cues(text, max_cue_chars=32)`
- 剪映交接单里字幕环节改为「VO 主字幕已烧进 mp4，跳过智能识别」；只留 3 处大字覆盖（**那是设计元素不是 VO 转写**）

**依赖：** `brew install ffmpeg-full`（keg-only in `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`）——系统 `brew install ffmpeg` 精简版**没编 libass/libfreetype**，subtitles/ass/drawtext filter 全用不了。脚本里必须硬编码 `FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"`。

**Exception：**
- 出镜型真人自录（无 seg_timing）→ 可以让剪映智能识别（但必须校对 + 记录 seg_timing 回填 pipeline，供下条复用）
- 快切大字（钩子设计元素）→ 仍归剪映或后续 `gen_bigtext_*.py`（ffmpeg drawtext），不是 VO 字幕

**Related:** [[feedback_dense-vo-no-dead-air]] · [[feedback_dense-vo-no-bgm-default]] · [[feedback_read-env-example-first]]
