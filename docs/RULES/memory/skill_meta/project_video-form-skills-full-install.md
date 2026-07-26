---
name: video-form-skills-full-install
description: case-study 全量装 15 个 video-form-* 子 skill(蒸馏自 higgsfield-seedance2-jineng);i2v-video-prompt 主门 + 15 子门结构
metadata: 
  node_type: memory
  type: project
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**事实:** 2026-07-20 全量装 15 个 `video-form-*` skill 到 `.agents/skills/`,蒸馏自 [beshuaxian/higgsfield-seedance2-jineng](https://github.com/beshuaxian/higgsfield-seedance2-jineng)。结构:主门 `i2v-video-prompt`(通用铁律 + 公式 + 索引 15 子门)+ 15 子门(video-form-cinematic / 3d-cgi / cartoon / comic-to-video / fight-scenes / anime-action / motion-design-ad / ecommerce-ad / product-360 / music-video / social-hook / brand-story / fashion-lookbook / food-beverage / real-estate)。

每个子 skill:
- frontmatter `name: video-form-{X}` · description 前置中文触发词(Claude 中文场景也能触发)· platforms: claude-code/cursor/codex
- 去 "Seedance 2.0 on Higgsfield" 硬绑 · description 改成 "任何 i2v/t2v 视频模型(grok-imagine/Seedance 2.0/Kling/Runway/Luma/Wan/HunyuanVideo/Veo)"
- 正文保留 en 主版(01-10 zh 是精简摘要 ~27% · 11-15 zh 是完整翻译但选定统一 en 减少歧义)
- 正文内遗留 "for Seedance 2.0 on Higgsfield" 字样是历史成本 · frontmatter 已声明通用性 · 不影响能力

**Why:** 2026-07-20 用户校正——上一版判断"repo 无 LICENSE + 违反反模板克隆铁律,只蒸馏不拷贝"两处错:
1. **反 template-clone 铁律**指的是 SCRIPT_REJECT_LOG 里"从上一条选题克隆分镜/画面",不是"不许有多个 skill";已有 gsap-* 8 个 + ai-image-prompts-skill,那也是多 skill,没人说是模板克隆
2. **无 LICENSE 不等于禁止使用** —— repo README 明说"复制 SKILL.md 到 Claude 技能目录",作者意图就是给用户装 · 项目内部 `.agents/skills/` 使用是合理引用不是二次分发
3. **15 个是能力不是模板** —— cinematic/3d-cgi/comic/food/real-estate 等是 15 种视觉语汇/形态,做美食 ASMR 需要"macro 特写 + 咀嚼 foley + 3200K 暖色"这类形态专属公式,通用主门给不出

**How to apply:**
- **调用顺序**:先读 `i2v-video-prompt` 主门拿项目铁律 → 按选题形态挂载对应 `video-form-{X}` 子门拿形态公式 → 两者合并成最终 prompt
- **形态映射**:演示/知识型 → cinematic 或 motion-design-ad;个人短片《熊熊》类温馨叙事 → cinematic 或 fashion-lookbook;带货型 → ecommerce-ad 或 product-360;漫画型 → comic-to-video 或 cartoon;美食带货 → food-beverage
- **铁律冲突处理**:子 skill 内出现 "cyberpunk neon" / "cool blue moonlit" / "dark developer canvas" 时**强制废止**,项目铁律优先(禁蓝紫/禁 AI 味深色/禁冷渲染)—— 见主门 §一
- **原件留存**:`tmp/higgsfield-seedance2/` 保留作原件备份,不删,后续可对照回滚
- **相关**:[[feedback_i2v-video-prompt-skill-mandatory]] · [[project_p011-seedance-i2v-candidate]] · [[feedback_no-neon-palette]] · [[feedback_no-ai-visual-dark-canvas]]
