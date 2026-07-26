# 01 · 铁律 1-11 · 结果负责制

> **本文所有铁律服从 [00_NORTH_STAR.md · 铁律 0](00_NORTH_STAR.md)。**
> **铁律不是「文件齐不齐」,是「观众会不会划走、会不会互动」。**

---

## 铁律速览

| # | 铁律 | 一句话 | 章节 |
|---|------|-------|------|
| 1 | 不看仓库有什么,只看哪条实现更强 | pipeline 存量不代表选型正确 | §1 |
| 2 | 内容门 + 形式门分开 | 两道门永不合并 fail-closed | §2 |
| 3 | 合规分 vs 效果分 | scorecard 纸面 90+ ≠ 能投 | §3 |
| 4 | 各环节专家对最终结果负责 | 不是对交差文件负责 | §4 |
| 5 | 尽一切可能让内容更好 | 宁可多一轮,不「能出片就行」 | §5 |
| 6 | 自我进化 | 提高标准 + REJECT_LOG + gate_check 升级 | §6 |
| 7 | 形式为数据假设服务 | 声明不了数据杠杆的形式不进片 | §7 |
| 8 | ⭐ 门禁是地板不是目标 · 抬高 3 档再验收 | 每到"能过了"的时刻,把目标往上提 3 档 | §8 |
| 9 | ⭐ 创意决定上限 · 打磨只是防守 | 平庸创意跑完全套 gate 产出的是打磨精良的平庸品 | §9 |
| 10 | `draft_self_generated` 无门禁效力 | 单跑 agent 不算通过 | §10 |
| 11 | 数据 A/B/C 分级 | 真实带来源 = A · 估算 = B · 无来源 = C | §11 |

---

## §1 · 不看仓库有什么,只看哪条实现更强

pipeline / 场景文件 / 工种名单**不是完成标准**;标准是:
- 观众会不会停、懂、互动/收藏
- 发布包能否直接外发

**实现选型见 `05_PIPELINE_CANDIDATES.md` §五维打分。**

**反例**:
- ❌ 因「P004 是默认视频线」/「Three 更酷」选实现
- ❌ 因「.agents/skills 里有 X」/「pipeline 里有 Y」当作能力齐了
- ❌ 「就走 P001/P004 吧」这类默认心智出现时,立即回 `05_PIPELINE_CANDIDATES.md` 五维打分

---

## §2 · 内容门 + 形式门分开(fail-closed)

**两道门永不合并。**

| 门 | pass 条件 | 作用 |
|---|---|---|
| **内容门** | 脚本 · 洞察 · P0 · 合规 · scorecard 90+ | pass 才允许 TTS / gpt-image / render |
| **形式门** | 分镜像素 · 视觉同质 · pre_publish_forecast · CTA · 视觉审计 | pass 才允许外发 |

**脚本 90+ ≠ 能投。** 内容 pass 形式 fail → `approved_content_blocked_form`,不得外发。

### 有成本工序铁律

**全 Phase A 工种 scorecard ≥90 + script_review pass → `gate_check(pre_render) PASS` → 才允许 TTS / gpt-image / P004 build / render。**

| 禁止 | 说明 |
|------|------|
| 提前 TTS | `audio_plan.status: not_started` 直至 pre_render PASS |
| 提前 render | `week_build.py --render` / `p004_video/build.py` 自动验 pre_render |
| `--force` 绕过 | 登记 `docs/design/GATE_BYPASS_LOG.md`,不可外发 |

### 三阶段 gate

```bash
python3 pipeline/gate_check.py --id W26D04 --phase pre_render   # render 前
python3 pipeline/gate_check.py --id W26D04 --phase post_render  # 有 mp4
python3 pipeline/gate_check.py --id W26D04 --phase approve      # 外发前
```

详规:`pipeline/gate_check.py` · `templates/design/content_form_split_gates.md`

---

## §3 · 合规分 vs 效果分

| 类型 | 说明 |
|------|------|
| **合规分** | 文件齐、互评格式对 — 易 90+ |
| **效果分** | 像素、同质、pre_publish_forecast — **外发以此为准** |

- 纸面 90+ 与效果分差 **>5** → 必填 `room/form_audit_{v}.yaml` · 登记 `docs/design/FORM_FAIL_LOG.md`
- 形式 forecast **fail** → `gate_check(approve)` 硬失败,不论 scorecard 纸面分

---

## §4 · 各环节专家对最终结果负责

