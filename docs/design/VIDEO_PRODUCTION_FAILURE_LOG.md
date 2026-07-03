# Video Production Failure Log

## 2026-07-03 · W28D01 · 低保真截图拼成 mp4

```yaml
content_id: W28D01
failure_type: prototype_assets_misused_as_video
status: system_rule_added
invalid_output: publish/2026-W28/D01-土但值钱的AI工具/douyin/rejected/video_static_slideshow_rejected.mp4
```

### 发生了什么

用户要求“直接输出最优状态的 mp4”。执行时错误地把目标理解成“尽快生成一个 mp4 文件”，使用 `prototype/qa_shots/s1.png` 到 `s8.png` 静态截图拼接，再用 macOS 系统 `say` 生成旁白，输出到了 `douyin/video.mp4`。

### 为什么这是系统事故

- `prototype/qa_shots/` 是低保真 QA 证据，不是成片素材。
- 静态截图拼接退化成幻灯片，违反“表现层增强”的目标。
- 系统 TTS 不是生产级配音，违反音频质量要求。
- 生成了 canonical `douyin/video.mp4` 路径，容易被后续流程误认为成片。

### 新硬规则

1. 禁止将 `prototype/qa_shots/`、低保真截图、静态 QA 帧直接拼接为 `douyin/video.mp4`。
2. 任何写入 `douyin/video.mp4` 的操作，必须先满足至少一种动态来源：
   - 动态 HTML/GSAP/Canvas/Three 录屏或帧序列；
   - OpenMontage 生产结果；
   - 真实录屏 / B-roll / 视频生成素材；
   - 项目正式 render pipeline。
3. 生产级 mp4 必须有生产级配音、字幕、BGM/SFX、动态镜头和逐镜验收。
4. 若只能产出静态拼接，只能写到 `douyin/rejected/` 或 `_build/`，不得写到 `douyin/video.mp4`。
5. 如果达不到生产级要求，必须报告 blocked，不能用“有文件”替代“有质量”。

### 修正动作

- 无效产物已从 `douyin/video.mp4` 移到 `douyin/rejected/video_static_slideshow_rejected.mp4`。
- W28D01 增加 `douyin/rejected/REJECTION.md`。
- `docs/SYSTEM.md`、`pipeline/CHECKLIST.md`、W28D01 `production_preflight.md` 增加对应硬门。

