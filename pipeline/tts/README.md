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

## MiniMax · speech-2.8-turbo（自然 TTS）

```bash
cp .env.example .env   # 填入 MINIMAX_API_KEY + MINIMAX_BASE_URL（三方中转根地址）

# 批量试听 6 个候选音色 → pipeline/tts/_previews/*.mp3
python3 pipeline/tts/preview_minimax_voices.py

# 启用 minimax：编辑 config.yaml → provider: minimax
python3 pipeline/tts/gen_speech.py --text "第五天一看数据，我傻眼了。" -o /tmp/test.mp3
```

接口：`{MINIMAX_BASE_URL}/v1/t2a_async_v2`，模型 `speech-2.8-turbo`。  
`.env` 里 `MINIMAX_BASE_URL` 优先于 `config.yaml` 的 `api_host`；未填则走官方 `api.minimaxi.com`。凭证缺失时自动回落 Edge TTS。

**P001 口播候选（按自然度优先）：**

| voice_id | 名称 | 特点 |
|----------|------|------|
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 | 叙事感强，默认首选 |
| `Chinese (Mandarin)_Gentleman` | 温润男声 | 中年、克制 |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 | 匹配「20年互联网」 |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 | 偏口语 |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 | 更生活化 |

慎选：`male-qn-qingse`（太嫩）、`Male_Announcer`（播音腔）、`male-qn-badao`（戏剧化）。

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
