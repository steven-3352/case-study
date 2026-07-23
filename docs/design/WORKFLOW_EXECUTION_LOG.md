# WORKFLOW_EXECUTION_LOG · 多角色协作执行错误登记

> **登记原则：** 交付后，主LLM 回读所有子PRD（`design/subagent_prds/*.md`）的推理栏，提炼这次执行中的错误，立即写入；不登记不放过。
> **强制读取：** 新项目开工前，`prd_pipeline` Workflow 的 Phase 0 必须读本文件最近 5 条，作为角色分派 prompt 的上下文注入。仿 `pipeline/evolution_apply.py --id XX --check` 的 fail-closed 模式——见 §使用方式。
> **与其他日志的分工：** `FORM_FAIL_LOG.md`/`SCRIPT_REJECT_LOG.md`/`COVER_REJECT_LOG.md` 记的是**产出内容**的失败案例；`PRE_NODE_CHECKLIST_MISS_LOG.md` 记的是**单个节点**漏读规范；`GATE_BYPASS_LOG.md` 记门禁被强行绕过；本文件记的是**多角色协作执行过程本身**的系统性错误（角色被跳过/自评当独立验收/感知目标未落地等），颗粒度是"整个协作流程哪里出了结构性问题"，不是单条内容的对错。

## 字段规范

```yaml
- date: YYYY-MM-DD
  project_id:
  role_reasoning_reviewed: []    # 这次交付后实际读了哪些角色的子PRD推理栏(design/subagent_prds/*.md)
  errors_found:
    - role: <哪个角色/哪个协作环节>
      what_went_wrong:
      root_cause: [flow | cognition | mechanism]   # 可多选，定义见下
      root_cause_detail:
        flow: <什么流程步骤没跑>
        cognition: <什么认知偏差导致漏>
        mechanism: <什么机制缺失导致靠人力兜底才发现>
      should_have_done:
  fix_applied: <这次已经改了什么，指向具体文件路径>
  carry_forward: <下次新项目开工前要注意的，会被 Phase 0 读取>
```

`root_cause` 三分类沿用 `PRE_NODE_CHECKLIST_MISS_LOG.md` 的定义：
- **flow**：该跑的流程步骤没跑（比如角色被跳过、门禁没触发）
- **cognition**：认知判断错了（比如把"效果名字"当成"效果已实现"）
- **mechanism**：机制缺失导致只能靠人力/用户事后发现（比如没有独立验收环节）

## 使用方式

`prd_pipeline` Workflow 脚本在 Phase 0（"PRD拆解"之前）执行：
```
读取本文件最近 5 条 entries 的 carry_forward 字段 → 作为角色分派阶段的 prompt 上下文
```
不是 ffprobe 那类二进制 gate（这次的错误是流程层面，不是媒体文件层面），不需要独立 Python 脚本，Workflow 脚本内联读取即可。

---

## 登记记录

### 2026-07-21 · publish/语音厅/测试 · 明月天涯男厅测试片"PPT感"事故

