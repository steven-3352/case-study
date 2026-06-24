# 形式层 Fail 登记

> 与 `SCRIPT_REJECT_LOG.md` 同级。**形式 pass 但效果 fail 必须登记**，供 Rubric / gate 进化。

## 登记格式

```markdown
## {project_id} · {content_version} · {日期}

- **纸面分：** …
- **诚实效果分：** …
- **fail 原因：** …
- **改法：** …
- **归档：** `room/form_audit_*.yaml` · `design/pre_publish_forecast.md`
- **进化：** 更新了哪些铁律/gate（链接）
```

---

## W26D04 · v10 · 2026-06-24

- **纸面分：** 动效/形式 avg ~92
- **诚实效果分：** ~81（`room/form_audit_v10.yaml`）
- **fail 原因：**
  - 专属模板仅 2 种；excel/wechat 各×2
  - catalog 38%（pain+compare+cta 与 D03 同族）
  - VO 50.5s / 成片 48s · CTA 裁尾
  - 无平台表现分析师 · 无发布前 go/no-go
- **改法：** v11 全专属 7 镜 · 0% catalog · 55.5s · 分析师 pass
- **进化：**
  - `content_form_split_gates.md`
  - `gate_check` visual diversity + forecast
  - CREATIVE ≥1 → **≥3** · catalog ≤35%
  - `system_evolution.md`

---

## W26D06 · form v1 · 2026-06-24

- **纸面分：** scorecard avg ~92（复制 D04）
- **诚实效果分：** ~72
- **fail 原因：** P004 暗色族换皮 · style.css · 与 D04/D05 同质
- **改法：** form v2 纸账本 · TTS 保留 · 6 镜无 style.css
- **归档：** `room/form_audit_v1.yaml`
- **进化：** `gate_check.check_no_dark_p004_clone()`

---

## W26D07 · form v1 · 2026-06-24

- **纸面分：** ~92
- **诚实效果分：** ~74
- **fail 原因：** 暗色表格/对比族 · 非泳道蓝图
- **改法：** form v2 蓝图三色泳道 · TTS 保留
- **归档：** `room/form_audit_v1.yaml`


- 假互评 92.5 → 见 `SCRIPT_REJECT_LOG.md`
- 进化：`scorecard_enforcement.md` · 独立 Agent readonly
