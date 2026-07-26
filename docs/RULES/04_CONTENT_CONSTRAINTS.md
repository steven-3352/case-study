# 04 · 内容硬约束(色板 / 视觉 / 音画 / 字体 / 相机 / 道具)

> **本文规定"什么绝对不许出现在成片里"。违反 = pre_publish gate fail,登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`。**

---

## 1. 留存铁律(音画图文通用)

1. **清晰直给** — 极短时间内,用语音、文字、图像同时抓住眼球;一张图/一屏只传达一个主信息
2. **图像清晰** — 语义无歧义,画面美观;禁止用抽象图标糊弄可识别的角色/物体(工种用卡通头像,输入输出用具体物件)
3. **文字可读** — 所有大字完整可见,标题 / 拟声 / CTA 互斥布局,出图后逐张目视检查叠层遮挡

---

## 2. 禁霓虹色(2026-06-27 W27D04 教训 · DECISIONS Q9)

| 类别 | 禁用 hex/token | 改用 |
|---|---|---|
| Dracula 紫 | `#bd93f9` / `var(--purple)` | — 直接删,不替代 |
| Dracula 粉 | `#ff79c6` / `var(--pink)` | — 直接删,不替代 |
| Dracula 青 | `#8be9fd` / `var(--blue)` | 真截屏自带的系统蓝(iOS/微信),不新造蓝 token |
| 暖红→冷蓝渐变 | `linear-gradient(*,#2a0e0e,#0a0e14)` 一类 | 纯黑 `#000` 或 `#0a0e14` 单色 |
| 偏粉红 | `#ff5252` / `#ff7e7e` | 血红 `#e53935` / `#c0392b` |

### 自动兜底

```bash
python3 pipeline/gate_check_palette.py <png>
```

主色域 HSL H=240~290(蓝紫)占比 >5% 直接 fail-closed。**pre_publish 必过。**

### 允许

真截屏自带的系统色(iOS 蓝、微信绿 `#95ec69`、淘宝橙等)—— 这是真实痕迹不是色板。

### 关联 · gen_ui 禁蓝紫渐变

`gen_ui` CSS `linear-gradient` 蓝紫端触发 palette gate 5% 阈;用单色 `#0a0e14` 代替;`gen_ui` 跑完立即 palette check。

依据:memory `feedback_no-neon-palette` · `feedback_gen-ui-avoid-blue-purple-gradient`

---

## 3. 禁"AI 味"深色开发者工具风(2026-07-16 T040 教训)

视觉语言策展师起稿时**默认选"暗色画布 + 克制 accent + Linear/Vercel/Cursor 式开发者工具美学"**——这套气质本身已经是生成式 AI/AI 工具类内容的高频默认套路,构成"AI 味"信号,**不因为"克制/证据感/开发者质感"这类理由豁免。**

| 禁用 | 说明 |
|---|---|
| 自造深色画布作默认起点(如 `#0a0e14`/`#141922` 一类自定深色 canvas) | 不得作为视觉方向的默认选择 |
| Linear/Vercel/Cursor 式"暗色高对比+克制 accent"整套气质 | 同上,过度常见、一眼 AI 套壳感 |
| 冷色调(蓝/青灰)为主的背景基底 | 与禁霓虹色表的蓝紫占比铁律同源,但这条更早介入——从"选方向"这一步就排除,不等到出图后靠 gate_check 兜底 |

### 改用

**浅色/白底为主的画布起手**,除非画面内容本身**就是真实截屏、且该 app 恰好原生深色 UI**(那是真实使用痕迹,不是设计选择,允许保留)。

### 自动兜底

视觉语言策展师起稿前列的候选方向必须包含至少一个浅色方案,不得让"暗色"成为唯一默认起点;每条视觉语言约束定稿前自查一遍本表。

依据:memory `feedback_anti-ai-visual` · `feedback_no-ai-visual-dark-canvas`

---

## 4. 视频音画硬门(2026-07-04 起 · BGM 由硬门下调为条件件)

### 硬门(必满足)

- **配音(VO)** 全程覆盖,前 6s RMS ≥ -25 dB,**禁沉默钉子**
- **字幕** 叠主画面

### 条件件(按形态判定)

**BGM**:

| 形态 | 密度判据 | BGM 默认 |
|---|---|---|
| 密 VO 演示/知识型(参考 WaytoAGI / 七七 / 浙大猫学长) | VO 覆盖 ≥85% + 无 3s+ 死区 | **默认无 BGM** |
| 稀疏 VO / 出镜型 / 情感叙事型 / 带货型 | — | **默认要 BGM** |

### 外发命名

| 有 BGM | 无 BGM |
|---|---|
| `*_with_bgm.mp4` | `*_no_bgm.mp4` **直接外发**(不再是"预览件") |

依据:memory `feedback_dense-vo-no-bgm-default` · `feedback_dense-vo-no-dead-air`

