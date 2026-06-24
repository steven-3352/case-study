# 48h 数据 · 手动导入 · 进化门禁

> **约定：** 衡量标准一律用 **发布后 48 小时** 数据。  
> 你定期从创作者中心下载 → 填 JSON 导入 → 系统自动进化。  
> **没有新数据 = 进化暂停**，D05+ 形式层不动 hypothesis。

## 1. 你的工作流

```
发布 → 等 48h → 创作者中心下载指标 → 填 JSON
    → python3 pipeline/import_metrics_48h.py --file xxx.json
    → evolution_brief.yaml 更新 · D05 overlay 可执行
```

## 2. 查看状态（进化是否暂停）

```bash
python3 pipeline/import_metrics_48h.py --status
# 或
python3 pipeline/evolution_apply.py --status
```

输出示例：
- `○ 未发布` — 如 D04，跳过
- `⏸ 等待 48h 数据` — 已发布但你还没导入
- `✓ 已有 48h 数据` — 可驱动进化

## 3. JSON 模板

复制 `templates/design/platform_metrics_import.example.json`，改数字即可：

| 字段 | 创作者中心位置 | 说明 |
|------|----------------|------|
| `completion_3s` | 数据分析 → 3s 完播 | 0.62 = 62% |
| `completion_rate` | 完播率 | |
| `avg_watch_s` | 平均观看时长（秒） | |
| `views` / `likes` / `comments` | 概览 | |
| `data_window` | 固定 `"48h"` | 必填 |

```bash
python3 pipeline/import_metrics_48h.py --file /path/W26D04_48h.json
```

导入后自动：写 `design/performance.yaml` → `performance_data.yaml` → `ops/metrics.csv` → `evolution_apply.py`。

## 4. 进化暂停规则

| 情况 | 系统行为 |
|------|----------|
| 无 48h JSON | `evolution_status: paused` · D05 hypothesis 不 confirm/reject |
| 导入 48h JSON | 跑 `evolution_apply` · 更新 `evolution_brief.yaml` |
| D04 未发布 | 不拉数、不进化、不 fail |

## 5. 与自动拉数的关系

Playwright 定时任务 **默认关闭**（`config.yaml scheduler.enabled: false`）。  
若以后想恢复自动拉数，仍不会自动进化——须走 48h 导入或 `--import-json`。

## 6. 命令速查

```bash
# 状态
python3 pipeline/import_metrics_48h.py --status

# 导入 + 进化
python3 pipeline/import_metrics_48h.py --file data/W26D04_48h.json

# 只写数据、不进化
python3 pipeline/import_metrics_48h.py --file data/W26D04_48h.json --no-evolve

# D05 开工前检查 overlay（不要求 D04 数据）
python3 pipeline/evolution_apply.py --id W26D05 --check
```
