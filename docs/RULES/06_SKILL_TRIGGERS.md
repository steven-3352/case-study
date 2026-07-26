# 06 · Skill 触发对照表 · 模型无关等价规范

> **这是本项目所有 `.agents/skills/*/SKILL.md` 的权威触发规范。**
> **与 skill frontmatter 冲突以本表为准。**

---

## 使用方式(按模型区分)

| 模型 | 挂载机制 |
|---|---|
| **Claude Code** | Skill tool 靠 `.agents/skills/*/SKILL.md` frontmatter 触发关键词自动匹配挂载。**agent 自己判断,用户不点单**(见 memory `feedback_agent-auto-mount-skills`)。本表是权威规范——若 Skill tool 挂错 skill,以本表为准 |
| **Codex / 其他模型** | **开工前根据用户描述文本,在本表匹配"触发场景"列的关键词**,主动 `read` 对应 `.agents/skills/{skill}/SKILL.md`。用户不需要指名 skill,agent 自己按本表匹配 |

---

## 项目铁律级 skill(4 个 · 出现关键词必读)

| 触发场景关键词 | 必读 skill | 补充 skill / 说明 |
|---|---|---|
| **任何内容制作**(选题 / 立项 / 前期规划 / 15 步流程) | `.agents/skills/tonbirds-content-engine/SKILL.md` | 本项目内容引擎核心 SOP · 覆盖 15 步全流程 |
| **生成一段视频** / i2v / t2v / **grok-imagine** / **Seedance** / **Kling** / **Runway** / **Luma** / **Wan** / **HunyuanVideo** / **Veo** / 分镜出现 `motion prompt` / `video prompt` 字段 / 调用 `pipeline/gen_video_frames.py` / `pipeline/p011_seedance_i2v/gen_video.py` / 任何 `gen_*_motion.py` | `.agents/skills/i2v-video-prompt/SKILL.md`(**项目铁律**) | 按形态挂 `video-form-{X}` + 需要时挂 `higgsfield-{X}`;详见 `04_CONTENT_CONSTRAINTS.md §15` |
| **视频生成完效果不满意** / 幻觉 / 伪影 / 角色崩 / 动作不自然 / AI 味重 / 相机运动看不出 / palette gate fail / **"这段不对/重生/改一下/为什么这么僵"** | `.agents/skills/i2v-video-diagnose/SKILL.md` | 7 类归因 + 4 步动作 + 3 次上限 · 3 次救不活升级换路线 · 详见 `04_CONTENT_CONSTRAINTS.md §16` |
| **语音厅 MV** / **纸片人** / **卡点 MV** / **立绘 PV** / **国乙**(国风乙女) / **现代国乙** / **男团宣传** / **CG 混剪** / **角色 PV** / **纸片人立绘** / 输入是"立绘 + 音频 + 歌词"的场景 | `.agents/skills/paperdoll-mv-packaging/SKILL.md` | 确定性 motion-graphics 包装层(非 i2v prompt 层)· 灵魂三件套 + 7 级视觉强度 + 5 层包装 + 12 背景生成器 + 14 风格库 + 艺术字层 · 详见 memory `reference_paperdoll-mv-packaging-skill` |

---

## video-form-* 形态 skill(15 个 · 与 i2v-video-prompt 组合)

**使用方式**:先挂 `i2v-video-prompt`(主门),再按形态挂对应 `video-form-{X}`(形态公式)。

