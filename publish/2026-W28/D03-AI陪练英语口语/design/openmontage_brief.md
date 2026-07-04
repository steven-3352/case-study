# OpenMontage 制作 brief · W28D03 AI 陪练英语口语

> 工种：OpenMontage 制作导演
> 状态：本条**必跑判断**（CLAUDE.md 铁律：每条必跑，未跑不得进 storyboard）
> 依赖：`insights/` 已 pass · `retention_beat_sheet.md` · `scripts/v0.md`（严格版为默认参照）
> 状态：`draft_self_generated` · 2026-07-04

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` §2.4b 生产 whitelist（含 OpenMontage）· §4.2 候选清单 · §3.1e 承诺=兑现
- [x] **template refs**：`templates/design/openmontage_brief.md` · `templates/design/openmontage_review.md`
- [x] **memory refs**：`feedback_no-default-tech-stack`（防"OpenMontage 不适合本条"这类跳过判断的话）· `feedback_pre-node-checklist`
- [x] **姊妹条 refs**：`publish/2026-W28/D01-*/design/openmontage_brief.md`（decision=disabled_by_choice）· `publish/2026-W28/D02-*/design/openmontage_brief.md`（decision=blocked_infrastructure）
- [x] **能力清单 refs**：
  - `integrations/openmontage/README.md` 已实读
  - `integrations/openmontage/openmontage.env.example` 已实读（含 Grok video / GPT Image 2 / MiniMax TTS 中转配置）
  - **`ls /Users/bubu/Documents/projects/OpenMontage` → 目录不存在**
  - **`ls ~/Documents/projects/OpenMontage` → 目录不存在**（当前用户 `wmzuo`，非文档中的 `bubu`）
  - `command -v openmontage` → 无 CLI

## 0. 启用判断

```yaml
enabled: false
content_id: W28D03
platform: douyin + xhs + wechat_video
target_duration_s: 58
recommended_pipeline: native_2d_workflow_p001_hybrid  # Pexels 深夜/暖光 B-roll + 手机屏录 + SVG 覆盖 + 分屏对比
render_runtime: undecided
budget_usd: 0
budget_mode: cap
target_metric: completion_3s + completion_rate + 收藏率（3 段 role prompt）
decision: blocked_infrastructure  # 与 D02 一致口径
decision_review_trigger:            # 满足任一条件时重新评估
  - openmontage_sibling_checked_out: true
  - system_user_matches_documented_path: true
  - first_openmontage_success_case_in_project: true
