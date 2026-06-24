# D04 · 投后复盘 · actual vs 预估

> **工种：平台表现分析师 + 编导** · 发布后 48–72h 填  
> content_version: **v11** · 结构化数据：`design/performance.yaml`

## 1. 发布信息

| 平台 | 计划时间 | 实际发布时间 | 形式 |
|------|----------|--------------|------|
| 抖音 | 2026-06-25 19:30 | _待填_ | video 55.5s · v11 |
| 小红书 | 2026-06-25 12:30 | _待填_ | P007 漫画 6 张 |

## 2. actual vs forecast（抖音）

| 指标 | 预估区间 | 实际 | 偏差 | 归因（填数据后写） |
|------|----------|------|------|-------------------|
| 3s 完播 | 58–68% | _待填_ | | 首镜 312/48→11 punch |
| 完播率 | 18–24% | _待填_ | | 7 专属镜 · 0% catalog |
| 互动率 | 2.2–3.5% | _待填_ | | CTA 发送+秒回完整 |
| 均播(s) | 12–18 | _待填_ | | |
| 播放 | — | _待填_ | | |
| 评/赞/转 | — | _待填_ | | |

**推荐（自动）：**

```bash
python3 pipeline/fetch_platform_metrics.py --login douyin      # 首次扫码
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04  # 发布后拉数 → 自动 evolution
```

**或手动 JSON：** `templates/design/platform_metrics_import.example.json`

```bash
python3 pipeline/fetch_platform_metrics.py --import-json path.json
```

## 3. 形式层复盘（v11 设计假设 · 待数据验证）

| 镜头 | 时间 | 假设 | 待验证 |
|------|------|------|--------|
| hook_count | @1s | 3s 完播高于 v10 Excel 冷开 | actual 3s vs 58% 下限 |
| wechat_type | @16s | unexpected 停划 | 均播是否过 16s |
| compare_reach | @42s | 中段不拖 | 完播曲线 40–50s |
| cta_send | @52s | 互动率支撑 | 评论里是否出现「靠表算」 |

## 4. 对下一条的进化指令（预填 · 数据确认后升级 confidence）

| ID | 信号 | 来源 | 应用到 | confidence |
|----|------|------|--------|------------|
| E001 | 数字 punch 首镜 > Excel/表格冷开 | D04 forecast + v10 教训 | D05–D07 | **hypothesis** |
| E002 | catalog 0% > pain+compare+cta 三连 | D04 form_audit | 全周 | **confirmed**（像素） |
| E003 | CTA 完整进片 > 裁尾 48s | D04 v10 vs v11 | D05+ | **confirmed**（结构） |
| E004 | 55s 可接受若均播>12s | D04 forecast | D05 时长 | **hypothesis** |

> **hypothesis** → 填 actual 后若验证，升级为 **confirmed** 写入 `evolution_brief.yaml`

## 5. 进化动作 checklist

- [ ] 填 `performance.yaml` actual
- [ ] 跑 `evolution_apply.py --week publish/2026-W26`
- [ ] 读 `publish/2026-W26/evolution_brief.yaml` 更新 D05 形式
- [ ] D05 开工前 `gate_check` 验 evolution_applied
- [ ] 偏差 >20% 登记 `docs/design/FORM_FAIL_LOG.md`

## 6. 联签

- [ ] 平台表现分析师 · 填 actual + variance
- [ ] 编导 · 确认 evolution_brief 已应用到 D05
