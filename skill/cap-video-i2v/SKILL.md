---
name: cap-video-i2v
description: 图生视频 / 文生视频(i2v/t2v)生成。当分镜里有 motion/video prompt 字段、需要把一张首帧图变成一段动态视频、或做纯文生视频时使用。当前 provider 为 Seedance 2.0(doubao-seedance,走中转)。支持单段快调和 yaml 批量,带重试/并发/断点续跑/可选后置 QA。需要 SEEDANCE_API_KEY / SEEDANCE_BASE_URL。写 motion prompt 前应先读 i2v-video-prompt skill。
license: MIT
capability: video-i2v
provider: seedance
---

# cap-video-i2v · 图生/文生视频能力

内容生产引擎「技能平面」的能力单元之一。把"i2v/t2v 视频生成"封装成自洽、可移植、可配置的能力,不绑任何项目路径。

## 何时用

- 分镜 storyboard 出现 `motion prompt` / `video prompt` 字段
- 有一张首帧图(立绘/场景),要生成一段动态视频(i2v)
- 纯文本生成一段视频(t2v,不给首帧)

> **写 motion prompt 前**:先按 i2v-video-prompt skill 的骨架写(2s 钩子公式、精确镜头运动、灯光 K 值、人物 anchor、NEGATIVES 段),再喂给本能力。本能力只负责"提交→轮询→下载",不负责 prompt 质量。

## 前置

- 依赖:`requests`、`pyyaml`(必需);`python-dotenv`(可选,缺失时自带 .env 解析)
- env:`SEEDANCE_API_KEY` / `SEEDANCE_BASE_URL`(必需)· `SEEDANCE_MODEL`(默认 `doubao-seedance-2-0`)· `SEEDANCE_WORKERS`(默认 2)
  - 可 export,或放进 .env 用 `--env` 指定

## 用法

```bash
# 单段快调(i2v · 给首帧)
python3 gen_video.py --prompt "<motion prompt>" --first-frame ./frames/S01.png --duration 5 --out ./out/S01.mp4

# 单段(t2v · 无首帧)
python3 gen_video.py --prompt "<motion prompt>" --duration 5 --out ./out/S01.mp4

# yaml 批量(图片相对 --asset-root,默认取 yaml 所在目录)
python3 gen_video.py --config storyboard.yaml --out-dir ./out --asset-root ./frames

# 断点恢复(跳过 .status.json 里已完成的 slug)
python3 gen_video.py --config storyboard.yaml --out-dir ./out --resume

# 接一个可选的成品体检脚本(rc=0 视为 PASS,不阻断)
python3 gen_video.py --config storyboard.yaml --out-dir ./out --qa-script /path/to/media_check.py
```

## 参数

| 参数 | 说明 |
|---|---|
| `--config` / `--out-dir` | 批量模式:yaml + 输出目录(配对) |
| `--asset-root` | 图片相对路径根,默认 yaml 所在目录 |
| `--resume` | 跳过 .status.json 已完成 slug |
| `--only` | 只跑指定 slug(逗号分隔) |
| `--workers` | 并发覆盖 |
| `--env` | 可选 .env 路径 |
| `--qa-script` | 可选成品 QA 脚本(接收 mp4 路径) |
| `--prompt` / `--first-frame` / `--duration` / `--negatives` / `--out` | 单段模式 |

## yaml 格式

```yaml
workers: 2
aspect_ratio: 9:16
resolution: 720p
scenes:
  - slug: S01_kitchen
    prompt: |
      <motion prompt>
    duration: 5
    first_frame: S01.png        # 相对 --asset-root · 省略走 t2v
    ref_frames:
      - S01_ref.png
    negatives: |
      NO face morphing, NO body stretching, NO neon purple/cyan.
```

## 输入 / 输出

- **输入**:motion prompt(+ 可选首帧/参考图)
- **输出**:`<out-dir>/<slug>.mp4` + `.status.json`(断点续跑)。已完成 slug 在 `--resume` 下自动跳过。

## 能力内建的健壮性

重试(429/503/408 指数退避,auth/url/payload/content-policy 硬错误不重试)· sync/async 双兼容(轮询探测多候选 endpoint)· 并发 worker · 断点续跑 · 可选后置 QA。

## 换 provider

当前 provider = Seedance。grok-imagine-video 等其他 i2v 模型走同一 `/v1/videos/generations` 协议形态,后续可在 `submit_with_retry` 抽 provider 层加入,`provider:` 字段随之扩展。选 provider 属流程平面的实现选型(五维打分),本能力只提供"接哪个模型"的开关。

## 与原实现的关系

封装自 `pipeline/p011_seedance_i2v/gen_video.py`,解耦点:①去掉写死的项目根 `ROOT`,`.env` 由 `--env` 指定;②图片相对路径改由 `--asset-root` 解析(原为项目根);③后置 QA 从硬指向 `pipeline/gate_check_media.py` 改为 `--qa-script` 可选注入。重试/轮询/并发/断点逻辑与原实现一致。原 `pipeline/` 脚本暂不动。