```

### 判断结论

- **是否启用 OpenMontage：** 否
- **一句话理由：** **基础设施不具备**——OpenMontage 是 sibling repo 架构（`integrations/openmontage/README.md` 明确 "not vendored into this repository, keep it as a sibling checkout"），本机文档指定路径 `/Users/bubu/Documents/projects/OpenMontage` 不存在，当前用户 `wmzuo` 与文档 `bubu` mismatch。**本条不是"选择性 disabled"，是"想启用也用不了"。**（与 W28D02 相同口径，不抄结论而是同一基础设施状态。）
- **服务的北极星指标：** completion_3s（对墙念英语深夜钉子） · completion_rate（群体锚释放 → 打卡幻灭 → 顿悟锚 → role prompt 演示，5 层动作性变化） · 收藏率（3 段完整 role prompt 直接可截图带走）
- **为什么当前项目原生路线够用（本条独立评估，不抄 D02 结论）：**
  1. D03 三块核心画面「深夜台灯 + 手 + 英语课本 B-roll / 手机屏录豆包语音 + role prompt 大字 / 分屏静图（游泳教程 vs 跳进泳池）」**全在原生 pipeline 能力覆盖内**（fetch_broll.py 拉 Pexels + QuickTime 屏录真机 + SVG/CSS 静态对比 + drawtext/drawbox 大字）
  2. D03 主打**学英语党共同体感**（"我 = 你 = 92% 中国人"），"沉稳同事口吻"要求画面**克制、去教程感**，OpenMontage animated explainer 反而可能拉高"我教你"的感觉，与 core_message.md 价值锚「不是教你怎么问 AI，是把我 22:30 用的救命 role prompt 给你」相悖
  3. D03 小红书 P5-P7 完整 3 段 role prompt 页要求**可截图带走**（收藏动机 · 见 retention_beat_sheet.md `save_rate ≥6%`），视频合成不利于逐帧截图；原生轮播优于视频合成
- **什么时候再启用：**
  1. **基础设施先具备**：OpenMontage sibling repo 在本机 `~/Documents/projects/OpenMontage` 或用户指定路径 checkout 完成
  2. **首个成功案例**：项目内至少一条选题跑通完整 OpenMontage 流程（export_request → sibling repo → collect_output），有 preview.mp4 + review pass 记录
  3. **D03 首轮数据回填后**：若测出**中段完播差（<25%）但 3s 停划高（>55%）**，说明钩子有效但中段塌陷，此时可评估 OpenMontage screen demo pipeline 增强 M6（24-36s role prompt 演示段）
  4. **情感型脚本 vA 若被选中且首轮数据差**：vA 第一人称沉浸型对镜头感染力要求更高，OpenMontage cinematic 或有帮助——但需先满足 1-2 条

### 禁止理由自检

- [x] **不是因为"更酷 / 更电影感 / 更高级"而启用**——反而因为「基础设施不具备 + 与 skin.tone_direction「同事沉稳口吻」不匹配」不启用
- [x] **没有启用，不会改写 chosen script**（scripts/v0.md 严格版 · vA 场景剧 · vB 数据锚三稿保留）
- [x] **当前内容适合原生 P001 混合路线**（Pexels 深夜暖光 + 手机真机屏录豆包 + SVG 打点 + 分屏静图）
- [x] **判断依据 D03 自身，未抄 D02**（D02 skin=打工人共谋 · D03 skin=学英语党共同体；北极星权重不同——D03 收藏率更高，需可截图轮播路径）
- [x] **本 brief 判断 disable 后，form_competition 仍要把 OpenMontage 显式列为候选并说明 blocked 原因**（防止候选池预先缩水的教训沉淀）

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | `week.yaml` audience_pool=学英语党 · 深夜自学者 | ready | 仅作参考，不进 OpenMontage |
| chosen script | `scripts/v0.md`（严格执行版为默认）· `vA.md`（场景剧型备选）· `vB.md`（数据锚型备选） | ready | 本条不进 OpenMontage |
| retention_beat_sheet | `retention_beat_sheet.md`（10 段 58s + 8 页轮播） | ready | 不进 OpenMontage |
| form_strategy | `design/form_strategy.md`（本节点后写） | pending | 待本 brief 出结论后写 |
| design_language | `design/design_language.md`（本节点后写） | pending | 同上 |

## 2. 不可改内容（若未来启用时的红线）

即使未来 blocked_infrastructure 解除、启用 OpenMontage，以下内容 OpenMontage 制作时**不得改动**：

- **核心选题：** AI 陪练英语口语（把语音 AI 当"不打断的英文陪练"）
- **价值锚：** 「不是教你怎么问 AI，是把我 22:30 用的救命 role prompt 给你。」
- **事实边界：**
  - 「92% 中国人不敢开口」「78% 缺安全场合」（讯飞录官方 · A 级绿区）
  - 「便宜 100 倍」**只在**同帧显示「对比线下 300 元/小时」口径下允许（B 级黄区 · 见 fact_check.md）
  - 「先敢说 30 分钟，比敢背 300 单词管用」（P1-1 使用姿势，不承诺流利）
- **禁用表达（红区）：** 30 天流利 / 秒变母语 / 哑巴英语克星 / AI 替代真人外教 / 具体考试通过率承诺 / 竞品 logo（多邻国界面出现但不打 logo · 只用连击数字截图）
- **CTA：** 「评论「面试 / 雅思 / 日常 / 旅游」——我把对应 role prompt 给你」
- **平台限制：** 抖音 58s 场景剧+演示型 · 小红书 8 页轮播（P5-P7 完整 3 段 role prompt 可截图）· 视频号 58s 同抖音口径

## 3. 制作导演签字

- **OpenMontage 制作导演：** pass_blocked_infrastructure
- **编导采纳：** pass_use_native_pipeline_hybrid
- **下一步：** 走原生 pipeline 混合路线（Pexels 深夜暖光 B-roll + QuickTime 真机屏录豆包 + SVG 打点 + 分屏静图 + drawtext 大字 + ffmpeg 合成）
- **回评触发条件（已记录）：** 见 §0 `decision_review_trigger` yaml 字段

## 4. Audience-First 自查三问（OpenMontage brief 层）

| 三问 | 自查结论 |
|------|---------|
| 观众会不会**共鸣**？ | ✅ 本判断结论「原生 P001 混合」保留了真实办公室/深夜台灯 B-roll 真实痕迹，共同体感强于 OpenMontage 电影感合成 |
| 画面**观赏性**够吗？ | ✅ 原生路线 10 段形式切换（B-roll + 大字数据锚 + UI 快切 + 分屏静图 + 手机屏录 + 侧躺 B-roll + 全屏大字 + CTA 大字），每 3-6s 变化点足够 |
| 内容**真材实料**吗？ | ✅ role prompt 走真机屏录（原生优势）· 3 段完整 role prompt 走轮播 P5-P7（可截图收藏）· OpenMontage 视频合成不利于逐帧截图 |