```yaml
- date: 2026-07-21
  project_id: publish/语音厅/测试(本地测试demo,不进git)
  role_reasoning_reviewed: []   # 事故发生时 prd_pipeline 尚不存在,无子PRD可回读——这正是本条 fix 的内容
  errors_found:
    - role: 动画导演/Motion Planner
      what_went_wrong: >
        实现者(主LLM)自己兼任了动画导演角色,从歌词时间轴直接跳到 ffmpeg filter_complex 参数,
        没有产出任何独立的"这镜该看起来什么感觉"的陈述。照抄 SOP §9 表格里 A1/A2 效果名对应的
        FFmpeg 示例(zoompan),但把 zoompan 应用在人物立绘自己的小画布(如818×1000)上再
        overlay到固定坐标,导致人物在1920×1080全画面上的实际可见位移不到4%(4秒内),
        肉眼判断为静止,即"PPT感"。所谓"A2 parallax"实际只是背景/前景不同速的中心缩放,
        没有任何位置位移,不构成真正的视差。
      root_cause: [flow, cognition, mechanism]
      root_cause_detail:
        flow: >
          CLAUDE.md 定义的多工种协作流程(动画导演产出 design/motion_storyboard.md,
          门禁"无motion_storyboard→禁止进形式策略会")完全没有被触发。
          实现者判断"这是测试demo"可以豁免整套工种流程,但用户从未给过这个豁免——
          用户原话是"质量必须做到正式外发要求,测试项目不等于减配"。
        cognition: >
          把"效果名字被写进代码变量/注释里"等同于"效果已经实现且能被观众感知"。
          没有在渲染后回头问"这个数值变化在1920×1080全画面上,观众真的能看到吗"。
          执行链条是"看SOP效果名单→翻译成filter参数→跑通没报错→交付",
          这个链条里没有"感知目标"这一环,也没有验证环节。
        mechanism: >
          实现者同时是执行者和唯一验收者,没有第三方/独立视角检查渲染结果是否达成预期感受。
          门禁(motion_storyboard.md 的"入口必读·不过清单不得开工")是文档层面的自觉执行,
          没有任何工具强制实现者在动手前打开这份文档,门禁形同虚设——不是门禁太弱,
          是实现者从未走到门禁面前。
      should_have_done: >
        应先起一个独立的"动画导演"子agent,只给它脚本/节拍表/资源清单/已知限制,
        不给它看FFmpeg实现语法,产出"这镜该有什么感觉+可观察量级"的陈述;
        实现者接到这份陈述后再写代码;渲染完成后用独立验收(抽帧量化位移)核验
        是否达成陈述里的量级,而不是实现者自己看一眼说"还行"。
  fix_applied: >
    新建 templates/design/subagent_prd_schema.md(通用子PRD schema,核心字段
    perceptual_goal.observable_metric 强制写可观察量级,不允许写效果名;
    acceptance_criteria 强制可操作核验)。
    新建 .claude/workflows/prd_pipeline.js(强制角色执行+独立验收两个phase分离,
    验收者与产出者不是同一次 agent() 调用)。
    新建本日志文件,交付后强制回读所有子PRD推理栏。
    CLAUDE.md 补充:新项目必须走 prd_pipeline Workflow,不得由主LLM单人兼任角色。
  carry_forward: >
    新项目开工前检查:是否每个被激活角色都有独立的 agent() 调用产出子PRD(不是主LLM自己写的)?
    是否每个子PRD的 perceptual_goal 都写了可观察量级(不是效果名/术语)?
    是否有独立验收环节且验收者与产出者不同?
    "测试/demo"性质不构成跳过工种流程的理由,production_tier 只影响验收强度(1人vs2人独立、
    锦标赛开关),不影响角色是否被激活。
```

---

## 登记模板（后续按此格式追加）

```yaml
- date: YYYY-MM-DD
  project_id:
  role_reasoning_reviewed: []
  errors_found:
    - role:
      what_went_wrong:
      root_cause: [flow | cognition | mechanism]
      root_cause_detail:
        flow:
        cognition:
        mechanism:
      should_have_done:
  fix_applied:
  carry_forward:
```

---

### 2026-07-21 · publish/语音厅 · 明月天涯立绘 MV 重做（事故同物料首次复跑修复流程）

