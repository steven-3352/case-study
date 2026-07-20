---
name: i2v-video-prompt
description: |
  **本项目所有 i2v / t2v 视频 prompt 工程强制调用本 skill**——无论用 Seedance 2.0 / grok-imagine-video / Kling / Runway / Luma / Wan / HunyuanVideo 哪个模型。
  蒸馏自 higgsfield-seedance2-jineng 与 higgsfield-ai-prompt-skill 的 2s 钩子公式、20+ 镜头运动词典、10+ 灯光库,
  并**与本项目铁律绑死**——反 AI 味 / 禁蓝紫 / 禁 AI 味深色 / audience-first / 密 VO 无 BGM / 密度 ≥ 画面变化。
  触发词(任一命中即挂载):i2v / t2v / image-to-video / text-to-video / 视频 prompt / motion prompt /
        seedance / grok-imagine / kling / runway / luma / veo / wan / hunyuan / higgsfield /
        相机运动 / camera motion / bullet time / crash zoom / dolly zoom / 360 orbit /
        镜头预设 / motion storyboard / 视频生成 / video generation。
  **未读此 skill 就写视频 prompt = 违反 CLAUDE.md 硬门,视为反 AI 味 / 禁蓝紫铁律未过。**
platforms:
  - claude-code
  - cursor
  - codex
---

# i2v / t2v 视频 Prompt 工程 · 本项目版

**模型无关:** 本 skill 输出的是**结构化 prompt 文本**,不绑任何具体模型/pipeline。生成好的 prompt:
- 已接的 `grok-imagine-video` 可用(走 `pipeline/gen_video_frames.py` 类脚本)
- 未来接的 Seedance 2.0(P011 stub)/ Kling / Runway / Luma / Wan / HunyuanVideo / Veo 可用
- 甚至暂未接的模型可**手工**粘到其网页/API 面板用(即梦、可灵、Runway web、Higgsfield web 均可)

skill 本身**不依赖** P011 或任何一条 pipeline 的存在。项目里现在只有 grok 也照用不误。

**边界:** 本 skill 只负责"写 prompt";不负责选实现(那属 form_strategy 五维打分,见 SYSTEM §4.2)。
如果分镜还没定用哪个视频模型,先回 §4.2 打分,别倒着来。

---

## 一、本项目铁律优先(超过所有 prompt 技巧)

调用本 skill 时,必须先跑一遍本清单——**违反直接毙,不进候选池**:

| 铁律 | 落地 | 违反后果 |
|---|---|---|
| **audience-first** | prompt 必须声明本镜服务 completion_3s / completion_rate / 收藏 / 评论 哪一项 | 无声明 → 形式策略官退稿 |
| **禁蓝紫** | prompt 里不得出现 `#bd93f9` `#ff79c6` `#8be9fd` `neon purple` `neon pink` `cyan` 或"暖红→冷蓝渐变";蓝紫在画面占比 >5% pixel gate fail | 见 `pipeline/gate_check_palette.py` |
| **禁 AI 味深色画布** | 不得默认 `#0a0e14`/`#141922` 类深色 canvas 或 Linear/Vercel/Cursor 式暗色开发者美学;起手默认浅色/白底 | 见 memory `feedback_no-ai-visual-dark-canvas`(T040 教训) |
| **反 AI 味** | prompt 不写"AI/generated/rendered/artificial";写"shot on Kodak Portra 400 film"/"iPhone 15 Pro handheld"/"documentary reportage" | AI 磨皮/塑料感即返工 |
| **密 VO 无死区** | 有 VO 的镜,前 6s 禁"silent hold"式沉默设计;prompt 里禁 "0-1s complete silence"这类默认套路 | 见 memory `feedback_dense-vo-no-dead-air` |
| **画面变化 ≥ 声音密度** | 每 2-4s 必须有明确画面变化(prompt 写 timeline 时逐秒安排,不允许 4s+ 静态) | 完播北极星硬门 |
| **蒙太奇不写实拍口播** | 演示/知识型的口播是画外音,不要 prompt "person speaking to camera",除非本条形态是"出镜型" | topic_brief.skin 里 form_type 决定 |

