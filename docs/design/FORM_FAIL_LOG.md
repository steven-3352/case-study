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

---

## W26D02 · form v4 · 2026-06-25

- **纸面分：** Phase A 9 工种 avg ~92（Python 批量生成 · notes 雷同 · 无 `reviewer_agent_id`）
- **诚实效果分：** spirit fail（假讨论室；与 artifact 脱节；Ken Burns/完播等套话出现在记者/网络调研员 notes）
- **fail 原因：**
  - 同 session 批量填 9×2 scorecard，两位 reviewer notes 仅两模板轮换
  - `gate_check(approve)` 当时无 `reviewer_agent_id` 硬校验，纸面 PASS
  - hook_benchmark 初版缺 https URL；cover 曾早于 video mtime
- **改法：**
  - 作废 Round 8–9 批量 scorecard；Round 10 Phase B + Round 11 Phase A 独立 Task 重写
  - `gate_check.py` 加固 agent_id / 批量检测 / cover mtime / hook URL
  - cover @1.0s 重导；hook_benchmark 补 3 URL
- **归档：** `room/discussion.md` Round 9 · `room/scorecards/*.yaml` optimization_round 10–11
- **进化：**
  - `gate_check.check_reviewer_agent_isolation()`
  - `reviewer_agent_id` 必填（post_render/approve）
  - `templates/design/scorecard_enforcement.md` §reviewer_agent_id
  - **`content_form_split_gates.md` §9** · `check_form_redo_content_gate()` — form 升版须声明脚本策略

---

## W26D08 · form v1 · 2026-06-25

- **纸面分：** 文档层自称 mixed_broll_evidence / Pexels + 私域看板 + Agent 分工卡
- **诚实效果分：** fail
- **fail 原因：**
  - `format_spec` 和 `storyboard` 承诺 Pexels / custom / 专属私域看板，但实际执行走通用 `pipeline/render.py`
  - 首镜未下载/剪入 Pexels B-roll，只把 Pexels 写成搜索建议
  - 抖音成片回落为旧 evidence 窗口卡片；小红书回落为 newspaper 通用轮播
  - 曾误标 `ready_to_publish`，违反“外发以像素为准”
- **改法：**
  - 删除 D08 已生成视频、封面、轮播和 `.staging/W26D08`
  - 状态退回 `approved_content_blocked_form`
  - `content.yaml` 移除会触发 newspaper 轮播的配置
  - D08 下一版必须真实引用本地 B-roll 或 `dNN_` / `pexels_` / `custom_` 专属模板
- **归档：** `publish/2026-W26/D08-电商私域Agent/room/verdict.yaml` · `design/pre_publish_forecast.md`
- **进化：**
  - `docs/SYSTEM.md` §3.1c
  - `templates/design/content_form_split_gates.md` §11
  - `pipeline/gate_check.py` · `check_custom_form_fulfillment()`