---

## 5. 禁合成假 BGM

- ffmpeg `aevalsrc`/`sine`/棕噪 拼的不是 BGM,是噪音
- **真 BGM** 走用户提供 mp3 或剪映自带库

依据:memory `feedback_no-synth-bgm`

---

## 6. 密 VO 无死区(视频硬门具体化)

- 视频前 6s 禁沉默钉子设计
- VO 从 0s 覆盖
- `anullsrc` 生成静音段是 bug 不是设计
- loudnorm -16 dB 目标

依据:memory `feedback_dense-vo-no-dead-air`

---

## 7. SFX 音效层独立必需

| 4 类 | 说明 |
|---|---|
| whoosh | 场景切/转场 |
| tick | 计数/进度 |
| hit | 强调/落点 |
| ambient | 底噪/氛围 |

- 密 VO 型 BGM 可 off,**但 sfx 不 off**
- 万能公式:`ambient + riser + hit`
- 情感型走"先定情绪选音乐"分支

依据:memory `feedback_sfx-layer-required`

---

## 8. 字幕由 pipeline 自动烧

- VO 字幕**必**由 pipeline 生 SRT/ASS + ffmpeg-full 烧进 mp4
- **剪映不跑智能识别**
- 系统 ffmpeg 无 libass → 用 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`(macOS)

依据:memory `feedback_pipeline-burn-subs`

---

## 9. 大字标题重影根治

苹方无真 900 字重 → Chrome faux-bold 涂抹重影。

**解决**:已装思源黑体 Heavy,`font-family: "SF Pro Text","Source Han Sans SC","PingFang SC"`。

依据:memory `cjk-bold-font-ghosting-fix`

---

## 10. 温馨片段禁刻意冷渲染(短片场景)

- ❌ 白呼气雾 / 缩脚 / 冷蓝调
- ✅ 冬季服装 + 暖光暗示季节即可
- **主基调是暖**

依据:memory `feedback_no-exaggerated-cold-atmosphere`

---

## 11. 严禁廉价程序化背景(2026-07-26)

**PIL 渐变 + blur 多边形堆的背景一眼廉价,叠再多 rim/落影/视差也救不回。**

背景须与立绘同插画级(真素材/真纹理/图像模型),**不许现搓渐变**。

依据:memory `feedback_no-cheap-procedural-background`

---

## 12. 重点运用复杂运镜(2026-07-26)

必须覆盖:**摇 / 甩 / 跟拍 / 仰拍 / 俯视 / 环绕 / 旋转 / 推 / 拉**

**禁连续 3 镜同一 cam;分镜必先列 cam 类型再写参数。**

依据:memory `feedback_richer-camera-movements`

---

## 13. 道具必须与立绘同画风(2026-07-26)

- ❌ 实拍机器配插画人物 = 两层皮
- ✅ 生图要线稿必须把 `LINE ART` 写成**主诉求**,只写 "illustration not photo" 会拿回三维产品渲染

依据:memory `feedback_props-match-tachie-style`

---

## 14. zoompan 动画幅度过小像 PPT

- `zoom_max<1.05` + 无横向漂移 + 默认 `x=0,y=0` 不居中 → 肉眼看不出变化
- 至少 `zoom>=1.10` + 居中 + 加 pan
- 渲后须**对比首尾帧**

依据:memory `feedback_zoompan-visible-motion`

**注**:zoompan 调好参数后仍"不会动"→ 根因是相机只能移窗口不能动内容;需升级 i2v(grok-imagine-video)且过本地代理下载,生成后必须逐帧 QA 幻觉伪影。依据:memory `feedback_camera-motion-vs-i2v-ceiling`

---

## 15. i2v / t2v 视频 prompt 硬门(2026-07-20 立)

**任何**要给视频模型写 prompt(不管是 grok-imagine-video / Seedance 2.0 / Kling / Runway / Luma / Wan / HunyuanVideo / Veo / 未接入的新模型)之前,**必读** `.agents/skills/i2v-video-prompt/SKILL.md` + 按形态挂载 `.agents/skills/video-form-{X}/`(15 个子 skill)+ 需要时挂载 `.agents/skills/higgsfield-{X}/`(30 个)。

**触发关键词表见 `06_SKILL_TRIGGERS.md`。**

### 必带落地

- 2s 钩子公式
- 精确镜头运动语句(ft/s + 时长)
- 灯光 K 值
- 人物 anchor
- NEGATIVES 段(禁蓝紫 / 禁 AI 味深色 / 禁 face morphing / 温馨场景禁冷渲染)

### 违反后果

视为反 AI 味 / 禁蓝紫 / 反 template-clone 铁律未过 → pre_publish gate fail → 登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md`

依据:memory `feedback_i2v-video-prompt-skill-mandatory` · `feedback_anti-ai-visual`

