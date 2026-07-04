# 表现形式竞争 · form_competition · W28D02（回炉版）

> 工种：形式策略官 + 平台原生策划 + 纪录片导演 + 动效分镜师
> 位置：`design/form_competition.md`
> 状态：`draft_self_generated · 回炉` · 2026-07-04
> 原产出（2026-07-04 上午）因**候选池预先缩水**（3 方案都在 P001 家族，未 include OpenMontage）作废，本文件为回炉版。
> 教训入 `docs/design/FORM_FAIL_LOG.md`（待补）

## 入口必读打勾（严格执行 · 5 类全过）

- [x] **SYSTEM refs**：`docs/SYSTEM.md` **§4.2 最新候选清单**（2026-07-04 版含 OpenMontage/Grok video/GPT-image-2/Remotion/HyperFrames）· §2.4b · §3.1e · §4.2 五维打分
- [x] **template refs**：`templates/design/form_competition.md`（新 §3 候选池完整性自查 + 跨家族强制）· `templates/design/openmontage_brief.md` · `templates/design/design_language.md`
- [x] **memory refs**：`feedback_no-default-tech-stack`（触发词打断） · `feedback_pre-node-checklist` · `feedback_anti-ai-visual`
- [x] **姊妹条 refs**：`publish/2026-W28/D01-*/design/openmontage_brief.md` 实读 · 本条已产出的 `openmontage_brief.md`（decision: blocked_infrastructure）实读
- [x] **能力清单 refs**：`ls integrations/` = openmontage/ · `ls pipeline/` 全清单已实查 · `ls integrations/openmontage/` 已实查（sibling repo 需外部 checkout）

**触发词自查（本次开工前主动检查）：**
- [x] 未出现"就走 P004 吧" / "就走 P001 吧" 念头
- [x] 未出现"OpenMontage 太重了不适合"这类未跑 brief 的排除话
- [x] 3 方案跨家族强制满足

## 3. 候选池完整性自查

### 3.1 候选池来源确认

```yaml
system_ref_version_read: 2026-07-04                # 读的 SYSTEM §4.2 最后同步日期
candidates_considered:
  native_pipeline:                                  # 从 pipeline/ 考虑的
    - P001 (render_p001.py + gen_evidence.py 高保真仿真)
    - P002 (报纸风轮播 · 与 skin.tone 不匹配，早排除)
    - P004 (HTML+GSAP · 反 AI 味风险)
    - P005/P006/P007 (带货/漫画 · 与形态不匹配)
    - fetch_broll.py Pexels 真实素材
    - QuickTime/OBS 真实屏幕录制
  integrations:                                     # 从 integrations/ 考虑的
    - OpenMontage (documentary montage / screen demo / animated explainer / cinematic)
    - Grok video (integrations/openmontage/openmontage.env.example)
    - GPT-image-2 (中转已配)
    - MiniMax TTS speech-2.8-turbo (已在 audio_plan 使用)
  raw_materials:                                    # 真实素材/真人出镜
    - 真实办公室拍摄 (用户明确无素材)
    - 真人出镜 (Q8 演示型默认不出镜)
    - Pexels CC0 商用真实拍摄 (已可用)
    - SVG/CSS 覆盖层 (静态代码)
```

### 3.2 openmontage_brief 判断（已跑）

```yaml
openmontage_brief_status: pass
openmontage_decision: blocked_infrastructure   # 见 openmontage_brief.md
openmontage_blocked_reason: |
  1. sibling repo 未 checkout 在本机（文档路径 /Users/bubu/... 与当前用户 wmzuo 不匹配）
  2. 项目内无成功 OpenMontage 案例参考（W28D01 也是 disabled_by_choice，未跑 preview）
  3. W28 曝光优先·日更节奏承担不起首次跑通的交付风险
  4. 与 skin.tone_direction "同事口吻、克制"匹配度低（OpenMontage animated explainer 有教程感风险）
openmontage_review_trigger: 见 openmontage_brief.md decision_review_trigger 字段
```

## 4. 三个候选表现方案（**跨家族强制满足**）

### 方案 A · 原生 P001 混合（family=`pipeline`）

- **名称：** Pexels B-roll + QuickTime 屏幕录制 + SVG 覆盖 + ffmpeg 合成
- **实现家族：** `pipeline`
- **核心画面机制：**
  - 0-6s：Pexels 傍晚办公室 B-roll + 手机屏幕特写（Q9 chaos_must_be_real_footage 兼容）
  - 6-32s：黑底大字 punch + AI 对话真实屏幕录制 + SVG 打点标签
  - 32-50s：静态 before/after 对比（CSS 静态） + 傍晚窗外 B-roll + 便签 CTA
