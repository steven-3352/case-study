# AI 小系统获客引擎

> 用 AI 解决小老板每天都烦的问题 · 小红书 / 抖音 / 视频号
> **当前阶段：Phase 0 备齐 pipeline（Project-001）**
> **决策锁定：** [docs/DECISIONS.md](docs/DECISIONS.md)

## 定位

这不是 AI 教程号，也不是单纯的经验分享号。

核心方向是：持续用 AI 做真实小项目，把小老板每天烦、重复、没人管的流程，改造成能跑的小系统，并用项目内容吸引有类似需求的人，最终转成咨询、定制开发、自动化交付客户。

一句话：

> 我用 AI 把小老板每天烦、重复、没人管的事，做成能跑的小系统。

内容重点不是证明「我懂 AI」，而是让潜在客户看到：

- 这个问题我也有
- 原来可以这样自动化
- 这个人能把模糊需求落成可用系统

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
persona/          IP 配置（persona.yaml）
queue/            小老板场景/项目选题队列（你主要输入）
templates/        脚本/发布模板
assets/           数字人 + B-roll 素材
pipeline/         生产流水线 + 空跑
ops/              指标、规则、数据规范
publish/          待发布成品（Phase 1）
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