---

## 16. i2v / t2v 视频生成后诊断硬门(2026-07-20 立)

视频**生成后**(mp4 已下载但你或用户觉得不满意时),**必读** `.agents/skills/i2v-video-diagnose/SKILL.md`。

### 补缺口

此前项目诊断力量集中在:
- ①事前 gate_check 门禁
- ②投后 evolution_apply/post_publish_retro

中间"这条镜为什么崩、怎么最小代价救"的层缺失——本 skill 补齐。

### 必带落地

- 4 步动作(扫描 → 7 类归因 → minimal-edit 只改 1-2 变量 → 登记 VIDEO_ITERATE_LOG)
- **3 次救不活升级换路线**(换模型/换实现/撤镜)

### 触发场景

- 视频生成完效果不满意
- 幻觉/伪影/角色崩/动作不自然/AI 味重/相机运动看不出/palette gate fail
- 用户说"这段不对/重生/改一下/为什么这么僵"

### 违反后果

瞎改 prompt 无限迭代 = 违反 D05 加速铁律。该 skill 强制"3 次上限 + 只改 1-2 变量"。

依据:memory `project_i2v-video-diagnose-skill`

---

## 17. gpt-image 多参考图 503 根因

- 503 无可用渠道是**并发过高**,不是模型名问题
- 降到 `GPT_IMAGE_WORKERS=2` 才是真解法

依据:memory `feedback_gpt-image-model-fallback`

---

## 18. 画布 · 出镜 · 双平台

### 画布

- 全局 9:16 → 1080×1920(图文 + 视频统一)
- 常量:`pipeline/screen_dims.py`

### 出镜(DECISIONS Q8)

数字人仍暂停;真人按形态:

| 形态 | 出镜 |
|------|------|
| 演示型(默认) | ❌ 全屏演示,不出镜 |
| 知识型 | ❌ 默认不出镜;可画中角上半身 |
| 带货型 | ✅ 真人(脸/手/产品)可作主画面 |
| 出镜型 | ✅ 真人为主,演示为辅 |

### 双平台(2026-07-05 起停做视频号)

- **抖音** + **小红书** 两个平台
- xhs 走视频 or 7 页图文由**形式策略官**定
- 判据:"抄下来"(图文)vs"看下来"(视频)

依据:memory `feedback_dual-platform-only`

---

## 19. 视觉路线 · 证据优先(DECISIONS Q9)

- **80% 画面** = 真实截屏/录屏(保留 URL 栏、状态栏等使用痕迹)
- **体裁混搭** — 同一套图文 ≥3 种体裁;禁多张同一 HTML 结构批量出图
- **禁作主视觉** — 黑金 `build_slides` 直出、统一备忘录 HTML 模版、精美包装帧整段停住
- **AI 生图** — 本路线不作主视觉;chaos 钩子**必须真实 B-roll**,禁 AI 替代手机场景
- 无实拍可用 `gen_evidence.py` 仿真体裁(仍须混搭、禁模版感)

---

## 20. 数据叙事分级(DECISIONS Q4 · `ops/data-policy.yaml`)

已迁至 `01_IRON_LAWS.md §11`(数据 A/B/C 分级)。**项目画面必须真实**,效果数字按 A/B/C。

---

## 21. 反 AI 味视觉风格优先(全局)

- 用户对"AI 味"零容忍
- HTML+GSAP **默认居中对齐是错的起点**
- 要走 P005 杂志 / P006 漫画风或新方向

依据:memory `feedback_anti-ai-visual`

---

## Source Map

- 原 `CLAUDE.md §内容硬约束`(留存铁律 · 禁霓虹色 · 禁 AI 味深色 · 密 VO 音画硬门 · i2v prompt 硬门 · i2v 诊断硬门 · 视频音画硬门 · 出镜)
- 原 `docs/SYSTEM.md §3.2 · 3.2a · 3.2b · 3.3`
- 原 memory:`feedback_no-neon-palette` · `feedback_no-ai-visual-dark-canvas` · `feedback_anti-ai-visual` · `feedback_dense-vo-*` · `feedback_dense-vo-no-bgm-default` · `feedback_no-synth-bgm` · `feedback_sfx-layer-required` · `feedback_pipeline-burn-subs` · `cjk-bold-font-ghosting-fix` · `feedback_no-cheap-procedural-background` · `feedback_no-exaggerated-cold-atmosphere` · `feedback_richer-camera-movements` · `feedback_props-match-tachie-style` · `feedback_zoompan-visible-motion` · `feedback_camera-motion-vs-i2v-ceiling` · `feedback_i2v-video-prompt-skill-mandatory` · `project_i2v-video-diagnose-skill` · `feedback_gpt-image-model-fallback` · `feedback_gen-ui-avoid-blue-purple-gradient` · `feedback_dual-platform-only`
