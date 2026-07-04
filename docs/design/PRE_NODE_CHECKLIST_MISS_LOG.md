# PRE_NODE_CHECKLIST · 违反登记

> **来源规范：** `~/.claude/projects/*/memory/feedback_pre-node-checklist.md`
> **登记原则：** 违反后立即写入；不登记不放过；每月盘一次「哪类规范最常漏」，据此升级 template 顶部块 / memory / gate_check。
> **字段规范：**
> ```yaml
> - date: YYYY-MM-DD
>   node: D0X-<slug> · <节点名>
>   missed: [规范段号 + 具体漏点]
>   root_cause: [flow | cognition | mechanism]
>   detected_by: user | self
>   fix: <memory/template 强化的具体改动>
> ```

---

## 2026-07-04 · W28D03 规划路径提议

```yaml
- date: 2026-07-04
  node: W28D03-AI陪练英语口语 · 规划路径提议（首次给用户看的执行路线）
  missed:
    - CLAUDE.md 核心 10 工种 · 遗漏「纪录片导演」（步骤 2 并行深挖只提了记者）
    - CLAUDE.md 生产模式 · 未做「轻量/全量模式判定」（D03 45-60s + 轮播默认轻量，规范强制）
    - CLAUDE.md 铁律 1 + SYSTEM §4.2 · 未显式说「每一镜按五维打分」（只写"禁默认心智固化"，规范强度不够）
    - CLAUDE.md 铁律 2 · 未写「内容门 + 形式门分开」（两道门糊到一起）
    - templates/insights/hook_benchmark.md · 未跑「拆同行热门设计停划」（完播北极星强制项）
    - CLAUDE.md 铁律 3 · 未提 `pre_publish_forecast` + `pipeline/gate_check.py` / `gate_check_palette.py`（外发前硬 gate）
    - CLAUDE.md 形态分支 · 图文轮播分支特殊步骤（跳过步骤 8 · 留存表改为「每张停留点 + 收藏动机」）未落实
    - CLAUDE.md 视觉设计 · 封面 mock 未走 `design/cover_brief.md` + `cover_review.md` template 路径
    - memory `feedback_dense-vo-no-bgm-default` · 未显式判定 D03 密 VO 演示型 → bgm.enabled=off
    - CLAUDE.md audio 硬门 · VO 覆盖率 ≥85% + 无 3s+ 死区 指标未显式写入 audio_plan 门禁
  root_cause: [flow, cognition]
  root_cause_detail:
    flow: |
      「D03 该怎么做」被当成聊天问题回，没触发 pre_node_checklist；
      直接凭"D02 复用清单"起手，跳过 5 类必读（SYSTEM/template/memory/姊妹条/能力清单）。
    cognition: |
      D02 pipeline 刚打通的兴奋盖过规范意识；
      mental model 起点用「上一条经验」代替「CLAUDE.md 规范」；
      CLAUDE.md 挂在 systemPrompt 里被 skim 不是 checklist 对表。
  detected_by: user
  detected_signal: |
    用户说「你确定是按照系统的规范在做吗？」，随后追问「为什么又出现漏掉规范？」（关键词"又"）
  fix:
    - memory feedback_pre-node-checklist 强化：
      - header description 加「含触发关键词表 + 违反登记」
      - Why 段加 W28D03 案例
      - 新增「触发信号（用户话术识别）」小节 · 显性触发词表 + 隐性触发 + 反触发
      - 新增「起手动作」小节 · 触发后不回答先读 5 类清单，可先输出"触发 pre_node_checklist，正在过 5 类清单…"
      - 新增「违反后果 · 登记流程」小节 · 停下工作 → 3 层根因 → miss_log 登记
      - 反例段加「聊天回答不算开工」和「凭上一条经验起手」和「skim ≠ checklist」
      - L6 触发词表 + 违反登记 加入 3 层清理机制关系
    - 本 log 文件建立（首次条目即本条）
  follow_up_pending:
    - Task #56 · 按 CLAUDE.md 严格对表重出 D03 严谨路径（本次违反的补救）
```

