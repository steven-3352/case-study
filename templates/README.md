# templates/ · 工种产出格式（不是成片套路）

> 系统全貌：[docs/SYSTEM.md](../docs/SYSTEM.md) · Agent 执行：[CLAUDE.md](../CLAUDE.md)
> 每条选题必须基于自己的洞察包、节拍表、分镜单独定表达；禁止克隆上一条的骨架、画面或 catalog 拼盘。

## 三类东西，别混

| 叫什么 | 路径示例 | 是什么 | 不是什么 |
|--------|----------|--------|----------|
| **工种产出格式** | `insights/`、`retention_beat_sheet.md`、`audio_plan.yaml`、`design/*` | 各工种交作业的**文档结构**（填空、门禁） | 成片画面、口播套路 |
| **渲染场景** | `pipeline/*/templates/*.html` | Playwright 截帧用的 **HTML+GSAP 画布壳**；可新建或为本条重写 | 每条选题默认复用的「标准模板」 |
| **形式词汇** | `assets/formats/catalog.yaml` | 分镜时描述「这类观感」（chaos、对比、漫画…） | 指定必须用哪个 `.html` 文件 |

## 正确流程

```
洞察包定稿 → 节拍表 → 分镜（为本条定画面隐喻与形式组合）
  → 需要新画面则写/改渲染场景或走 P002/真实素材
  → storyboard.yaml 引用场景 + 注入本条 data
  → 出图后按留存铁律检查可读性
```

## 反例（拒稿级）

- 从上一条复制分镜，只改几个字
- 用 `02_pain + 06_compare + 08_cta` 标配三连交差
- 同一 HTML 场景占全片 >40% 或同场景重复多镜
- 脚本 90+ 但画面与上条同质仍外发

详见：`CLAUDE.md` 反例 · `templates/design/scorecard_rubric.md` · `docs/design/SCRIPT_REJECT_LOG.md`
