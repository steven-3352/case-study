# docs/RULES/memory/ · 从 Claude Code memory 下沉的稳定规则

> **本目录是 SSOT 的 memory 部分。** 原来住在 `~/.claude/projects/-Users-wmzuo-Documents-project-case-study/memory/` 的稳定 feedback / project 规则**已全部下沉到这里**,任何模型都能读。
> **原路径 memory 目录只保留 SESSION-TEMP / PROJECT-STATE / REFERENCE 类**(见 `~/.claude/.../memory/MEMORY.md`)。

---

## 索引(按主题)

### audience/ · 用户/受众
- [feedback_audience-first.md](audience/feedback_audience-first.md) — 铁律 0 落地条

### gates/ · 门禁与验收
- ⭐ [feedback_gate-floor-not-target.md](gates/feedback_gate-floor-not-target.md) — 门禁是地板不是目标 · 抬高 3 档
- ⭐ [feedback_build-to-reference-not-floor.md](gates/feedback_build-to-reference-not-floor.md) — 第一版就要对标参考不能建到底线就停
- ⭐ [feedback_no-gaming-the-verifier.md](gates/feedback_no-gaming-the-verifier.md) — 禁用改验收器输入的方式过门
- [feedback_pre-node-checklist.md](gates/feedback_pre-node-checklist.md) — 每节点入口必读清单
- [feedback_user-picks-active-agents.md](gates/feedback_user-picks-active-agents.md) — active_roles 用户拍板

### palette/ · 色板与视觉禁区
- [feedback_no-neon-palette.md](palette/feedback_no-neon-palette.md) — 禁 Dracula 紫粉青
- [feedback_gen-ui-avoid-blue-purple-gradient.md](palette/feedback_gen-ui-avoid-blue-purple-gradient.md) — gen_ui 禁蓝紫渐变
- [feedback_anti-ai-visual.md](palette/feedback_anti-ai-visual.md) — 反 AI 味视觉风格优先

> **注:** "禁 AI 味深色开发者工具风"规则未单独立 memory,直接见 `../04_CONTENT_CONSTRAINTS.md §3`。

### voice_audio/ · 音画/字幕/TTS
- [feedback_dense-vo-no-bgm-default.md](voice_audio/feedback_dense-vo-no-bgm-default.md) — 密 VO 演示/知识型默认无 BGM
- [feedback_dense-vo-no-dead-air.md](voice_audio/feedback_dense-vo-no-dead-air.md) — 密 VO 无死区
- [feedback_no-synth-bgm.md](voice_audio/feedback_no-synth-bgm.md) — 禁合成假 BGM
- [feedback_sfx-layer-required.md](voice_audio/feedback_sfx-layer-required.md) — sfx 音效层独立必需
- [feedback_pipeline-burn-subs.md](voice_audio/feedback_pipeline-burn-subs.md) — 字幕由 pipeline 自动烧
- [feedback_pipeline-full-platform-output.md](voice_audio/feedback_pipeline-full-platform-output.md) — pipeline 直出双平台 mp4
- [feedback_ai-voice-known-gap.md](voice_audio/feedback_ai-voice-known-gap.md) — AI 声音已识别 gap · 暂不动
- [tts-estimate-duration-pre-synth.md](voice_audio/tts-estimate-duration-pre-synth.md) — TTS 时长前置估算
- [feedback_vo-script-must-be-spoken-language.md](voice_audio/feedback_vo-script-must-be-spoken-language.md) — VO 稿必须口语化

### skill_meta/ · Skill 相关元规则
- [feedback_agent-auto-mount-skills.md](skill_meta/feedback_agent-auto-mount-skills.md) — agent 自主挂 skill · 用户不点单
- [feedback_skill-vs-template-distinction.md](skill_meta/feedback_skill-vs-template-distinction.md) — ⭐ 可复用技能 ≠ 模板 · 铁律
- [feedback_i2v-video-prompt-skill-mandatory.md](skill_meta/feedback_i2v-video-prompt-skill-mandatory.md) — i2v/t2v 视频 prompt skill 强制调用
- [project_i2v-video-diagnose-skill.md](skill_meta/project_i2v-video-diagnose-skill.md) — 视频生成后诊断 skill
- [reference_paperdoll-mv-packaging-skill.md](skill_meta/reference_paperdoll-mv-packaging-skill.md) — 国风乙纸片人 MV 包装设计规范 skill
- [project_higgsfield-mcsla-ecosystem-install.md](skill_meta/project_higgsfield-mcsla-ecosystem-install.md) — Higgsfield MCSLA 生态全量装
- [project_video-form-skills-full-install.md](skill_meta/project_video-form-skills-full-install.md) — video-form 15 skill 全量装
- [gsap-skills-available.md](skill_meta/gsap-skills-available.md) — GSAP Skills 能力登记

