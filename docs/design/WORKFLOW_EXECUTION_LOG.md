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
