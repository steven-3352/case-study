# 平台数据自动拉取 · 抖音 / 小红书

> **结论：** 不能「零配置读你账号」——平台无个人开放 API，须 **一次扫码登录** 或 **JSON 导入**。  
> 登录后会话存本地，后续 `--sync` 可自动化，并串联 `evolution_apply.py`。

## 1. 为什么不能完全零 touch？

| 方式 | 可行性 | 说明 |
|------|--------|------|
| 官方开放 API | 企业/巨量资质 | 个人创作者中心 **无** 稳定个人 API |
| Agent Reach | 仅公开内容调研 | **不能**读你的后台数据 |
| Playwright + Cookie | **推荐** | 模拟创作者中心，一次登录 |
| 手动 JSON 导入 | **兜底** | 从后台复制或导出 |

## 2. 一次性 setup（约 2 分钟）

```bash
cd /Users/bubu/Documents/projects/case-study
.venv/bin/pip install playwright pyyaml
.venv/bin/playwright install chromium

# 抖音 · 弹出浏览器扫码登录
python3 pipeline/fetch_platform_metrics.py --login douyin

# 小红书（可选）
python3 pipeline/fetch_platform_metrics.py --login xhs

# 检查会话文件
python3 pipeline/fetch_platform_metrics.py --check-session douyin
```

会话文件（**不入库**）：

```
ops/platform_sessions/douyin_state.json
ops/platform_sessions/xhs_state.json
```

## 3. 发布后自动拉数（48–72h）

```bash
# 单条 · 按 content.yaml 标题/hook 在列表页匹配
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04

# 小红书轮播
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04 --platform xhs

# 整周 pending
python3 pipeline/fetch_platform_metrics.py --sync-week publish/2026-W26
```

**自动写入：**

1. `publish/.../D04/design/performance.yaml` · actual  
2. `publish/2026-W26/performance_data.yaml`  
3. `ops/metrics.csv`  
4. 触发 `evolution_apply.py` → 更新 `evolution_brief.yaml`

## 4. 兜底：手动 JSON 导入

从创作者中心抄数，或使用示例 JSON：

```bash
cp templates/design/platform_metrics_import.example.json /tmp/d04.json
# 编辑 actual 数字
python3 pipeline/fetch_platform_metrics.py --import-json /tmp/d04.json
```

示例见 `templates/design/platform_metrics_import.example.json`。

## 5. 填数口径（抖音创作者中心 → 字段）

| 后台显示 | performance.yaml |
|----------|------------------|
| 3s完播率 | `completion_3s` (0.62) |
| 完播率 | `completion_rate` (0.21) |
| 播放量 | `views` |
| 平均播放时长 | `avg_watch_s` |
| 点赞 / 评论 | `likes` / `comments` |

小红书：`views` · `likes` · `collects` · `comments`

## 6. 与进化闭环

```
fetch_platform_metrics.py --sync
        ↓
performance.yaml + metrics.csv
        ↓
evolution_apply.py（自动触发）
        ↓
evolution_brief.yaml → D05 evolution_overlay
```

## 7. 故障

| 现象 | 处理 |
|------|------|
| 会话过期 | 重新 `--login douyin` |
| 匹配不到标题 | 改 `content.yaml` title 与后台一致，或 `--import-json` |
| 页面改版解析失败 | 提 issue / 暂用手动 JSON；我们会更新 `config.yaml` 关键词 |
| 不想用浏览器 | 长期用手动 JSON；或申请抖音开放平台企业 API |

## 8. 安全

- Cookie **仅本机** · 已加入 `.gitignore`
- 勿提交 `ops/platform_sessions/`
- 团队共用机器时用独立 session 文件

## 9. 命令速查

```bash
python3 pipeline/fetch_platform_metrics.py --login douyin
python3 pipeline/fetch_platform_metrics.py --sync --id W26D04
python3 pipeline/fetch_platform_metrics.py --import-json path.json
python3 pipeline/evolution_apply.py --id W26D04
python3 ops/analyze_metrics.py --topic T012
```
