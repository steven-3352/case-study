# 素材策略 · W30D04

事实可以生成，但来源不能伪造。

## 素材来源类型

`source_type`: `real_private`、`real_code_inspection`、`generated_fact`、`synthetic_visual`、`cc0_sfx`。

## 镜头素材计划

| 素材 | source_type | 进入像素 | 边界 |
|---|---|---|---|
| journal 路径与 commit | real_private | 脱敏路径+真实短提交 | 不冒充公开产品证据 |
| 飞书“没有记录” | real_private | 原句情景还原 | 标“真实日志摘录”而非截图 |
| build_system 四项读集 | real_code_inspection | 四节点逐项显示 | 不改写成所有 bot 通用 |
| X 光路径/端口/探针 | synthetic_visual | 解释层 | 不能冒充真实后台 |
| SFX | cc0_sfx | 扫描/断点 | catalog 本地文件 |

## 允许 AI 生成的事实

只允许不承载结论的路径占位；`generated_fact` 不得声称真实客户、真实后台、真实成交或平台机制。

## 不得声称

不得把 synthetic_visual 说成真实系统界面，不得声称消费级 AI 都使用文件式记忆，不得把模型回复当代码日志。

## asset_log

`build/asset_log.md` 记录 raw export 行号、脱敏规则、source_type、哈希和最终像素文本。任何真实项目名、凭证、绝对路径必须脱敏。