---

## 二、写 prompt 前 3 个必答问题

不答完不许开写:

1. **本镜的一句话意图** — 停划?看懂?收藏?评论?(SYSTEM §4.1 表)
2. **本镜时长** — Seedance 单次 4-15s;grok 单次 5-10s;超时长必须拆多段并说明衔接
3. **有没有 GPT-image-2 首帧图作 i2v 起点** — 有 → 走 i2v(prompt 只写"动作变化",不重复描述画面,参考 `pipeline/gen_video_frames.py` 教训);没有 → 走 t2v(需完整场景描述)

---

## 三、2 秒钩子公式(蒸馏版)

**原理:** 0.5-2s 是人脑无意识注意力窗;算法也在这个窗口判断"要不要继续推"。

### 12 种钩子(pick 1,或叠加 2 种作 "hook stacking")

| 钩子 | 语言公式 | 适合场景 |
|---|---|---|
| **极特写 → 广角揭示** | "Extreme macro of [detail]. At 0.5s whip-cut to extreme wide of [scene]. Contrast 100:1." | 尺度反差 |
| **黑屏 → 光爆** | "Pure black. At 0.8s explosive light burst from [top-left]. Amber floods frame in 0.3s. Lens flare across center." | 情绪起点 |
| **逆向运动** | "First 2s: object slides backward across frame. Water droplets float upward. Impossible motion." | 认知违和,大脑锁定 |
| **陌生尺度** | "Extreme macro of mundane object [fabric weave / concrete pore / leaf vein]. Treat as vast landscape. Viewer doesn't recognize scale for 2s." | 疑问驱动看下去 |
| **静默 → 爆音**(仅音画层,和视频 prompt 联动) | "First 1.2s complete silence, no ambient. At 1.3s sudden [gunshot / door slam / music drop]. Sync frame cut." | ⚠️ **本项目密 VO 型禁用**——用"静音铺垫→VO 猛进"替代 |
| **极端色移** | "Frame opens desaturated blue-grey. At 0.6s snap to warm amber-gold. 50% color shift in 0.4s." | ⚠️ 蓝紫色域受铁律限制,改冷灰→暖橙 |
| **入画高速运动** | "Subject enters frame from edge at extreme velocity. Motion blur trails. Enter from edge, not center." | 动作型 |
| **rack focus** | "Two planes both sharp. At 1s racking to foreground blur background. f/1.4 cinema." | 电影感 |
| **几何锐对比** | "Sharp horizontal vs vertical elements. High-contrast light. Asymmetric frame." | 静态但张力 |
| **眼睛睁开/直视** | "Close on eyes low-light. At 0.8s eyes snap open, lock camera. Pupil dilate." | 拟真人型;⚠️ 演示型跳过 |
| **相机旋转失衡** | "Camera tilts/rolls 45°-180° in 0-1.5s. Stabilizes to level at 2s." | 情绪片段 |
| **不可能的尺度** | "Tiny human in vast [desert/ocean/space]. OR giant object in confined space. Emphasize via distance and proportion." | 世界感 |

### Hook stacking(高级)
- 黑屏 + 光爆 + 特写揭示 = 三感官叠加
- 逆向运动 + 眼睛睁开 + 几何对比 = 认知+原始+构图叠加

---

## 四、镜头运动词典(20+ · Seedance / grok 通用)

**用法:** prompt 里指定**精确速度**(feet/second)+ 时长,不写"fast/slow"。参考 `pipeline/gen_video_frames.py` S01_MOTION 里的 "Camera very slowly pushes in by about 3 percent" 就是这类精度。

