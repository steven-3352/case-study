# OpenMontage 制作 brief · W28D04 AI 帮想视频选题

> 工种：OpenMontage 制作导演
> 位置：`design/openmontage_brief.md`
> 状态：本条**必跑判断**（CLAUDE.md 铁律：每条必跑，未跑不得进 storyboard）
> 依赖：`insights/` 已 pass · `retention_beat_sheet.md` · `scripts/vA.md`（**抖音主推**）· `scripts/vB.md` v2（**A/B 备胎 · 双评 avg 90.5 pass**）
> 状态：`draft_self_generated` · 2026-07-05

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` §2.4b 生产 whitelist（含 OpenMontage）· §4.2 候选清单 · §3.1e 承诺=兑现 · §3.2 留存铁律
- [x] **template refs**：`templates/design/openmontage_brief.md` · `templates/design/openmontage_review.md`
- [x] **memory refs**：
  - `feedback_no-default-tech-stack`（防"OpenMontage 太重"这类跳过判断的话）
  - `feedback_pre-node-checklist`
  - `feedback_anti-ai-visual`（OpenMontage animated explainer 有教程感 AI 味风险）
  - `feedback_contrast-hook-3s`（D04 chaos-punch-reveal 屏录三拍是本条差异化资产）
- [x] **姊妹条 refs**：
  - `publish/2026-W28/D01-*/design/openmontage_brief.md`（decision=disabled_by_choice）
  - `publish/2026-W28/D02-*/design/openmontage_brief.md`（decision=blocked_infrastructure）
  - `publish/2026-W28/D03-*/design/openmontage_brief.md`（decision=blocked_infrastructure · 同基础设施状态）
- [x] **能力清单 refs**：
  - `integrations/openmontage/README.md` 已实读（sibling repo 架构 · 不 vendor 进本仓）
  - `integrations/openmontage/openmontage.env.example` 已实读（含 Grok video / GPT Image 2 / MiniMax TTS 中转配置）
  - **`ls /Users/bubu/Documents/projects/OpenMontage` → 目录不存在**（文档指定路径）
  - **`ls ~/Documents/projects/OpenMontage` → 目录不存在**（当前用户 `wmzuo`，非文档中的 `bubu`）
  - `command -v openmontage` → 无 CLI
  - 项目内 W28D01/D02/D03 均未跑通 OpenMontage 案例

## 0. 启用判断

```yaml
enabled: false
content_id: W28D04
platform: douyin + xhs + wechat_video
target_duration_s: 58
recommended_pipeline: native_p001_hybrid_screen_recording_first  # 屏录 chaos-punch-reveal + Pexels 白天办公 B-roll + SVG 覆盖 + 分屏静图 + drawtext 大字 + ffmpeg
render_runtime: undecided
budget_usd: 0
budget_mode: cap
target_metric: completion_3s + completion_rate + 收藏率（4 段 prompt 结构 + 5 判据表格 + 小红书 P4-P7 完整 prompt）
decision: blocked_infrastructure  # 与 D02/D03 一致口径 · 但独立评估 D04 内容适配性
decision_review_trigger:            # 满足任一条件时重新评估
  - openmontage_sibling_checked_out: true
  - system_user_matches_documented_path: true
  - first_openmontage_success_case_in_project: true
  - first_data_returned_signals_first_3s_hook_weak: true  # D04 若 3s 完播 <50%，评估 OpenMontage documentary 首镜是否可补
