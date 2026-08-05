# MV 导演助手

用 Codex 对话，一步一步把一首歌做成完整的音乐视频。

---

## 快速开始

### 1. 安装环境

**Windows：**
```
setup.bat
```

**Mac / Linux：**
```bash
bash setup.sh
```

安装脚本会自动做三件事：装 Python 依赖、**下载本地语音对齐模型（faster-whisper medium，约 1.5GB）**、生成 `.env`。
medium 模型下到 `~/.local/share/mvstudio/models/`（三平台一致），运行时自动发现，无需手动配置。

> 首次下载较慢；国内网络可先设镜像再跑 setup：
> `export HF_ENDPOINT=https://hf-mirror.com`（Windows：`set HF_ENDPOINT=...`）
> 单独补下模型：`python download_whisper.py`

### 2. 配置 API Key

编辑 `.env` 文件，填入你的 API Key：
```
LLM_API_KEY=你的 OpenAI Key
GPT_IMAGE_API_KEY=你的图像 API Key
SEEDANCE_API_KEY=你的 Seedance Key
```

### 3. 用 Codex 打开本目录，开始对话

告诉 Codex："帮我做一支 MV"，它会引导你完成全部六步。

---

## 给 Codex 的一句话（直接复制）

> ⚠️ 一律用仓库 venv：`/home/ubuntu/case-study/.venv/bin/python -m conductor.cli`（系统 python 缺 numpy 会静默失败）。LLM 步骤可能要 2~3 分钟，别设短超时。

**继续之前的项目：**
```
用 mv-agent 继续做项目 <片名>：进 mv-agent/，先 status <片名> 看进度，再 run <片名> 跑到下一个拍板点。
```

**新项目初始化：**
```
用 mv-agent 新做一支 MV，片名 <片名>，物料在 <物料目录>：进 mv-agent/，先 init <片名> <物料目录>（项目根=物料目录，必填），再 run <片名>。
```

> 新项目的骨架和产物建在**物料目录**，不进工具仓库；`init` 会把「片名→物料目录」记入 `projects/_registry.json`，之后按片名操作即可。约定见 `docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1`。

---

## 六步流程

| 步骤 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| 第 0 步 | 收集素材（音乐、歌词、人物图、创作意图） | 提供文件路径 |
| 第 1 步 | LLM 分析 → 故事框架 | 确认方向对不对 |
| 第 2 步 | 出分镜脚本（X 个镜头） | 确认分镜 |
| 第 3 步 | 出首帧图 | 逐张确认 |
| 第 4 步 | 出每镜视频 | 逐段确认 |
| 第 5 步 | 合成 + 字幕 + 剪辑 | 确认最终片 |

---

## 目录结构

```
mv-agent/
  AGENTS.md          ← Codex 对话指南（自动读取）
  .env               ← API Key（自己填，不提交到 Git）
  .env.example       ← API Key 模板
  requirements.txt   ← Python 依赖
  conductor/         ← 控制器核心代码
  prompts/           ← 可编辑的中文提示词模板
  projects/          ← 你的片子工作目录（自动创建）
    <片名>/
      00_intake/     物料校验产物
      01_analysis/   LLM 分析产物
      02_storyboard/ 分镜脚本
      03_keyframes/  首帧图
      04_shots/      视频片段
      05_delivery/   最终成片
```

---

## 手动运行（不用 Codex 时）

```bash
# 初始化新片（项目根 = 物料目录，必填）
python -m conductor.cli init 我的MV /path/to/物料目录

# 查看进度
python -m conductor.cli status 我的MV

# 跑到下一个等待点
python -m conductor.cli run 我的MV

# 批准当前步骤
python -m conductor.cli ok 我的MV 01_analysis

# 打回重做（附意见）
python -m conductor.cli reject 我的MV 02_storyboard "第3个镜头太平淡了"
```

---

## 修改提示词

`prompts/` 目录下的 `.md` 文件就是给 LLM 的指令，可以直接编辑：

- `analysis.lyrics_segment.md` — 歌词分析
- `analysis.character.md` — 人物关系
- `storyboard.creative.md` — 创意分镜
- `image.background.md` — 背景生成
- `image.keyframe.md` — 首帧生成
- `video.motion.md` — 视频动作
- `translate.md` — 中译英

每次初始化新片时，系统会把这里的模板复制一份到 `projects/<片名>/prompts/`，改那里的副本只影响当前片子。

---

## 公共工具库

本包调用 `mv_platform/`（项目根目录的共享库）：
- `mv_platform.application.prompt_catalog` — 提示词默认值
- `mv_platform.application.control_plane` — API 配置加载

运行时 Python 路径会自动指向项目根目录。

---

## 当前状态（M1）

- ✅ 六步流水线骨架完整
- ✅ 提示词模板已有真实内容（来自 `mv_platform.prompt_catalog`）
- ✅ API 配置加载（`.env` → `mv_platform.ENV_MAP`）
- ⏳ M2：接入真实 LLM / 图像 / 视频 API（逐步替换 `conductor/tools.py`）