**禁止「讨论室 approved + render 跑通」但成片与上条同质。** 每个工种对整条链的**最终成片/成图/成文**负连带责任——上游不能只写 markdown 说「形式 F3」却产出与 F1 同质的 slideshow。

各工种"对什么结果负责"详表见 `02_WORKFLOW.md §工种责任表`。

---

## §5 · 尽一切可能让内容更好

**默认动作**:多一轮讨论、换 pipeline、重写分镜、重出封面、重写口播、双人互评迭代——而不是「能 render 就行」。

**验收问句(任何工种交稿前自问):**

> 如果我是观众,划到这条会不会觉得「又是同一个模板」?
> **形式门:** catalog 三连?同 HTML 播两次?CTA 口播进片了吗?
> **分析师:** 完播/互动预估敢写「可外发」吗?
> 如果我是老板,看完会不会想评论或收藏?
> 如果现在要发,我敢不敢用这条代表账号?

任一答「不敢」→ 该环节负责工种继续改,**不得**推给下一环或 render 脚本。

---

## §6 · 自我进化(标准持续抬高)

提高标准 → 多轮测试 → 更新 Rubric + `gate_check` + REJECT_LOG。任何"定稿/最终采用/pass/approved"判断前,先过 `templates/design/pre_work_self_audit_checklist.md`——**不靠用户事后抓包发现问题**。

详规:`templates/design/system_evolution.md` — 触发器 · 三级标准 L1/L2/L3 · `topic_evolution_from_data.md`

---

## §7 · 形式为数据假设服务

**每个高级视觉镜头必须声明服务** `completion_3s` / `completion_rate` / 理解 / 收藏 / 评论 **中的哪一项**;不能声明数据杠杆的形式,不进入成片。

---

## §8 · ⭐ 门禁是地板不是目标 · 抬高 3 档再验收

> **2026-07-21 立 · 语音厅 MV 事故后升为铁律**

任何 gate / QA / scorecard 阈值 / forecast 评级,语义都是「最低及格线」,不是「验收目标」。

**每到"我觉得这个能过"的时刻,那个"能过"的感觉本身就是"标准定低了"的信号**——强制自问:**能不能把验收目标往上提 3 个档次?** 把抬高后的标准当成真正的验收目标去建,再验收。

### 触发点 = 一切"它过了 / 达标了 / 可以 approve 了"的判断时刻

内容 scorecard、`gate_check_media`、`gate_check_palette`、运镜/多样性 QA、脚本锦标赛、封面评审、`pre_publish_forecast`——每一道打算因"过了"而放行的地方都先跑此反问。

### "3 档"= 刻意的实质性大跳,不是 +1 敷衍

逼自己从"最低可接受"心智切到"什么才算明显出色",把抬高后的标准写成新验收目标。

### 抬高的是"起手瞄准的目标",动手前设定

第一次就照抬三档的标准去建,不是过后无限返工。**与闭环上限(≤2 轮)/D05 加速不冲突**——那些管"失败后重做几轮",本条管"第一次瞄多高";先瞄高 + 返工有上限,两者相容,别误读成"无限镀金"。

### 判据自查

若放行理由是"它过了 gate",停——问"过的是目标还是代理指标?这道地板是'好/出色'的代理,清了它等于什么都没说"。

**本项目所有制作视频的 workflow 每一道验收都必须遵守本条。**

依据:memory `feedback_gate-floor-not-target` · `feedback_build-to-reference-not-floor`

### 相关铁律 · 禁用改验收器输入的方式过门

给非主体挂 bbox / 把主体清空 / 改 motion-track 记录方式,**都比 fail 更糟**(假 pass 静音信号);验收器只接受"画面真的动了",不接受"记录方式改了让它显示动了"。已两次实例。依据:memory `feedback_no-gaming-the-verifier`。

---

## §9 · ⭐ 创意决定上限 · 打磨只是防守

> **2026-07-26 立**

### 层级次序(覆盖本文所有其他机制)

| 层 | 作用 | 上限 |
|---|---|---|
| **创意** | 唯一能"超出"的东西 | **无上限**,也可能是 0 |
| **参照 / 规格** | 不低于水准线 | 平台现有最好水平 |
| **细节打磨 / 密度** | 防止观众进入审视模式 | **只能守,攻不了** |

### 门禁:创意不过关时,禁止进入执行层

