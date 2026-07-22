---
name: cap-tts
description: 文字转语音口播合成。当需要给脚本/口播文案配音、生成旁白 mp3/wav 时使用。支持三 provider:edge(免费保底,无需 key)/ minimax(海螺,自然音)/ volcengine(火山/豆包),由 config.provider 决定,自然 TTS 失败可回落 edge。输入脚本 md(按 marker 抽口播)或直接文本,输出 mp3/wav。
license: MIT
capability: tts
provider: edge|minimax|volcengine
---

# cap-tts · 语音合成能力

内容生产引擎「技能平面」的能力单元之一。把"口播/旁白 TTS 合成"封装成自洽、可移植、多 provider 的能力,不绑任何项目路径。

## 何时用

- 给脚本/口播文案配音,生成旁白音频
- 视频音画硬门要求 VO 全程覆盖,用本能力出口播

## 前置

- 依赖:`pyyaml`(必需)· `ffmpeg`(仅 wav 输出需要)· `edge-tts`(edge provider 保底,`pip install edge-tts`)
- env(按选用 provider):
  - **edge**:无需 key(本地 edge-tts)
  - **minimax**:`MINIMAX_API_KEY` + `MINIMAX_BASE_URL`(中转,注意可能需 `/minimax` 前缀)+ `MINIMAX_GROUP_ID`(可选)
  - **volcengine**:`VOLC_TTS_APPID` + `VOLC_TTS_TOKEN` + `VOLC_TTS_BASE_URL`(可选)
  - 可 export 或放 .env 用 `--env` 指定

## 用法

```bash
# 直接给文本(用 config.provider,默认 minimax,失败回落 edge)
python3 gen_speech.py --text "你好世界这是一段测试口播文本" -o out.mp3 --env ./.env

# 从脚本 md 按 marker 抽口播
python3 gen_speech.py --script script.md -o out.mp3 --env ./.env

# 强制某 provider / 输出 wav
python3 gen_speech.py --text "..." -o out.wav --provider edge
```

## 参数

| 参数 | 说明 |
|---|---|
| `--text` / `--script` | 二选一:直接文本 / 从 md 按 `script_extract.markers` 抽口播 |
| `-o/--output` | 输出路径(.mp3 或 .wav);wav 走 ffmpeg 转码 mono |
| `--provider` | 覆盖 config.provider(edge/minimax/volcengine) |
| `--config` | 配置文件(默认同目录 config.yaml) |
| `--env` | 可选 .env 路径 |

## provider 切换

由 `config.yaml` 的 `provider:` 字段决定;`strict_provider: true` 时选定 provider 失败即报错(生产建议开),`false` 时回落 edge。各 provider 参数(voice_id/emotion/speed 等)在 config.yaml 对应段。

## 输入 / 输出

- **输入**:口播文本(`--text`)或脚本 md(`--script`,按 marker 抽取,去空白,<10 字报错)
- **输出**:`-o` 指定的 mp3/wav + 同名 `.tts.yaml`(记录 provider + voice)

## 库函数

`synthesize_text(text, out_mp3, config_path, *, emotion, speed, provider)` 可被上层流程按段调用(逐段传 emotion/speed 做抑扬),返回实际使用的 provider 名。

## 组成文件

- `gen_speech.py` — 主入口 + 三 provider 合成
- `minimax_client.py` — MiniMax 异步 t2a_async_v2 客户端
- `local_env.py` — 本地 .env 加载 + api_base(替代原项目根 env_loader)
- `config.yaml` — provider 与音色参数

## 与原实现的关系

封装自 `pipeline/tts/gen_speech.py` + `minimax_client.py` + `env_loader.py`,解耦点:①`pipeline.env_loader`(import 即从项目根加载 .env)→ 本地 `local_env`(显式 `--env`);②`pipeline.tts.minimax_client` 包路径 import → 同目录 `minimax_client`;③CLI 从"只走 edge"改为暴露完整 provider 切换(原 edge-only 的 main 只是历史入口,多 provider 逻辑本就在 `synthesize_text`);④清掉 config 里项目专属注释与 uid。合成逻辑与原实现一致。原 `pipeline/` 脚本暂不动。
