# AI 小系统获客引擎

通过持续展示「我用 AI 解决小老板每天都烦的问题」来获客的内容生产与增长反馈系统。详见 **[PROJECT.md](PROJECT.md)**。

## 当前阶段

**Phase 0 · 备齐 pipeline（Project-001）**

→ 辩论结论：[docs/DECISIONS.md](docs/DECISIONS.md)
→ 每日任务：[docs/TODO.md](docs/TODO.md)

## 内容方向

账号不是 AI 教程号，也不是经验分享号。主线是：

> 我用 AI 把小老板每天烦、重复、没人管的事，做成能跑的小系统。

每条内容优先回答：这个项目帮哪类小老板省时间、减少错误、接住线索，或提高转化。

## 核心文档

| 文档 | 说明 |
|------|------|
| [PROJECT.md](PROJECT.md) | 项目入口 |
| [docs/BLUEPRINT.md](docs/BLUEPRINT.md) | 总蓝图 |
| [docs/SCHEDULE.md](docs/SCHEDULE.md) | 按天工期 |
| [docs/TODO.md](docs/TODO.md) | 每日任务 |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | 技术栈 |

## 环境配置

API 密钥统一放在仓库根目录 **`.env`**（不入库）：

```bash
cp .env.example .env
# 三方中转：每个服务填 KEY + BASE_URL（见 .env.example 注释）
```

| 服务 | KEY | BASE_URL（中转根地址） |
|------|-----|------------------------|
| MiniMax TTS | `MINIMAX_API_KEY` | `MINIMAX_BASE_URL` |
| Claude | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL` |
| 火山 TTS | `VOLC_TTS_APPID` + `VOLC_TTS_TOKEN` | `VOLC_TTS_BASE_URL` |
| OpenAI 图像 | `OPENAI_API_KEY` | `OPENAI_BASE_URL` |

## 旧版说明（案例素材包）

本 repo 最初是半匿名自动化案例素材包，现升级为内容增长引擎。
旧脚本见 [legacy/README.md](legacy/README.md)。

```bash
python3 build_shots.py    # 真实截图帧（B-roll 用）
python3 build_slides.py   # 架构图（降级）
python3 build_video.py    # TTS 草稿（降级）
```
