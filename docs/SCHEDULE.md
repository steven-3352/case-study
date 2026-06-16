# 工期 · 按天排期

> **Phase 0：28 天备齐（零发布）** → **Phase 1：8 周起号（手动发布）**
> 起始日请填入 `start_date`，Day 1 = 启动日。

```yaml
start_date: YYYY-MM-DD   # 辩论确认计划后填写
phase0_days: 28
phase1_weeks: 8
```

---

## Phase 0 · 备齐（D1–D28，零发布）

### W1 · IP 资产（D1–D7）

| 天 | 主题 | 交付物 |
|----|------|--------|
| D1 | 项目对齐 | 填 `persona.yaml` name/handle；复制 `metrics.template.csv` → `metrics.csv` |
| D2 | 干音录制 | `assets/avatar/dry_audio/` 10 分钟 wav |
| D3 | 数字人试播 A | 两个工具各 10s 试播，填 avatar/README 表格 |
| D4 | 数字人定稿 | 选定工具；生成固定形象；2 个场景背景 |
| D5 | 形象验收 | 本人+家人看 10s，不像恐怖谷则过 |
| D6 | 口头禅定稿 | 更新 persona.yaml openings/catchphrases |
| D7 | W1 缓冲 | 补漏；Git commit 所有 config |

### W2 · B-roll 素材（D8–D14）

| 天 | 主题 | 交付物 |
|----|------|--------|
| D8 | 录屏 1 | BR001 落地页 + BR002 表单 |
| D9 | 录屏 2 | BR003 欢迎邮件 + BR010 邮件序列 |
| D10 | 截图 1 | BR004–BR005 后台数据（打码） |
| D11 | 对比+内容 | BR006 对比图 + BR007 pin 三张 |
| D12 | 备忘录模板 | BR008–BR009；跑 `build_shots.py` 补帧 |
| D13 | 素材登记 | 更新 `catalog.yaml`，≥10 条 status=done |
| D14 | W2 缓冲 | 缺什么补什么 |

### W3 · 空跑生产（D15–D21）

| 天 | 主题 | 交付物 |
|----|------|--------|
| D15 | 脚本 | T001 小老板烦恼改造成稿 → `pipeline/dry-run-001/script.md` |
| D16 | 脚本审 | 按 persona + data-policy 改一版 |
| D17 | 数字人录制 | dry-run-001 口播 raw |
| D18 | 剪辑抖音版 | 45–60s，前 1s 字幕钩子 |
| D19 | 剪辑小红书视频 | ≤60s，可同素材微调 |
| D20 | 图文 6 张 | dry-run-001/carousel/ |
| D21 | 三平台文案 | dry-run-001/publish.md |

### W4 · 验收与 SOP（D22–D28）

| 天 | 主题 | 交付物 |
|----|------|--------|
| D22 | 自检 | 走 `pipeline/CHECKLIST.md` 全流程 |
| D23 | 路人测试 | 2 人看 30s，记录「像不像 AI 号」 |
| D24 | 修订 | 按反馈改封面/前 3s/文案 |
| D25 | SOP 文档 | 确认 `pipeline/README.md` 可照着做 |
| D26 | Phase 1 排期 | 填 Phase 1 发布日历（8 周） |
| D27 | 账号准备 | 三平台账号资料、简介、头像（数字人） |
| D28 | Phase 0 签收 | 勾选 BLUEPRINT 验收；**可发 Project-001 首条**（P001-A 或 P001-C） |

---

## Phase 1 · 起号（W5–W12，手动发布）

| 周 | 发布 | 你的动作 | 系统动作 |
|----|------|----------|----------|
| W5 | P001-A + P001-C | 审片、发布、48h 填表 | 故事图文 + 成长视频 |
| W6 | P001-B | 同上 | 干货拆解图文 |
| W7 | P001-C 小红书 | 同上 | 同视频微调 |
| W8 | P001-D | 同上 | 视频号复盘 |
| W9 | 总结周 | 写四形态对比表 | 定下月复制哪形态 |

**Phase 1 结束标准：** W9 完成 Project-001 总结（不设硬性 KPI，见 DECISIONS Q6）

---

## Phase 2 · 半自动（W13–W20）

- 写 `weekly_report.py`
- 选题推荐（人工批准）
- 剪映模板固定，缩短剪辑时间

## Phase 3 · 闭环（W21+）

- 脚本生成 API 化
- 数字人 API（若 SaaS 支持）
- 你只：weekly 选题勾选 + 月度方向

---

## 工时估算（每周）

| 阶段 | 你 | 合计 |
|------|-----|------|
| Phase 0 | 8–10h/周 | 约 32–40h |
| Phase 1 | 3–4h/周 | 约 24–32h |
| Phase 2 | 1–2h/周 | — |
| Phase 3 | <0.5h/周 | — |
