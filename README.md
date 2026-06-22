# AI 小系统获客引擎

**指定选题 → 自动采料 → 多 Agent 工种编排 → 可发布自媒体成品** 的内容生产与增长反馈系统。详见 **[PROJECT.md](PROJECT.md)**。

## 核心用途（系统）

针对 `queue/topics.yaml` 中的指定选题：

1. 自动/半自动收集资料（证据、消费者声音、B-roll、项目画面）
2. 多 Agent 专业化编排（见 `CLAUDE.md` 工种清单：编导、记者、编剧、合规…）
3. 流水线落地（`pipeline/`：脚本 → 画面 → 配音 → 成片/图文）
4. 输出发布包（`publish/`：成片 + 三平台文案 + 验收清单）

终态：你每周 <30 分钟定选题和方向，其余生产/采集/报告自动化。

## 当前阶段

**Phase 0 · 备齐 pipeline（Project-001）**

→ 辩论结论：[docs/DECISIONS.md](docs/DECISIONS.md)
→ 每日任务：[docs/TODO.md](docs/TODO.md)

## 当前内容皮肤（账号）

「小老板烦事 → 能跑的小系统」是**现阶段验证流水线的垂直选题与账号人设**，不是系统的边界。换选题后，同一套引擎仍应能跑通。

账号不是 AI 教程号，也不是经验分享号。当前主线：

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
