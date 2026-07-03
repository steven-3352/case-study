# Rejected Video · W28D01

```yaml
content_id: W28D01
rejected_at: "2026-07-03"
rejected_file: douyin/rejected/video_static_slideshow_rejected.mp4
original_path: douyin/video.mp4
status: rejected_invalid_preview
must_not_publish: true
```

## 结论

这个 mp4 是无效产物，不能作为 W28D01 成片、审片版本或发布候选。

它已经从 `douyin/video.mp4` 移到：

`douyin/rejected/video_static_slideshow_rejected.mp4`

## 为什么失败

1. 画面来自 `prototype/qa_shots/s1.png` 到 `s8.png`，本质是低保真 QA 截图拼接。
2. 每个镜头是静态图停留，缺少真实动效、转场、计数同步和动作节奏。
3. 配音使用 macOS 本地 `say -v Tingting`，不是项目要求的生产级配音。
4. 背景音是 ffmpeg 低频噪声，不是 BGM/SFX 设计。
5. 它绕过了此前约定：表现层必须增强视频表达，不能退回幻灯片模式。

## 直接教训

- `prototype/qa_shots/` 只能做 QA 证据，不能作为 `douyin/video.mp4` 成片素材。
- 用户要求“直接输出最优状态 mp4”时，不能理解成“先随便生成一个 mp4 文件”。
- 如果做不到生产级 mp4，必须明确 blocked；不能用低质 mp4 顶替。

## 后续恢复路径

1. 保持 `douyin/video.mp4` 缺失，直到真正生产级视频完成。
2. 正式视频必须来自动态表现层：HTML/GSAP/OpenMontage/录屏/视频生成之一。
3. 配音必须走项目配置的生产级 TTS，例如 Minimax，而不是系统 `say`。
4. 成片必须含字幕、BGM/SFX、动态镜头、逐镜抽帧复验。

