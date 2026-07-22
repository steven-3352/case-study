---
name: cap-stock-footage
description: 拉免费可商用的竖屏视频素材(B-roll)到本地。当需要真实质感的背景/垫片素材、反差钩子第一帧、或任何"找一段免费视频素材"的场景时使用。当前 provider 为 Pexels(CC0-like,免费可商用)。需要 PEXELS_API_KEY。输入关键词(英文最佳),输出 mp4 + 元数据 json 到指定目录。
license: MIT
capability: stock-footage
provider: pexels
---

# cap-stock-footage · 免费素材库能力

内容生产引擎「技能平面」的能力单元之一。把"从免费素材库按关键词拉竖屏 B-roll"封装成一个自洽、可移植、可配置的能力,不绑任何具体项目路径。

## 何时用

- 分镜需要真实手机/生活质感的背景或垫片素材
- 反差钩子(chaos)第一帧需要真实素材
- 任何"帮我找一段免费的 XX 视频素材"的需求

## 前置

- 环境变量 `PEXELS_API_KEY`(https://www.pexels.com/api/ 免费申请,200 req/h)。
  可直接 export,或放进当前目录 `.env`(脚本会读 `--env` 指向的文件,默认 `./.env`)。

## 用法

```bash
# 基本:拉 5 条 "messy desk late night" 竖屏素材到 ./stock_footage/
python3 fetch_stock_footage.py --q "messy desk late night" --count 5

# 指定时长范围和输出目录
python3 fetch_stock_footage.py --q "tired entrepreneur" --count 3 --min-dur 2 --max-dur 8 --out-dir ./broll

# 只看命中不下载
python3 fetch_stock_footage.py --q "city night" --dry-run
```

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--q` | (必填) | 搜索关键词,英文最佳 |
| `--count` | 5 | 目标条数 |
| `--min-dur` / `--max-dur` | 1.5 / 15.0 | 时长范围(秒) |
| `--min-height` | 1080 | 最低分辨率高度(强制竖屏 portrait) |
| `--out-dir` | `stock_footage` | 输出目录 |
| `--env` | `.env` | 可选 .env 文件路径 |
| `--dry-run` | off | 只打印命中,不下载 |

## 输入 / 输出

- **输入**:关键词字符串(`--q`)
- **输出**:`<out-dir>/<slug>__<pexels_id>.mp4` + 同名 `.json`(Pexels 元数据 + 作者署名 + license 标注)。已存在则跳过(按 id 去重)。

## 许可

- **本能力脚本**:自有代码,随引擎分发(MIT)。
- **拉取的素材内容**:Pexels 为 CC0-like,免费可商用;json 里保留作者署名(CC0 不强制但建议保留)。

## 换 provider

当前只接了 Pexels。以后加别的 CC0 库(Pixabay / Coverr 等)时,在 `search()`/`pick_file()` 抽一层 provider 接口即可,SKILL.md 的 `provider:` 字段随之扩展。

## 与原实现的关系

封装自 `pipeline/p004_video/fetch_broll.py`(本项目内实现),解耦点:去掉写死的 `PROJECT_ROOT/assets/broll/raw` 输出路径,改为 `--out-dir`;`.env` 由 `--env` 指定而非写死项目根。逻辑、Pexels 参数、requests/urllib 双回退与原实现一致。原 `pipeline/` 脚本暂不动(项目还在用),本副本是可发布的移植版。
