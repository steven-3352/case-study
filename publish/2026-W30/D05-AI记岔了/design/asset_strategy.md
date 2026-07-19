# 素材策略 · W30D05

事实可以生成，但来源不能伪造。

## 素材来源类型

`source_type`: `real_private`、`real_code_inspection`、`generated_fact`、`synthetic_visual`、`cc0_sfx`。

## 镜头素材计划

| 素材 | source_type | 用途 | 边界 |
|---|---|---|---|
| journal/commit 回执 | real_private | 证物槽 1 | 脱敏绝对路径与项目名 |
| 旧入口“没有记录” | real_private | 证物槽 2 | 原句摘录，不伪造成截图 |
| build_system 读集 | real_code_inspection | 根因门槛 | 只限当时版本 |
| 写入/升格记录 | real_private | 局部通过证 | 只证明写入升格，不冒充原入口复问通过 |
| QA 台、夹具、尺标 | synthetic_visual | 解释/收藏 | 不冒充系统后台 |
| SFX | cc0_sfx | 盖章/工位 | catalog 本地文件 |

## 允许 AI 生成的事实

允许生成不承载事实的编号、占位和机械容器。`generated_fact` 不得声称真实用户、真实后台、真实成交或真实平台能力。

## 不得声称

不得写“旧 bot 翻遍记录”“AI 自己坦白根因”；不得把 synthetic_visual 当工具日志；不得把本项目验收外推所有产品。

## asset_log

`build/asset_log.md` 记录 raw export 行号、脱敏文本、source_type、哈希、进入像素位置和 CC0 授权；缺一项不外发。
