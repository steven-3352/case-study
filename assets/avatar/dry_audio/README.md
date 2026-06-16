# 声音克隆参考音（已归档用途）

> 2026-06-16 起**不作 pipeline 依赖**。保留供数字人 SaaS 上传或日后重试微调。

| 字段 | 值 |
|------|-----|
| 原始文件 | 已删/外置（曾：`常惠路.m4a`） |
| 克隆用 | `dry_v1.wav`（32kHz mono） |
| 时长 | ~89 秒 |
| 文案对照 | `prompt.txt` |

参考切片（历史 A/B 测试，可忽略）：

- `ref_clip.wav` + `prompt_clip.txt` — 开场
- `ref_clip_narrative.wav` + `prompt_narrative.txt` — 叙事
- `ref_clip_turn.wav` + `prompt_turn.txt` — 转折

克隆 CLI 见 `legacy/voice-clone/`。