一个平庸创意跑完 gate_check / 证据包 / scorecard 全套,产出的是**打磨精良的平庸品**——执行层的一切机制都不解决创意平庸。

### 为什么必须靠机制,不能靠"我再想想"

**LLM 的默认输出 = 训练分布的中位数 = "平庸"的定义。** 让 agent"想得更好一点",得到的是同一个中位数换个说法。**只能靠机制强迫,不能靠努力。**

### 淘汰率买在创意层,不买在成片层

- 创意层单次迭代**近乎免费**;执行层渲染**很贵**
- 在便宜的地方跑 20 选 1,在昂贵的地方只做 1-2 版
- 反过来做 = 在最贵的地方反复修补,当前成本结构最大的漏洞

### 以产线实测为准,不以类比推演为准

从"好莱坞画面炸裂"顺推出"加图层数"是错的(与 `paperdoll-mv-packaging` 故障 2/3/4 实测冲突:堆层数是廉价/脏乱的病因)。密度不足时该加的是**对比与构图变化**,不是层数。

**落地机制见 `03_VISUAL_CREATIVE_GATE.md`。**

依据:memory `feedback_skill-vs-template-distinction`

---

## §10 · `draft_self_generated` 无门禁效力

**单跑 agent 不算通过。** 所有 `pass / approved / score >=90` 必须有来源:

```yaml
status: draft_self_generated     # 不具备门禁效力
status: pass_agent_reviewed
status: pass_human_reviewed
status: pass_gate_checked
scorecard_valid: false           # 自生成 scorecard 必须标 false
```

**一个模型代替多个工种写出的讨论室和 scorecard,只能是 `draft_self_generated`,不能当作真实互评。**

### 视频生产硬门:禁止 QA 截图冒充成片

`prototype/qa_shots/`、低保真 HTML 截图、静态 QA 帧只用于证明"画面进入像素",不得直接拼接为 `douyin/video.mp4`。写入 canonical 成片路径前必须满足:
- 画面来自动态表现层(动态 HTML/GSAP/Canvas/Three 录屏或帧序列、OpenMontage、真实录屏/B-roll/视频生成素材、或正式 render pipeline)
- 配音来自项目生产级 TTS/录音方案,不得用系统 `say` 冒充
- 成片包含字幕、BGM/SFX、动态镜头节奏和逐镜验收
- `gate_check(pre_render)` 未通过时,mp4 只能作为 `_build/` 临时预览或 `rejected/` 事故归档

达不到 = `blocked`,不是"生成一个长得像视频的文件"。

---

## §11 · 数据 A/B/C 分级

| 层 | 用法 |
|---|---|
| **A · 真实** | 真实私信/后台/录屏/发布后数据 — 优先 |
| **B · 项目真实+区间** | 系统确有其物,效果用区间(「留资个位数」) |
| **C · 叙事修饰** | 无精确数时的合理表述,禁可验证假里程碑 |

**项目画面必须真实**;效果数字按 A/B/C,禁止 P 图假后台。详规 `ops/data-policy.yaml`。

---

## 补充铁律(D02-D08 沉淀)

### §Δ1 · 形式重做时脚本门禁(D02 沉淀)

**问题:** 用户抱怨「形式千篇一律」时,执行易窄化为只换模板;`script_review` 旧 pass 被当作永久免死金牌。

| # | 铁律 | 执行 |
|---|------|------|
| 1 | 触发词分流 | 「形式/同质/模板」类抱怨 → discussion **两列**:形式问题 + 叙事/脚本问题 |
| 2 | 叙事骨架同质 → 双升 | Round 记录「叙事骨架/近 D{NN} 同」→ 须 `content_version` +1 并重写 `script_vo`,不能只升 `form_version` |
| 3 | 数据症状分流 | 7139 播/2 评 → forecast/discussion 拆列:3s/视觉 vs 评论/CTA/原话 |
| 4 | form 领先须声明 | `form_version` > `content_version` → `script_review` 须 `content_redo: true` **或** `content_ab_frozen: true` + 理由,否则 gate_check FAIL |
| 5 | 形式 A/B 后第二轮 | W26 等固定脚本测形式实验结束后 → 允许固定形式改脚本做 content vN+1 |

**验收问句(内容层 · 形式重做时必问):** 关掉声音,中段还像不像 lecture?原话进片了吗?CTA 能勾评论吗?若形式已换、脚本仍是 vC 压缩版 → **内容门未真正重验**。

### §Δ2 · 形式承诺兑现门禁(D08 沉淀)