| 镜头 | 精确 prompt 语句 | 时长 | 典型意图 |
|---|---|---|---|
| Dolly Forward(推近) | `Camera dolly forward at constant 2 ft/s. Subject center-frame. Slight lens breathing.` | 1-3s | 拉观众入戏 |
| Dolly Backward(拉远) | `Camera pulls back 15 ft at 3 ft/s. Subject center. Background gradually reveals.` | 1-4s | 揭示尺度 |
| Truck L/R(横移) | `Camera trucks left 10 ft at 2 ft/s. Subject frame-right. Parallax reveals BG.` | 2-4s | 展环境 |
| Pan L/R(横摇) | `Camera pan left 60° at 30°/s. Smooth accel/decel.` | 0.5-2s | 转移焦点 |
| Tilt Up/Down(竖摇) | `Camera tilts up feet-to-face at 20°/s. Reveals vertical scale.` | 1-3s | 显尺度 |
| Whip Pan(甩镜) | `Whip pan A→B in 0.5s. 90°/s. Motion blur acceptable.` | 0.3-0.6s | 无痕转场 |
| Handheld(手持) | `Handheld follow. Micro-vibration 0.5-1mm jitter at 2 Hz. Breathing 1-2px frame. NOT locked-off.` | 2-6s | 纪录/紧迫感 |
| Steadicam / Gimbal | `Gimbal-smooth follow. 3-ft distance. Zero micro-vibration. Liquid-smooth motion.` | 3-8s | 电影质感 |
| Tracking(跟拍) | `Camera tracks subject from 4-ft side. Subject frame-right, env frame-left. Sync 2 mph walk.` | 3-6s | 主角动感 |
| Crane Up(升) | `Camera rises vertically 30 ft over 4s. Subject in lower frame. BG reveals as crane rises.` | 3-6s | 结尾宏大 |
| Crane Down(降) | `Camera descends 20 ft over 3s. Start overhead, end eye-level. Tilt up to maintain subject.` | 2-4s | 从上帝到人间 |
| 360 Orbit | `Camera orbits 270° CCW at 54°/s over 5s. Constant 8-ft distance. Subject frame-center.` | 4-8s | 全展示 |
| Spiral(螺旋) | `Simultaneous rise 15 ft + orbit 180° over 5s. 2.5 ft/s vertical + 36°/s horizontal.` | 4-8s | 梦幻 |
| Rack Focus | `Rack focus FG(2 ft)→BG(25 ft) over 1.5s. Midfield blurs. f/1.4.` | 0.5-2s | 引导注意 |
| Dutch Angle(斜角) | `Frame tilted 20° CCW. Diagonal horizon. Hold throughout clip.` | 3-8s | 心理失衡 |
| Push-In + Zoom(dolly zoom) | `Simultaneous dolly forward 5 ft AND zoom to 85mm over 3s. Compression illusion.` | 2-4s | Vertigo 效果 |
| Parallax Pan(视差) | `Pan left 20° over 3s. FG moves 100%, mid 65%, BG 35%.` | 2-4s | 层深 |
| Whip Transition(甩切) | `Whip pan/blur A→B in 0.5s. Motion blur obscures cut point.` | 0.4-0.7s | 隐藏剪辑点 |
| Lock-Off(死机位) | `Camera locked. Zero movement. Subject moves through frame.` | 2-6s | 观察者 |
| Crash Zoom In | `Explosive zoom from wide to ECU on [subject]'s eyes in 0.8s. Motion-blurred streaks.` | 0.5-1s | 打点/情绪 |
| Bullet Time | `Camera orbits 180° around suspended [subject] frozen mid-air over 3s. Debris hangs motionless.` | 3-6s | 视觉炸点 |
| Fisheye | `20mm ultra-wide fisheye. Extreme barrel distortion at edges. Subject center.` | 2-5s | Vlog/魔幻 |
| Timelapse | `Timelapse: 8 hours compressed to 4s. Clouds streak, shadows sweep, humans blur.` | 2-6s | 时间尺度 |
| Hyperlapse | `Hyperlapse walking through [location]. Locked-on subject as background streams past.` | 3-8s | 空间尺度 |

