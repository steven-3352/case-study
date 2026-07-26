---
name: p004-lib-config-driven
description: W29+ 每条新内容走 pipeline_config.yaml + run_pipeline.py --step all，不再 5 脚本 copy；W28D01-D06 保持原脚本作为 golden reference
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# p004_video/lib · 视频合成 config-driven 架构（2026-07-04 P0 完成）

**位置：** `pipeline/p004_video/lib/`（ffmpeg/subs/tts/render/platforms/config 6 模块）+ `pipeline/p004_video/run_pipeline.py` 驱动 + `pipeline/tts/estimate_duration.py` 前置估算

## W29+ 新内容工作流

1. 建目录 `publish/2026-WXX/DYY-*/`
2. 写 `gen_ui_<content>.py`（HTML → Chrome headless → PNG）· 本 lib **不承担** UI 渲染
3. 写 `pipeline_config.yaml` · schema 见 `pipeline/p004_video/lib/README.md`
4. **合成前跑估算**（关键！D03 教训）：
   ```
   python3 pipeline/tts/estimate_duration.py --config publish/2026-WXX/DYY-*/pipeline_config.yaml
   ```
   若 fail（≥30% 溢出）→ 改稿或降 speed
5. 一键出片：
   ```
   python3 pipeline/p004_video/gen_ui_<content>.py
   python3 pipeline/p004_video/run_pipeline.py --config <yaml> --step all
   ```

## VO 先锁 · 防整片重合成返工（2026-07-05 D06 教训）

**根因：** `--step all` 每次都重合成 VO，MiniMax 时长非确定（同稿 60.87s→60.64s 跳）。若按 estimate（常低估 ~20%）写的 scene 时长 → VO 实发更长 → 段落累积漂移 → **CTA ship gate FAIL** → 手改 scenes/overlays 后重跑 all → **又重掷时长骰子**，白改。

**修复（已落 run_pipeline.py）：** VO idempotent —— 已有 `vo_<id>.mp3` + `seg_timing.json` 时 `--step vo`/`all` 默认**复用**（打印「♻ VO 复用」），不重合成。换 voice_id/改 text 才加 `--force-vo`。

**新内容首渲推荐顺序：**
1. `--step vo` 合成并锁 VO → seg_timing.json（打印 scene realign 建议）
2. 据**实测** seg_timing 调 config 的 scenes/overlays（**不按 estimate 值**）
3. `--step preview`（ship gate + 底片 · 复用锁定 VO）
4. `--step platforms`（三平台字幕 + overlay）

锁定后重跑 `--step all` 也安全（复用 VO，改稿即时生效）。

## W28D01-D06 golden reference · 不动

`gen_vo_wXXdYY.py` / `build_wXXdYY_preview.py` / `build_platforms_wXXdYY.py` / `gen_subs_wXXdYY.py` / `gen_ui_wXXdYY.py` 全部保留原状。等价性已用 D03 验证（ASS/filter chain byte-equivalent）。

## 内建修复（写入 lib）

1. `apad=whole_dur=<窗口>` 替代 `apad=pad_dur`（保证补足到目标而非仅补 X 秒）
2. mp3 concat 强制 `-c:a libmp3lame -ar 24000 -b:a 128k`（修 -c copy 丢帧 ~11s bug）
3. `_run_img_clip` / `_run_broll_clip` 独立函数替代 `to_clip()` dict-in-list `"-vf": None` 语法错误
4. 所有 ffmpeg/ffprobe 走 `/opt/homebrew/opt/ffmpeg-full/bin/`

## 相关 memory

- [[feedback_pipeline-burn-subs]]（字幕必 pipeline 烧）
- [[feedback_pipeline-full-platform-output]]（三平台 mp4 直出）
- [[feedback_dense-vo-no-dead-air]]（apad 修复背景）
- [[feedback_read-env-example-first]]（ffmpeg-full 路径来源）