| 触发场景 | skill |
|---|---|
| **电影感** / cinematic / 电影级 / 长焦 / 电影感转场 | `.agents/skills/video-form-cinematic/SKILL.md` |
| **3D CG** / three-dimensional / CG 特效 / 3D 建模感 | `.agents/skills/video-form-3d-cgi/SKILL.md` |
| **卡通** / cartoon / Q 版 / 卡通片 | `.agents/skills/video-form-cartoon/SKILL.md` |
| **漫画到视频** / comic-to-video / 漫画感 / 分镜漫画 | `.agents/skills/video-form-comic-to-video/SKILL.md` |
| **电商广告** / ecommerce / 短视频带货 / 产品短视频 | `.agents/skills/video-form-ecommerce-ad/SKILL.md` |
| **时尚 lookbook** / fashion / 走秀 / 时装 | `.agents/skills/video-form-fashion-lookbook/SKILL.md` |
| **打斗** / fight / 动作 / 对打 / 武打 | `.agents/skills/video-form-fight-scenes/SKILL.md` |
| **食品饮料** / food-beverage / 美食 ASMR / 饮品广告 | `.agents/skills/video-form-food-beverage/SKILL.md` |
| **motion design 广告** / motion graphics ad / 动态设计广告 | `.agents/skills/video-form-motion-design-ad/SKILL.md` |
| **音乐 MV** / music video / MV / 音乐可视化 | `.agents/skills/video-form-music-video/SKILL.md` |
| **产品 360** / product-360 / 产品旋转 / 全景产品展示 | `.agents/skills/video-form-product-360/SKILL.md` |
| **房产漫游** / real-estate / 户型 / 空间漫游 | `.agents/skills/video-form-real-estate/SKILL.md` |
| **社交钩子** / social-hook / 病毒钩子 / 短视频钩子 / viral hook | `.agents/skills/video-form-social-hook/SKILL.md` |
| **日漫动作** / anime-action / 日式动漫打斗 | `.agents/skills/video-form-anime-action/SKILL.md` |
| **品牌故事** / brand-story / brand film / 品牌片 | `.agents/skills/video-form-brand-story/SKILL.md` |

**判断口径**:15 个 video-form 是**能力**不是**模板**——反 template-clone 铁律是分镜层不是 skill 层。见 memory `feedback_skill-vs-template-distinction`。

---

## Higgsfield MCSLA 生态(30 个 · OSideMedia MIT · 精细能力)

**使用方式**:MCSLA 元公式(camera / soul / facs / motion / models 等)与 15 个 video-form-* 互补。命名保原名便于 upstream 同步。

### 挂载建议

| 触发场景 | skill |
|---|---|
| **相机运动**细节(dolly / crane / gimbal / handheld) | `.agents/skills/higgsfield-camera/SKILL.md` |
| **人物 soul / 情绪** / vibe / 内在情感 | `.agents/skills/higgsfield-soul/SKILL.md` |
| **面部动作单元** / FACS / 眨眼 / 嘴角 / 微表情 | `.agents/skills/higgsfield-facs/SKILL.md` |
| **运动学**(人物动作) / motion primitives | `.agents/skills/higgsfield-motion/SKILL.md` |
| **模型选型** / model params / seed / lora | `.agents/skills/higgsfield-models/SKILL.md` |
| **shot list 导演** | `.agents/skills/higgsfield-shotlist-director/SKILL.md` |
| **角色设计** | `.agents/skills/higgsfield-character-design/SKILL.md` |
| **电影感镜头**(higgsfield 版) | `.agents/skills/higgsfield-cinema/SKILL.md` |
| **动效设计**(higgsfield 版) | `.agents/skills/higgsfield-motion-design/SKILL.md` |
| **风格库** | `.agents/skills/higgsfield-style/SKILL.md` |
| **prompt 工程**(higgsfield 元公式) | `.agents/skills/higgsfield-prompt/SKILL.md` |
| **元入口**(不知道该挂哪个时) | `.agents/skills/higgsfield/SKILL.md` |

### 其他 higgsfield 子技能(按需查表)

- `higgsfield-assist` / `higgsfield-audio` / `higgsfield-canvas` / `higgsfield-content-factory` / `higgsfield-gpt-image-2` / `higgsfield-image-shots` / `higgsfield-marketing-studio` / `higgsfield-mixed-media` / `higgsfield-moodboard` / `higgsfield-pipeline` / `higgsfield-recipes` / `higgsfield-seedance` / `higgsfield-seedance-vfx` / `higgsfield-troubleshoot` / `higgsfield-vibe-motion`

### 忽略清单(平台耦合子 skill · 项目不订阅 Higgsfield workspace)

- `higgsfield-apps` / `higgsfield-workspaces` / `higgsfield-recall` / `higgsfield-stack`

### 与项目铁律的冲突覆盖

Higgsfield 子 skill 若涉及 **cyberpunk / cool-blue / dark-canvas** 一律以本项目铁律替代(见 `04_CONTENT_CONSTRAINTS.md §2 禁蓝紫 · §3 禁 AI 味深色`)。

---

## GSAP 网页动效(8 个 · greensock/gsap-skills)

**使用方式**:项目未主动跑网页动效,但落地页/长滚动案例页/交互式作品集/Before-After 对比/网页动效录屏当 B-roll 时启用。