- **首屏：** Pexels office_dusk_evening 已下载素材 + iPhone 锁屏 18:55 拍摄
- **中段：** AI 对话 QuickTime 屏录 + SVG 五段打点淡入淡出
- **CTA：** 纸黄底便签 + CSS 光标闪动
- **服务指标：**
  - 3s 停划：真实办公室 B-roll 匹配打工人下班场景 → 一秒认领
  - 完播：屏录连续动作性变化 + SVG 打点 5 段变化点，中段不塌陷
  - 收藏：小红书 P5 静态 prompt 页可截图带走
  - 评论：同事口吻 + 具体钉子场景（18:55）
- **优点：**
  - 与 SYSTEM Q9 证据优先 100% 一致
  - 与 skin.tone_direction "同事口吻、克制"完全匹配
  - Pexels 已拉 7 条素材落地，`.env` 配了 MiniMax TTS 和 GPT-image-2，无阻塞
  - 制作成本可控（1 天完成）
- **风险：**
  - 首镜纯 Pexels 素材可能与其他 AI 教程号撞（差异化靠"沉默 3s + 时间戳"设计）
  - 屏幕录制需要准备"工作流水账" generated_fact 样本
- **制作成本：** ★★ 中（1 天）

### 方案 B · OpenMontage 混合（family=`integrations`）

- **名称：** OpenMontage documentary montage 前段 + screen demo 中段 + cinematic 结尾
- **实现家族：** `integrations`
- **核心画面机制：**
  - 0-6s：OpenMontage documentary montage 电影感钉子（Grok video 或 Pexels 素材由 OpenMontage 剪辑）
  - 6-32s：OpenMontage screen demo pipeline（AI 对话演出）
  - 32-50s：OpenMontage cinematic 结尾 + 情感落点
- **首屏：** OpenMontage 剪辑电影感开场（3 秒沉默钉子会更连贯）
- **中段：** screen demo 电影感演出（比 QuickTime 屏录更连续）
- **CTA：** cinematic 收尾
- **服务指标：**
  - 3s 停划：**理论上电影感钉子 > Pexels 拼接** → completion_3s 可能 +5-8%
  - 完播：连续镜头感 > 分段拼接
  - 收藏：小红书视频版可能有帮助，但轮播仍需原生 P001
  - 评论：情感感染力更强
- **优点：**
  - 电影感能拉高首镜 completion_3s（理论）
  - 连续镜头比拼接更专业
  - 若成功可复用到 W28 其他条目和 W29 破圈实验
- **风险：**
  - **🔴 基础设施阻塞（`blocked_infrastructure`）**：sibling repo 未 checkout · Grok video 无成功案例参考 · export_request → collect_output 跨仓库首跑
  - 项目内无 OpenMontage 成功案例（W28D01 也 disabled）
  - W28 日更节奏承担不起首跑失败
  - 与 skin.tone_direction "克制"不匹配（电影感/animated explainer 有过度倾向）
- **制作成本：** ★★★★ 高（若跑通 3-5 天含 sibling repo 搭建 + 首跑调优）
- **决策：** 因 `openmontage_brief.decision = blocked_infrastructure` **本方案排除**

### 方案 C · 纯真人拍摄（family=`raw`）

- **名称：** 全片真人拍摄 + 剪映后期
- **实现家族：** `raw`
- **核心画面机制：**
  - 0-6s：真实办公室拍摄（灯光 + 手机 + Excel）
  - 6-32s：真实操作者演示（真人打字 + 真实屏幕 + 真实旁白）
  - 32-50s：真人到窗外/傍晚 + 手写便签
- **首屏：** 真实办公室 + 真人（不出脸，可拍手/背影）
- **中段：** 真人操作 AI 全流程
- **CTA：** 真人手写便签
- **服务指标：**
  - 3s 停划：真实拍摄可信度最高（B 级证据 > Pexels 通用素材）
  - 完播：真人动作连续性最强
  - 收藏：真实操作可复制性最强
  - 评论：真实感激发共鸣
- **优点：**
  - 完全真实（A 级证据 > Pexels B 级 > OpenMontage 合成 C 级）
  - 与 skin.persona_anchor "老兵同事" 契合度最高
- **风险：**
  - **🔴 素材缺失阻塞**：**用户明确说没素材**（本次对话已确认："我没有可以提供的素材")
  - 无法在无用户素材前提下执行
- **制作成本：** ★★★ 中（若用户能拍 · 1 天）
- **决策：** 因**素材缺失**（用户已明确）**本方案排除**

## 跨家族满足自查