**组合规则:** 单镜 4-8s 可叠加 2-3 个运动(如 "dolly forward + whip pan + tracking")。**超过 3 个 → 观感混乱,退回 form_strategy 拆镜。**

---

## 五、灯光库(6 个高频 · 精确到 K 值)

| 布光 | prompt | 情绪 |
|---|---|---|
| Golden Hour | `Warm 3000K directional light at low 15° angle (sun near horizon). Diffused atmospheric haze. Shadows have warm 2000K spill.` | 温暖/怀旧 |
| Practical Tungsten Household | `Visible 2700K table lamp/ceiling fixture as primary source. Warm spill. Natural window ambient at 20-30% fill.` | 家居/亲密 |
| Chiaroscuro | `Hard 3000K key at 45° left. Fill 10-15%. Rim 40%. 85% frame in shadow, 15% illumination. Black crush.` | 悬疑/张力 |
| Silhouette Backlit | `Subject fully backlit against bright 5000K BG (window/fire/sunset). Zero fill. Rim only defines outline.` | 神秘/离别 |
| Soft Overcast | `Diffused uniform daylight 5500K. No harsh shadows. Soft edges, 10-ft soft-edge radius. Omnidirectional.` | 清晰/日常 |
| Volumetric God Rays | `Directional 3000K key through particle-filled atmosphere. Visible light shafts. Dust motes in beams. Lens flare at source.` | 神性/宏大 |

⚠️ **本项目禁用** 的布光:
- ❌ Cyberpunk Neon(饱和 140%+ · 蓝紫强对比)—— 违反禁蓝紫铁律
- ❌ Moonlit Cool Blue(6500K+ 冷蓝调 · 蓝紫像素占比会 fail palette gate)—— 除非本条形态明确要冷冽情绪,且和视觉语言策展师对齐
- ❌ Fluorescent Institutional(冷绿色偏)—— AI 味重

---

## 六、i2v 专用规则(有 GPT-image-2 首帧图时)

参考 `pipeline/gen_video_frames.py` 的 4 段 motion prompt(短片《熊熊》S01-S04)——是本项目验证过的 i2v prompt 范式。

### 铁律
1. **prompt 只描述"动作变化",不重复描述人物/场景/环境**——首帧图已经承担
2. **相机运动幅度不能太小**:zoompan `zoom_max < 1.05` 肉眼看不出;i2v 也一样,`camera slowly pushes in 3-5%` 起,别写 `1-2%`(见 memory `feedback_zoompan-visible-motion`)
3. **NEGATIVES 段必写** — grok-imagine 尤其容易幻觉:
   ```
   IMPORTANT NEGATIVES: NO face morphing, NO body stretching, NO limb elongation, 
   NO rubber-band arms, NO warping, NO ghosting, NO extra fingers.
   ```
4. **情感/温度限定** — 反例见 memory `feedback_no-exaggerated-cold-atmosphere`:
   ```
   NO visible breath puff from mouth, NO white vapor, NO cigarette smoke, 
   NO cold blue tint on skin.  (温馨场景禁刻意冷渲染)
   ```
5. **人物一致性锚点** — 每次都重复 anchor 特征(如 "40-year-old woman with long black hair, oval face, in cream pajamas"),防跨段漂移
6. **生成完必做逐帧 QA** — 幻觉/伪影/尺寸变化都要挑,不能"跑通就发"(memory `feedback_camera-motion-vs-i2v-ceiling`)

---

## 七、视频模型分工(不当"默认")

**这一节是决策辅助;真正拍板走 SYSTEM §4.2 form_strategy 五维打分。**

### 7.1 项目已接 / 待接状态(2026-07-20)

