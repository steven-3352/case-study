---
name: project_lyrics-shared-core-convergence
description: "多端(对话/web/未来端)共享一套核心逻辑;歌词读取+容错对齐已收敛进 src/mvstudio 共享核心,两端都调它,禁止再造平行实现"
metadata:
  node_type: memory
  type: project
  originSessionId: 6c6ea528-33e5-4c3b-becb-fef57f81ebbe
---

case-study 项目铁则:**前端(展示形式)可以各有界面/流程,核心功能代码逻辑必须一套。**对话形式(mv-agent conductor)、web 形式(apps/mv_api + mv_platform)、以后更多端——用户输入相同、期望输出相同,就不允许分开多套实现。共享核心住在 `src/mvstudio/*`,各端只做薄适配壳。

**Why:** 2026-08-05 用户指出我给「歌词→时间码」造了第三套平行实现(conductor/media.py 的容错对齐),此时项目里已有三套:①`src/mvstudio/director/`(strict,web 用)②`mv_platform.application.service._xlsx_lyrics` ③我的 conductor 容错版。用户原话:「对话形式,web形式,只是前端界面不同,但是逻辑是一样的。用户的输入,期望的输出也是一样的。分开多套,不合适。以后还会有更多端(展示形式)。目前两部可以有自己界面流程侧的不同,但是核心功能代码逻辑应该是一套。」用户选了「提升进共享核心」。

**这次收敛的落地(2026-08-05,已合并 main):**

1. **共享核心新增(`src/mvstudio/`)= 唯一事实源:**
   - `director/alignment.py`:`normalize_token`(NFKC+isalnum,原重复 3 处)+ `proportional_entries`(纯容错对齐映射器:文字权威、whisper 只出时间、按字符占比贴合、纯器乐退化均匀铺;随行数收缩的 epsilon 天花板保证严格递增且落 `[0,duration)`)
   - `providers/alignment_faster_whisper.py`:加 `tolerant` 开关。`tolerant=False` 保留原「逐字精确覆盖」严格门(唱歌必挂,但作质量门保留,其测试仍绿);`tolerant=True` 跑共享比例映射器
   - `director/intake.py`:`read_plain_lyric_lines`(.txt/.xlsx 自动选列,复用已有 zipfile+ElementTree,**不引 openpyxl**)

2. **两端都改成调它:**
   - conductor `media.py`:删 `_read_xlsx_lyrics`/`_norm_cjk`/`whisper_word_timestamps`/`align_lyrics_to_audio` 实现体/`_even_spread`,换薄委托壳
   - web `service.py`:对齐端翻 `tolerant=True`(它本来也有唱歌挂的同款 bug)

**How to apply:**

1. **任何「用户输入相同、输出相同」的功能,先搜 `src/mvstudio/` 有没有现成核心**;有就调它、没有就提升进去,**绝不在某个端里另起一套**。触发词:「我在 conductor 里写个 X」「web 那边也需要 X,复制过来」——立即打断,回本条。
2. **strict/tolerant 这类策略差异用「开关/参数」表达,不用「另一套实现」表达。**已测的严格路径不许动(会挂契约测试);新能力做成 opt-in flag。
3. **改 `src/mvstudio/*` 或 `mv_platform/*` = 改 web 核心,是门禁级决策**,须 owner 批准(本次用户选「提升进共享核心」即批准)。改动必须先跑基线测试留绿底,再证明无回归。
4. **各端 I/O 契约可不同**:conductor 写简版 `lyrics_timed.json {entries:[{start_seconds,text}]}`;web 写完整 manifest+evidence。**壳可不同,算法必须共享。**
5. 验证锚点:`tests/mvstudio/director/test_alignment.py` `test_intake.py` `tests/mvstudio/providers/test_alignment_faster_whisper.py` + web 集成 `test_director_animatic_workflow.py`。本次新增 14 条持久测试覆盖比例映射边界/tolerant 漂移/txt·xlsx 读取。

**待办/可选后续(owner 拍板):** web 以前转录对不上是**直接拦停**(防 whisper 幻觉质量门),现改容错对齐。若要 web 保留幻觉防线(如低置信度告警),是个小后续。

**反例(不要这么做):**
- ❌ 在 conductor / 某新端里复制粘贴一份歌词读取或对齐逻辑
- ❌ 为「唱歌容错」再造 strict 的孪生实现(应加 `tolerant` flag)
- ❌ 为读 .xlsx 引 openpyxl(共享核心 zipfile 够用,已删该依赖)
- ❌ 改 `src/mvstudio/*` 不跑基线、不留绿底就直接改

**关联:**
- [[feedback_read-env-example-first]] — 接手先摸清共享核心位置,别急着另起炉灶
- 边界铁规见 `CLAUDE.md` / `11_MV_DIALOGUE_PLAYBOOK.md §边界铁规`(`src/mvstudio/` `mv_platform/` 只读引擎,改动走 owner PR)
