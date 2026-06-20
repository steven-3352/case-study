# TTS · 双 provider

> 2026-06-16 放弃自研声音克隆（GPT-SoVITS 零样本效果不达标）。  
> 正式 pipeline 用 **Edge TTS**（默认/免费）或 **MiniMax T2A v2**（付费,音色更稳）。

## 选哪个

| 场景 | 推荐 | 理由 |
|------|------|------|
| 短文本 / 逐段循环（build_video.py 13 段） | Edge TTS | 同步、免费、无轮询开销 |
| 单段长文本 / 一份 mp3 一次成 | MiniMax async | 音色稳、情感参数、支持 100 万字 |
| 重要选题正式发布 | MiniMax | 音色辨识度高于 Edge |

两个脚本 CLI 完全对齐,可互相替换:

```bash
# 同样的 --script / --text / -o / --no-jitter
python3 pipeline/tts/gen_speech.py          --script X.md -o out.mp3   # Edge
python3 pipeline/tts/gen_speech_minimax.py  --script X.md -o out.mp3   # MiniMax
```

---

## Edge TTS（默认）

### 用法

```bash
pip install -r pipeline/tts/requirements.txt   # 或 .venv/bin/pip

python3 pipeline/tts/gen_speech.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

剪映导入 `speech.mp3` 对齐 B-roll;需要 wav 时输出 `-o speech.wav`（内部经 ffmpeg 转码）。

### 参数离散随机（默认开启）

每次合成从 `config.yaml` 的 `rate_options` / `pitch_options` / `volume_options` 中各随机取一,中心值约为 rate +15%、pitch -2Hz、volume -2%。

同目录会写 `speech.tts.yaml` 记录本次实际参数。固定参数时加 `--no-jitter`。

### 换音色

编辑 `config.yaml`:

| 参数 | 当前 | 作用 |
|------|------|------|
| `voice` | YunjianNeural | 男声底模 |
| `rate` | +15% | 语速 |
| `pitch` | -2Hz | 略降调,弱化默认 TTS 感 |
| `volume` | -2% | 略压低 |

备选男声:`zh-CN-YunyangNeural`（新闻/专业,更稳）。

---

## MiniMax T2A async v2（付费）

经 **yunwu.ai 中转**调用 MiniMax `t2a_async_v2`。模型默认 `speech-2.8-turbo`,音色默认 `male-qn-jingying-jingpin`。

### 配置

在仓库根目录 `.env` 写入（已加到 `.env.example`):

```
TTS_API_KEY=sk-...
TTS_BASE_URL=https://yunwu.ai
TTS_MODEL=speech-2.8-turbo
TTS_VOICE=male-qn-jingying-jingpin
```

### 用法

```bash
pip install requests python-dotenv pyyaml   # 或 pip install -r pipeline/tts/requirements.txt

python3 pipeline/tts/gen_speech_minimax.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

流程:`submit → poll (3s 一次,默认 5min 超时) → 取 file_id 下载链接 → 写 mp3`。

### 参数微调

编辑 `config_minimax.yaml` 的 `voice_setting`:

| 参数 | 范围 | 中心 | 作用 |
|------|------|------|------|
| `speed` | 0.5–2.0 | 1.0 | 语速 |
| `pitch` | -12 到 12（整数） | 0 | 音高 |
| `vol` | 0.1–10 | 1.0 | 音量 |
| `emotion` | neutral/happy/sad/angry/fearful/disgusted/surprised | neutral | 情绪 |

`audio_setting`:

| 参数 | 选项 |
|------|------|
| `format` | mp3 / pcm / flac / wav |
| `sample_rate` | 8000–44100 |
| `bitrate` | mp3 比特率 |
| `channel` | 1（单声道,口播默认） / 2 |

`poll` 控制轮询,`http` 控制重试。

### 换音色

完整 voice_id 列表见 MiniMax 文档。常用:

| voice_id | 音色 |
|----------|------|
| `male-qn-jingying-jingpin` | 男·精英·精品（默认） |
| `male-qn-qingse-jingpin` | 男·青涩·精品 |
| `female-shaonv-jingpin` | 女·少女·精品 |
| `female-yujie-jingpin` | 女·御姐·精品 |
| `presenter_male` | 男·主持人 |

### 注意

- async 接口为长文本设计,**短文本逐段循环时不划算**。`build_video.py` 13 段循环目前仍用 Edge TTS。
- 单次文本上限 100 万字,实测短文本也能跑（开销主要在轮询)。
- 下载 URL 有效期 9 小时。

---

## 平台会不会识别 TTS?

**简短结论:有可能检测「AI 配音特征」,但靠 pitch/rate 微调并不能可靠「骗过」平台;对数据影响通常小于内容本身。**

| 担心 | 实际情况 |
|------|----------|
| 音色被平台拉黑 | 无公开证据表明某 Edge / MiniMax 音色会被限流;大量账号在用同类 TTS |
| 微调后能「识别不出来」 | pitch ±2Hz、speed ±5% 只让成片和「默认参数」略有区别,不是换一个人 |
| 什么更影响数据 | 前 3s 钩子、完播、真实 B-roll ≥60%、剪辑节奏(不像念稿) |

**剪映可再做一层(可选)**: 极轻 EQ(略抬中频)、1–2% 房间底噪、句间手动留白 —— 比反复换 TTS 参数更有效。

## 已归档

声音克隆模块见 `legacy/voice-clone/`（含 GPT-SoVITS 集成,不再维护)。

