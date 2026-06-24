# 内容 vs 形式 · 分层铁律（D04 v10→v11 沉淀 · 全系统适用）

> **从 D04 教训归纳：** 口播可以 90+ 过关，成片仍可能是 catalog 拼盘假 approved。  
> 本文件与 `.cursor/rules/content-outcome-accountability.mdc` 同级，**自 D04 起严格执行**。

## 1. 两道门 · 永不合并

| 门 | 验什么 | 通过标准 | 不通过则 |
|----|--------|----------|----------|
| **内容门** | 脚本、原话、P0、合规 | 编剧 Round6+ · script_review pass · avg≥90 | 禁止 TTS |
| **形式门** | 分镜、像素、同质、平台预估 | 视觉审计 + 分析师 forecast pass · 形式 scorecard≥90 | 禁止外发 |

**禁止：** `verdict.status=approved` 但形式层 catalog 拼盘 / CTA 裁切 / 与上条同族仍外发。

**状态示例：**

- `approved_content_blocked_form` — 脚本可保留，成片不得外发（D04 v10）
- `approved` — 内容 + 形式双 pass（D04 v11）

## 2. 形式层硬门槛（gate_check 可执行）

| 指标 | 门槛 | 来源 |
|------|------|------|
| 专属视觉隐喻 | **≥3** 种（d{NN}_* 或本条新建 HTML） | D04 v10 仅 2 种 fail |
| catalog 时长占比 | **≤35%**（02_pain/06_compare/08_cta 等） | v10 实测 38% fail |
| 同 template 重复 | **≤1 镜** | v10 excel×2 wechat×2 fail |
| 48s+ 不同 template | **≥6** 种 | v10 仅 5 种 fail |
| CTA 口播 | **完整进片** | v10 VO 50.5s / 片 48s fail |

工具：`pipeline/gate_check.py` · `check_visual_diversity()` · `check_pre_publish_forecast()`

## 3. 分数 · 合规分 vs 效果分

| 类型 | 含义 | 陷阱 |
|------|------|------|
| **合规分** | 文件齐、互评格式对、checkbox pass | 容易 90+，不等于能投 |
| **效果分** | 像素、同质、完播/互动预估 | D04 v10 形式 honest **~81** |

**铁律：**

- 形式层须填 `room/form_audit_{version}.yaml` 当纸面分与效果分差距 **>5 分**
- **外发以效果分为准**；forecast fail → approve 硬失败
- 禁止「notes 写了扣分仍 pass」

## 4. 平台表现分析师（必激活 · Phase B）

**产出：** `design/pre_publish_forecast.md`（模板：`templates/design/pre_publish_forecast.md`）

**须含：**

1. 视觉多样性客观计数（对照上表）
2. 抖音 / 小红书 / 视频号 **未发布区间预估** + 依据
3. **go/no-go**：外发 / 改分镜 / 仅图文

**分工：**

- 脚本 90+ ≠ 可外发
- 形式 forecast pass + `gate_check(approve)` PASS 才可外发

## 5. 形式设计原则（可复用）

1. **内容可复用，形式不可复用** — 口播 v10 保留；分镜须 v11 级重做，非换皮
2. **专属镜 ≥3，catalog 作过渡或不用** — 禁止 pain+compare+cta 三连
3. **时长为完整表达服务** — 宁可 55s 专属镜，不压 48s 裁 CTA
4. **首镜一眼不同** — 数字 punch / 新 metaphor，非 Excel 冷开换 data
5. **每条写清「为何本条唯一」** — motion_wow CREATIVE-N + 口播锚点

## 6. 变更级联（形式专用）

| 变更 | 动作 |
|------|------|
| storyboard 形式大改 | `content_version` +1 · 形式 scorecard 全作废重评 |
| 分析师 forecast fail | `form_publish_pass: false` · 禁止 approve |
| 纸面 90+ / 效果 fail | 写 `form_audit_*.yaml` · discussion Round 记录 |

## 7. 参考案例

| 文件 | 说明 |
|------|------|
| `publish/2026-W26/D04-复购流失/room/form_audit_v10.yaml` | v10 形式 honest fail 归档 |
| `publish/2026-W26/D04-复购流失/design/pre_publish_forecast.md` | v11 分析师 pass |
| `docs/design/FORM_FAIL_LOG.md` | 形式层 fail 登记 |
| `templates/design/system_evolution.md` | 标准自我进化 |

## 8. 验收问句（形式层）

> 关掉声音划 3 秒，像不像上一条的后半段？  
> catalog 三连是否仍在？同一 HTML 是否播了两次？  
> CTA 口播在 mp4 里能听完吗？  
> 分析师敢写「可外发」吗？

任一答「否」→ **形式门 blocked**，不得推 approved。
