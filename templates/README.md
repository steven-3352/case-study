# templates/ · 工种产出格式（不是成片套路）

> 系统全貌：[docs/SYSTEM.md](../docs/SYSTEM.md) · Agent 执行：[CLAUDE.md](../CLAUDE.md)
> 每条选题必须基于自己的洞察包、节拍表、分镜单独定表达；禁止克隆上一条的骨架、画面或 catalog 拼盘。
> **实现选型：** 参见 `docs/SYSTEM.md §4.2 候选实现清单`；OpenMontage 与 P001/P002/P004/P005-P007 **同级候选**，无默认顺序。

## 三类东西，别混

| 叫什么 | 路径示例 | 是什么 | 不是什么 |
|--------|----------|--------|----------|
| **工种产出格式** | `insights/`、`retention_beat_sheet.md`、`audio_plan.yaml`、`design/*` | 各工种交作业的**文档结构**（填空、门禁） | 成片画面、口播套路 |
| **渲染场景** | `pipeline/*/templates/*.html` | Playwright 截帧用的 **HTML+GSAP 画布壳**；可新建或为本条重写 | 每条选题默认复用的「标准模板」 |
| **形式词汇** | `assets/formats/catalog.yaml` | 分镜时描述「这类观感」（chaos、对比、漫画…） | 指定必须用哪个 `.html` 文件；每条 format 的 `pipeline_candidates` 只是**当前可选实现之一**，不是唯一 |
| **视觉语言参考** | `assets/design-md/`、`design/design_language.md` | 从 DESIGN.md 萃取本条色板、字体、组件、禁用项 | 品牌仿冒、整站照抄 |
| **候选实现能力** | `pipeline/`（原生）· `integrations/`（外部制作插件如 OpenMontage/Grok video/GPT-image-2）| **同级候选池**，无默认顺序 | 把 P001/P004 当"主路径"，把 OpenMontage 当"备选" |

## 正确流程

```
洞察包定稿 → 节拍表 → 分镜（为本条定画面隐喻与形式组合）
  → 视觉语言策展师写 design_language.md（token / 组件 / 禁用项）
  → **motion_storyboard.md（动画导演 · 单跑不双评 · 判 WaytoAGI/七七/Vibe Motion 风格 + 9 字段逐秒分镜）**
  → form_competition（3 方案不得同家族）+ openmontage_brief（每条必判 enabled/disabled/blocked）
  → 按 SYSTEM §4.2 五维打分选实现（原生 pipeline / OpenMontage / GPT-image-2 / 真实素材 平权比较）
  → storyboard.yaml 引用场景 + 注入本条 data
  → 出图后按留存铁律检查可读性
```

OpenMontage 走插件目录：

```
publish/{week}/Dxx-*/openmontage/
```

回流验收通过前，不得替换 `douyin/video.mp4`。

## 反例（拒稿级）

- 从上一条复制分镜，只改几个字
- 用 `02_pain + 06_compare + 08_cta` 标配三连交差
- 同一 HTML 场景占全片 >40% 或同场景重复多镜
- 脚本 90+ 但画面与上条同质仍外发
- **候选池预先缩水**（3 方案都是 P001 变体或都是 P004 变体；OpenMontage/Grok video/GPT-image-2 未被并列考虑）
- 未跑 `openmontage_brief.md` 即进 storyboard

详见：`CLAUDE.md` 反例 · `templates/design/scorecard_rubric.md` · `docs/design/SCRIPT_REJECT_LOG.md`
