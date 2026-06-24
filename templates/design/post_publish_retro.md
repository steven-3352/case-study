# 投后复盘 · actual vs 预估

> **工种：平台表现分析师 + 编导** · 发布后 48–72h 填  
> **结构化数据：** `design/performance.yaml` · 跑 `python3 pipeline/evolution_apply.py --id {project_id}`

## 0. 填数（先做）

编辑 `design/performance.yaml` → `platforms.douyin.actual`：

或使用自动拉取：

```bash
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04
# 或手动 JSON：--import-json path.json
```

然后：

```bash
python3 pipeline/evolution_apply.py --id W26D04
# 读 publish/2026-W26/evolution_brief.yaml · 下条 design/evolution_overlay.md
```

## 1. 发布信息

| 平台 | 发布时间 | 形式 |
|------|----------|------|
| 抖音 | | video / 图文 |
| 小红书 | | carousel / video |

## 2. actual vs forecast

| 指标 | 预估（pre_publish_forecast） | 实际 | 偏差 | 归因 |
|------|------------------------------|------|------|------|
| 3s 完播 | | | | |
| 完播率 | | | | |
| 互动率 | | | | |

## 3. 形式层复盘

- 哪几镜停划/流失与预估一致？
- 哪几镜出乎意料（好/坏）？
- 下条 Rubric/gate 建议调整（具体阈值）：

## 4. 进化动作

- [ ] 登记 `docs/design/FORM_FAIL_LOG.md`（若形式预估严重偏差）
- [ ] 提议更新 `gate_check.py` 阈值（如 catalog 35%→25%）
- [ ] 提议更新 `scorecard_rubric.md`

## 5. 联签

- [ ] 平台表现分析师
- [ ] 编导
