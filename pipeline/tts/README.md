# TTS · 多 provider 统一入口

> 2026-06-16 放弃自研声音克隆（GPT-SoVITS 零样本效果不达标）。  
> 正式 pipeline 用 **`gen_speech.py`** 统一入口，按 `config.yaml` 的 `provider` 切换。

## 选哪个

| 场景 | provider | 理由 |
|------|----------|------|
| 无凭证 / 保底 | `edge` | 免费、同步 |
| 短口播逐段（render.py） | `minimax` | 音色稳、支持 emotion；云雾中转 async |
| 火山/豆包 | `volcengine` | 自然对话男声 |

```bash
cp .env.example .env   # 填入 MINIMAX_API_KEY + MINIMAX_BASE_URL 等

python3 pipeline/tts/gen_speech.py --script pipeline/dry-run-001/script.md -o out.mp3
python3 pipeline/tts/preview_minimax_voices.py   # 批量试听音色
```

---

## Edge TTS（默认 / 回落）

```bash
pip install -r pipeline/tts/requirements.txt

python3 pipeline/tts/gen_speech.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

每次合成从 `config.yaml` 的 `rate_options` / `pitch_options` / `volume_options` 随机取一。固定参数加 `--no-jitter`。

| 参数 | 当前 | 作用 |
|------|------|------|
| `voice` | YunjianNeural | 男声底模 |
| `rate` | +15% | 语速 |
| `pitch` | -2Hz | 略降调 |
| `volume` | -2% | 略压低 |

---

## MiniMax · speech-2.8-turbo

凭证见 `.env`：`MINIMAX_API_KEY` + `MINIMAX_BASE_URL`（云雾示例 `https://yunwu.ai/minimax`）。

编辑 `config.yaml` → `provider: minimax`。当前默认音色 **`male-qn-badao`**，模式 **`async`**（云雾中转 sync 报 1008，async 走 retrieve+tar 解包）。

`render.py` 按段传入 `emotion` / `speed`，让口播有情绪起伏。

| voice_id | 名称 | 特点 |
|----------|------|------|
| `male-qn-badao` | 霸道青年 | **当前选用** |
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 | 叙事感强 |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | 中年克制 |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 | 匹配「20年互联网」 |

---

## 平台会不会识别 TTS？

有可能检测 AI 配音特征，但 pitch/rate 微调不能可靠「骗过」平台；对数据影响通常小于内容本身（前 3s 钩子、完播、真实 B-roll）。

## 已归档

- 声音克隆：`legacy/voice-clone/`
- 旧版独立 MiniMax 脚本 `gen_speech_minimax.py` 已合并进 `gen_speech.py`（勿再用）