**问题:** D08 文档写了 "Pexels B-roll + 私域客户看板 + Agent 分工卡",但实际用通用 `pipeline/render.py` 输出旧 evidence 卡片和 newspaper 轮播,仍被误标 `ready_to_publish`。

| # | 铁律 |
|---|------|
| 1 | 不看 format_spec 写了什么,只看最终像素 — render 后抽关键帧复验;画面不像承诺形式 → `approved_content_blocked_form` |
| 2 | 承诺 Pexels/B-roll 必须真进画面 — storyboard 须引用已下载本地素材;只写搜索词/说明不算 |
| 3 | 承诺 custom/专属看板须有专属模板 — storyboard 至少包含 `dNN_` / `pexels_` / `custom_` 级模板或真实素材 |
| 4 | 通用 evidence/newsprint 不得冒充新形式 — `pipeline/render.py` evidence 卡片、`render_carousel()` newspaper 只能做内部草稿 |
| 5 | 像素失败不得 ready — `pre_publish_forecast` D/C、blocked_form、通用模板吞掉 → `gate_check(approve)` FAIL |

### §Δ3 · 正向复用协议(D08 重做版沉淀)

**核心结论:不要设形式优先级;要设镜头任务和兑现检查。**

| 镜头任务 | D08 重做做法 | 以后复用 |
|---|---|---|
| 停划 | 真实店主/店铺素材 + 大字反常识 Hook | 首 3s 必须同时有场景锚点和一句可懂冲突 |
| 看懂痛点 | 私域消息瀑布:新客/老客/售后/沉默/复购混在一起 | 把抽象痛点变成一个可扫读的工作现场 |
| 看懂方案 | Agent 三件事分拣:分层/提醒/预警 | 把"AI 能做什么"拆成明确工位/职责 |
| 证据感 | 今日待跟进看板:人数/下一步/人工优先 | 仿真看板可以用,但必须声明为解释性画面 |
| 停留变化 | 风险雷达:退款/差评/高价值客户不回 | 中后段必须换一种视觉语法 |
| 互动 | 四选项 CTA:分层/回访/复购/售后 | 评论问题让用户能低成本选一个具体答案 |

**实施顺序:**
1. 先写 `retention_beat_sheet`:每段标 `停划 / 看懂 / 证据感 / 情绪 / 互动`
2. 再写 storyboard:每段必须有不同"画面任务",不是换色卡片
3. 再选能力:Pexels、录屏、HTML+GSAP、Three、静帧、真人、P001/P004 都只是候选;谁更能完成该镜头任务就用谁
4. 素材必须落本地:Pexels/B-roll 不许只写搜索词
5. 专属模板必须存在:storyboard 引用的 `dNN_*.html` / `custom_*.html` 必须真实创建并进最终 mp4
6. 成片后抽帧复验:至少看首镜/痛点镜/方案镜/证据镜/风险镜/CTA 镜
7. 若抽帧发现旧字幕/黑屏/路径丢图/旧模板感,必须返工

**防旧模板回流:**
- 不从"上条视频模板"开始改;从"本条观众要看懂什么"开始设计
- 旧 pipeline 可用作渲染器,但不能决定画面结构
- `format_spec` 写了什么不算,`video.mp4` 抽帧看见什么才算
- 如果某个镜头看起来能替换成任意选题文案仍成立,它就是模板化风险
- 如果 6 张关键帧像同一个设计系统的卡片轮播,形式门默认不过

### §Δ4 · 双平台分轨(W26 数据沉淀 · 2026-06-25)

**W26 实测:** 抖音 5 条合计 121 播 / 1 赞 / 0 评;小红书 5 条 539 曝 / 46 观 / 0 藏。跨平台 `video_reuse` 全弱。

| # | 铁律 | 自 W27 起 |
|---|------|-----------|
| 1 | 禁止跨平台 mp4 复用 | `meta.yaml` / `verdict.yaml` 不得出现 `video_reuse`;抖音视频 ≠ 小红书视频 |
| 2 | 分立项、分脚本、分形式 | 同痛点可成对设计,须独立 `douyin/` 与 `xhs/` |
| 3 | 日更分轨 | 每平台每天 1 条(xhs 12:30 · dy 19:30) |
| 4 | 平台默认形态 | 抖音:38–45s 叙事视频;小红书:轮播/清单/字段表 |