| 模型 | 状态 | pipeline 入口 | 备注 |
|---|---|---|---|
| **grok-imagine-video** | ✅ 已接 | `pipeline/gen_video_frames.py` · 各 `gen_*_motion.py` | 本项目唯一现役 i2v |
| **Seedance 2.0** | 🟡 stub(env + gen_video.py 已建,待用户补 API key) | `pipeline/p011_seedance_i2v/gen_video.py` | 云雾中转 `doubao-seedance-2-0` |
| Kling / Runway / Luma / Wan / HunyuanVideo / Veo | ⚪ 未接 | — | skill prompt **也能用**,手工粘到各家 web/API |

### 7.2 场景 → 模型倾向

| 情况 | 已接的选谁 | 若考虑接新的选谁 |
|---|---|---|
| 需要**明确相机运动**(bullet time / 360 / crash zoom) | grok 试,幅度 3-5% 起 | Seedance 2.0(Higgsfield 词典本就是给它) |
| **人体细致动作**(手/脚/说话嘴形/走姿) | grok 谨慎 · 加详细 NEGATIVES | Kling 3.0(人体物理业内最稳) |
| **氛围/环境类**(空镜/风景/静物) | grok 够用 | 差异不大,不为此接新模型 |
| **已有 grok 跑通的选题续做** | grok | §4.2 tie-breaker 少赶工 |
| 需要**照片级真实**(反 AI 味刚需) | grok 塑料感明显,先上真实 B-roll | Seedance 或 Kling |
| 需要**长时长**(>10s 单镜) | 都 ≤10-15s,拆多段;grok 每段 5-10s | 同上 |
| 需要**电影级镜头语言**(景深/焦距/构图) | grok 有限 | Seedance 或 Runway Gen-4 |
| **投后差评"AI 味重"** | 换真实 B-roll 或 P001 截图 | Seedance/Kling 试;仍差 → 弃 i2v 上真实 |

### 7.3 skill 不依赖任何具体模型接入

只要项目里存在**任何一个能生成视频的通道**——已接的 API / 未接但你有手动账号 / 剪映 AI 生成 / 网页版模型——都可以把本 skill 输出的 prompt 拿去用。skill 输出是**结构化 prompt 文本**,不是脚本代码。**没有 Seedance 也完全能跑。**

---

## 八、Prompt 骨架(粘贴即用)

```
[意图声明] 本镜服务:completion_3s / completion_rate / 收藏率 / 评论率(单选)

[钩子·0-2s] 
[从§三选 1-2 种,精确到 0.1s 时间戳,写出感官刺激]

[主动作·2s-<end>s]
[i2v: 只写动作变化 · t2v: 写完整场景]
[镜头运动: 从§四选 1-2 个 · 精确速度 ft/s + 时长]
[灯光: 从§五选 1 个 · K 值 + 角度 + 比例]

[人物 anchor · 每次重复]
[year-old 性别 hair face body / 服装 / 姿态锚点]

[技术规格]
Focal length: 35mm cinema equivalent  (变量: 24 广/50 人像/85 特写)
Depth of field: f/1.4 shallow  (变量: f/2.8 mid / f/5.6 deep)
Duration: 5s  Aspect ratio: 9:16  Resolution: 720p

[Look ref]
Photorealistic, Kodak Portra 400 film grain, [warm/cool] [mood]  
No AI/rendered/artificial words.

[NEGATIVES · 铁律强绑]
NO face morphing, NO body stretching, NO limb elongation, NO warping, NO ghosting.
NO breath puff, NO white vapor, NO cold blue tint. (温馨场景)
NO neon purple/pink/cyan, NO Dracula palette, NO dark developer-tool canvas.  (禁蓝紫+禁AI味深色)
NO on-camera speaking. (非出镜型)
```

---

## 九、按形态深钻子 skill(15 个 · 2026-07-20 全量装)

