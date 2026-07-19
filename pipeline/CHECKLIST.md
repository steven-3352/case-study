# 发布前验收清单

> **北极星：** 验收的是观众会不会看完、会不会互动 — 不是文件齐不齐。宗旨与选型：`docs/SYSTEM.md` §1.0 · §4.2  
> 每条内容发布前必过。Phase 0 空跑也要过。

> 每条内容发布前必过。Phase 0 空跑也要过。

## 洞察与编排（Layer 2 门禁）

- [ ] 可实验的核心 claim 已先完成 Stage 0 evidence spike，保留输入/输出/模型/参数/时间/哈希与 claim boundary
- [ ] 派 reviewer 前已建立 `角色 × content_version × form_version × Phase` 覆盖矩阵，无重复碰运气或漏岗
- [ ] `GAP_REPORT.md` 完成且无 blocking；若为 `draft_self_generated` / `blocked_before_*`，禁止进入下一阶段
- [ ] `insights/topic_brief.md` 完成：受众、钉子场景、≥5 条原话
- [ ] `insights/core_message.md` 完成：P0 ≥ 3 条 + 价值锚 + 钩子
- [ ] `insights/domain_notes.md` 完成（演示/知识/带货型）或注明跳过原因
- [ ] `insights/fact_check.md` 完成：无红区表述进入脚本
- [ ] `retention_beat_sheet.md` 完成（视频/强互动图文）
- [ ] `design/form_competition.md` 完成：至少 3 个表现方案 + 推荐方案 + 不选其他方案原因 + 最近 5 条撞形检查
- [ ] `design/form_strategy.md` 完成：逐镜比较 ≥3 类表达方式，声明数据杠杆与推荐理由
- [ ] `design/asset_strategy.md` 完成：素材来源标清，generated_fact / synthetic_visual 不冒充真实来源
- [ ] `design/visual_originality_gate.md` 完成：证明本条首屏/中段/CTA 不是旧模板换字
- [ ] 若使用 Web 3D / Three / GSAP / 复杂 HTML / 风险雷达：`design/motion_tech_plan.md` 完成
- [ ] 视频：形式 ≥ 3 种（`assets/formats/catalog.yaml`）

## IP 与人味

- [ ] 像「真实项目改造者」，不像 AI 教程号或经验分享号
- [ ] 用了 persona.yaml 的口吻（具体、克制、不喊口号）
- [ ] 标题无 banned_words.title 中的词
- [ ] 前三秒有具体小老板问题（非空泛「分享一个方法」）

## 视频

- [ ] **禁止幻灯片冒充成片**：`prototype/qa_shots/`、低保真截图、静态 QA 帧不得直接拼接为 `douyin/video.mp4`
- [ ] **动态来源**：成片画面来自动态 HTML/GSAP/Canvas/Three、OpenMontage、真实录屏/B-roll/视频生成素材或正式 render pipeline
- [ ] **成片 ffprobe 体检**：`python3 pipeline/gate_check_media.py <成片.mp4>` PASS（无 ≥1s 黑帧 / 无 ≥3s 静音死区 / 前 6s mean_volume ≥ -25dB / 无爆音）——①确定性闸，只抓技术坏，不判创意（幻灯片/机器音等创意弱靠 ②③）
- [ ] **全屏**为项目演示（录屏/数据/系统页面/真实截图）— **演示型/知识型默认**
- [ ] **出镜**符合形态（`docs/DECISIONS.md` Q8）：
  - 演示型 / 知识型（默认）：❌ 真人、❌ 数字人（含小窗、画中画、封面大头）
  - 知识型例外：画中角上半身讲解 — 须在分镜标明机位
  - 带货型 / 出镜型：✅ 真人出镜按分镜；**数字人仍暂停**