| 触发场景 | skill |
|---|---|
| **GSAP 核心** / gsap.to() / from() / fromTo() / 基本 tween / easing / stagger / matchMedia | `.agents/skills/gsap-core/SKILL.md` |
| **动画时间轴** / timeline / gsap.timeline() / 序列 / 编排 / 位置参数 | `.agents/skills/gsap-timeline/SKILL.md` |
| **滚动动画** / ScrollTrigger / 滚动触发 / 视差 / pin / scrub | `.agents/skills/gsap-scrolltrigger/SKILL.md` |
| **GSAP 插件** / ScrollToPlugin / ScrollSmoother / Flip / Draggable / Inertia / Observer / SplitText / ScrambleText / SVG plugins / CustomEase | `.agents/skills/gsap-plugins/SKILL.md` |
| **动画性能** / GSAP 60fps / avoid layout thrashing / will-change / batching | `.agents/skills/gsap-performance/SKILL.md` |
| **gsap.utils** / clamp / mapRange / random / snap / toArray / wrap / interpolate | `.agents/skills/gsap-utils/SKILL.md` |
| **React 动画** / useGSAP / gsap.context() / Next.js / React cleanup | `.agents/skills/gsap-react/SKILL.md` |
| **Vue / Svelte 动画** / Nuxt / SvelteKit / onMounted / onMount / onDestroy | `.agents/skills/gsap-frameworks/SKILL.md` |

**索引**:`.agents/skills/gsap-llms.txt`

---

## 静态图 prompt 工程(1 个)

| 触发场景 | skill |
|---|---|
| **静态图 prompt** / GPT-image-2 / midjourney / Stable Diffusion prompt / 图生图 prompt | `.agents/skills/ai-image-prompts-skill/SKILL.md` |

---

## 场景 → skill 组合矩阵(常见组合速查)

| 场景 | 组合 |
|---|---|
| 语音厅《明月天涯》纸片人 MV | `paperdoll-mv-packaging` **(主)** · 出图段可挂 `higgsfield-image-shots` / `ai-image-prompts-skill` |
| 抖音短视频用 i2v 生成一段电影感开头 | `i2v-video-prompt`(主)+ `video-form-cinematic` + `higgsfield-camera`(细节) |
| 生成一段音乐 MV | `i2v-video-prompt` + `video-form-music-video` + `higgsfield-vibe-motion` |
| 电商带货 15s 短视频 | `i2v-video-prompt` + `video-form-ecommerce-ad` + `video-form-social-hook`(前 3s 钩子) |
| 落地页做长滚动交互作品集 | `gsap-scrolltrigger` + `gsap-timeline` + `gsap-performance` |
| Next.js 页面加动效 | `gsap-react` + `gsap-core` + `gsap-timeline` |
| 视频生成完了效果差要修 | `i2v-video-diagnose`(主 · 只改 1-2 变量)+ 再挂对应 `video-form-{X}` 补 prompt |
| 立绘卡点 MV 里某段想插入 i2v 生成的相机推进 | `paperdoll-mv-packaging`(主)**+ 短段落里挂** `i2v-video-prompt` + `video-form-cinematic`(混用,不是完全替换) |

---

## 违反后果

违反 → 视为反 AI 味 / 禁蓝紫 / 反 template-clone / D05 加速铁律未过 → `pre_publish_forecast` gate fail → 登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`。

---

## 新装 skill 的正确姿势

**装新 skill 后必须同步更新本表。**

1. 把 skill 装到 `.agents/skills/{skill_name}/`(保留 upstream 命名便于同步)
2. 在本表添加一行:触发关键词 + skill 路径 + 与其他 skill 的组合关系
3. 若与项目铁律冲突(如新 skill 默认走蓝紫色板),在本表该行加 `## 与项目铁律的冲突覆盖` 说明
4. 若属新范畴(如新增"3D 建模" skill 家族),新增一节
5. 提交 PR 时同步更新 `09_MIGRATION_SOP.md` §3(新装 skill 检查项)

---

## Source Map

- 新写(部分参考 `.agents/skills/*/SKILL.md` frontmatter description 字段)
- 原 memory:`feedback_i2v-video-prompt-skill-mandatory` · `project_i2v-video-diagnose-skill` · `reference_paperdoll-mv-packaging-skill` · `project_higgsfield-mcsla-ecosystem-install` · `project_video-form-skills-full-install` · `feedback_agent-auto-mount-skills` · `feedback_skill-vs-template-distinction` · `gsap-skills-available`
