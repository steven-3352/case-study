# AI 小系统获客引擎

> 指定选题 · 多 Agent 编排 · 可发布成品 · 小红书 / 抖音 / 视频号
> **当前阶段：Phase 0 备齐 pipeline（Project-001）**
> **决策锁定：** [docs/DECISIONS.md](docs/DECISIONS.md)

## 核心用途（系统）

本仓库建的是**自媒体内容自动化生产引擎**，不是某个垂直行业的单点工具。

针对指定选题（`queue/topics.yaml`），系统自动或半自动完成：

```
选题立项 → 资料收集与整理 → 多 Agent 工种编排 → 流水线出片 → 发布包验收
```

| 环节 | 做什么 | 主要路径 |
|------|--------|----------|
| 输入 | 你定选题、形态、验收标准 | `queue/topics.yaml` |
| 采料 | 证据链、消费者声音、B-roll、项目画面 | 记者 / Agent-Reach / `assets/` |
| 编排 | 多工种并行产出（脚本、分镜、合规、文案…） | `CLAUDE.md` 工种清单 |
| 生产 | 脚本 → 画面 → 配音 → 成片/图文 | `pipeline/*` |
| 输出 | 可直接发布的成品 + 三平台文案 | `publish/` |

**终态**（见 [docs/BLUEPRINT.md](docs/BLUEPRINT.md)）：你每周 <30 分钟定选题和方向；其余生产、采集、报告自动化。

换一批选题（行业、形态、平台），**同一套引擎仍应能跑**；垂直方向是可替换的「内容皮肤」，不是引擎定义本身。

## 当前内容皮肤（账号）

现阶段用「小老板 + 小系统」验证流水线，并顺带获客。这是**当前选题与人设**，不是项目边界。

这不是 AI 教程号，也不是单纯的经验分享号。

对外一句话：

> 我用 AI 把小老板每天烦、重复、没人管的事，做成能跑的小系统。

内容重点不是证明「我懂 AI」，而是让潜在客户看到：

- 这个问题我也有
- 原来可以这样自动化
- 这个人能把模糊需求落成可用系统

变现路径（当前皮肤下）：项目内容吸引共鸣 → 等私信 → 咨询 / 定制开发 / 自动化交付。详见 [docs/CONVERSION.md](docs/CONVERSION.md)。

## 快速入口

| 文档 | 用途 |
|------|------|
| [docs/BLUEPRINT.md](docs/BLUEPRINT.md) | 总蓝图、模块、阶段 |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | 技术选型 |
| [docs/SCHEDULE.md](docs/SCHEDULE.md) | 28 天 + 8 周排期 |
| [docs/TODO.md](docs/TODO.md) | **每日任务清单（执行用）** |
| [pipeline/CHECKLIST.md](pipeline/CHECKLIST.md) | 发布前验收 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Q1–Q6 辩论结论 |
| [docs/CONVERSION.md](docs/CONVERSION.md) | 等私信转化 |
| [docs/PHASE1_CALENDAR.md](docs/PHASE1_CALENDAR.md) | Project-001 四形态排期 |

## 目录结构

```
persona/          IP 配置（persona.yaml）· 当前内容皮肤的人设
queue/            指定选题队列（你主要输入）· 见 topics.yaml
templates/        脚本/发布模板
assets/           B-roll / 项目截图录屏
pipeline/         生产流水线（渲染组装层）
publish/          可发布成品 + 三平台文案
ops/              指标、规则、数据规范
docs/             蓝图、排期、TODO
legacy/           旧案例素材生成器（降级）
```

## 今日做什么

1. 打开 [docs/TODO.md](docs/TODO.md) 找到当前 Day
2. 在 [docs/SCHEDULE.md](docs/SCHEDULE.md) 填 `start_date`
3. 填 [persona/persona.yaml](persona/persona.yaml) 的 name/handle

## 阶段

| 阶段 | 状态 | 目标 |
|------|------|------|
| Phase 0 | **进行中** | 28 天备齐 pipeline，Project-001 空跑 |
| Phase 1 | 待启动 | 同一项目 4 形态发布，W9 总结 |
| Phase 2 | 待启动 | 半自动报告+选题 |
| Phase 3 | 待启动 | 只选题+方向 |

## 遗留工具

旧「案例素材包」脚本仍可用，但**不作首发默认**：

```bash
python3 build_shots.py   # 真实页面截图帧（推荐保留）
python3 build_slides.py  # 黑金架构图（仅素材库，见 legacy/）
python3 build_video.py   # TTS 草稿预览（不作正式发布）
```

## 原则

- 可行优先，不追求完美
- 先人工干预，逐步自动化
- 真实数据从小到大，不编造里程碑
- 视频全屏演示 + 口播字幕，不出真人/数字人（见 Q8）
- 项目结果先于方法论，业务问题先于技术栈