- [ ] **封面**：`design/cover_review.md` 为 **pass**（视觉设计对 render 产出 PNG 签字）
- [ ] **封面反例**：禁止纯黑金渐变回落场景直接外发（`templates/design/cover_standards.md`）
- [ ] **配音**：`audio_plan.yaml` 已填；口播 MP3 已生成并与脚本对齐
- [ ] **TTS 小样**：provider/voice/emotion 已用 5–10s 单句 dry-run；生产配置 `strict_provider: true`，无静默回退
- [ ] **配音质量**：不得用 macOS `say` / 系统默认 TTS 冒充生产级配音；临时音频只能放 `_build/`，不得发布
- [ ] **BGM 条件件**：密 VO 演示/知识型（VO ≥85% 且无 3s+ 死区）默认可无 BGM；其他形态默认有 BGM。命名遵循 `*_with_bgm.mp4` / `*_no_bgm.mp4`
- [ ] **字幕**：SRT + 烧录/叠字；前 3s 钩子大字可见
- [ ] **真实时长驱动**：runtime storyboard 来自最终 VO timing；各镜已做 1.0×/1.5× 压力测试
- [ ] **并行隔离**：frame/audio/cache/concat 路径含 `content_id`，逐场景路径含 `scene_id`
- [ ] **机器 QC 先于 Phase B**：黑帧、静音、规格、字幕/音轨通过；`freezedetect` 最长连续冻结 ≤4.00s
- [ ] 人工听 30s：VO 清晰；有 BGM 时不盖人声
- [ ] 抖音版 45–60s / 小红书 ≤60s

## 图文（如有）

- [ ] 6–8 张，非 11 张黑金架构体
- [ ] 封面有项目画面或真实截图，**不是人物照**
- [ ] 真实截图 ≥ 3 张
- [ ] 架构流程图不是主视觉
- [ ] 图内大字可读（图文可豁免 BGM；有配音版须满足音画三件套）

## 视觉与可读性（图文静帧 + 视频关键帧）

- [ ] **表现形式不可模板化**：脚本结构可复用，但首屏、中段机制、CTA 形态必须本条专属
- [ ] **先竞争后分镜**：不得复制上一条 storyboard 后改字；必须从本条视觉命题生成新分镜
- [ ] `storyboard.yaml` 中任何 `template:` 复用都写明 `reuse_reason / visual_difference / risk`
- [ ] **证据优先**（Q9）：真实截屏/录屏为主；体裁混搭 ≥3；chaos 须真实 B-roll
- [ ] **留存铁律**：前屏直给；图像清晰无歧义、画面美观；文字不被遮挡
- [ ] 一屏一个主信息（输入→输出、对比、单句钩子）
- [ ] 角色/工种用可识别卡通头像或实物，非抽象圆点徽章
- [ ] 标题 / 拟声 SFX / CTA 无叠层遮挡（出图后逐张目视）
- [ ] 漫画轮播：`python3 pipeline/p007_xhs_engine_comic/capture_carousel.py --all` 后检查 PNG

## 文案

- [ ] 第一人称，有具体场景和真实结果
- [ ] 数据符合 ops/data-policy.yaml
- [ ] CTA 指向具体重复流程，无「私信/扣1/导流」
- [ ] 标签 3–5 个，来自 persona.tags.preferred

## 合规

- [ ] 品牌/客户/邮箱已打码
- [ ] 无编造里程碑数据
- [ ] 生成事实 source_type 标为 `generated_fact`，不冒充真实客户案例
- [ ] 仿真视觉 source_type 标为 `synthetic_visual`，必要时画面标“示意”

## 运营

- [ ] content_id 已分配
- [ ] publish.md / publish_三平台.md 齐全
- [ ] metrics.csv 已预填一行（publish_date 待填）
- [ ] 周包：`gate_check.py` pass；`pre_publish_forecast` 形式门 pass（若适用）
- [ ] 周包：scorecard Phase A/B 各工种 ≥90（`room/scorecards/`），且不是 `draft_self_generated` / 单 Agent 草稿
- [ ] Phase B scorecard 与 forecast 记录当前 `douyin/video.mp4` SHA-256；哈希变化后旧结论已作废并重审

## 路人测试（Phase 0 必须，Phase 1 建议）

- [ ] 至少 1 人看前 30s
- [ ] 反馈「这是一个真实小老板问题」或已按反馈修改