**注:** 2026-07-05 起停做视频号;xhs 走视频 or 7 页图文由形式策略官定,判据"抄下来"vs"看下来"。见 memory `feedback_dual-platform-only`。

---

## 双人互评(90 分门禁 · 与主铁律同级)

> 详规:`.cursor/rules/content-outcome-accountability.mdc`(归档) · `templates/design/scorecard_enforcement.md`

### 硬性规则

| 规则 | 说明 | 不满足则 |
|------|------|--------|
| 每工种 ≥2 人 | 各写 `room/scorecards/{工种}.yaml` | blocked |
| 不同角度 | 两位 reviewer 的 `angle` 不得相同 | 评分无效 |
| 禁止自评 | 产出者不得评自己的工种 | 评分无效 |
| **通过线 90** | 每位 score ≥90 且 avg ≥90;**89 = fail** | 继续改,不得下一阶段 |
| 分阶段 | Phase A 立项 scorecard + Phase B 复验 scorecard | 缺任一 = blocked |
| **独立评** | `review_mode: independent`;禁同 session 自填 | 缺则 gate_check FAIL |

### 变更级联作废(改 A 必重评 B)

| 变更 | 作废 scorecard / 文档 |
|------|------------------------|
| 口播 / script | 编剧、留存、编导、script_review、vo_listen_notes |
| storyboard | 动效分镜师、动效设计师、留存 |
| render 新 mp4 | 动效设计师、视觉设计、编剧、编导、motion_wow Phase B、cover_review |
| cover `at` 变 | 视觉设计、cover_review |

作废后 `verdict.status` 不得为 approved,直至 gate_check PASS。

### 禁止偷工(Agent 行为)

| 禁止 | 说明 |
|------|------|
| 同 Agent 自评 pass | 产出 `scripts/` + 写 `scorecards/编剧.yaml` pass → 无效;须独立 Agent/Task 打分 |
| 假分身 reviewer | `编剧审校-A`、`子 Agent`、`-甲/-乙` → gate_check FAIL |
| 形式互评偷工 | 缺 `review_mode: independent`、notes<40 字、无扣分项、两 notes 相同 → FAIL |
| 手填 gates | `gates.scorecards_all_pass: true` 但 gate_check FAIL → 编导退稿 |
| 跳 Phase | 无 mp4 不得 `approve`;无 vo_listen_notes 不得 Phase B pass |
| 过期 scorecard | 大版本变更后 `artifact_version` 不匹配 → 级联作废重评 |

---

## 三版脚本铁律 · 禁 stub

- **v0** 故事/场景向 · **vA** 数据/反差向 · **vB** 单场景/单原话深挖
- vB/v0 一行占位 = **直接 reject**
- 与上条 approved 口播 **≥3 处同序同句式** = reject

**编剧下限(洞察包消费):**
- ≥**4** 条 `topic_brief` 原话进片(铁律:少于 4 条直接 fail)
- 钉子场景五要素齐全(谁/什么时间/在哪/烦什么/要什么结果)
- 每个 P0 对应一镜/一节拍,非旁白堆叠

---

## 动效铁律 · 禁 PPT / 幻灯片 / 静态图

> 画面必须**动起来**。交付物是动效视频或 GSAP 时间轴产物,不是静态排版 PNG 冒充成片。

| 禁止 | 说明 | 负责工种 |
|------|------|----------|
| PPT 风 / 幻灯片风 | 分屏提案页、黑金渐变堆字、左文右窗 mock、flow→terminal→metric 三连 | 形式选型师 + 视觉设计 |
| 静态图片风 | Ken Burns 证据卡 slideshow、纯报纸排版轮播、无时间轴的"设计稿 PNG" | 平台原生策划 + 动效分镜师 |
| 静态封面冒充原生 | 抖音 `light_split` / 独立排版 cover 与成片脱节 | 视觉设计 |

| 必须 | 说明 |
|------|------|
| 抖音 | 出 `video.mp4`(`p004_gsap` / `p005` 等);封面 `video_frame` 成片定格 |
| 小红书 | 轮播走 P007 漫画 GSAP(动效渲帧);禁纯静态报纸风 |
| 全片 | ≥3 种 P004 模板;单模板 ≤40% 时长;5–8s 有视觉变化 |
| render_evidence | 每周 ≤1 天,且不得与相邻天同 route |

