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
   **例外（须显式声明）：** 周形式 A/B 实验可 `content_ab_frozen: true`；**叙事骨架被 Round 标同质时不得引用本例外**（须 content +1）
2. **专属镜 ≥3，catalog 作过渡或不用** — 禁止 pain+compare+cta 三连
3. **时长为完整表达服务** — 宁可 55s 专属镜，不压 48s 裁 CTA
4. **首镜一眼不同** — 数字 punch / 新 metaphor，非 Excel 冷开换 data
5. **每条写清「为何本条唯一」** — motion_wow CREATIVE-N + 口播锚点

## 6. 变更级联（形式专用）

| 变更 | 动作 |
|------|------|
| storyboard 形式大改 | `form_version` +1 · 形式 scorecard 全作废重评 |
| **form 升版且讨论标叙事同质** | **`content_version` +1** · 编剧三版 · `script_review` 重验 · 禁止只换 HTML |
| **form 数字 > content 数字** | `script_review` 须 `content_redo: true` 或 `content_ab_frozen: true` + 理由 |
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

## 9. 形式重做时 · 脚本不可静默复用（D02 沉淀 · 2026-06-25）

> **从 D02 教训归纳：** form v4 换了 6 镜 UI，但口播仍是 vC 压缩版；7139 播/2 评被全归因首镜；Round 7 已标「叙事骨架近 D01」却未升 content。  
> 脚本对完播/互动权重 **高于** 动画库/模板换皮；形式重做 **默认须重验内容门**，而非继承旧 `script_review` pass。

### 9.1 五条铁律（与 `docs/SYSTEM.md` §3.1b 一一对应）

#### ① 重做触发词分流

用户或 Round 抱怨含 **形式/同质/模板/千篇一律/太简单** 等词时，discussion **须分两列**，不得只开 form 工单：

| 列 | 须回答 |
|----|--------|
| **形式** | 模板/c catalog/route/首镜像素/关声 3s |
| **内容** | 叙事弧/原话/场景句/CTA/中段 lecture/评论低 |

**决议模板：** 「形式：…；内容：…；本轮动：form only / content only / 双升」

#### ② 叙事骨架同质 → 强制 content +1

discussion 任一 Round 出现以下表述时，**禁止**仅升 `form_version`：

- 「叙事骨架与 D{NN} 相同 / 近 …」
- 「改造实录模板 / flow→terminal→metric→CTA」
- 「第三人称 lecture / 口令解法 / 原话未进片」（作为 **同质结论** 而非待办）

**必做：** `content_version` +1 · 编剧 v0/vA/vB · `script_vo` 重写 · 编剧/纪录片导演 scorecard 作废重评 · `script_review` 重走 Phase A/B。

#### ③ 数据症状分流（播/评/完播）

| 症状 | 形式归因 | 脚本归因 |
|------|----------|----------|
| 3s 低 / 划走快 | 首镜停划、hook 体 | 首句信息密度、钩子句 |
| 完播低、均播短 | 中段切镜、单镜过长 | 痛点平铺、缺呼吸、lecture |
| **播尚可、评论 0–2** | CTA 字幕是否进片 | **讨论型 CTA 弱、缺共鸣原话、场景虚** |

`pre_publish_forecast.md` 须含 **「互动/评论风险」** 一行；禁止把「2 评」只写进形式改首镜。

#### ④ form 领先 content → script_review 须声明

当 `verdict.yaml` 中 **form 版本数字 > content 版本数字**（如 form v4 / content v2）：

`design/script_review.md` **必须**包含以下 **二选一**（`gate_check` 硬验）：

```yaml
# 路径 A · 内容同步重做（推荐，叙事同质时强制）
content_redo: true
content_version: v3   # 与 verdict 一致
```

```yaml
# 路径 B · 周形式 A/B 实验冻结脚本（叙事未标同质时才允许）
content_ab_frozen: true
content_ab_rationale: |
  W26 固定 vC 测 F3 原生 UI；discussion Round N 记录。
  已知风险：…；content vN+1 计划：…
```

**禁止：** form 大改后 `script_review` 仍仅标旧 content pass、无上述字段。

#### ⑤ 形式 A/B 周 · 第二轮实验

`week.yaml` 目标含「测 F1–F4 / 固定脚本」时：

- **第一轮（形式轮）：** 允许 `content_ab_frozen: true`
- **第二轮（内容轮）：** 同选题 **固定胜出形式**，**改脚本** → content vN+1；discussion 须写「形式轮结论 + 内容轮假设」

禁止形式轮结束后仍 indefinitely 沿用 frozen 脚本外发而不做 content 轮。

### 9.2 script_review 必填字段（form 领先时）

