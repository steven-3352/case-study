# EP 全长真声版 · 复刻 EP01 制作 PLAYBOOK

> 目标:把某集的真人录音(脚本/EP0X/*.m4a)做成「真声全长版抖音成片」,
> 皮肤/流程/门禁**完全复刻 EP01**。EP01 是黄金参考,所有脚本/模板照抄改文案。
> 画布 1080×1920 @30fps。绝不用机器音;真声是灵魂。

## EP01 参考文件(照抄这些)
- 主轨: `pipeline/p004_video/build_ep01_vo.py`
- 重定时现成场景: `pipeline/p004_video/build_ep01_scenes.py`
- 字幕层: `pipeline/p004_video/build_ep01_subs.py`
- 音效床: `pipeline/p004_video/gen_sfx_ep01_full.py`
- 最终合成: `pipeline/p004_video/build_ep01_final.py`
- 冒烟测试: `pipeline/p004_video/smoke_ep01.py`
- 新建场景样板(复制改文案): `templates/ep01f_hook.html`(开场钩子) / `ep01f_recap.html`(互动拉观众) / `ep01f_land.html`(发凉/落点/勾下集)
- 共享桌面底图: `templates/ep01f_desk.jpg`(直接复用,所有新场景 `background-image:url("ep01f_desk.jpg")`)
- 皮肤参考(现成场景): `templates/ep0X_*.tmpl.html`(本集已建的 4 个场景,body 照用,只换 `<script>` 时间轴)

## Python 全部用 `/Users/bubu/Documents/projects/case-study/.venv/bin/python`,cwd=项目根。

## 步骤(照 EP01 顺序)

### 1. 主轨 VO
复制 `build_ep01_vo.py` → `build_ep0X_vo.py`,改:
- `SRC` 指向 `publish/2026-W29/连载-把AI调教成我的助理/脚本/EP0X`
- `OUT` 改为 `out/ep0Xfull`
- `BEATS` 列表:按录音文件名 + 拍序,`(文件名.m4a, beat_id, 拍后气口秒)`。beat_id 用 hook/b1/b2...。气口:普通 0.4,段落转折 0.6,顶点/发凉前 0.7-0.8。
运行 → 得 `out/ep0Xfull/vo_master.wav` + `vo_timeline.json`(每拍 start/end/dur)。**记下每拍绝对时间。**

### 2. 场景计划(关键)
- 每个 beat 对应一个 scene。**cut 点 = 该拍 VO 起点 − 0.2s**(画面提前 0.2s 出)。
- scene 时长 = 下一 cut − 本 cot;最后一个 scene 到 vo 总长。
- 现成场景 = 复制其 `ep0X_*.tmpl.html` 的 body(把 `__DESK_B64__` 换成 `ep01f_desk.jpg`),`<script>` 换成重定时时间轴(照 `build_ep01_scenes.py` 的写法:加 `#term` 呼吸漂移 `scale 1.0→1.013 duration=全长`,主 reveal 排在 0.2–;落章块照抄;尾部 `tl.to({},{duration:1.0}, 全长-0.2)`)。**底部 `.caption` 大字不再动画(留给底部跟读字幕,互斥不叠)。**
- 新建场景 = 复制 EP01 的 `ep01f_hook/recap/land.html`,**只改文案+时间点**匹配本拍 VO(见下方本集分场表)。
- 输出全部到 `templates/ep0Xf_*.html`,写 `storyboard_ep0X_full.yaml`(video: output_name ep0X_full_silent.mp4, voice_volume 1.0, music_volume 0.0; scenes 列表 id/template/duration)。

### 3. 冒烟测试
复制 `smoke_ep01.py` → 改模板名+关键时刻,跑,确认 **0 JS 错误 + __timeline 注册**,Read 几张关键帧目视排版(大字别出血、别和底部字幕带 bottom<200 打架)。

### 4. 渲帧
`.venv/bin/python pipeline/p004_video/capture_frames.py --all --storyboard pipeline/p004_video/storyboard_ep0X_full.yaml`
`.venv/bin/python pipeline/p004_video/capture_frames.py --template ep0Xf_subtitles.html --duration <vo总长> --out-id ep0Xf_subs --transparent`

### 5. 字幕层
复制 `build_ep01_subs.py` → `build_ep0X_subs.py`,改 `out/ep0Xfull` 路径 + `BEATS` 每拍切 ≤14 字/屏(金句 hot=1 红字)。输出 `templates/ep0Xf_subtitles.html`。**先跑这个再渲字幕层。**

### 6. 音效床
复制 `gen_sfx_ep01_full.py` → `gen_sfx_ep0X_full.py`,改 `TOTAL`=vo总长、`out/ep0Xfull`,按本集 scene 绝对时间重排 cue(打字 lay/落章 boom+whoo/弹入 tap/发送 tick/发凉 low_tone)。低增益不抢人声。

### 7. 最终合成
复制 `build_ep01_final.py` → `build_ep0X_final.py`,改 `SCENE_IDS`、`OUT`、`SUBS=frames/ep0Xf_subs`、`output_name`。跑 → `out/ep0Xfull/EP0X_全长版_真声_抖音.mp4` + 纯VO备份。

### 8. 门禁(必过)
- `.venv/bin/python pipeline/gate_check_media.py <成片> --min 30 --max 130`(前6s ≥−25dB、无死区、无爆音)
- `.venv/bin/python pipeline/gate_check_palette.py <各场景一帧>`(禁蓝紫霓虹 H240-290;全 PASS)
- Read 3-4 张成片抽帧(ffmpeg -ss <t> -i 成片 -frames:v 1)确认字幕+画面不打架。

### 9. 交付
`cp` 成片 → `publish/2026-W29/连载-把AI调教成我的助理/成片/EP0X_<副标>_真声全长版_抖音_no_bgm.mp4`
纯VO备份 → `..._真声纯VO_备份.mp4`

## 硬约束
- 前6s 有真声 RMS≥−25dB(禁沉默钉子)。
- 禁蓝紫霓虹(UI 蓝 hue<235 可,别用紫/粉)。
- 现成场景/新场景底图统一 `ep01f_desk.jpg`。
- 完成后回报:成片路径、时长、两道门结果、每 scene 时长表。
