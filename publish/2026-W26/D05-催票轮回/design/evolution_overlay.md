# D05 · 数据进化 overlay · 来自 D04 v11

> **状态：evolution_required** · D05 旧 approved 为 pre-D04-lessons 流程  
> **数据源：** `publish/2026-W26/evolution_brief.yaml` · D04 `design/performance.yaml`  
> **原则：** 口播 vA 保留 · **形式按 D04 数据教训重做**

## 1. 为什么 D05 要重开形式门

| | D05 现状 | D04 教训 |
|---|----------|----------|
| 形式 scorecard | 无 v11 级互评 | 纸面 90 ≠ 能投 |
| 分析师 forecast | 无 | 须 pre_publish + post_publish |
| catalog | 可能 F2 标配 | **0–25%** |
| 首镜 | 未定 | **数字 punch**，非 Excel 冷开 |
| CTA | 旧流程 | 须完整进 mp4 |

## 2. D05 形式进化指令（E001–E005 应用）

### 钩子 · E001（hypothesis · 待 D04 actual 确认）

- **现 hook：**「30条催进度」
- **进化 hook 画面：** 数字 punch · 如 **「30 个节点 → 只催了 7 个」** 或 **「5 人公司 · 30 条微信 · 3 个漏催」**
- **禁止：** Excel 表格冷开（D04 v10 已证拖 3s）

### 专属镜 · ≥4 种 d05_*（比 D04 多 1）

| 建议镜 | 隐喻 | 口播锚点 |
|--------|------|----------|
| d05_hook_count | 30→7 漏催 | 行政每天 30 条 |
| d05_node_list | 开票/盖章/提单节点变红 | 到期提醒 |
| d05_wechat_chase | 连发催进度 ghost | 事后追 30 条 |
| d05_compare_deadline | 到期提醒 vs 事后追 | 价值锚 |
| d05_silent_vendor | 供应商静默 | 漏催后果 |
| d05_cta_confirm | 确认收到+讨论 CTA | 评论区 |

### 禁止清单

- catalog：`02_pain` · `06_compare` · `08_cta`
- D04 皮肤直复用：`d04_*` 全部
- 同 template 播 2 次

### 时长 · E004

- 目标 **50–55s**（保 CTA）· 待 D04 `avg_watch_s` actual 确认后微调

## 3. 开工 checklist（D05 形式 v1）

```
[ ] 读 evolution_brief.yaml · topic_overrides.W26D05
[ ] 新建 d05_* HTML ≥4
[ ] storyboard v1 · 0% catalog · 无重复
[ ] motion_wow ≥4 CREATIVE
[ ] gate_check(pre_render) PASS
[ ] render → pre_publish_forecast → gate_check(approve)
[ ] 填 D04 performance.yaml actual → evolution_apply.py
[ ] 据 actual 微调 D05 时长/钩子
```

## 4. 数据回填后自动更新

D04 发布后 48–72h：

```bash
# 1. 填 publish/2026-W26/D04-复购流失/design/performance.yaml · actual
# 2. 合并到周汇总并生成进化报告
python3 pipeline/evolution_apply.py --week publish/2026-W26
# 3. 读 evolution_brief.yaml 变更 · 更新本 overlay
```

## 5. 联签

- [ ] 平台表现分析师 · overlay 与 brief 一致
- [ ] 编导 · D05 形式重开（content 保留 vA）
