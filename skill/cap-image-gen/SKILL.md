---
name: cap-image-gen
description: 通用出图能力(文生图 + 参考图驱动)。当需要生成插画/背景/角色/场景静图时使用。两种模式:纯文生图,或"参考图驱动"(给一张角色设定图当 ref,后续每镜从它 edit 出图以锁角色一致性)。当前 provider 为 GPT-image-2。支持单张和 yaml 批量。需要 GPT_IMAGE_API_KEY / GPT_IMAGE_BASE_URL。写 prompt 可配合 ai-image-prompts / higgsfield-gpt-image-2 等 prompt skill。
license: MIT
capability: image-gen
provider: gpt-image-2
---

# cap-image-gen · 通用出图能力

内容生产引擎「技能平面」的能力单元之一。把"文生图 + 参考图驱动出图"封装成自洽、可移植、可配置的能力,不绑任何项目路径。

## 何时用

- 生成插画 / 背景板 / 角色立绘 / 场景静图
- **角色一致性场景(重点)**:先出一张角色设定图,后续每镜以它为参考图 `--ref` 走 edit 模式改姿态/场景,而不是每镜独立盲生成——这是"漫画/音乐/MV"风格锁角色不漂移的关键做法

## 两种模式

| 模式 | 触发 | 底层 | 用途 |
|---|---|---|---|
| **文生图 t2i** | 只给 `--prompt` | `images.generate` | 背景板、概念图、无一致性约束的画面 |
| **参考图驱动 edit** | `--prompt` + `--ref` | `images.edit(image=refs)` | 角色/风格一致性:参考图定基准,prompt 改变化 |

## 前置

- 依赖:`openai`(SDK,必需)· `pyyaml`(仅批量模式)
- env:`GPT_IMAGE_API_KEY` / `GPT_IMAGE_BASE_URL`(必需,回落 `OPENAI_*`)· `GPT_IMAGE_MODEL`(默认 `gpt-image-2`)· `GPT_IMAGE_WORKERS`(默认 2)
  - 可 export,或放 .env 用 `--env` 指定

## 用法

```bash
# 文生图单张
python3 gen_image.py --prompt "<出图 prompt>" --out out.png --env ./.env

# 参考图驱动单张(角色一致性:从设定图改姿态)
python3 gen_image.py --prompt "same character, now sitting at a desk, side view" \
    --ref char_sheet.png --out S01.png

# 多参考图
python3 gen_image.py --prompt "..." --ref front.png side.png --out S02.png

# yaml 批量(refs 相对 --asset-root,默认 yaml 所在目录)
python3 gen_image.py --config scenes.yaml --out-dir ./imgs --asset-root ./refs
```

## 参数

| 参数 | 说明 |
|---|---|
| `--prompt` / `--out` | 单张模式:prompt + 输出 png |
| `--ref` | 单张模式:0..N 张参考图(给了走 edit 模式) |
| `--config` / `--out-dir` | 批量模式:yaml + 输出目录 |
| `--asset-root` | 批量:参考图相对根(默认 yaml 所在目录) |
| `--size` | 出图尺寸(默认 1024x1536) |
| `--model` / `--workers` | 覆盖模型 / 并发 |
| `--env` | 可选 .env 路径 |

## yaml 格式

```yaml
size: 1024x1536
model: gpt-image-2
scenes:
  - slug: char_sheet
    prompt: |
      <角色设定图 prompt>
  - slug: S01
    prompt: |
      same character, now at a night desk, 3/4 view
    refs:                    # 有 ref → edit 模式(相对 --asset-root)
      - char_sheet.png
```

## 输入 / 输出

- **输入**:prompt(+ 可选参考图)
- **输出**:`<out-dir>/<slug>.png`;已存在则跳过(便于断点/增量)

## 写 prompt

本能力只负责"提交→落盘",不含 prompt 库。写 prompt 时配合 `ai-image-prompts` / `higgsfield-gpt-image-2` 等 prompt-director skill;色板/禁用项遵循使用者项目自己的视觉铁律。

## 换 provider

当前 provider = GPT-image-2(OpenAI 兼容 images API)。换 Nano Banana / MJ 等时,在 `_make_client` + `generate_one` 抽 provider 层,`provider:` 字段随之扩展。

## 与原实现的关系

**从零新写的参数化封装**,不是抽某个现有脚本——原项目 `p002_carousel_gen.py` 把 prompt/文案 6×3 版内联写死、输出路径写死,没有通用入口。本脚本以 `pipeline/gen_d07_bg.py`(直连 `/v1/images/generations`)+ `pipeline/gen_scene_frames.py`(`images.edit` 参考图形态)为骨架,抽成 prompt/尺寸/参考图/输出全参数化的通用能力。重试(4 次 5s 退避)+ 并发 + 已存在跳过与原实现一致。
