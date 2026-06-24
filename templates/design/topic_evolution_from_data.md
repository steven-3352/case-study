# 选题进化 · 数据驱动规范

> **L3 闭环：** 投后 actual → `evolution_apply.py` → `evolution_brief.yaml` → 下一条选题/形式  
> 与 `system_evolution.md` · `content_form_split_gates.md` 同级

## 1. 数据流

```
发布前                          发布后 48–72h
────────                        ────────────────
pre_publish_forecast.md    →    performance.yaml (actual)
performance_data.yaml      →    post_publish_retro.md
                                evolution_apply.py
                                        ↓
                                evolution_brief.yaml
                                        ↓
                                下一条 evolution_overlay.md
                                        ↓
                                gate_check · storyboard · motion_wow
```

## 2. 填数口径 · 手动 48h 优先

**标准流程（发布后约 48h）：**

```bash
# 1. 查看谁在等数据
python3 pipeline/import_metrics_48h.py --status

# 2. 从创作者中心下载指标，填 JSON（见 platform_metrics_import.example.json）
python3 pipeline/import_metrics_48h.py --file path/W26D04_48h.json
```

详规：`templates/design/metrics_48h_workflow.md`

**无数据 = 进化暂停。** 不要手改 performance.yaml 指望自动进化。

| 字段 | 取数位置 | 写入 performance.yaml |
|------|----------|-------------------------|
| **3s 完播** | 数据分析 → 完播率 → 3s | `completion_3s` — **首要复盘项** |
| **完播率** | 完播率 | `completion_rate` — **北极星** |
| 互动率 | (评+赞+转)/播放 | `interaction_rate` |
| 均播 | 平均观看时长 | `avg_watch_s` |
| 播放/赞/评 | 概览 | `views` `likes` `comments` |

小红书：`collects/views` → `collect_rate`

## 3. hypothesis → confirmed 规则

| 条件 | 动作 |
|------|------|
| actual 在 forecast 区间内 | hypothesis **confirmed** · 阈值保持或微抬 |
| actual > forecast 上限 | **强化**信号（如 exclusive_min +1） |
| actual < forecast 下限 | **修正**信号 · 登记 FORM_FAIL_LOG · 下条改形式 |
| 连续 2 条同信号 fail | `queue_evolution.lower_priority` 触发 |

## 4. 进化简报字段

`publish/{week}/evolution_brief.yaml`：

| 块 | 用途 |
|----|------|
| `thresholds` | gate 下一档常量（evolution_apply 可写回 gate_check 建议） |
| `learnings` | confirmed · 不依赖 actual 的结构教训 |
| `hypotheses` | 待 actual 验证 · 含 if_confirmed / if_rejected |
| `topic_overrides` | **下一条具体指令**（hook、forbid、required_metaphors） |
| `queue_evolution` | 选题队列优先级升降 |

## 5. 下一条开工门禁

D05+ **pre_render 前**：

1. `evolution_brief.yaml` 存在且 `source_days` 含最近已发布条
2. 该条 `design/evolution_overlay.md` 已读 · checklist 勾完
3. `gate_check` 可选 `--require-evolution`（见 pipeline）

## 6. 命令

```bash
# 单条：填 D04 performance.yaml 后
python3 pipeline/evolution_apply.py --id W26D04

# 整周：合并 + 更新 brief + 打印报告
python3 pipeline/evolution_apply.py --week publish/2026-W26

# 下一条开工前：验 evolution 已应用
python3 pipeline/evolution_apply.py --id W26D05 --check
```

## 7. 相关文件

- 模板：`templates/design/performance_data.yaml` · `post_publish_retro.md`
- 周汇总：`publish/2026-W26/performance_data.yaml`
- 简报：`publish/2026-W26/evolution_brief.yaml`
- 工具：`pipeline/evolution_apply.py`