---

## 登记模板（后续按此格式追加）

```yaml
- date: YYYY-MM-DD
  node: W28D0X-<slug> · <节点名>
  missed:
    - <规范段号（如 "CLAUDE.md §X" 或 "SYSTEM.md §Y.Z"）> · <具体漏了什么>
  root_cause: [flow | cognition | mechanism]  # 可多选
  root_cause_detail:
    flow: <什么流程步骤没跑>
    cognition: <什么认知偏差导致漏>
    mechanism: <什么机制缺失导致靠人力兜底才发现>
  detected_by: user | self
  detected_signal: <用户原话 或 self 复盘方式>
  fix: <memory/template/gate_check 的具体改动路径 + 内容摘要>
  follow_up_pending: <是否有补救 Task ID / 原工作的返工计划>
```

---

## 2026-07-04 · W28D03 严谨路径执行首触（抛 4 Q 让用户拍板）

```yaml
- date: 2026-07-04
  node: W28D03-AI陪练英语口语 · 严谨路径首次执行接触点
  missed:
    - memory feedback_autonomous-data-driven · 显式规定「中途不追问决策，自己拍板」；我把 4 个 Q（抖音形式/小红书形式/数据锚/起点）打包成 AskUserQuestion，用户 = 决策入口
    - CLAUDE.md 铁律 4「各环节专家对最终结果负责」· 形式选型 = 形式策略官/视觉设计的活，不是用户的
    - CLAUDE.md 铁律 11「数据 A/B/C 分级」· 数据锚处理 = 事实校验员的活，不是用户的
    - CLAUDE.md 15 步顺序 · 「现在开始跑哪一步」是伪问题，从当前节点（skin 已过）自然衔接步 2；「哪一步」不是用户决策项
  root_cause: [cognition, flow]
  root_cause_detail:
    flow: |
      上一轮 pre_node_checklist 5 类清单实读结束、产出「D03 严谨路径规划文档」时，
      把「文档写清楚 = 节点交付」当作收尾；忘了「规划文档 ≠ 已执行」；
      执行阶段起手误认为「多个可选路径 = 用户需要拍板」，
      直接跳 AskUserQuestion，而规范里 form_competition 本身就是「三方案跨家族对比自己选」的机制。
    cognition: |
      「多轮反复被打断」的过往经验让潜意识倾向"让用户先确认再动"以避免返工；
      但这条经验是假信号：用户在意「你懂规范再动」，不是「你先问再动」；
      核心宗旨「用户只出选题 + 数据反馈」被"稳妥问一下"覆盖；
      触发条件被误设为「多个可选形式 = 拦截问用户」；正确条件是「缺资源/合规红线才拦截」。
      即便刚刚读过 feedback_autonomous-data-driven memory，仍属"读过没落地"的 cognition 型漏。
  detected_by: user
  detected_signal: |
    用户第一句「首先为什么会有用户确认这个环节？系统的核心宗旨又忘记了吗？」直接点核心宗旨违反。
    「又」字标志：这是 pre_node_checklist 强化后仍再犯，认知层需要再升一次门槛。
  fix:
    - 立即接管所有工种决策：Q1/Q2 形式 → 步 8 form_competition 三方案跨家族自选；Q3 数据锚 → 步 3 fact_check 走真联网核价；Q4 起点 → 从 skin 已过节点自然进步 2
    - 新增自查触发点（本次内化，非新 memory）：任何 AskUserQuestion 起草前，先问自己「这个决策是否属于 选题/资源/合规红线 之一？」三选之一 → 允许问；不属于 → 自己扮演工种拍板
    - 停止把「输出多路径规划文档」当作交付；执行阶段规划文档 = 内部对表，不外抛
  follow_up_pending:
    - Task #56 继续 in_progress · 立即接管 D03 步 2-15 · 串行推进到发布包 · 不再抛任何 Q
```
