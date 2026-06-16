# Edge TTS · 默认口播

> 2026-06-16 放弃自研声音克隆（GPT-SoVITS 零样本效果不达标）。  
> 正式 pipeline 用 **Edge TTS** 或 **数字人 SaaS 原生音色**。

## 用法

```bash
pip install edge-tts pyyaml   # 或 .venv/bin/pip install edge-tts pyyaml

python3 pipeline/tts/gen_speech.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

剪映导入 `speech.mp3` 对齐 B-roll；需要 wav 时输出 `-o speech.wav`（内部经 ffmpeg 转码）。

## 参数离散随机（默认开启）

每次合成从 `config.yaml` 的 `rate_options` / `pitch_options` / `volume_options` 中各随机取一，中心值约为 rate +15%、pitch -2Hz、volume -2%。

同目录会写 `speech.tts.yaml` 记录本次实际参数。固定参数时加 `--no-jitter`。

## 换音色 / 微调

编辑 `config.yaml`：

| 参数 | 当前 | 作用 |
|------|------|------|
| `voice` | YunjianNeural | 男声底模 |
| `rate` | +15% | 语速 |
| `pitch` | -2Hz | 略降调，弱化默认 TTS 感 |
| `volume` | -2% | 略压低 |

备选男声：`zh-CN-YunyangNeural`（新闻/专业，更稳）

## 平台会不会识别 Edge TTS？

**简短结论：有可能检测「AI 配音特征」，但靠 pitch/rate 微调并不能可靠「骗过」平台；对数据影响通常小于内容本身。**

| 担心 | 实际情况 |
|------|----------|
| 音色被平台拉黑 | 无公开证据表明某 Edge 音色会被限流；大量账号在用同类 TTS |
| 微调后能「识别不出来」 | pitch ±2Hz、rate ±5% 只让成片和「默认参数」略有区别，不是换一个人 |
| 什么更影响数据 | 前 3s 钩子、完播、真实 B-roll ≥60%、剪辑节奏（不像念稿） |

**剪映可再做一层（可选）：** 极轻 EQ（略抬中频）、1–2% 房间底噪、句间手动留白——比反复换 TTS 参数更有效。

## 已归档

声音克隆模块见 `legacy/voice-clone/`（含 GPT-SoVITS 集成，不再维护）。
