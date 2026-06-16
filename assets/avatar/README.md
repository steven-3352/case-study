# 数字人 / 形象资产

> **2026-06-16：数字人暂停。** Phase 0–1 视频不出真人/数字人，全屏演示 + Edge TTS + 字幕。  
> 本目录资产保留，恢复数字人时再启用。

## 当前视频方案

```
画面：录屏 / 数据 / 系统演示（全屏）
声音：pipeline/tts/gen_speech.py → speech.mp3
字幕：剪映自动生成或手工校对
人物：不做
```

## 目录（暂缓使用）

```
assets/avatar/
├── reference/            # 自拍（暂停，不必急拍）
├── dry_audio/            # 干音（归档）
├── scenes/               # 背景图（数字人用）
└── exports/              # 数字人成品
```

## 恢复数字人时

1. 将 `persona/persona.yaml` → `avatar.status` 改回 `active`
2. 完成 D3–D4 工具选型（见 `docs/TODO.md`）
3. 更新 `video_layout` 是否重新启用小窗

## 验收标准（恢复后）

- [ ] 像本人，不像网红滤镜
- [ ] 口型无明显延迟
- [ ] 背景是书房/桌面，非演播室