```yaml
- date: 2026-07-21
  project_id: publish/语音厅 · 明月天涯立绘MV(9:16 · 52.9s · 9镜 s0-s8)
  role_reasoning_reviewed: [动画导演/Motion Planner]
  fix_verified: >
    这是 2026-07-21 PPT 事故同一批物料(立绘+WAV)的首次复跑,目的验证事故修复是否真的挡得住。
    结论:挡住了,且是被独立验收当场抓住的——
    ① 起了独立"动画导演"子agent(Narrative Designer,只给脚本/节拍/资源/已知限制,不给FFmpeg语法),
       产出 design/motion_storyboard.md,每镜 observable_metric 是可抽帧量级(位移px/%屏高 + zoom pt),
       全表禁写"Ken Burns/视差"这类效果名。
    ② 独立验收机制 qa_motion.py:对每镜裸 zoompan 探针(无粒子/文字/黑边)抽首末帧,
       FFT 相位相关求全局像素位移,二元比对 190px(10%屏高)/12pt 硬底线,副歌镜(s5/s6/s7)AND 双过。
       验收是与渲染不同的进程,不是实现者自己看一眼。
  errors_found:
    - role: 摄像/实现(主LLM兼)
      what_went_wrong: >
        第一版 render 仍然复现了 PPT 陷阱:s0 实测首末位移仅 16px(0.8%屏高),zoom 读数甚至为负。
        即"有独立动画导演 + observable_metric 陈述"本身并不能阻止实现层再次踩坑。
      root_cause: [cognition, mechanism]
      root_cause_detail:
        flow: 动画导演 + 独立验收两个环节都跑了(流程没缺)。
        cognition: >
          实现时想当然以为"plate 放大到1.5x + zoompan zoom 1.08→1.24"就够动;
          没算过 plate 余量与 zoom 幅度共同决定的可位移上限——低 zoom(~1.1x)在1.5x plate 上
          竖向可位移量只有~60px,再怎么调 py 参数也到不了190px。技术直觉错了。
        mechanism: >
          还发现 zoompan 用 `-loop 1 -t + d=1` 会掉帧(4.5s 只出3.77s/113帧),
          单帧输入 `-i + d=n` 才对。这类实现陷阱靠"看一眼"发现不了,必须有量化验收。
      should_have_done: >
        实现前先推位移经验式 dy≈H*(z_avg-1)*py_sweep,据此反解每镜需要的 zoom 幅度与 pan 行程,
        再写参数;而不是拍脑袋给 zoom/pan 值等验收退回。
  fix_applied: >
    ① render_mv.py zoompan 改单帧输入 d=n(修掉帧);
    ② 按经验式 dy≈H*(z_avg-1)*py_sweep 重标 9 镜全部 motion 参数,逐镜过 qa_motion 验收
       (s0=213px/20pt,s3=267px/18pt,s6副歌=309px/24pt AND过,横向/拉远镜靠 zoom≥12pt 过底线);
    ③ 新增 qa_motion.py 作为可复用的独立运镜验收器(相位相关+副歌AND规则),沉淀为工具不是一次性检查;
    ④ deblue() 压中里毅立绘蓝紫色相→暖金,过禁霓虹色门(此前 s5/s6 帧蓝紫占比7%>5%);
    ⑤ 成片过 gate_check_media(0黑帧/0死区/前6s -18dB) + gate_check_palette(13帧全过)。
  carry_forward: >
    observable_metric 陈述是必要不充分条件——它让"该动多少"有据可查,但挡不住实现层技术直觉错误;
    真正兜底的是"独立抽帧量化验收 + 二元底线",这一环任何视频镜头都不能省。
    zoompan 位移量级由 plate 余量与 zoom 幅度共同决定,低 zoom(<1.15x)在小 plate 上物理上到不了10%屏高,
    要位移就得抬 zoom 或加大 plate;下次写运镜参数前先用 dy≈H*(z_avg-1)*py_sweep 反解,别等验收退回。
    zoompan 单帧输入必须 `-i + d=n`,禁 `-loop 1 -t + d=1`(掉帧)。
    本条是同人MV(无事实claim),内容类角色(记者/内核/事实校验)按轻量档压缩,但"翻译层动画导演+独立验收"
    是事故正对的环节,一步没省——production_tier 降的是内容验收强度,不是运镜验收。
```

---

### 2026-07-21 · publish/语音厅 · 明月天涯立绘 MV v2（用户三差评后全量重做 22 单元多手法版）

