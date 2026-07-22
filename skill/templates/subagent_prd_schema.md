# 子 PRD 通用 Schema · subagent_prd_schema

> 位置：`design/subagent_prds/{role_slug}.md`（每个被激活角色一份）
> 时机：由主 LLM 在 `skill/workflows/` 的 PRD 流水线「PRD 拆解」phase 生成，`agent()` 调用时作为 `schema` 参数强制结构化返回
> 目的：修复「感知目标从未被写成独立、可核验的产物」这一事故类型（见 §0）。**任何角色的产出如果不能装进这份 schema，视为未交付。**
> 角色目录唯一事实源：`skill/roles/registry.yaml` · 质量门：`skill/quality/quality_registry.md`

## 0. 这份文档解决什么问题（不要跳过这段直接抄字段）

一次典型事故：实现者（主 LLM）自己兼任了「动画导演」角色，从需求直接跳到实现代码，效果名（Ken Burns / parallax）被当成了「已实现」的凭证，实际渲染结果人物位移不到画面宽的 4%，肉眼不可见。复盘发现两个洞：
1. **感知目标从未独立存在**——只有效果名字，没有「这镜看起来该是什么感觉、变化量级多大」这句可核验的话
2. **验收者=产出者**——自己写代码、自己看一眼说「还行」，没有独立视角

本 schema 强制堵这两个洞：`perceptual_goal` 字段必须写成可观察量级，`acceptance_criteria` 字段必须是可操作的核验动作；配合 PRD 流水线的「独立验收」phase（验收者与产出者不是同一次 `agent()` 调用，即 `QG-PRD-ACCEPTANCE`），不允许自己验收自己。

> 关联维度：D01 运镜 / D02 动效的「常见踩雷」正是「效果名≠已实现」；本 schema 的 `observable_metric` 是从设计侧堵住该踩雷的第一道地板。基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收。

## 1. 字段规范

```yaml
role:                        # 角色名，对应 skill/roles/registry.yaml 的 name 字段（如"动画导演"，一字不差）
production_tier: explore | lightweight | full   # 继承自项目 content.yaml（见 skill/docs/PROCESS.md §6）

input_received:              # 实际拿到的输入摘要，不是"应该拿到什么"，是"这次真的给了什么"
  resources: []               # 用户给的原始资源（图片/参考视频/脚本/音频……有什么列什么）
  upstream_artifacts: []      # 上游角色的产出文件路径（如 insights/core_message.md）
  known_gaps:                 # 从总 PRD 继承的资源缺口/矛盾（已经问过用户的）
    - gap:
      user_decision:          # 用户怎么决定处理这个缺口的

deliverable:                  # 本角色的实际产出（文字描述或文件路径）

perceptual_goal:              # 核心字段·不允许写效果名/术语，必须是可观察现象+量级
  # 反例（禁止）："Ken Burns 缓推""视差效果""有生命感"
  # 正例（要求）："镜头结束时人物占画面可视宽度应比开始时至少变化 12%，3 秒内肉眼可辨"
  statement:
  observable_metric:          # 怎么量化这句话（数值/百分比/可数的现象），没有量级的感知目标视为无效

implementation_approach:      # 选了什么方式实现
  method:
  why_this_fits_perceptual_goal:   # 这个方式如何达成上面的 perceptual_goal，不能只说"能做"

alternatives_considered:      # 至少 1-2 个替代方案，不要求锦标赛式打分排名，但必须真的想过
  - option:
    why_rejected:
  - option:
    why_rejected:

known_limitations:            # 诚实自曝的局限/bug，允许存在，禁止隐瞒
  - limitation:
    impact:                   # 这个局限会造成什么可观察后果

acceptance_criteria:          # 怎么核验这个产出达标，必须可操作(可读/可抽帧/可脚本量化)，不要求打分排名
  - criterion:
    how_to_verify:            # 具体核验动作，比如"抽 clip 首尾帧，量化人物边界像素位移"
```

## 2. 与现有角色模板的关系（不替代，是外壳）

如果该角色已有独立模板（如 `motion_storyboard.md`、`form_competition.md`、`insights/core_message.md` 等），本 schema **不替代**其内容要求，是在其上补一层「感知目标+实现依据+验收标准」外壳：

| 已有模板字段 | 对应本 schema 字段 |
|---|---|
| `motion_storyboard.md` §2.2 判定依据/不选理由 | `alternatives_considered` |
| `motion_storyboard.md` §3 逐秒分镜"设计目的" | `perceptual_goal`（需补量级，原字段常缺可观察指标——这正是事故的漏洞） |
| `form_competition.md` §5 推荐方案/不选其他方案原因 | `implementation_approach` + `alternatives_considered` |
| `design_language.md` 参考来源+为什么适合 | `implementation_approach.why_this_fits_perceptual_goal` |

没有独立模板的角色（编导/记者/纪录片导演/导演/摄像·视觉/剪辑 + 带货扩展 4 + 出镜扩展 2），本 schema **就是**它们的完整交付格式，不必另写模板。角色是否有独立模板见 `skill/roles/registry.yaml` 的 `output_template` 字段。

## 3. 验收规则（`QG-PRD-ACCEPTANCE`）

- `perceptual_goal.observable_metric` 为空 → 该子 PRD 视为未交付，退回重写，不进入「独立验收」phase
- `alternatives_considered` 少于 1 项 → 视为未认真考虑候选方案，退回
- 独立验收 agent **只读** `acceptance_criteria` + 最终产物，不读 `implementation_approach`（避免验收者被「听起来很专业的理由」说服，只看结果是否达标）
- 验收结果为二元 pass/fail + 具体原因，**不做多方案打分排名**（不锦标赛，符合 `production_tier: explore` 精简原则）
- 验收者 ≠ 产出者（不同 `agent()` 调用）——这是 `QG-PRD-ACCEPTANCE` 的硬约束

## 4. `production_tier` 对本 schema 的影响

| 档位 | 字段要求变化 |
|---|---|
| explore | `alternatives_considered` 可以只写 1 项；独立验收 1 位（非双人） |
| lightweight | 同 explore |
| full | `alternatives_considered` ≥ 2 项且需跨「实现家族」（对应 `form_competition.md` 的候选池完整性铁律 `QG-FORM-COMPETITION`） |

**不因档位变化的字段**：`perceptual_goal.observable_metric`（可观察量级）、`acceptance_criteria`（可操作核验）——这两条是防「效果名=已实现」事故重演的底线，三档一个不少。档位只影响验收强度（reviewer 数、是否走锦标赛），不改变该激活哪些角色（见 `skill/docs/PROCESS.md §6`）。