```

### 判断结论

- **是否启用 OpenMontage：** 否
- **一句话理由：** **基础设施不具备**——OpenMontage 是 sibling repo 架构（`integrations/openmontage/README.md` 明确 "not vendored into this repository, keep it as a sibling checkout"），本机文档指定路径 `/Users/bubu/Documents/projects/OpenMontage` 不存在，当前用户 `wmzuo` 与文档 `bubu` mismatch，项目内 W28D01/D02/D03 均未跑通。**本条不是"选择性 disabled"，是"想启用也用不了"。**（与 W28D02/D03 相同基础设施口径，但 D04 独立评估内容适配性。）
- **服务的北极星指标：**
  - `completion_3s`（0-3s 屏录 chaos-punch-reveal 三拍：打字「帮我想 10 个」→ AI 输出「如何做好 XX」被红叉打掉 → display 大字入）
  - `completion_rate`（9 段形式切换：屏录反差 → 实景群体锚 → 分屏爆款对比 → 3 段反例屏录 → 4 段 prompt 演示核心 → 5 判据表格 → 全屏价值锚 → CTA）
  - **收藏率**（25-40s 4 段 prompt 结构大字滑入 · 40-48s 5 判据表格打勾 · 小红书 P4-P7 完整 prompt 全屏）
- **为什么当前项目原生路线够用（本条独立评估 D04，不抄 D02/D03 结论）：**
  1. **D04 首镜是屏录 chaos-punch-reveal 三拍**（0-3s），核心画面是 AI 对话框光标闪 → 打字 14 字 → AI 输出被红叉打掉 → 大字入。**原生 QuickTime 屏录 + drawtext + accent_red 红叉 SVG 覆盖 100% 能覆盖**，OpenMontage documentary montage 电影感反而会稀释"我上周就打过一模一样的 prompt"的同频代入
  2. **D04 skin=中腰部创作者·同行说话**（不是学英语党共同体感 · 不是老板圈方法论感）· `feedback_anti-ai-visual` 与 `skin.tone_direction`「不 preach 不 sell 秘籍」双约束下，OpenMontage animated explainer 或 cinematic 极易被识破"AI 教程套路"（同行"AI 一键出爆款"话术已在 hook_benchmark 打脸）
  3. **D04 P0-3 4 段 prompt 结构 + P0-4 5 判据表格是收藏动机核心**，走的是屏录 + SVG 淡入 badge + 静态打勾表格 · **原生轮播 P4-P7 完整 prompt 可截图带走**（保守 save_rate ≥6%），OpenMontage 视频合成路线**不利于逐帧截图**，与 D03 收藏率 KPI 冲突口径一致
  4. **D04 中段 40w 赞 vs 800 赞分屏、5 判据表格**都是**静态版式**（截图 + drawtext + SVG），原生 P001 混合覆盖率 100%，OpenMontage 电影感对此无增量
- **什么时候再启用：**
  1. **基础设施先具备**：OpenMontage sibling repo 在本机 `~/Documents/projects/OpenMontage` 或用户指定路径 checkout 完成
  2. **首个成功案例**：项目内至少一条选题跑通完整 OpenMontage 流程（export_request → sibling repo → collect_output），有 preview.mp4 + review pass 记录
  3. **D04 首轮数据回填后**：若测出**3s 完播 <50%**（同行反差首镜未达预期），评估 OpenMontage documentary 电影感首镜是否可补——但需先满足 1-2 条
  4. **视频号 65-72s 加长版**：若视频号扩展加长版投后数据显示中段塌陷（>25%），OpenMontage cinematic 结尾情感落点或有帮助，同样需先满足 1-2 条

### 禁止理由自检

- [x] **不是因为"更酷 / 更电影感 / 更高级"而启用**——反而因为「基础设施不具备 + 与 skin.tone_direction「同行说话」不匹配 + 屏录反差首镜是本条差异化资产不能被 OpenMontage 稀释」不启用
- [x] **没有启用，不会改写 chosen script**（scripts/vA.md 主推 · scripts/vB.md v2 备胎双评 pass 保留）
- [x] **当前内容适合原生 P001 混合路线**（屏录 chaos-punch-reveal + Pexels 白天办公 B-roll + SVG 覆盖 + 分屏静图 + drawtext 大字）
- [x] **判断依据 D04 自身，未抄 D02/D03**：
  - D02 skin=打工人共谋 · D03 skin=学英语党共同体 · **D04 skin=中腰部创作者·同行说话**（三个受众对"AI 教程感"敏感度不同 · D04 最敏感）
  - D02 首镜=打工人下班 18:55 傍晚办公室 · D03 首镜=深夜 23:12 台灯 · **D04 首镜=白天 3800-4200K 办公桌 + 摄像头亮 + 屏录 chaos-punch-reveal**（三个首镜光温 / 场景 / 动作全不同）
  - D02/D03 无屏录反差首镜 · **D04 屏录 chaos-punch-reveal 是本条唯一同行没做的首镜手法**（同行"AI 一键出爆款"话术打脸靠此手法）
- [x] **本 brief 判断 disable 后，form_competition 仍要把 OpenMontage 显式列为候选并说明 blocked 原因**（防止候选池预先缩水的教训沉淀 · memory `feedback_no-default-tech-stack`）

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | `week.yaml` audience_pool=中腰部创作者·自媒体运营 | ready | 仅作参考，不进 OpenMontage |
| chosen script | `scripts/vA.md`（**抖音主推 · chaos-punch-reveal 型**）· `scripts/vB.md` v2（**A/B 备胎 · 数字精简+原话情感 · 双评 avg 90.5 pass**）· `scripts/v0.md`（baseline 场景共情型 · 视频号加长版材料源） | ready | 本条不进 OpenMontage |
| retention_beat_sheet | `retention_beat_sheet.md`（9 段 55-58s + 7 页轮播） | ready | 不进 OpenMontage |
| design_language | `design/design_language.md`（已产出 · 10 色板类 · 5 字体层级 · 12 组件规则）| ready | 不进 OpenMontage |
| cover_brief | `design/cover_brief.md`（已产出 · 抖音 video_frame 2.4s · 小红书独立共情锚 · 视频号同抖音）| ready | 不进 OpenMontage |
| form_strategy | `design/form_strategy.md`（本节点后写） | pending | 待本 brief 出结论后写 |

## 2. 不可改内容（若未来启用时的红线）

即使未来 blocked_infrastructure 解除、启用 OpenMontage，以下内容 OpenMontage 制作时**不得改动**：

- **核心选题：** AI 帮想视频选题（把 4 段 prompt 结构给中腰部创作者作可复现选题起草器）
- **价值锚：** 「不是教你用 AI，是把我上周 30 分钟搞定下周 5 条的那 4 段 prompt 给你。」
- **事实边界：**
  - 「9 成中腰部创作者早期都会遇到选题问题」（知乎专栏 · A 级绿区 · topic_brief 原话表 #1）
  - 「同行 40w 赞我也拍过、我 800 赞」（reporter_notes 家居博主小林 · A 级具体案例 · 单位显式硬约束"赞"字必须出现）
  - 「10 里 8 能用」**只在**同帧显示「5 判据 · 通过 4 条」口径下允许（domain_notes 筛选标准 · A 级可校）
  - 「30 分钟搞定下周 5 条」（core_message 价值锚 · 具体动作产出 · 不承诺爆款效果）
- **原话直引硬约束（编剧硬门禁 pass 门 · 已跨过 ≥4 条）：**
  - #2「为什么我抄爆款别人爆我不爆啊」（人人都是产品经理 · A · 直引带引号）
  - #3「每周发一篇变成半个月发一篇」（少数派 · A · 直引带引号）
  - #5「最后就一个字：累」（网易 · A · 直引带引号 · 大字定格）
  - #1「9 成中腰部创作者遇到选题问题」（知乎 · A · 转述）
- **禁用表达（红区 · SCRIPT_REJECT_LOG.md 已登记）：**
  - 爆款秘籍 / 流量密码 / 涨粉神器 / 变现 / 千万播放 / 必上热门
  - 「月涨粉 X 万 / 30 天变现 / 一键出爆款」等承诺
  - 竞品 logo（ChatGPT / DeepSeek / 豆包 UI 允许出现原生色，但**不打 logo** · 不打脸 · 不背书）
  - 点名真实同行账号（家居博主小林是化名 · 40w 赞截图必须马赛克遮挡真实头像/账号名）
- **CTA：** 「私信『你在做什么账号 · 想拍什么方向』——我给你 5 条选题」（skin.landing_intent 硬约束 · 走私信喂选题 · **不推付费群/星球/课程**）
- **平台限制：**
  - 抖音 55-58s vA 主推 chaos-punch-reveal 型 + vB v2 数字精简+原话情感型（A/B 备胎）
  - 小红书 7 页轮播（P1 共情锚封面 · P4-P7 完整 4 段 prompt 可截图）
  - 视频号 65-72s 加长版（v0 场景共情 + vB v2 数字锚 + 原话情绪段材料源）
- **屏录 UI 铁律：** 保留 iOS/macOS 状态栏 + AI 对话框原生 UI + 光标闪 + 打字节奏 30ms/字 · **禁裁掉状态栏 · 禁抠白底 · 禁加自造装饰性框 · 禁打 AI 工具 logo**

## 3. 制作导演签字

- **OpenMontage 制作导演：** pass_blocked_infrastructure
- **编导采纳：** pass_use_native_pipeline_hybrid_screen_recording_first
- **下一步：** 走原生 pipeline 混合路线（**屏录 chaos-punch-reveal 三拍**首镜 + Pexels 白天办公 3800-4200K B-roll + SVG 覆盖 accent_soft 淡黄 badge 分段标签 + drawtext display 大字 + drawbox 白闪快切 + 分屏静图 + ffmpeg 合成）
- **回评触发条件（已记录）：** 见 §0 `decision_review_trigger` yaml 字段

## 4. Audience-First 自查三问（OpenMontage brief 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ 本判断结论「原生 P001 混合 · 屏录 chaos-punch-reveal 首镜」保留了「我上周就打过一模一样的 prompt」的同频真实感，共同体感强于 OpenMontage 电影感合成 · skin.tone_direction「同行说话·不 preach·不 sell 秘籍」与原生屏录 UI 原生色天然匹配 |
| 画面**观赏性**够吗？ | ✅ 原生路线 9 段形式切换（M1-M3 屏录 chaos-punch-reveal + M4 白天办公 B-roll 群体锚 + M5 分屏爆款对比 + M6 3 段反例快切 + M7 屏录 4 段 prompt 演示 + M8 5 判据表格 + M9 全屏价值锚 + M10 CTA），每 3-8s 变化点足够 · 单段最长 M7 15s = 26% < 40% 上限 |
| 内容**真材实料**吗？ | ✅ 4 段 prompt 演示走真机屏录（原生优势）· 完整 4 段 prompt 走小红书轮播 P4-P7（可截图收藏）· 5 判据表格 accent_green 静态打勾（承诺兑现）· OpenMontage 视频合成不利于逐帧截图，原生路线更适合 D04 收藏率北极星 |
