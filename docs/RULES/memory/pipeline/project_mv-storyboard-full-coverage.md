---
name: mv-storyboard-full-coverage
description: "mv-agent 02_storyboard 分镜必须铺满整首歌；段落按能量自适应切成多个 4~15s 子镜（tiling），绝不出现镜头总长 < 歌曲时长"
metadata:
  node_type: memory
  type: project
---

mv-agent 生成式线（conductor 六步）里，02_storyboard 的分镜**必须覆盖整首歌**——镜头拼起来的总长≈歌曲时长，绝不允许「镜头总长 < 歌曲时长」。曾经的 bug：`mv-agent/conductor/tools.py._assemble_shots` **一段一镜 + `min(15,…)` 硬截**，8 个音乐段落 × 15s = 120s 天花板，与歌曲真实时长无关；再叠加 `compose` 的 `-t body_dur` 把成片截到镜头总长，导致画面短、歌也被砍。这**不是提示词问题**（那句「每段一镜/单镜≤15s」是硬编码 Python 逻辑，项目级 prompt 突破不了）。

**Why:** 音乐段落（`src/mvstudio/director/drafting.py` 的 `sections`）本来就已经铺满整首歌，问题纯在 conductor 适配层把每段塌缩成单个 ≤15s 镜头。Seedance i2v 有硬限：单镜必须落在 `[4,15]s`（`src/mvstudio/providers/seedance.py:155`），所以「一段一长镜」根本装不下长段落——正解是把长段落**平铺（tile）**成多个 4~15s 子镜。

**How to apply:**
- 修复在**可改的 conductor 适配层**（`mv-agent/conductor/tools.py`），不碰只读引擎 `src/mvstudio` 和引擎 schema（`visual_score.creative_draft_requested` 的 `shots` 仍是扁平 list、`id` 自由文本）。
- 平铺算法：`_plan_shots` / `_split_durations` —— 每段按 `energy`(1~5) 自适应目标单镜时长 `{1:12,2:11,3:9,4:7,5:6}`（能量越高切得越碎、切换越快），切成若干整数时长子镜，每镜严格 `[4,15]s`，子镜和≈段落真实时长。
- LLM 创意：payload 给每段带 `energy` + `shots_needed`，指令要求「每段产出 N 条递进、不重复的镜头，id 用 `{section_id}#{n}`」——契合引擎提示词本就写的「同段各镜不得同义重复」。`_assemble_shots` 按段落前缀归组匹配 draft，**LLM 少给时优雅回落，覆盖率由规划保证、不依赖 LLM 听话**。
- `MV_MAX_SHOTS` 小样上限改成按**镜头总数**截断（`_cap_plan`），而非按段落数——被保留的段落仍整段铺满。
- 验收：`storyboard.md` 直接标「覆盖 Xs / 歌曲 Ys」，meta 带 `covered_seconds`/`song_seconds`，一眼可验 drift≈0。
- 铁律引申：分镜要与歌曲背景/歌词/情绪贴切、围绕创作意境递进表达，不是靠复用同一创意凑时长——见引擎提示词 `mv-agent/prompts/storyboard.creative.md`。

关联：[[mv-agent-workflow-contract]]（Codex 调度这六步的执行契约）· [[mv-two-line-dispatch]]（生成式 vs 程序化分派）· [[camera-motion-vs-i2v-ceiling]]（i2v 是内容运动天花板，与本条的时长覆盖是两个正交问题）。
