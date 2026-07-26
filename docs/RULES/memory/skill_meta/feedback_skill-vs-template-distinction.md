---
name: skill-vs-template-distinction
description: "可复用技能(方法/公式/词典/流程)与模板(具体内容一次性产物)是完全不同的东西;反 template-clone 铁律只管后者,不许套用到 skill 库"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**规则:** 「可复用技能(skill)」与「模板(template)」是**两个不可混为一谈的概念**。反 template-clone 铁律([[feedback_no-default-tech-stack]] · SCRIPT_REJECT_LOG · templates/README.md)只**禁止后者**,不禁前者。判据表:

| 维度 | 可复用技能 (skill) | 模板 (template clone 反例) |
|---|---|---|
| 内容形态 | 方法 / 公式 / 词典 / 流程 / 判据 / 骨架 | 具体分镜内容 / 具体画面 / 具体 prompt 文本 / 一次性产物 |
| 服务对象 | **跨选题**反复调用 | 只服务**上一条**选题 |
| 加载方式 | Claude 触发词/形态匹配自动挂载 | 手工 copy-paste |
| 独立性 | 每个 skill 是**独立的一种能力**,15 个 = 15 种视觉语汇 | 拷同一个模板去多条选题 = 同质化毁片 |
| 示例(应该有) | Camera Movement Encyclopedia · 2s 钩子公式 · 灯光 K 值库 · gsap-timeline · video-form-food-beverage 的"macro 特写 + 咀嚼 foley + 3200K 暖色" | — |
| 示例(应该禁) | — | 拷 S01_winter_bedroom 的 motion prompt 到新短片 · 拷 D06 武侠分镜到 D07 明月天涯 · catalog 三连拼盘代替本条分镜 |

**Why:** 2026-07-20 用户明确指出——上一版判 15 个 video-form-* skill 为"违反反模板克隆铁律,只蒸馏不批量拷"是错的。反 template-clone 铁律讲的是 SCRIPT_REJECT_LOG 里"从上一条克隆分镜/画面",不是"skill 库不许多样"。项目已有 8 个 gsap-* + ai-image-prompts-skill,15 个 video-form-* 加进来同性质,15 种视觉语汇本身就是**可复用能力池**,与模板克隆无关。**用户重复"重要"三次 = 建永久铁律**,不是一次性纠错。

**How to apply:**
- 出现"要不要加 N 个 skill?" → 判据:每个 skill 是独立能力(方法/公式/流程),就装;是重复的一次性内容,就拒
- 出现"这跟反 template-clone 冲突吗?" → 先问"是能力还是产物?"—— 能力不冲突;产物才要防
- 出现"是不是模板克隆?" → 只有当**具体分镜/画面/prompt 文本**被从上一条拷到下一条时,才是;技能库多样化不是
- 具体决策示例:
  - ✅ 装 15 个 video-form-* skill(15 种视觉语汇 = 15 种能力)
  - ✅ 装 8 个 gsap-* skill(gsap 8 个子域各是能力)
  - ✅ 未来接入 Kling/Runway 时给它们各自的 prompt 优化 skill
  - ❌ 拷 shortfilm_memory/S01 的 motion prompt 到新短片(具体产物克隆)
  - ❌ 拷 D06 武侠分镜结构到 D07(具体产物克隆)
  - ❌ catalog 三连当分镜写(具体产物克隆)
- **相关**:[[feedback_no-default-tech-stack]](反默认技术栈 · 与本条不冲突,是不同层的铁律)· [[project_video-form-skills-full-install]] · SCRIPT_REJECT_LOG · templates/README.md