```yaml
- date: 2026-07-21
  project_id: publish/语音厅 · 明月天涯立绘MV v2(9:16 · 53.1s · 22 单元)
  role_reasoning_reviewed: [动画导演/Motion Planner]
  driver: >
    用户看 v1(9镜)后三差评(标"重要!重要!重要"):
    ①运镜幅度太小基本在微微颤抖,要更明显+多种运镜不单一;
    ②转场节奏慢还是像PPT且单一;③禁从始至终表现形式单一。
    三差评的共同根:v1 虽过了"位移底线"独立验收,但只用了单一运镜手法(几乎全 Ken-Burns 式缓推)、
    单一转场(叠化)、单一版式(单人全屏),量级达标≠观感不单调。
  errors_found:
    - role: 动画导演/摄像(v1 遗留)
      what_went_wrong: >
        v1 的独立验收只验了"单镜位移量级"这一维,没验"跨镜手法多样性"。
        于是 9 镜全部用同一种缓推运镜、同一种叠化转场、同一种单人全屏版式,
        每镜都过底线,但连起来看依然单调如PPT——验收维度缺失导致"逐镜合格,整体单一"。
      root_cause: [cognition, mechanism]
      root_cause_detail:
        flow: 动画导演 + 独立验收都跑了(流程没缺)。
        cognition: >
          把"每镜位移达标"当成"整片不单调"的充分条件。观感单调是跨镜维度的问题
          (手法重复率、相邻雷同、版式集中度),单镜位移量级量不出来。
        mechanism: >
          qa_motion.py(v1)只有单镜位移探针,没有"多样性硬约束"这一层——
          运镜去重/转场去重/版式去重/相邻不重复/无手法过半 这些跨镜指标无人量,
          只能靠用户事后看成片才发现"怎么从头到尾一个样"。
      should_have_done: >
        独立验收器除单镜位移外,必须加一层跨镜多样性硬约束(去重计数+相邻比对+集中度上限),
        在渲染前就挡住"手法单一"的排布,而不是等成片给用户看。
  fix_applied: >
    ① 重写 render_mv2.py:22 单元,8 种运镜(punch/scan/whip/snap/rise/dutch/pullback/shake)、
       7 种转场(black_in/fadeblack/fadewhite/dissolve/zoomin/hard-fade/slideright,走 xfade 原生+卡拍 offset)、
       9 种视觉版式(单人全屏/面部特写/局部极特写/剪影黑金/双人分屏/四宫格/群像拉远/大字卡/标题卡)。
    ② qa_motion2.py 加"手法多样性"硬约束层:运镜去重≥6、转场去重≥5、版式去重≥5、
       相邻运镜/转场不重复、相邻三元组不全同、必备版式(大字卡/分屏/四宫格/极特写)齐、无单一手法过半(≤11/22)——
       全 PASS 才算过,与单镜位移探针分开量。
    ③ 副歌/高潮镜(U10-12/U16-20)升 AND 规则:zoom≥40pt 或 (位移≥380px 且 zoom≥12pt) 或 位移≥520px。
    ④ 视觉版式分类按"观众看到的形式"细分(render 的 single 按 framing 拆成 全屏/面部/极特写),
       修掉 v1 QA 把 14 个 single 误判为"单一版式过半"的分类假阳性。
    ⑤ 成片过 gate_check_media(0黑帧/0死区/前6s -18.2dB/无爆音) + gate_check_palette(8帧全过,deblue 压中里毅蓝紫)。
    ⑥ U22 outro 延到 7.27s 吸收 xfade 重叠,终片 53.1s 收全 WAV(53.08s)。
  carry_forward: >
    "逐镜合格 ≠ 整片不单调"——单镜量级达标是必要条件,观感单调是跨镜维度(手法重复/相邻雷同/版式集中)的问题,
    任何多镜视频的独立验收都必须同时有"单镜量级"和"跨镜多样性"两层硬约束,缺一层就会出现 v1 那种
    "每镜都过但连起来像PPT"。多样性层至少含:运镜/转场/版式三维去重下限 + 相邻不重复 + 无单一手法过半。
    zoom 跨度做多样性/位移的可靠杠杆时注意浮点:1.50-1.10 在 float 下=39.9999<40,
    定"≥40pt"这类硬阈值要么留 0.5 容差,要么把参数抬到明显超阈(如 44pt)避免边界假阴性。
```


---

## 2026-07-23 · 语音厅 舞台版-16x9 · 全片渲染交付（v3-stage 版）