### workflow/ · 工作流/协作
- [feedback_multi-role-collab.md](workflow/feedback_multi-role-collab.md) — 新选题处理:多工种协作模式
- [feedback_autonomous-data-driven.md](workflow/feedback_autonomous-data-driven.md) — 自主推进、数据导向
- [feedback_full-autonomy-no-confirm.md](workflow/feedback_full-autonomy-no-confirm.md) — ⭐ 全自动 · 不确认
- [feedback_d05-parallel-agents.md](workflow/feedback_d05-parallel-agents.md) — D05 加速 A · Agent 并行化
- [feedback_delta-docs-only.md](workflow/feedback_delta-docs-only.md) — D05 加速 B · Delta 文档
- [feedback_dual-platform-only.md](workflow/feedback_dual-platform-only.md) — 双平台规则(抖音+小红书)
- [project_user-agent-4step-workflow.md](workflow/project_user-agent-4step-workflow.md) — 顶层工作模式 · 4 步 5 拍板点
- [project_weekly-form-ab-test.md](workflow/project_weekly-form-ab-test.md) — 周形式 A/B 测试规则
- [feedback_contrast-hook-3s.md](workflow/feedback_contrast-hook-3s.md) — 3s 反差钩子模板
- [feedback_intake-contract-autonomous.md](workflow/feedback_intake-contract-autonomous.md) — 前置对话→需求契约→后台自主 · 两拍小样套路

### visual/ · 视觉硬约束(色板以外)
- [feedback_no-cheap-procedural-background.md](visual/feedback_no-cheap-procedural-background.md) — ⭐ 严禁廉价程序化背景
- [feedback_richer-camera-movements.md](visual/feedback_richer-camera-movements.md) — ⭐ 重点运用复杂运镜
- [feedback_props-match-tachie-style.md](visual/feedback_props-match-tachie-style.md) — ⭐ 道具必须与立绘同画风
- [feedback_no-exaggerated-cold-atmosphere.md](visual/feedback_no-exaggerated-cold-atmosphere.md) — 温馨片段禁刻意冷渲染
- [feedback_yishuzi-term.md](visual/feedback_yishuzi-term.md) — 术语「艺术字」不是「美术字」
- [cjk-bold-font-ghosting-fix.md](visual/cjk-bold-font-ghosting-fix.md) — 大字标题重影根治
- [visual-form-inspiration-library.md](visual/visual-form-inspiration-library.md) — 视觉形式灵感库
- [project_audience-open-skin-per-topic.md](visual/project_audience-open-skin-per-topic.md) — 受众开放 · 选题定皮肤

### pipeline/ · 生产层与工具
- [feedback_no-default-tech-stack.md](pipeline/feedback_no-default-tech-stack.md) — 禁默认技术栈心智固化
- [feedback_read-env-example-first.md](pipeline/feedback_read-env-example-first.md) — 接手项目第一动作
- [p004-lib-config-driven.md](pipeline/p004-lib-config-driven.md) — p004_video/lib config-driven 架构
- [feedback_camera-motion-vs-i2v-ceiling.md](pipeline/feedback_camera-motion-vs-i2v-ceiling.md) — 相机运动 vs i2v 是两种天花板
- [feedback_zoompan-visible-motion.md](pipeline/feedback_zoompan-visible-motion.md) — zoompan 动画幅度过小像 PPT
- [feedback_gpt-image-model-fallback.md](pipeline/feedback_gpt-image-model-fallback.md) — gpt-image 多参考图 503 根因
- [gpt-image-2-api.md](pipeline/gpt-image-2-api.md) — GPT-image-2 API 配置

### shortfilm/ · 副线短片专用(40 岁夫妻回忆)
- [project_shortfilm-memory-piece.md](shortfilm/project_shortfilm-memory-piece.md) — 40 岁夫妻回忆短片定型

---

## 与主 RULES/*.md 的关系

**主 `docs/RULES/*.md`** 是**规范/铁律的主体**(该做什么、不该做什么、为什么、如何做)。

**本目录 memory/*.md** 是**沉淀的教训**(某次踩坑的具体案例、根因、修法),提供:
- **原始事故上下文**(哪次生产出的问题)
- **判据细节**(什么算触发本规则)
- **诊断步骤**(修的时候检查哪一步)

**主规范文件已在正文引用相关 memory**(如 `04_CONTENT_CONSTRAINTS.md §2 禁蓝紫` 尾部会写 `依据:memory feedback_no-neon-palette`)。

---

## 为什么下沉

**原来**:memory 只有 Claude Code 会自动注入,其他模型看不到。等于稳定规则只对 Claude Code 有效,项目**不是真的模型无关**。

**下沉后**:任何模型接入 `docs/RULES/` 都能看到所有稳定规则。原 memory 目录**只留**会话临时状态 / 项目当前进度 / 外部引用。

参见 `../09_MIGRATION_SOP.md`。
