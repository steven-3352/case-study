---
name: project_mv-agent-workflow-contract
description: mv-agent 线 G 执行照 WORKFLOW.md 契约,别通读 conductor 源码烧 token
metadata:
  type: project
---

跑 mv-agent 生成式六步流水线(线 G)时,**执行契约在 `mv-agent/WORKFLOW.md`,读这一份就够,禁止再通读 `conductor/` / `src/mvstudio/` 源码**。契约已固化:控制面(全部 6 条 CLI 命令)· 状态机 + 调度主循环 · 前置条件(`.env` 按步骤对照)· 每步(跑前念白=脚本+用途 / 输入 / 命令 / 产物用途 / Codex 校验 / 合理建议 / 失败码)· 一屏速查。

**Codex 职责边界(WORKFLOW.md 顶部「职责边界」节)**:只做三件——① 流程控制(发 `init`/`run`/`ok`/`reject`)② 必要结果校验(只看"停在 awaiting / 产物非空 / 读一次人可读报告",不解析 json 内部、不打开图/播视频判断质量)③ 合理建议(命中信号才提醒)。红线:不读源码、不改底层、不绕过 CLI 直接调工具函数、不把命令/错误栈甩给用户。

**分工**:`WORKFLOW.md` = 执行契约(机器面)· `AGENTS.md` = 对用户的话术/人格(顶部已加指针)· 路线分流(线 G 生成式 vs 线 P 程序化)见 [[project_mv-two-line-dispatch]]。

**Why:** 之前 Codex 每次跑流水线都要翻 `conductor/` 七八个源文件才敢发命令,烧 token 且易误判。把 I/O、命令、校验点、失败码一次性固化成契约,Codex 只当调度器 + 校验器 + 建议者,不当实现者。

**How to apply:** 命中"做片"且判定为线 G → 直接读 `mv-agent/WORKFLOW.md` 按主循环调度,不 grep/read conductor 源码。用户要改流水线文案(用途/产物说明)→ 改 `conductor/pipeline.py` 的声明式数据,不在对话里临时编。

关联:[[project_mv-two-line-dispatch]](先分派再进流程)· [[project_lyrics-shared-core-convergence]](线 G 核心已收敛进 src/mvstudio)。