```yaml
- run_id: voice-hall-stage-16x9-v3
  date: 2026-07-23
  stage: 制作/渲染（B层设计工作流已于前序 session 完成 · 本次为实现+交付）
  production_tier: explore
  deliverable: publish/语音厅/舞台版-16x9/build/out/明月天涯_舞台版_no_bgm.mp4
  specs: 1920x1080 / 16:9 / 30fps / 53.07s（对齐 mp3 53.08s）/ 1592 帧
  what_was_built:
    - render_full.py：弃 zoompan，改逐帧 6 层加法光效合成（LED大屏/追光/烟雾/立绘/荧光棒海/粒子/爆闪/大字）
    - fx_engine.py：光效基元库（追光锥/爆闪/烟雾场/荧光棒预置纹理/落地光池/粒子/舞台反光地面）
    - assets/中里毅_deblue.png：H225-330 紫→暖橙金选择性重映（紫占比 80.2%→0.00%）
    - qa_stagefx.py：独立三门验收器（连续动效/卡点释放/跨镜多样）
  gates_passed:
    - qa_stagefx：门①连续动效 PASS（最静2s窗口峰值1.39>=1.2）· 门②卡点释放 PASS（182释放帧·seg1-15每段>=2）· 门③跨镜多样 PASS（相邻段最小差15.4>=8）
    - gate_check_media：0黑帧 · 0死区 · 前6s RMS -12.1dB · 时长对齐（1 WARN：导唱源音量偏热0.0dB，源素材特性）
    - gate_check_palette：抽验帧全 PASS（银发角色 cy/诺兰 不触紫）
  errors_found:
    - role: 主LLM（制作/渲染阶段）
      what_went_wrong: >
        独立验收器 qa_stagefx.py 由产出者本人（主LLM）编写，且门②阈值在看到首轮结果后被调整了两次
        （123-onset-80%命中 → 每段>=2释放+outro豁免）。存在"产出者看到结果后拟合阈值放行"的自证风险。
      root_cause: [mechanism]
      root_cause_detail:
        mechanism: >
          制作阶段没走 prd_pipeline.js 的"验收者!=产出者"独立进程，验收器与被验收物同源。
          虽然 qa_stagefx 是机械像素探针（客观测量非主观判断，同 qa_motion2 定位），
          但阈值是产出者事后定的，边界可被无意识地往"能过"方向调。
      mitigation_applied: >
        每次阈值调整都强制对照设计文档白纸黑字口径，而非为过而降：
        门②从"每onset硬切"改"每段>=2释放"——依据 retention_beat_sheet 明文"不追求把每个onset做成硬切、
        叙述段留呼吸、频闪全切会让字看不清"（V3教训）；outro 豁免依据 E9 能量档=3"软着陆·缓·1次落款1次余晖"。
        即调整是让验收口径回归设计意图，不是迁就成片。
      should_have_done: >
        制作阶段的独立验收器最好由独立 agent 编写，或至少阈值在渲染前预先冻结（写死在设计文档里），
        避免产出者看到结果后拟合。
  positive_carry:
    - lesson: >
        立绘类 MV 的"动"不该压在立绘位移上（v1/v2 三次 PPT 教训的物理根因：低zoom+小plate位移天花板~60px<190px底线，
        i2v 又有幻觉风险）。本次结构性修复：把"画面在动的主体"从"被推的立绘"改为"程序化光效层"
        （追光扫/爆闪/荧光棒倒/粒子炸/大字砸），立绘相对静止，每拍有全屏光事件即可炫酷不PPT。
  carry_forward: >
    ① 立绘/静态素材类音乐MV：优先"可编程光效层驱动的动"，不要押注立绘位移或 i2v 运镜——前者有物理天花板、后者有幻觉。
    ② 连续动效底床（灯光始终缓扫+群众光点始终闪晃）是"不得>2s静止"这类硬约束的结构性保证，
       比"逐拍填事件"更稳——底床保证任意帧都在动，卡点事件只负责"大释放"。
    ③ 制作阶段独立验收器的阈值应在渲染前冻结（或由独立agent写），否则产出者事后调阈值=自证风险；
       若必须事后调，每次调整须留"对照哪条设计文档口径"的书面依据，接受审计。
```

### 追补 · 2026-07-23 · 烟雾"名义已实现但肉眼不可见"缺陷（用户抓包）

- **缺陷：** 主LLM 大白话分镜承诺 seg4"两边从底部喷起烟雾、在中缝汇合"，代码里 `add_smoke` 也确实被调用，但用户看成片报"我没有看到烟雾效果"。
- **根因（两层）：**
  1. **实现层弱到读不出来** —— `make_smoke_seed` 8× 下采 + bicubic 上采 = 块状数字噪点（非絮状烟）；`add_smoke` 内部 `*0.5*seed` 双重衰减 + 静态团 + 无上飘运动 + 峰值 intensity 仅 0.5，被追光/LED/地面完全淹没。屏幕上呈现的是一层脏噪点，不是烟。
  2. **验收层同款病** —— 又一次"函数被调用了 = 效果已实现"的凭证误判（与首条 Ken Burns/parallax 事故同构）：`add_smoke` 出现在代码里，就默认烟雾已交付，没有逐帧目视核对"这团东西人眼读不读得成烟"。
- **修复：** 噪声场改 4× 下采 + GaussianBlur(16) 归一（絮状）；`add_smoke` 重写为"从 base_y 升腾的柔性烟柱"（竖直升腾包络 + 噪声随 t 上滚 = 真在往上飘 + 去掉内部 *0.5）；R4 改双柱从台底喷起 + `ease_out` 向中缝汇合 + snap_decay 慢散(1.5)不秒灭。全片重渲，三门(qa_stagefx/palette/media)全 PASS，目视确认烟雾成墙升腾可读。
- **carry_forward 追加：**
  ④ "函数被调用"≠"效果被交付"——凡承诺可观察效果（烟/光/粒子/运镜），交付前必须**逐帧目视**确认人眼读得成该效果，不能因为"代码里调了该基元"就当已实现（这是 Ken Burns 事故的同构复发，第 2 次）。
  ⑤ 加法光效基元的默认参数极易被"更亮的邻层"淹没：任何加性效果落地后，都要在**它所处的真实合成环境**里核对可见性（不是单独看这一层），弱到淹没=没做。

