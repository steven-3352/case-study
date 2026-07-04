"""p004_video 共享库 · 从 W28D01-D06 抽取的稳定件.

模块划分：
- ffmpeg   : ffmpeg-full 路径 + 时长探测 + 安全执行
- subs     : ASS/SRT 生成 + tokenize/pack + burn_subs
- tts      : VO 分段合成 + apad(whole_dur) + concat + loudnorm
- render   : img_clip / broll_clip / concat_video_only / attach_vo
- platforms: PlatformSpec + 三平台字号差异 + drawtext 覆盖
- config   : pipeline_config.yaml 载入 + 结构校验

W28D01-D06 保持原脚本形态作为 golden reference，本 lib 面向 W29+ 使用。
"""
