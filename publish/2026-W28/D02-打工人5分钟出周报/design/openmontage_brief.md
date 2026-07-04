# OpenMontage 制作 brief · W28D02

> 工种：OpenMontage 制作导演
> 状态：本条**必跑判断**，无论 enabled/disabled/blocked
> 依赖：`insights/` 已 pass · `retention_beat_sheet.md` · `scripts/vA.md` · `design_language.md`（旧）
> 状态：`draft_self_generated` · 2026-07-04

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` §2.4b 生产 whitelist（含 OpenMontage）· §4.2 候选清单
- [x] **template refs**：`templates/design/openmontage_brief.md` · `templates/design/openmontage_review.md`
- [x] **memory refs**：`feedback_no-default-tech-stack`（防"OpenMontage 不适合本条"这类跳过判断的话）· `feedback_pre-node-checklist`
- [x] **姊妹条 refs**：`publish/2026-W28/D01-*/design/openmontage_brief.md` 完整实读（W28D01 decision=disabled，理由「曝光周定调 + 原生 2D 够用」）
- [x] **能力清单 refs**：
  - `integrations/openmontage/README.md` 已实读
  - `integrations/openmontage/openmontage.env.example` 已实读（含 Grok video / GPT Image 2 / MiniMax TTS 中转配置）
  - **`ls /Users/bubu/Documents/projects/OpenMontage` → 目录不存在**
  - **`ls ~/Documents/projects/OpenMontage` → 目录不存在**（当前用户 `wmzuo`，非文档中的 `bubu`）
  - `command -v openmontage` → 无 CLI

## 0. 启用判断

```yaml
enabled: false
content_id: W28D02
platform: douyin + xhs
target_duration_s: 50
recommended_pipeline: native_2d_workflow_p001_hybrid  # Pexels B-roll + 屏录 + SVG 覆盖
render_runtime: undecided
budget_usd: 0
budget_mode: cap
target_metric: completion_3s + completion_rate + 评论率
decision: blocked_infrastructure  # 与 W28D01 disabled_by_choice 区分
decision_review_trigger:            # 满足任一条件时重新评估
  - openmontage_sibling_checked_out: true
  - system_user_matches_documented_path: true
  - first_openmontage_success_case_in_project: true
```

### 判断结论

- **是否启用 OpenMontage：** 否
- **一句话理由：** **基础设施不具备**——OpenMontage 是 sibling repo 架构（`integrations/openmontage/README.md` 明确写 "not vendored into this repository, keep it as a sibling checkout"），本机文档指定路径 `/Users/bubu/Documents/projects/OpenMontage` 不存在，当前用户 `wmzuo` 与文档 `bubu` mismatch。**本条不是"选择性 disabled"，是"想启用也用不了"。**
- **服务的北极星指标：** completion_3s（下班场景钉子） · completion_rate（AI 屏录动作性变化） · 评论率（同事口吻 CTA）
- **为什么当前项目原生路线够用（本条独立评估，不抄 D01）：**
  1. D02 三块核心画面「真实办公室 B-roll + 手机特写 / AI 对话屏幕录制 / 静态前后对比」**都是原生 pipeline 能力覆盖**（fetch_broll.py 拉 Pexels + QuickTime 屏录 + SVG/CSS 静态对比）
  2. D02 主打**打工人共谋感**，"同事口吻"要求画面**克制、去教程感**，OpenMontage animated explainer 反而可能增加"教程感"
  3. D02 小红书 P5 完整 prompt 页要求**可截图带走**，视频合成不利于截图；原生轮播优于视频
- **什么时候再启用：**
  1. **基础设施先具备**：OpenMontage sibling repo 在本机 `~/Documents/projects/OpenMontage` 或用户指定路径 checkout 完成
  2. **首个成功案例**：项目内至少一条选题跑通完整 OpenMontage 流程（export_request → sibling repo → collect_output），有 preview.mp4 + review pass 记录
  3. **D02 首轮数据回填后**：若测出**中段完播差（<25%）但 3s 停划高（>60%）**，说明钩子有效但中段塌陷，此时可评估 OpenMontage screen demo pipeline 增强 M6 演示段

### 禁止理由自检

- [x] **不是因为"更酷 / 更电影感 / 更高级"而启用**——反而因为「基础设施不具备 + 与 skin.tone_direction 克制感不匹配」不启用
- [x] **没有启用，不会改写 chosen script**（scripts/vA.md 保留）
- [x] **当前内容适合原生 P001 混合路线**（Pexels + 屏录 + SVG 打点）
- [x] **判断依据 D02 自身，未抄 D01**（D01 disabled_by_choice · D02 blocked_infrastructure，语义不同）
- [x] **本 brief 判断 disable 后，form_competition 仍要把 OpenMontage 显式列为候选并说明 blocked 原因**（防止候选池预先缩水的教训沉淀）

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | `week.yaml` audience_pool=C端·打工人 | ready | 仅作参考，不进 OpenMontage |
| chosen script | `scripts/vA.md`（场景剧强化版） | ready | 本条不进 OpenMontage |
| retention_beat_sheet | `retention_beat_sheet.md` | ready | 不进 OpenMontage |
| form_strategy | `design/form_strategy.md`（旧版，回炉待判） | pending_reevaluate | 待 form_competition 回炉后同步 |
| design_language | `design/design_language.md`（旧版，回炉待判） | pending_reevaluate | 同上 |

## 2. 不可改内容（若未来启用时的红线）

即使未来 blocked_infrastructure 解除、启用 OpenMontage，以下内容 OpenMontage 制作时**不得改动**：

- **核心选题：** 打工人 5 分钟出周报（AI 帮打工人做敷衍但必须交的活）
- **价值锚：** 「不是教你写周报，是把我下班前 5 分钟的救命 prompt 给你」
- **事实边界：** 「5 分钟」是 B 级区间表达（"能出个能用的初稿"）· 「老板夸你写得细」仅限封面/title，不进片内 · 无「效率提升 80%」等商业宣称
- **禁用表达：** 教你摸鱼 / AI 帮你躺平 / 打工人狂喜 / 效率革命 / 逆袭
- **CTA：** 「评论区告诉我你什么岗位/上一次因周报加班到几点，我按行业发一版 prompt」
- **平台限制：** 抖音 45-75s 场景剧型 · 小红书 6-8 页轮播（P5 完整 prompt 页可截图）

## 3. 制作导演签字

- **OpenMontage 制作导演：** pass_blocked_infrastructure
- **编导采纳：** pass_use_native_pipeline_hybrid
- **下一步：** 走原生 pipeline 混合路线（Pexels + QuickTime 屏录 + SVG 打点 + ffmpeg 合成）
- **回评触发条件（已记录）：** 见 `decision_review_trigger` yaml 字段