```markdown
> status: pass | blocked
> content_version: v3
> content_redo: true          # 或 content_ab_frozen: true
> content_ab_rationale: |     # frozen 时必填 ≥40 字
>   …
```

### 9.3 工具 enforcement

- `pipeline/gate_check.py` → `check_form_redo_content_gate()`（`pre_render` + `approve`）
- 讨论标叙事同质 + form 升版 + 无 `content_redo` → FAIL
- 案例：`docs/design/FORM_FAIL_LOG.md` · W26D02 · `room/discussion.md` Round 7–9

## 10. 验收问句（内容层 · 形式重做时追加）

> 关掉声音，11–23s 还像不像连续旁白 lecture？  
> topic_brief 原话有几句进了口播？  
> 「7139 播 2 评」——评论低是 CTA 问题还是首镜问题，写清了吗？  
> form 升了、content 没升——`script_review` 里声明了吗？

任一答「否」或「没写」→ **内容门未重验**，禁止仅凭形式 gate PASS 外发。

## 11. 形式承诺必须兑现到像素（D08 沉淀 · 2026-06-25）

> **从 D08 教训归纳：** format_spec 写 “Pexels B-roll + 私域客户看板 + Agent 分工卡”，storyboard 也写了 `pexels_broll_cut.html` 等专属意图；但实际执行走通用 `pipeline/render.py`，最终画面仍是旧 evidence 窗口卡片 / newspaper 轮播。文档创新没有进入像素，结果必然模板化。

### 11.1 硬门禁

| 检查 | 通过标准 | 失败动作 |
|------|----------|----------|
| Pexels / B-roll 承诺 | storyboard 引用已下载本地素材，或最终 mp4 关键帧可见真实 B-roll | `approved_content_blocked_form` |
| custom / 专属看板承诺 | storyboard 使用 `dNN_` / `pexels_` / `custom_` 专属模板，且关键帧可见 | 形式重做 |
| 通用 evidence | 仅允许内部草稿，不得当作承诺成品 | 删除成品，禁止 ready |
| newspaper 轮播 | 仅当本条明确报纸风且与选题强相关才允许 | 否则 blocked |
| 像素复验 | 抽 5–7 张关键帧，和 format_spec 逐条对照 | 任一核心承诺未兑现即 fail |

### 11.2 gate enforcement

`pipeline/gate_check.py` 的 `check_custom_form_fulfillment()` 在 `approve` 阶段 fail-closed：

- 文档含 `pipeline/render.py` / 通用 evidence / newsprint / newspaper 阻塞信号 → FAIL
- 文档承诺 Pexels/B-roll 但 storyboard 未引用本地素材 → FAIL
- 文档承诺 custom/专属视觉但 storyboard 无 `dNN_` / `pexels_` / `custom_` 模板 → FAIL
- `content.yaml` 仍以 evidence/web 段为主体，且缺少 ≥3 个专属模板或真实素材 → FAIL

### 11.3 交付语句

> 这条不是 “是否能 render”，而是 “format_spec 承诺的形式有没有进入最终像素”。  
> 没进入，就不是新版，只是旧模板换文案。

## 12. D08 重做成功样式 · 以后新选题复用（2026-06-25）

> **从 D08 正向版本归纳：** 好转来自“多画面任务 + 像素兑现”，不是来自固定偏好某种技术。Pexels、GSAP、HTML、看板、B-roll 都只是为目标服务的能力。

### 12.1 每条视频必须先过“画面任务表”

| 位置 | 目标 | 可用形式举例 | 验收 |
|------|------|--------------|------|
| 0–3s | 停划 | 实拍/B-roll/强冲突截图/真人动作/高信息密度 HTML | 抽首帧能说出选题冲突 |
| 痛点 | 看懂 | 消息瀑布、订单堆、后台列表、聊天错位、手写单据 | 关声音也知道哪里乱 |
| 方案 | 看懂 | 分拣、流程、工位、Agent 职责卡、对比操作 | 不是“AI 很强”，而是“AI 做哪一步” |
| 证据 | 信任 | 本地素材、录屏、仿真看板、可核验数据结构 | 不冒充真实后台，结构能解释问题 |
| 变化 | 防疲劳 | 雷达、地图、时间轴、实拍切回、屏幕录制、手势 | 与上一镜不是同一类卡片 |
| CTA | 互动 | 单选/二选一/具体经历问题 | 用户能 3 秒内决定怎么评论 |

**门禁：** storyboard 没有这 6 类任务中的至少 5 类，不得直接进入渲染。

### 12.2 选能力的唯一合法理由

每个镜头写一句：

```text
本镜使用 {能力/素材/模板}，因为它更有利于 {停划/看懂/证据/互动}，具体表现为 {可观察画面变化}。
```

