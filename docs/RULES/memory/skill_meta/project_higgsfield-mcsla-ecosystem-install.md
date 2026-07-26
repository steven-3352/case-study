---
name: higgsfield-mcsla-ecosystem-install
description: OSideMedia/higgsfield-ai-prompt-skill(MIT · MCSLA 元公式生态)全量装到 .agents/skills/;主门 higgsfield + 30 子门;与 15 个 video-form-* 互补
metadata: 
  node_type: memory
  type: project
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**事实:** 2026-07-20 全量装 [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)(MIT)到 `.agents/skills/`,共 **31 个 skill**:1 主门 `higgsfield/` + 30 子门 `higgsfield-{X}/`。主门附带 shared refs(vocab.md · model-guide.md · image-models.md · prompt-examples.md · photodump-presets.md · production-benchmarks.md · DISCIPLINE.md · INDEX.md · LICENSE)。

30 个子 skill 类别:
- **相机/运镜**:higgsfield-camera · higgsfield-motion · higgsfield-vibe-motion
- **模型对比**:higgsfield-models · higgsfield-seedance · higgsfield-seedance-vfx · higgsfield-gpt-image-2
- **视觉方向**:higgsfield-cinema · higgsfield-style · higgsfield-moodboard · higgsfield-canvas
- **角色/表演**:higgsfield-soul(Soul ID 角色一致性)· higgsfield-character-design · higgsfield-facs(FACS 微表情)
- **生产流程**:higgsfield-pipeline · higgsfield-shotlist-director · higgsfield-content-factory · higgsfield-recipes
- **场景专项**:higgsfield-motion-design · higgsfield-image-shots · higgsfield-mixed-media · higgsfield-marketing-studio · higgsfield-audio
- **元技艺**:higgsfield-prompt(MCSLA 公式深度)· higgsfield-assist · higgsfield-troubleshoot
- **平台耦合(项目可忽略)**:higgsfield-apps · higgsfield-workspaces · higgsfield-recall · higgsfield-stack

**Why:** 用户 2026-07-20 决策"装"——补齐我上轮免费复刻建议里唯一没做的这条。MIT 许可明确允许 · 与已装 15 个 video-form-*(形态专属)是**互补关系**——15 个是分形态视觉语汇,MCSLA 是元公式(Model/Camera/Subject/Look/Action 五维骨架 · 全形态通用)+ 30 个精细子能力(Soul ID/FACS/vibe-motion/troubleshoot 等)。

**How to apply:**
- **skill 优先级(硬门)**:i2v-video-prompt(项目铁律)→ video-form-{形态}(形态公式)→ higgsfield-{X}(具体子能力)—— 见 `[[i2v-video-prompt]]` §九·补
- **命名策略**:保留原名 `higgsfield-*`,和 upstream 一致 · 方便以后 `git pull` upstream 更新时对齐
- **本地改动**:每个 SKILL.md 加 `platforms:` 段 + description 前置中文触发词 + 正文首个 H1 后追加"项目适配说明"(不订阅 Higgsfield / 铁律优先 / 冲突处理)
- **铁律冲突处理**(所有 higgsfield-* 通用):遇 cyberpunk neon / cool blue moonlit / dark developer canvas / 蓝紫饱和 → **一律改本项目铁律替代**([[feedback_no-neon-palette]] · [[feedback_no-ai-visual-dark-canvas]] · [[feedback_no-exaggerated-cold-atmosphere]])
- **平台耦合忽略**:higgsfield-apps/workspaces/recall/stack 假设你在 Higgsfield workspace,项目不订阅 Higgsfield,忽略即可
- **与项目自建 skill 互补**:
  - `[[i2v-video-diagnose]]`(项目版诊断,含 VIDEO_ITERATE_LOG + 3 次迭代上限 + 铁律绑)vs `higgsfield-troubleshoot`(泛用诊断)— **项目版本优先**,后者作补充
  - `higgsfield-seedance` 里可能有增量 Seedance 特性,和 `[[project_p011-seedance-i2v-candidate]]` 结合读
- **原件留存**:`tmp/higgsfield-ai-prompt-skill/` 保留全 repo 作原件备份,不删
- **相关**:[[feedback_skill-vs-template-distinction]](本次证明"skill 能力多样化 = 装,不冲突")· [[project_video-form-skills-full-install]] · [[i2v-video-prompt]] · [[i2v-video-diagnose]]
