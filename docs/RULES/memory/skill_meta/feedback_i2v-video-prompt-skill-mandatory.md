---
name: i2v-video-prompt-skill-mandatory
description: 任何 i2v/t2v 视频 prompt 必调用 .agents/skills/i2v-video-prompt/;CLAUDE.md 有硬门
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**规则:** case-study 项目里,任何要给视频生成模型写 prompt 之前,**必读** `.agents/skills/i2v-video-prompt/SKILL.md`。**该 skill 与具体模型解耦**——无论后端是已接的 `grok-imagine-video`、待接的 Seedance 2.0(P011 stub)、未接的 Kling / Runway / Luma / Wan / HunyuanVideo / Veo,甚至暂无 API 手动粘到网页版的模型,**都走同一个 skill**。skill 输出的是结构化 prompt 文本,不是脚本代码,拿去哪都能用。

该 skill 蒸馏自 higgsfield-seedance2-jineng 的 2s 钩子公式 + 20+ 镜头运动词典 + 6+ 灯光库,并绑定本项目铁律(反 AI 味/禁蓝紫/禁 AI 味深色/密 VO 无死区/温馨禁冷渲染/i2v 相机运动幅度足够可见)。

**Why:** 2026-07-20 立(与视频 prompt 工程升级一并落地,不与任何具体 pipeline 绑)。视频 prompt 是本项目最容易漏铁律的地方——蓝紫/AI 味/冷渲染/相机运动看不出/i2v 幻觉都从这里流入终片,反手就是 palette gate fail 或投后"AI 味重"差评。skill 把所有铁律和公式集中一份,避免每次重新想。用户明确说"做 i2v 视频时都自动调用",故 CLAUDE.md 已加"i2v/t2v 视频 prompt 硬门"作为兜底,不依赖 Claude 自动匹配 description。**关键澄清(2026-07-20 用户指出):skill 不依赖 Seedance/P011 存在;项目只有 grok 也照用不误。**

**How to apply:**
- 触发场景:分镜 storyboard 出现 `video/motion prompt` 字段 · 编辑 `pipeline/gen_video_frames.py` 类脚本 · 调用 `pipeline/p011_seedance_i2v/gen_video.py` · 用户说"生成一段视频/一段 i2v/一段动效"
- 违反登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`(与 [[feedback_pre-node-checklist]] 同处理)
- 相关:[[feedback_no-neon-palette]] · [[feedback_no-ai-visual-dark-canvas]] · [[feedback_camera-motion-vs-i2v-ceiling]] · [[feedback_anti-ai-visual]] · [[feedback_no-exaggerated-cold-atmosphere]] · [[feedback_pre-node-checklist]]
