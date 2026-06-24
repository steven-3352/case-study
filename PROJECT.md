# 项目入口

> **系统全貌已合并至 [docs/SYSTEM.md](docs/SYSTEM.md)**（宗旨 · 工作方式 · 铁律 · 能力组织 · 文档地图）。
>
> 本文仅作兼容跳转，勿在此重复维护长文。

## 快速链接

| 文档 | 用途 |
|------|------|
| [docs/SYSTEM.md](docs/SYSTEM.md) | **首读** — 系统说明 |
| [CLAUDE.md](CLAUDE.md) | Agent 执行细则与工种 |
| [docs/TODO.md](docs/TODO.md) | 今日任务 |
| [pipeline/CHECKLIST.md](pipeline/CHECKLIST.md) | 发布验收 |
| [docs/DECISIONS.md](docs/DECISIONS.md) | 皮肤层辩论结论 |

## 目录结构（摘要）

```
queue/      选题输入
templates/  工种产出格式（非成片套路）
pipeline/   渲染与组装
publish/    发布包（媒体 git 忽略）
ops/        指标与规则
docs/       系统文档
legacy/     旧素材包（降级）
```

Git：唯一分支 `main`。
