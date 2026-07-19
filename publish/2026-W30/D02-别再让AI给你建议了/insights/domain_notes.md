# 领域笔记 · 事前验尸用于 AI 计划评估

> 状态：`draft`

## 实验设计

- 模型：`claude-opus-4-8`，项目已配 LLM 中转。
- 人称实验：同模型、同 system、同事实、同要求，仅“我”改“小林”，两轮。效应不稳定，否决。
- 事前验尸实验：同模型和同计划；A 为普通评价，B 假设六个月后已失败并倒推。两轮原文完整落盘。

## 可说与不可说

- 可说：B 组稳定以“死因 → 计划现有事实 → 失败路径”组织回答。
- 可说：它把普通风险清单改成了失败路径倒推。
- 不可说：更凶、更准、一定能避免失败、陌生人视角必然更客观。

## 可复现命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pipeline/w30d02_persona_ab.py --mode persona
PYTHONDONTWRITEBYTECODE=1 python3 pipeline/w30d02_persona_ab.py --mode premortem
```
