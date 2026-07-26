# 07 · 环境配置

> **首次接手项目 · 5 步初始化**(按操作系统区分)

---

## 1. Python 3.9+

```bash
# macOS(自带 python3 · 或用 brew install python@3.11)
python3 --version   # 应 ≥ 3.9

# Linux(Ubuntu/Debian)
sudo apt install python3.11 python3.11-venv   # 或 3.9+ 任一

# Windows
# 从 https://www.python.org/downloads/ 下 3.11.x · 装时勾 "Add to PATH"
```

## 2. 虚拟环境 + Python 依赖(强烈建议隔离)

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Windows(PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Post-install(playwright 装浏览器 · 所有系统)

```bash
playwright install chromium
```

## 4. 系统依赖(不通过 pip · 按 OS 装)

| 依赖 | 用途 | macOS | Linux(Debian/Ubuntu) | Windows |
|---|---|---|---|---|
| **ffmpeg**(基础版) | 音视频合成 | `brew install ffmpeg` | `sudo apt install ffmpeg` | 从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下 · 加 PATH |
| **ffmpeg-full**(含 libass) | 字幕烧录必需 | `brew install ffmpeg-full`(路径 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`) | apt 自带 ffmpeg 通常已含 libass | gyan.dev 的 "full" build 已含 |
| **Google Chrome** | P001 pipeline HTML 截图渲染 | 官网下载 | apt install google-chrome-stable | 官网下载 |
| **git** | 版本控制 | 系统自带或 `brew install git` | apt install git | Git for Windows |
| **剪映**(可选) | 人肉后剪辅助 | 仅 macOS · App Store 下 | ❌ 无 Linux 版 | 有 Windows 版但项目未验证 |

## 5. 复制 .env 模板填 API keys

```bash
cp .env.example .env   # macOS/Linux
copy .env.example .env # Windows PowerShell
# 然后打开 .env 填入 GPT_IMAGE_API_KEY / TTS_API_KEY / GROK_API_KEY / SEEDANCE_API_KEY 等
```

**必读**:`.env.example` 里每条中转服务都有配置范例(如云雾中转的 `/minimax` `/openai-v1` 前缀),忽略容易漏写。

## 可选:调研工具 · agent-reach

用途:小红书/B站/Reddit 公开内容调研(消费者声音),**不用于**商品/电商详情爬取。

```
让 Claude/Codex 跑:帮我安装 Agent Reach:
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md
```

## 验证初始化成功

```bash
python3 -c "import openai, PIL, dotenv, edge_tts, playwright, pydantic, requests, yaml; print('OK')"
```

---

## Git 与分支

- **唯一工作分支:`main`** — 日常开发、提交、推送均在 `main` 上完成
- 不创建日期分支或长期 feature 分支;小改动直接 commit,大改动可在本地 short-lived 分支做完后 **merge 回 `main` 并删除**
- 克隆后默认:`git checkout main && git pull origin main`

## 统一画布规格

- 全局 9:16 → 1080×1920(图文 + 视频统一)
- 常量定义:`pipeline/screen_dims.py`(`CANVAS_W/H`, `VIDEO_W/H`, `IPHONE_W/H`)

## 接手项目第一动作(调用通用服务前)

调 TTS / GPT-image / LLM / 向量等共享服务前**必做**三件事:

1. `cat .env.example` — 看每条服务的中转地址范例,对照 `.env` 看凭证 + URL 是否齐全(尤其云雾中转的 `/minimax` `/openai-v1` 一类前缀,容易漏写)
2. `grep -r "<服务名>" publish/2026-W*/ pipeline/p004_video/_d*_*_config.yaml` — 找最近一条跑通的姊妹脚本,直接抄它的 config
3. 4xx/5xx 不能直接降级 fallback — 先核对 URL 拼写,再查凭证,最后才考虑切 provider

依据:memory `feedback_read-env-example-first`

---

## Source Map

- 原 `CLAUDE.md §环境配置`
- 原 `CLAUDE.md §Git 与分支`
- 原 `CLAUDE.md §统一画布规格`
- 原 `docs/SYSTEM.md §2.5 Git`
- 原 memory `feedback_read-env-example-first`