- [x] 3 方案覆盖 3 个不同家族（`pipeline` + `integrations` + `raw`）✅
- [x] 3 方案不是同家族变体（不是"P001 A/B/C"或"P004 A/B/C"）
- [x] 方案 B 因 `integrations` 家族基础设施 `blocked_infrastructure` 排除，理由明确
- [x] 方案 C 因 `raw` 家族素材缺失排除，理由明确
- [x] 方案 A 是可执行的唯一候选，不因"缩水"而是"客观唯一"

## 5. 选择与不选择

### 推荐方案

- **推荐：** 方案 A · 原生 P001 混合（Pexels + QuickTime 屏录 + SVG + ffmpeg）
- **为什么最能服务北极星：**
  - completion_3s：Pexels 真实办公室素材（已下载 7 条）+ 手机屏幕特写钉子 → 打工人 1s 认领
  - completion_rate：屏录连续动作 + SVG 5 段打点 → 中段变化点丰富
  - 收藏：小红书 P5 静态 prompt 页 CSS 静态 → 可截图带走
  - 评论：与 skin.tone_direction "同事口吻"匹配 → 打工人共谋感自然
- **与最近 5 条最大差异：**
  - 与 W27D01-D06 老板圈 catalog 完全不同（audience 池切换 + 首屏真实 B-roll · W27 全 HTML 卡片）
  - 与 W28D01（未定稿）方向不同（D01 老板圈方法论 · D02 打工人场景剧）

### 不选其他方案原因

| 方案 | 不选原因 | 是否可作为后续备选 |
|------|----------|--------------------|
| A | 已选 | — |
| B | OpenMontage sibling repo 基础设施未 checkout + 项目内无成功案例 + W28 日更承担不起首跑风险 | ✅ **待 sibling repo 到位 + 首个成功案例后重新评估**（见 openmontage_brief.decision_review_trigger） |
| C | 用户明确说无真实素材可拍 | ✅ **待用户有拍摄条件后可切换** |

## 6. 禁止从旧 storyboard 开始改

- [x] 本条不是复制上一条 storyboard 后改字（W27 全 HTML 卡片，本条真实 B-roll + 屏录）
- [x] 本条不是旧模板换标题、换颜色、换字幕
- [x] 复用 P001 + punch_black 时明确声明"复用能力，不复用画面"（见 visual_originality_gate.md）
- [x] 分镜从本条视觉命题「打工人下班沉默钉子 + AI 屏录 + 静态对比 + 情感落点」生成

## 7. 进入 form_strategy 的条件

- [x] 至少 3 个候选方案完整（本次严格 3 个 · 跨 3 家族）
- [x] 3 个方案覆盖 ≥2 个不同家族（本次 3 家族全覆盖）
- [x] 有明确推荐方案（方案 A）
- [x] 写清楚不选其他方案原因（B 基础设施 blocked · C 素材缺失）
- [x] 写清楚与最近 5 条的差异（W27 老板圈 vs D02 打工人 · 首屏机制不同）
- [x] 明确禁止旧 storyboard 改字
- [x] **`openmontage_brief.md` 已跑，decision 明确（blocked_infrastructure）**
- [x] **候选池完整性自查 §3 五条全过**

`status: pass · decision: proceed_to_form_strategy`

## 五维打分（对照 SYSTEM §4.2）

| 维度 | 权重 | 方案 A | 方案 B | 方案 C |
|------|------|--------|--------|--------|
| 停划力（首镜 ×2） | ×2 | 9 → 18 | 8 → 16 | 10 → 20 |
| 看懂速度 | ×2 | 8 → 16 | 7 → 14 | 8 → 16 |
| 节奏变化 | ×1 | 8 | 9 | 7 |
| 互动钩子 | ×1 | 8 | 7 | 9 |
| 信任/证据 | ×1 | 8 | 5 | 10 |
| 交付风险 | ×0.5 | 8 → 4 | **1 → 0.5**（blocked） | **1 → 0.5**（blocked） |
| **合计 / 60** | | **62** | **51.5**（+blocked 惩罚 = 25.75 实际不可选） | **62.5**（+blocked 惩罚 = 31.25 实际不可选） |

**方案 A 胜出，且是**唯一可执行**方案。**

## 决策总结

- **决策：** 方案 A 原生 P001 混合
- **家族：** pipeline
- **不启用 OpenMontage 的原因：** blocked_infrastructure（非 disabled_by_choice）
- **不用真人拍摄的原因：** 素材缺失（用户明确）
- **候选池预先缩水的教训：** 已入 memory `feedback_no-default-tech-stack` + template `form_competition.md` §3
- **未来 revisit 条件：** 见 openmontage_brief.md `decision_review_trigger`
