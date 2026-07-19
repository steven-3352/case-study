# 素材策略 · W30D03

事实可以生成，但来源不能伪造。

## 素材来源类型

`source_type`: `real_api_output`、`real_private`、`generated_fact`、`synthetic_visual`、`cc0_sfx`。真实 A/B 输出和 raw export 是事实源；轨道与闸门只是解释容器。

## 镜头素材计划

| 素材 | source_type | 用途 | 风险控制 |
|---|---|---|---|
| 双轮 A/B 首答 | real_api_output | 首屏/边界 | 显示响应短哈希或“双轮”，不得改写成效用结果 |
| 三步九问 | real_private | 三关 | 来自 7/15 Prompt 草案，标“流程草案” |
| 第十问 | generated_fact/编辑补充 | 验收门 | 明示“编辑补充·待验证” |
| 轨道、闸门、出口票 | synthetic_visual | 解释 | 不能冒充产品 UI 或实验后台 |
| 音效 | cc0_sfx | 开关/通过 | 只用 catalog 本地文件 |

## 允许 AI 生成的事实

只允许排版占位和明确标注的编辑补充。不得声称 Prompt 帮真实用户找到方向，不得声称真人行动结果。

## 不得声称

`generated_fact` 与 `synthetic_visual` 不得冒充真实用户原话、真实后台或平台数据。无真实客户、成交和效果数字。

## asset_log

render 前在 `build/asset_log.md` 记录每镜来源路径、哈希、source_type 与进入像素文字；缺项不外发。
