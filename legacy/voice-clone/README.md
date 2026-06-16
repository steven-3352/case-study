# 声音克隆 · 已归档（不再使用）

> **2026-06-16 放弃**：GPT-SoVITS 零样本克隆效果不达标（不像本人、机械感重）。  
> 默认口播改 **`pipeline/tts/gen_speech.py`（Edge TTS）** 或数字人 SaaS 原生音。  
> 决策见 `docs/DECISIONS.md` Q7。

---

# ~~声音克隆 · 公共模块~~（历史文档）

> 输入：参考录音 + 文案 → 输出：口播 wav/mp3  
> 引擎：本地开源 TTS 服务（HTTP API），本 repo 只负责调用。

## 架构

```
assets/avatar/dry_audio/dry_v1.wav   ← 你的参考录音
pipeline/voice/config.yaml           ← 音色与 API 配置
pipeline/voice/gen_voice.py          ← 公共 CLI
        │
        ▼ HTTP
┌───────────────────────────────────────┐
│  任选其一（独立部署，建议 Docker/GPU）   │
│  · GPT-SoVITS api_v2  ← Phase 0 推荐  │
│  · Speech-AI-Forge    ← 多引擎统一 API │
│  · CosyVoice FastAPI                   │
│  · Fish Speech                         │
└───────────────────────────────────────┘
        │
        ▼
pipeline/{id}/speech.wav  → 剪映 / 数字人口型
```

## 快速开始

### 1. 准备参考音

```bash
# 录好后放这里（3–10 分钟，wav/mp3）
assets/avatar/dry_audio/dry_v1.wav
```

`config.yaml` 里 `prompt_text` 填**参考音前几秒对应的文字**（与录音内容一致），克隆质量会明显更好。

### 2. 部署 GPT-SoVITS API（推荐）

```bash
# 另开目录，不与 case-study 混装
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
conda create -n GPTSoVits python=3.10 && conda activate GPTSoVits
bash install.sh --device MPS --source HF-Mirror   # macOS
# 或 --device CU126（NVIDIA 云/GPU 机）

python api_v2.py -a 127.0.0.1 -p 9880
```

macOS 可用 MPS/CPU，速度较慢但能跑；**有 NVIDIA GPU 的机器或 Docker 更适合常驻服务**。

### 3. 生成口播

```bash
# 从空跑脚本提取口播并合成
python3 pipeline/voice/gen_voice.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.wav

# 或直接传文本
python3 pipeline/voice/gen_voice.py \
  --text "第五天一看数据，我傻眼了。" \
  -o /tmp/test.wav
```

## 开源方案对比

| 方案 | 许可 | 中文 | API | 参考音 | 适合 |
|------|------|------|-----|--------|------|
| **[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)** | MIT | ✅ | 自带 `api_v2.py` | 5s 零样本，1min 微调更佳 | **首选**，成熟 |
| **[Speech-AI-Forge](https://github.com/lenML/Speech-AI-Forge)** | — | ✅ | 统一 REST | 多引擎可切换 | 想换模型不改代码 |
| **[CosyVoice](https://github.com/FunAudioLLM/CosyVoice)** | Apache | ✅ | FastAPI | 零样本 | 质量高，偏重 |
| **[Fish Speech](https://github.com/fishaudio/fish-speech)** | Apache | ✅ | 有 | 短参考 | 与 Fish 商业同系 |
| **[Index-TTS](https://github.com/index-tts/index-tts)** | — | ✅ | 有 | 短参考 | B 站系，中文好 |

**不建议 Phase 0 用的：** Coqui XTTS（社区停更）、纯 Edge TTS（非克隆，仅草稿）。

## 与本项目流水线衔接

```
script.md → gen_voice.py → speech.wav
                ↓
         剪映：speech + B-roll（数字人≤40%）
                ↓
         douyin.mp4 / xhs_video.mp4
```

旧 `build_video.py`（Edge TTS）仅作**对比草稿**，正式发布走本模块。

## 环境变量（可选）

```bash
export VOICE_API_URL=http://127.0.0.1:9880
export VOICE_REF_AUDIO=/path/to/dry_v1.wav
export VOICE_PROMPT_TEXT="做了二十年互联网了，自己创业中。"
```

## 故障排查

| 问题 | 处理 |
|------|------|
| 连接 refused | 确认 `api_v2.py` 已启动，端口与 config 一致 |
| 声音不像 | 加长参考音；补准 `prompt_text`；用 1min 微调 |
| macOS 很慢 | 换 GPU 云主机跑 API，本机只调 `gen_voice.py` |
| 漏字/重复 | 换 GPT-SoVITS v2Pro/v4；文本分段生成再拼接 |