**验收问句:** 把声音关掉划 3 秒,画面还在动吗?封面点开和视频是同一套视觉吗?
**惊艳问句(动效设计师):** 全片至少 2 处让人"停一下",且 ≥1 处 unexpected(非 catalog 标配预期内)?
**创意问句:** 关掉声音看画面,像不像"又一套模板排列"?若是 → **动效设计师 fail**。

---

## 口播脚本铁律 · 禁念 PPT / 禁模板克隆

> 这种水平的脚本**直接 pass 不允许产出**。

| 禁止通过 | 说明 | 负责工种 |
|----------|------|----------|
| 念 PPT 式口播 | 数字→痛点→字段连读→CTA,无场景无对话 | 编剧 |
| 模板克隆上条 | 与上一条同骨架(如「不是让你多买系统」+ 四字段 + 讨论 CTA) | 编剧 + 编导 |
| 三版造假 | vB/v0 一行 stub,discussion 却写"三版讨论" | 编剧 |
| 无 script_review | 未 `design/script_review.md` pass 即 TTS / build | 编剧 + 编导 |
| 编剧自批 pass | 须留存设计师(节奏)+ 内核提炼师(P0)联签 | 编剧 |

**必过项:** 前 5s 有场景;**≥4 句**对话/原话;P0 融叙事(禁字段名连读);v0/vA/vB 结构明显不同。

**禁过骨架(≥3 处同序同句式即 reject):** 数字钩子 → 痛点排比 →「不是多买系统」→ 字段连读 → 服务触达 → 讨论 CTA。

详规:`templates/design/script_standards.md` · 反例:`docs/design/SCRIPT_REJECT_LOG.md`

---

## 创意铁律 · 多 Agent 的核心目的

> **专业 Agent 不是为了填表,是为了产出创意。** 模板式动效/口播 = 与"尽一切可能让内容更好"冲突。

| 禁止 | 说明 | 负责工种 |
|------|------|----------|
| catalog 标配交差 | 仅排列 punch+reveal+pain+compare 等换皮组合 | 动效设计师 + 形式选型师 |
| 无本条专属创意 | motion_wow 写不出"为何只有这条适合、观众为何会 unexpected 停" | 动效设计师 |
| 预期内动效 | 高潮在 D01–D03 已见过,无新 metaphor/镜头 | 动效设计师 + 留存 |
| 为时长删叙事 | 口播/场景被削到 bullet | 编剧 + 编导 |

**必须:** motion_wow 含 **≥3 专属创意点**(不同视觉隐喻;非同一 HTML 换 data)+ 创意说明;**catalog ≤35%** · 同 template ≤1 镜;scorecard 创意维度 <90 → fail。

---

## 拒稿级反例(摘要)

- 跳过洞察包写稿 · 无节拍表出分镜 · 发裸片
- 克隆上一条分镜/画面 · catalog 标配三连
- 全片单一渲染场景 · 脚本 90+ 但形式 fail 仍外发
- 形式 vN 重做但 `content_version` 不动、无 `script_review` 声明
- 因"默认 pipeline"或"技术更酷"选实现,未按 `05_PIPELINE_CANDIDATES.md` §五维打分
- 带货跳过合规 · 正文私信导流
- 静态 PNG / PPT 分屏 / 证据卡 slideshow 冒充动效成片
- 小红书主形态为纯静态报纸轮播(无 GSAP 漫画)
- 未走 Phase A+B 多 Agent 讨论即 approved / 外发
- 无 motion_wow.md 或全片无惊艳点
- vA/vB/v0 占位 stub 冒充三版讨论
- 任一工种 scorecard avg < 90 仍 pass / render
- 无 pre_publish_forecast 或形式 forecast fail 仍 approve
- 纸面 90+ 效果分 fail 未归档 form_audit

完整列表:`docs/design/SCRIPT_REJECT_LOG.md` · `docs/design/FORM_FAIL_LOG.md` · `docs/design/COVER_REJECT_LOG.md`

---

## Source Map

- 原 `docs/SYSTEM.md` §3(全部 3.1 / 3.1a-e / 3.2 / 3.4 / 3.5)
- 原 `CLAUDE.md` §铁律 R0-R9(11 条)
- 原 `.cursor/rules/content-outcome-accountability.mdc` 全文(17.8 KB · 最大源)
- 原 memory:`feedback_gate-floor-not-target` ⭐ / `feedback_build-to-reference-not-floor` ⭐ / `feedback_no-gaming-the-verifier` ⭐ / `feedback_skill-vs-template-distinction` ⭐