**本 skill = 总门(铁律 + 通用公式)。真做某个形态的视频时,继续加载对应的子 skill 拿到形态专属公式(食欲诱惑 macro/漫画式动效/机甲战斗节拍等)。**

15 个 video-form-* 子 skill 已在 `.agents/skills/`,frontmatter 都带中文+EN 触发词,Claude 会按选题形态自动加载:

| 子 skill | 触发形态 | 中文触发词(节选) |
|---|---|---|
| `video-form-cinematic` | 电影感/胶片质感 | 电影感 · 大片 · Hollywood · 戏剧性打光 · 景深 · noir |
| `video-form-3d-cgi` | 3D 渲染/照片级 CG | Pixar · Unreal · Blender · Octane · 光线追踪 · PBR |
| `video-form-cartoon` | 2D 动画 | 卡通 · 赛璐璐 · 手绘 · 扁平矢量 · 水彩 · motion graphics |
| `video-form-comic-to-video` | 漫画动画化 | 漫画转视频 · 条漫动效 · manga 动画 · 分镜动画 |
| `video-form-fight-scenes` | 打斗/动作 | 武打 · 追逐 · 超级英雄 · 剑战 · 拳脚 · 兵器 |
| `video-form-anime-action` | 日漫 | 日漫 · 机甲 · 少年漫 · isekai · OP/ED |
| `video-form-motion-design-ad` | SaaS/软件动效广告 | 产品发布动效 · UI 动效 · 图形动画 · 软件广告 |
| `video-form-ecommerce-ad` | 电商带货 | 带货短片 · 种草视频 · 拆箱 · 淘宝/抖音商品广告 |
| `video-form-product-360` | 转台/多角度产品秀 | 产品 360° · 转台 · 多角度 · 材质秀 · turntable |
| `video-form-music-video` | MV/节拍同步 | MV · 音乐视频 · beat sync · 可视化 |
| `video-form-social-hook` | 病毒短视频钩子 | 抖音钩子 · Reels 钩子 · scroll-stopping · TikTok hook |
| `video-form-brand-story` | 品牌故事/企业叙事 | 品牌故事 · 创业故事 · 使命 · about us · 企业文化 |
| `video-form-fashion-lookbook` | 时尚/穿搭/走秀 | lookbook · 走秀 · 穿搭 · OOTD · runway · streetwear |
| `video-form-food-beverage` | 美食/饮品/ASMR | 美食 ASMR · 餐厅 · 菜谱 · 咖啡 · 食欲诱惑 · mukbang |
| `video-form-real-estate` | 房产/建筑漫游 | 房屋参观 · 建筑 · 室内设计 · 房产漫游 · property tour |

**调用顺序**(强制):
1. **先** 读本 skill(`i2v-video-prompt`)—— 拿项目铁律 + 通用 2s 钩子/镜头运动/灯光公式 + prompt 骨架
2. **再** 按形态挂载对应 `video-form-{X}` —— 拿形态专属公式(如 food-beverage 的"macro 特写 + 咀嚼 foley + 3200K 暖色"这类通用 skill 给不出的东西)
3. 两者产出**合并**成最终 prompt

**注意事项:**
- 子 skill 正文内可能出现"for Seedance 2.0 on Higgsfield"等原始表述(蒸馏自 Higgsfield 官方 skill 库),**忽略平台绑定**——skill 输出的公式对**任何视频模型**通用
- 子 skill 内的钩子/镜头/灯光**必须过本 skill §一的项目铁律** —— 冲突时铁律优先(尤其禁蓝紫/禁 AI 味深色 vs 子 skill 里的 "cyberpunk neon" / "cool blue moonlit" / "dark developer canvas")

---

## 九·补 · higgsfield MCSLA 生态(2026-07-20 全量装 · MIT)

除 15 个形态专属 `video-form-*` 外,项目还装了 [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)(MIT · MCSLA 元公式生态):