禁止写：

- “这类视频默认用 P004”
- “真实录屏优先”
- “GSAP 只在某种情况用”
- “Three.js 更酷所以用”
- “为了快，沿用上一条”

允许写：

- “首镜用 Pexels 店主场景，因为比抽象 AI 图更快建立电商老板语境。”
- “中段用 HTML 看板，因为要让用户一眼看到分层/人数/下一步。”
- “风险段用雷达，因为它和前面的看板视觉语法不同，能制造节奏变化。”

### 12.3 像素级校验流程

渲染后必须抽帧：

```bash
ffmpeg -y -i publish/.../douyin/video.mp4 \
  -vf "select='eq(n,30)+eq(n,180)+eq(n,420)+eq(n,720)+eq(n,960)+eq(n,1230)'" \
  -vsync vfr /tmp/topic_frames/frame_%02d.png
```

逐帧回答：

1. 首帧是否有本条独有冲突，而非通用封面？
2. 至少 5 张关键帧是否属于不同画面任务？
3. 是否有素材路径丢失、黑屏、旧字幕、旧模板残留？
4. 看板/数据是否被误读为真实后台？
5. CTA 是否完整可读且能触发具体评论？

任一失败：返工该镜头，不得用文档说明抵消像素问题。

### 12.4 防旧模板干扰清单

- storyboard 引用的模板必须真实存在。
- B-roll 必须落成本地文件，不能只写搜索词。
- 旧模板只能作为实现参考，不能作为画面结构。
- 关键帧如果能替换任意选题文案仍成立，判为模板化风险。
- `pre_publish_forecast` 必须写“与上一条不同在哪里”，不能只写指标区间。
- 最终以 `video.mp4` 抽帧为准，不以 `format_spec` 自述为准。

## 13. 形式策略会 · 表达方式必须为数据假设服务（2026-06-25）

> **新增结论：** 表达方式不是为了完成任务，也不是为了炫技；它必须服务 `completion_3s`、`completion_rate`、理解、收藏或评论中的一个明确数据假设。Web 3D、GSAP、实拍、截图、UI 看板、字幕都是候选能力，只有逐镜竞争胜出才进入成片。

### 13.1 形式策略官职责

在脚本三版和 storyboard 定稿之间，形式策略官必须为关键镜头输出 `design/form_strategy.md`：

| 字段 | 必填内容 |
|------|----------|
| 镜头任务 | 停划 / 看懂痛点 / 看懂方案 / 证据感 / 情绪 / 互动 |
| 候选表达方式 | 至少 3 种；如实拍、2D UI、消息流、GSAP、Three/Web 3D、截图、字幕 |
| 数据杠杆 | 服务 3s、完播、理解、收藏、评论中的哪一项 |
| 理解成本 | 小屏 1–2 秒能否看懂；是否会喧宾夺主 |
| 制作成本 | 素材、建模、动画、渲染、剪辑成本 |
| 技术风险 | 资产缺失、性能、导出、文字可读性、移动端观感 |
| 推荐方案 | 选中方案 + 不选其他方案的原因 |

**门禁：** 视频/强互动图文缺 `form_strategy`，或只写“用 P004 / 用 Three / 用 B-roll”而没有数据杠杆，形式门默认 blocked。

### 13.2 Web 3D / 高级动效使用规则

Web 3D 适合表达“混乱变有序、空间关系、分拣、风险雷达、流程流转、数字孪生”等主题；不适合作为每条视频默认包装。

使用 Web 3D / GSAP / 复杂 HTML 动效前，动效技术导演必须输出 `design/motion_tech_plan.md`：

| 检查 | 通过标准 |
|------|----------|
| 适用性 | 3D 比 2D UI / 实拍更能提升停划或看懂 |
| 可读性 | 9:16 小屏文字、主体、运动方向清楚 |
| 资产 | 模型、贴图、字体、B-roll、数据结构可落地 |
| 导出 | 能稳定截帧/录屏/合成进 mp4 |
| 风险控制 | 复杂度不拖慢节奏，不抢走脚本主信息 |

**铁律：** “Three/Web 3D 更酷”不是合法理由；“本镜用 3D 消息风暴，因为它比聊天截图更快让用户看见私域混乱，服务 0–3s 停划和痛点理解”才是合法理由。

### 13.3 推荐结构

对适合系统化表达的短视频，可优先考虑：

```text
前 3 秒：3D/强视觉钩子
中段：2D UI / 看板 / 消息流解释
高潮：3D 分拣 / 风险雷达 / 关系变化
结尾：简洁 CTA
```

但该结构只是候选，不是模板。每条仍须由形式策略会按主题、脚本和数据假设重新选择。
