# pipeline/p004_video/lib · 视频合成共享库

> **W28D01-D06 每条 5 个 pipeline 脚本**（gen_vo / gen_ui / gen_subs / build_preview / build_platforms）复制成本高。
> 本 lib 面向 **W29+ 的每条新内容**：写一份 `pipeline_config.yaml`，跑 `run_pipeline.py --config <yaml> --step all`。
> W28D01-D06 golden reference 不动。

## 模块划分

| 模块 | 作用 |
|---|---|
| `ffmpeg.py` | `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` 路径 + `dur()` + `run()` |
| `subs.py` | ASS/SRT 生成 · tokenize/greedy_pack · burn_subs · SubStyle 差异化 |
| `tts.py` | `VOSegment` · `synthesize_segments` · `apad(whole_dur)` · concat + loudnorm（含 D03 修复的 mp3 concat 丢帧 bug） |
| `render.py` | `ClipSpec` · `SceneSpec` · img/broll → clip → concat → attach VO |
| `platforms.py` | `PlatformSpec`（抖音/小红书/视频号字号差异）· `DrawTextOverlay` · `render_platform` |
| `config.py` | `PipelineConfig` · YAML 载入 + 路径解析 + 结构校验 |

## 一条新内容如何用（W29+）

1. 建目录：`publish/2026-WXX/DYY-<主题>/`
2. 生成 UI PNG：写 `gen_ui_<content>.py`（HTML → Chrome headless → PNG）· 本 lib 不承担 HTML 渲染
3. 写 `pipeline_config.yaml`：
   ```yaml
   content_id: WXXDYY
   paths: {root_rel: publish/2026-WXX/DYY-<主题>}
   ffmpeg: {crf: 20}
   tts:
     voice_id: male-qn-jingying-jingpin
     base_speed: 0.95
     segments:
       - {sid: s2, target_start: 3.0, target_dur: 5.0, emotion: neutral, speed: 0.95,
          text: "...", tail_pad: 0.15}
       - ...
   scenes:
     - name: M1_XXX
       total_dur: 3.0
       clips:
         - {src_type: broll, src_rel: assets/broll/raw/<file>.mp4, duration: 2.0}
         - {src_type: img, src_rel: build/assets_ui/01_XXX.png, duration: 1.0}
   platforms:
     douyin: {subs_size: 42, margin_v: 200, max_cue_chars: 32, max_line_chars: 17}
     xhs: {subs_size: 50, margin_v: 220, max_cue_chars: 26, max_line_chars: 14}
     weixin: {subs_size: 42, margin_v: 200, max_cue_chars: 32, max_line_chars: 17}
   overlays:
     - {text: "23:12", t_start: 2.0, t_end: 3.0, fontsize: 64, y_expr: h-500}
   ```
4. **合成前跑估算**（P3）：
   ```
   python3 pipeline/tts/estimate_duration.py --config publish/2026-WXX/DYY-*/pipeline_config.yaml
   ```
   若有段 verdict=fail（≥30% 溢出）→ 改稿或降 speed；若有 warn（15-30%）→ 关注可接受
5. **一键出片**：
   ```
   python3 pipeline/p004_video/gen_ui_<content>.py           # HTML → PNG
   python3 pipeline/p004_video/run_pipeline.py --config publish/2026-WXX/DYY-*/pipeline_config.yaml --step all
   ```
   `all` = vo → preview → platforms · 单步跑就 `--step vo` / `preview` / `platforms`

## D03 golden reference 等价性

- `subs.gen_ass` 输出与 `build_platforms_w28d03.gen_platform_ass` **byte-for-byte 相同**
- `platforms.build_filter_chain` 输出与原 filter 链 **byte-for-byte 相同**
- 验证脚本：见 conversation log · 2026-07-04

## 内建修复（不再复现 D03 bug）

1. `to_clip()` 移除 dict-in-list `"-vf": None` 语法错误（用 `_run_img_clip` / `_run_broll_clip` 分派）
2. `apad=pad_dur=X` → `apad=whole_dur=<窗口>`（保证补到目标窗口，不是"只补 X 秒"）
3. mp3 concat `-c copy` → `-c:a libmp3lame -ar 24000 -b:a 128k`（修复丢帧 ~11s）
4. 全部 ffmpeg/ffprobe 走 `/opt/homebrew/opt/ffmpeg-full/bin/`（系统 ffmpeg 缺 libass、dyld libx265）

## 不承担的部分

- HTML → PNG UI 渲染：每条 UI 版面独有，走 `gen_ui_<content>.py` 用 Chrome headless
- storyboard 设计：这是导演/编剧的活儿
- 洞察包 / retention_beat_sheet / motion_storyboard：产线上游
- 三平台文案：`weixin/publish.md` / `xhs/publish.md` / `douyin/publish.md` 手写
