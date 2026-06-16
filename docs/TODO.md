# 每日 TODO 清单

> 用法：每天打开对应 Day，完成后把 `[ ]` 改成 `[x]`。
> 启动前在 SCHEDULE.md 填 `start_date`。

---

## W1 · IP 资产

### D1 · 项目对齐
- [ ] 读 `docs/BLUEPRINT.md` 和 `docs/TECH_STACK.md`
- [ ] 填 `persona/persona.yaml` 的 name、handle
- [ ] 复制 `ops/metrics.template.csv` → `ops/metrics.csv`
- [ ] 确认 `queue/topics.yaml` T001 为 approved

### D2 · 干音（归档）
- [x] 原始录音 + `dry_v1.wav`（已完成，暂不使用）
- [x] ~~声音克隆~~ → 已放弃（Q7）
- [x] ~~数字人~~ → **暂停**（Q8，视频不出真人）

### D3 · 数字人试播 — ⏸ 暂停
- [ ] ~~选工具、试播~~ → 跳过，待恢复再做

### D4 · 数字人定稿 — ⏸ 暂停
- [ ] 选定工具，上传参考照+干音
- [ ] 生成固定形象
- [ ] 导出 2 个场景背景到 `assets/avatar/scenes/`

### D5 · 形象验收
- [ ] 10s 试播给 1–2 人看
- [ ] 不像恐怖谷 / 不像企业宣传 → 通过
- [ ] 不通过则回 D4 调参数

### D6 · 口头禅定稿
- [ ] 从试播中删「像 AI」的句子
- [ ] 更新 persona.yaml openings/catchphrases
- [ ] 定账号简介文案（三平台统一口吻）

### D7 · W1 缓冲
- [ ] 检查 W1 所有交付物
- [ ] Git 提交 config 变更

---

## W2 · B-roll 素材

### D8 · 录屏 1
- [ ] BR001 落地页浏览 ~10s
- [ ] BR002 表单提交 ~8s
- [ ] 登记 catalog.yaml

### D9 · 录屏 2
- [ ] BR003 收到欢迎邮件 ~12s
- [ ] BR010 邮件序列 ~10s
- [ ] 登记 catalog.yaml

### D10 · 截图 1
- [ ] BR004 曝光数据截图（打码）
- [ ] BR005 留资数据截图（打码）
- [ ] 登记 catalog.yaml

### D11 · 对比+内容
- [ ] BR006 AI图 vs 精排对比
- [ ] BR007 真实 pin 3 张
- [ ] 登记 catalog.yaml

### D12 · 备忘录模板
- [ ] BR008 背景问题备忘录图
- [ ] BR009 复盘备忘录图
- [ ] 运行 `python3 build_shots.py` 补真实页面帧

### D13 · 素材登记
- [ ] catalog.yaml ≥10 条 status=done
- [ ] 文件命名符合规范

### D14 · W2 缓冲
- [ ] 缺素材补拍
- [ ] 每条素材能对应脚本里的 [B-roll 标注]

---

## W3 · 空跑生产

### D15 · 脚本
- [ ] 复制 `templates/script_小老板改造.md` → `pipeline/dry-run-001/script.md`
- [ ] 按 T001 Project-001「第5天我傻眼了」写完全稿（60s 轴，见 dry-run-001/script.md）

### D16 · 脚本审
- [ ] 对照 persona 禁用词
- [ ] 对照 data-policy 数据表述
- [ ] 标注每段 B-roll 素材 ID

### D17 · ~~数字人录制~~ — ⏸ 跳过
- [ ] ~~数字人生成口播~~ → 不做
- [ ] 时长 55–65s（以口播 + B-roll 为准）

### D18 · 抖音版
- [ ] 剪映：**全屏 B-roll + speech.mp3 + 字幕**，无人物出镜
- [ ] 前 1s 字幕钩子
- [ ] 导出 `dry-run-001/douyin.mp4` 45–60s

### D19 · 小红书视频
- [ ] 同素材微调 ≤60s
- [ ] 导出 `dry-run-001/xhs_video.mp4`

### D20 · 图文 6 张
- [ ] 按 `templates/script_项目图文.md` 顺序出 6–8 张
- [ ] 存 `dry-run-001/carousel/`

### D21 · 三平台文案
- [ ] 按 `templates/publish_三平台.md` 写 `dry-run-001/publish.md`

---

## W4 · 验收与 SOP

### D22 · 自检
- [ ] 过 `pipeline/CHECKLIST.md` 每一项

### D23 · 路人测试
- [ ] 2 人只看前 30s
- [ ] 记录反馈到 `dry-run-001/feedback.md`：是否觉得这是一个真实小老板问题

### D24 · 修订
- [ ] 改封面 / 前 3s / 标题（至少 1 项）

### D25 · SOP 确认
- [ ] 按 pipeline/README 再跑一遍流程（计时）

### D26 · Phase 1 排期
- [ ] 写 `docs/PHASE1_CALENDAR.md`（W5–W12 发什么）

### D27 · 账号准备
- [ ] 三平台头像、简介、背景图
- [ ] 简介不出现「服务商/科技」

### D28 · Phase 0 签收
- [ ] 勾选 BLUEPRINT 空跑验收 6 条
- [ ] 确认 pipeline 可复用（计时一遍 SOP）
- [ ] 可选：发 Project-001 首条（P001-A 或 P001-C）
- [ ] 进入 Phase 1（见 PHASE1_CALENDAR）

---

## Phase 1 · 每周重复块（W5 起）

### 每条内容发布前
- [ ] 从 queue 选 approved 选题
- [ ] 小老板场景 → 脚本 → 数字人 → 剪辑 → 文案
- [ ] CHECKLIST 过一遍
- [ ] 手动发布
- [ ] 48h / 7d 填 metrics.csv
- [ ] 周末按 rules.yaml 打 verdict

### W9 专项复盘
- [ ] 统计各形态 win/lose
- [ ] 完成 Project-001 四形态对比总结（PHASE1_CALENDAR W9 模板）
- [ ] 更新 queue direction.month_focus
- [ ] 记录是否有私信（assets/leads/）
