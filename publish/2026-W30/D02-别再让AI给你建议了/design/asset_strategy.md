# 素材策略 · T041

> 状态：draft · **事实可以生成，但来源不能伪造**。

## 素材来源类型

`source_type` 仅允许 `real_api_output`、`generated_fact`、`synthetic_visual`、`cc0_sfx`。真实输出必须可回到原始证据；生成计划必须披露；合成容器不能冒充真实后台。

## 镜头素材计划

| 镜 | 素材 | source_type | 来源 | 像素规则 | 误读风险 |
|---:|---|---|---|---|---|
| 1 | 两条匿名回答路径 | real_api_output | `insights/premortem_ab_evidence.md` | 逐字引用、隐藏问法标签 | 不能暗示B更准 |
| 2 | 辞职代运营计划 | generated_fact | 实验固定计划 | 常驻“测试案例” | 不得冒充本人经历 |
| 3 | A组三风险 | real_api_output | 同上 A组两轮 | 只做摘录并保留来源 | 不得贬低A |
| 4 | 失败原因到依据的结构 | real_api_output | 同上 B组两轮 | 明示两轮具体原因/排序不同，依据可为已给事实或信息缺口 | 不得合成固定三死因 |
| 5 | 封条与证据签 | synthetic_visual | 自绘 | 标“两轮实测”与窄结论 | 不做胜率图 |
| 6 | 事前验尸Prompt | real_api_input | 实验脚本 | 全文可读 | 不截成口号 |
| 7 | 计划验尸票 | synthetic_visual | 自绘 | 明显是互动控件 | 不冒充平台UI |

人称实验只作为否决证据，不进主叙事。SFX 只用项目 catalog 中有本地文件和许可记录的 `cc0_sfx`，禁止合成占位。

## 允许 AI 生成的事实

只允许 `generated_fact` 的虚构测试计划和无事实含义的排版占位，且必须同时显示“测试案例”。不得声称为真实客户、真实后台、真实成交或真实用户原话。

## 不得声称

不得声称事前验尸更准、更凶、能预测真实失败；不得声称人称替换有效；不得把 `synthetic_visual` 时间线当作真实概率模型；不得把自绘证物容器说成商业产品界面。

## asset_log

生产时写入 `assets/asset_log.md`，逐镜记录 source_type、来源路径、原文哈希、许可和最终是否使用。缺记录的素材不得外发。