- **主门:** `.agents/skills/higgsfield/SKILL.md` — MCSLA 公式(Model/Camera/Subject/Look/Action)· HARD RULES · 路由表 · shared refs(vocab.md · model-guide.md · image-models.md · prompt-examples.md · photodump-presets.md · production-benchmarks.md · DISCIPLINE.md · INDEX.md)
- **30 个 higgsfield-* 子 skill**(各自独立触发,按用户提问自动挂):

| 类别 | 子 skill |
|---|---|
| 相机运动/运镜 | `higgsfield-camera` · `higgsfield-motion` · `higgsfield-vibe-motion` |
| 模型对比 | `higgsfield-models` · `higgsfield-seedance` · `higgsfield-seedance-vfx` · `higgsfield-gpt-image-2` |
| 视觉方向 | `higgsfield-cinema` · `higgsfield-style` · `higgsfield-moodboard` · `higgsfield-canvas` |
| 角色/表演 | `higgsfield-soul`(Soul ID 一致性)· `higgsfield-character-design` · `higgsfield-facs`(FACS 微表情) |
| 生产/流程 | `higgsfield-pipeline` · `higgsfield-shotlist-director` · `higgsfield-content-factory` · `higgsfield-recipes` |
| 场景专项 | `higgsfield-motion-design` · `higgsfield-image-shots` · `higgsfield-mixed-media` · `higgsfield-marketing-studio` · `higgsfield-audio` |
| 元技艺 | `higgsfield-prompt`(MCSLA 公式深度)· `higgsfield-assist` · `higgsfield-troubleshoot`(和项目 `[[i2v-video-diagnose]]` 互补) |
| 平台耦合(项目可忽略) | `higgsfield-apps` · `higgsfield-workspaces` · `higgsfield-recall` · `higgsfield-stack` — 这几个假设你在用 Higgsfield workspace,项目**不订阅 Higgsfield**,忽略即可 |

**调用优先级(2026-07-20):**
1. **本 skill(i2v-video-prompt)最优先** — 项目铁律 + 通用公式在这里,先读
2. **video-form-{形态}** — 按选题形态挂载(15 选 1)
3. **higgsfield-{X}** — 按具体问题触发(如问相机运动挂 higgsfield-camera + higgsfield-motion;问 Soul ID 挂 higgsfield-soul;问失败诊断挂 higgsfield-troubleshoot **但优先** `i2v-video-diagnose`)
4. **higgsfield 主门** — 元公式 MCSLA 深度调用,或跨形态复杂需求时的调度

**铁律冲突处理**(所有 higgsfield-* 子 skill 通用):
- 子 skill 里遇到 cyberpunk neon / cool blue moonlit / dark developer canvas / 蓝紫饱和 / cold blue tint 表述 → **一律改本项目铁律替代**,不套原文
- 子 skill 里假设你在 Higgsfield workspace 里工作(如 `~/Higgsfield/...` 路径、Photodump workflow、Credit optimization) → **忽略**,只取 prompt 能力

---

## 十、来源与致谢

- **蒸馏自:** [beshuaxian/higgsfield-seedance2-jineng](https://github.com/beshuaxian/higgsfield-seedance2-jineng)(15 个 Claude skill · 全量装 · 各按 `video-form-{name}` 落地)
- **元公式生态:** [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)(MIT · 主门 + 30 子门全量装 · 见 §九·补)
- **相似资源:** [OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)(MIT · MCSLA 公式 + vocab)
- **本项目关联铁律 memory:** `feedback_no-neon-palette` · `feedback_no-ai-visual-dark-canvas` · `feedback_dense-vo-no-dead-air` · `feedback_camera-motion-vs-i2v-ceiling` · `feedback_zoompan-visible-motion` · `feedback_no-exaggerated-cold-atmosphere`
- **Seedance 官方 prompt 指南:** https://docs.volcengine.com/docs/82379/2291680
