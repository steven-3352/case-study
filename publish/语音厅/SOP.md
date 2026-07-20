# 语音厅立绘 MV · 可复制 SOP

**来源:** 反向工程分析 `/Users/wmzuo/Downloads/听潮阁·礼-*.mp4` 4 条视频(2026-07-20 抽帧多模态分析)
**目标:** 换立绘/换歌/换品牌即可生成同类视频 · 不需要重画每一帧
**适用平台:** 抖音 · 小红书 · 视频号(项目已停视频号,只做抖+xhs · 见 [feedback_dual-platform-only](feedback_dual-platform-only.md))
**关联 skill:** [i2v-video-prompt](i2v-video-prompt) · [video-form-music-video](video-form-music-video) · [higgsfield-shotlist-director](higgsfield-shotlist-director) · [higgsfield-character-design](higgsfield-character-design)

---

## 一、样本共性提炼(4 视频 100% 命中)

| 维度 | 通用规格 |
|---|---|
| **格式** | 16:9 · 30fps · 720p 或 576p · 30-38 秒 · MP4/H264 · AAC 44.1kHz 立体声 |
| **主体** | **100% AI 立绘**(无真人)· 一个演唱者 = 一个虚拟形象 · 每人 1-2 张(全身立绘 + 可选 Q 版) |
| **结构** | **三段式**:群像开场(2-4s)→ 独唱轮转(每人 3-5s · N 人 = N 段)→ 群像收尾 or 假播放器 UI 收尾(3-4s) |
| **底部角色标** | 固定位置 · 格式 `T.[名字]` 或 `T.[名A]/[名B]` · 谁在唱标谁 · 底部居中或偏左 |
| **品牌水印** | 品牌英文名(如 `TINGCHAOGE`)四角淡淡打 · 不干扰主视觉 |
| **大字歌词层** | 每镜 1-3 个关键字压层 · 与开唱时机同步 · 字号 = 屏宽 30-70% · 有时错位重复 3 遍 |
| **场景切换** | 每人独唱背景不同 · 3-5s 一切 · 与角色人设/歌词意象匹配 |
| **音源** | 原歌 mp3 + 演唱者接唱录音混音 · 无 VO 旁白 |
| **字幕** | 关键歌词大字 = 视觉设计 · 全歌词小字 `.ass` 烧进 mp4(项目铁律 [feedback_pipeline-burn-subs]) |

---

## 二、4 类玩法差异化(按曲风选)

| 曲风 | 视觉主题 | 背景意象 | 字体/文字层 | 色板 | 特色技法 |
|---|---|---|---|---|---|
| **A · 流行合唱**<br>(参考:爱的主打歌) | 霓虹夜景 · 都市摩登 | 城市天际线 · 建筑夜景 · 半调网点 · 唱片圆盘 | 粗黑体 · 错位重复 3 遍 · 大字压层 | 黑金底 + 粉/水蓝/绯红霓虹 ⚠️ **本项目改用低饱和替代(见 §六 铁律)** | Q 版 + 精修立绘双风格混搭 · 收尾**假音乐播放器 UI** |
| **B · 抒情陪伴**<br>(参考:无人之岛) | 清新自然 · 治愈系 | 天蓝云海 · 爱琴海白墙 · 灯塔 · 星光 | 手写体 · 单字大字 | 天蓝 + 云白 + 冷灰 + 淡珊瑚 | **图字联动**(词面配图面 · 如"倒影"配立绘上下倒挂)· **情感道具**(花束/信纸/Q版陪衬/薯条挂件) |
| **C · 国风情歌**<br>(参考:甲乙丙丁) | 古典写意 · 冷寂哀婉 | 罗马数字时钟 · 钢琴 · 星空 · 城市剪影 · 相框边饰 | **书法毛笔字**(非黑体)· 竖排 · 错位 | 冷灰 + 水墨黑 + 淡金 | 具象化歌词(时钟/钢琴/狐狸道具)· **对称/镜像**构图 · 画框式版面 |
| **D · 嘻哈接唱**<br>(参考:怒音 rapper) | 涂鸦舞台 · 反差萌 | 血红竖条 motion blur · 涂鸦墙 · 舞台聚光 | 中英字块 · 立体粗字 · "On fire / Cuz I'm on" 类押韵字 | 血红 + 纯黑 + 白 | **Q 版为主(反差萌)** · 顶部**接唱者头像列**(10 人一字排)· 抽象 motion blur 转场帧 · 镜像 Q 版 |

**选型规则:**
- 曲风命中就走对应玩法 · 别混
- 演唱者 ≥8 人 → 优先玩法 D(接唱头像列容纳量大)
- 女声/柔情曲 → 玩法 B
- 国风/戏腔 → 玩法 C
- 主流华语流行 → 玩法 A(但需换色板 · 见 §六)

---

## 三、7 步制作流程(换立绘可复用)

### Step 1 · 拆歌词分工(前期规划 · 用户拍板)

- 全歌词按乐句拆分(通常 6-10 段)
- 每段分配一位演唱者(或群像合唱)
- 输出 `storyboard.yaml`(见 `templates/storyboard_template.yaml`):
  ```yaml
  song_title: "XXX"
  original_singer: "XXX"
  covered_by: "听潮阁·XXX"
  style: A|B|C|D            # 4 类玩法
  duration_target: 35        # 30-38s
  segments:
    - slug: intro_group
      time: [0, 3.0]
      lyrics: "XXX"           # 群像开场歌词(通常无字幕或首句)
      role_type: chorus
      characters: [all]
      scene_bg: "夜景城市"
      big_text: "TINGCHAOGE"
    - slug: solo_01_张三
      time: [3.0, 7.5]
      lyrics: "什么都想给你"
      role_type: solo
      characters: [张三]
      scene_bg: "花束+城市夜景"
      big_text: ["什么", "都"]         # 大字层
      char_pose_ref: "抱花 · 微笑"
    # ... N 段独唱
    - slug: outro_group
      time: [30.0, 35.0]
      role_type: chorus_or_ui
      characters: [all]
      scene_bg: "音乐播放器 UI"        # 或"夜景合唱"
      big_text: "歌名"
  ```

### Step 2 · 出立绘(每人 1-2 张 · GPT-image-2 首选)

- **每位演唱者**:1 张全身立绘(必)+ 1 张 Q 版(选,若玩法 A/D 需要)
- **prompt 骨架**(见 `templates/prompt_立绘_template.md`):
  ```
  Anime-style character portrait, [角色年龄/性别/身高], [服装:详细描述 · 与曲风一致],
  [表情:与人设一致 · 冷酷/温柔/俏皮 等], full body, standing pose, 
  [道具:如花束/戒指/耳机/麦克风 等],
  [背景:纯白或简单渐变 · 独立立绘 · 便于后期抠图组合],
  9:16 vertical composition (即使最终 16:9 · 立绘出 9:16 便于裁切), 
  detailed line art, cel-shading, high quality anime illustration.
  ```
- **禁用**(与项目铁律对齐):
  - ❌ 塑料感真人(反 AI 味)- 保持二次元立绘风格
  - ❌ 蓝紫霓虹主色(禁蓝紫铁律)- 走血红/深灰/水墨蓝替代
- **一致性锚点**:同角色跨镜必须**同发型/同服装/同配饰** · 记录 anchor 到 `characters.yaml`

### Step 3 · 出场景背景(可复用素材库)

按玩法准备 5-8 张背景:
- 玩法 A:城市夜景 · 半调网点 · 唱片圆盘 · 假播放器 UI 底图
- 玩法 B:天蓝云海 · 爱琴海建筑 · 灯塔 · 信纸 · 花田
- 玩法 C:罗马数字时钟盘 · 钢琴 · 星空 · 相框边饰 · 城市剪影
- 玩法 D:血红 motion blur 底 · 涂鸦墙 · 舞台聚光

**复用策略**:场景库分 A/B/C/D 4 组 · 每组一次做齐后**跨条复用**(不违反反 template-clone · 因为**背景是能力素材库不是分镜内容** · 见 [feedback_skill-vs-template-distinction](feedback_skill-vs-template-distinction))

### Step 4 · 大字歌词层(按玩法配字体)

- 玩法 A:粗黑体 · 错位复制 3 遍 · 抖动效果
- 玩法 B:手写体 · 单字大 · 淡入淡出
- 玩法 C:书法毛笔字 · 竖排 · 逐笔露出
- 玩法 D:立体粗字块 · 中英字混排 · 摇晃/闪光

**统一格式**:字号 = 屏宽 30-70% · 与开唱时机同步(音画铁律)

### Step 5 · 时间线组接(FFmpeg 主导 · 复用 p004_video/lib)

- 场景切换用 fade / whip pan / motion blur(玩法 D 尤其)
- 每段 3-5s · 整体 30-38s
- 底部固定 `T.[名字]` 角色标 + 品牌四角水印
- 玩法 D 顶部**全程**10 人头像小列固定(接唱标识)

### Step 6 · 音画同步 + 字幕烧录

- BGM = 原歌 · 演唱者接唱声音混入 · loudnorm -16dB(项目铁律 [feedback_dense-vo-no-dead-air])
- 全歌词生成 `.ass` · `ffmpeg-full`(macOS `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` 含 libass)烧进 mp4([feedback_pipeline-burn-subs])
- **不能后期在剪映烧** · 必须 pipeline 一次到位

### Step 7 · gate 门禁 + 三平台适配

- `pipeline/gate_check_media.py`(时长/黑帧/静音/规格 fail-closed)
- `pipeline/gate_check_palette.py`(禁蓝紫 · >5% fail 返工)⚠️ **玩法 A 原样式高危 · 见 §六**
- 生成后走 [i2v-video-diagnose](i2v-video-diagnose) 4 步诊断(若崩)
- 三平台文案:抖音竖屏首帧含钩子 · xhs 图文轮播备份(见 [feedback_dual-platform-only](feedback_dual-platform-only))

---

## 四、SOP 与项目 4 步 5 拍板点的映射

| 项目 4 步 | 语音厅立绘 MV 对应动作 | 👤 用户点 |
|---|---|---|
| **1 选题** | agent 从 material/ 翻歌单原矿 → 扩展 N 条(歌 × 演唱者组合)| ① 定方向 ② 拍板 1 条 |
| **2 前期** | 洞察包(演唱者人设/歌词意象/翻唱与否合规)→ 拆歌词分工 → 出 storyboard.yaml → 视觉玩法定 A/B/C/D | ③ 拍板脚本(=歌词分工+人设)+ 形态大方向(玩法 A/B/C/D)· ④ 抽验立绘一次 |
| **3 制作** | 出立绘 → 场景背景组 → 大字层 → FFmpeg 组接 → 字幕烧 → gate 门禁 → 生成后诊断 | 无(除非诊断 3 次仍崩) |
| **4 交付+复盘** | 三平台包 → 用户外发 → 48h/7d 数据回填 → `evolution_overlay` 反哺下条 | ⑤ 外发 |

**周维度 A/B 测试**:一周 D01-D07 走"同主题簇不同形"([project_weekly-form-ab-test](project_weekly-form-ab-test))时,**7 天里最多 2-3 天用本类 SOP**,其余走不同渲染家族(P001/P004/P006 等),避免三维伪多样。

---

## 五、素材复用与增量成本

| 换新歌新演唱者时 · 需重新做的 | 可直接复用的 |
|---|---|
| 演唱者立绘(1-2 张/人) | 场景背景库(4 组玩法各 5-8 张) |
| 每段大字歌词内容 | 字体/排版/动效模板 |
| 分工与 storyboard | FFmpeg 组接脚本 · 字幕烧录 pipeline |
| 底部角色标 `T.[名]` 文字 | 品牌水印 · 底部角色标位置/字号 |
| 音源(原歌 + 接唱录音) | 声音处理链 · loudnorm 参数 |

**首次做**成本约 6-8h(立绘出图 + 场景库 + storyboard + 组接)· **续做**约 2-3h(仅换立绘 + 大字歌词 + 组接微调)。

---

## 六、项目铁律绑定(重要)

样本视频的部分视觉选择**违反本项目铁律**,复制时必须替代:

| 样本原样 | 违反的项目铁律 | 复制时替代方案 |
|---|---|---|
| 玩法 A 大量霓虹粉紫蓝 | [feedback_no-neon-palette](feedback_no-neon-palette) 禁 Dracula 系 | 血红 `#e53935` + 深金 + 冷灰;水蓝改真截屏系统蓝(iOS/微信) |
| 玩法 A/D 纯黑深色 canvas | [feedback_no-ai-visual-dark-canvas](feedback_no-ai-visual-dark-canvas) 禁 AI 味深色 | 娱乐 MV 深色**允许**(有环境实感:舞台/夜景/rap 场景)· 但**不能是纯黑纯 canvas** · 必须有具体环境元素 |
| 玩法 D motion blur 抽象转场 | 无违反,但需过 gate_check_media(避免被判为"黑帧/花屏") | 转场帧 ≤ 0.5s · 前后镜清晰 |
| 立绘 AI 生成 | 不违反 [feedback_anti-ai-visual](feedback_anti-ai-visual)(那条针对**塑料感真人磨皮**)· 二次元立绘是**受众接受的产品视觉语言** | 保持原样 · 但立绘 anchor 必须一致(禁跨镜换脸) |
| 玩法 B/C 冷蓝调 | 若冷蓝像素占比 >5% 触 gate_check_palette | **保留但控占比** · palette gate 前置跑一次自查 |

**pre_publish 硬门**:每条外发前必过 `pipeline/gate_check_media.py` + `pipeline/gate_check_palette.py`(玩法 A 最容易挂,palette 门要提前跑)+ `pre_publish_forecast ≥ B`(见 [feedback_audience-first](feedback_audience-first))。

---

## 七、下一步落地建议

1. **首条试跑**:用玩法 B(抒情陪伴 · 色板最安全)+ 一首简单流行歌 + 3-5 个新立绘 · 走完 4 步 5 拍板点跑通
2. **建 pipeline**:确认可跑后,可考虑建 `pipeline/p012_voice_lounge_mv/`(与 P011 同结构 · 立绘+大字+组接一体化 · 参考 `pipeline/p004_video/lib/` config-driven 模式)—— **但不预建**,等首条真跑通再拆 lib(教训见 [project_p011-seedance-i2v-candidate](project_p011-seedance-i2v-candidate) · 一次到位而非 stub)
3. **接入 skill**:agent 自动挂 `[[higgsfield-character-design]]`(立绘)· `[[higgsfield-shotlist-director]]`(分镜)· `[[video-form-music-video]]`(节拍同步)· `[[higgsfield-cinema]]`(视觉方向)· `[[higgsfield-soul]]`(跨镜一致性)· `[[higgsfield-motion]]`(动效)· `[[higgsfield-vibe-motion]]`(节拍运镜)

---

## 九、动效层清单(2026-07-20 补 · 用户指出漏洞后深挖)

**方法学:** 场景检测(`ffmpeg -vf select=gt(scene,0.25)`)定位每视频真实转场时间戳 + 转场点 ±0.5s 密集抽帧(10fps)· 逐帧观察动效细节。

**样本关键数据:**
| 视频 | 转场数(37s 内) | 平均切镜间隔 | 转场类型 |
|---|---|---|---|
| V1 爱的主打歌 | **37 个** | ~1s(高密度 · 卡节拍) | Vertical motion blur whip 为主 · 有 3 帧内闪切三连 |
| V2 无人之岛 | 9 个 | ~3s(节奏舒缓) | Hard cut + 180° flip 呼应"倒影" |
| V3 甲乙丙丁 | 17 个 | ~2s(中密度) | Hard cut · 慢速淡入 · slat 竖分屏 slide-in |
| V4 怒音 rapper | 21 个 | ~1.4s(高密度 · rap 节拍) | Hard cut · 抽象 motion blur 转场帧 · 逐字露出大字 |

### 9.1 转场动效家族(6 类)

| # | 转场名 | 时长 | 视觉特征 | 出现在 | FFmpeg 实现 | HTML+GSAP 备选 |
|---|---|---|---|---|---|---|
| **T1** | **Vertical Motion Blur Whip** | 100-200ms | 竖条纯模糊擦除 · 中间帧全糊 · 力量感 | V1 主用 | `xfade=transition=vuwind:duration=0.15` + `boxblur=1:8:1:8` | GSAP + CSS `filter:blur(40px)` + `scaleY(1.5)` |
| **T2** | **Hard Cut**(硬切) | 0ms | 无过渡 · 卡歌词/鼓点重音 | V3/V4 主用 · V2 独唱段 | 直接 `concat` | 直接 replace |
| **T3** | **Flip Vertical 180°**(倒影翻转) | 200-400ms | 全画面 or mask 内 180° 上下翻转 · 图字联动 | V2 "倒影"歌词处 | `vflip` + `xfade=transition=distance:duration=0.3` | CSS `transform:rotateX(180deg)` + `transition:0.3s ease-in-out` |
| **T4** | **Slat / Panel Slide-In** | 300-500ms | 立绘竖长方形格逐个从侧面滑入 · 4-6 slat 排开 | V3 5s 处 | 多层 overlay · 每层 `x='max(-W,W-t*W*2)'` 位移 | GSAP `stagger:0.1` slide from side |
| **T5** | **Zoom + Motion Blur** 抽象转场帧 | 200-400ms | 无立绘 · 纯血红/黑竖条 motion blur | V4 5s / 15s | `boxblur=15:15` + `nullsrc` 帧 | CSS `filter:blur(30px)` + 空画面 |
| **T6** | **Cross-fade(渐隐叠溶)** | 500-800ms | 前一场景渐消 + 下一场景渐现 | V3 慢速切场 | `xfade=transition=fade:duration=0.6` | GSAP `opacity` timeline |

### 9.2 立绘/场景动效家族(7 类 · 全片持续)

| # | 动效名 | 特征 | 视频 | FFmpeg 实现 | GSAP 备选 |
|---|---|---|---|---|---|
| **A1** | **Ken Burns(zoompan 缓推)** | 立绘 1.0→1.10 缓推 · 5-8s · 防 PPT 感 | 全 4 视频通用 | `zoompan=z='min(pzoom+0.0008,1.10)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720` | GSAP `scale 1→1.1` 5s ease |
| **A2** | **Multi-layer Parallax** | 前景立绘慢速位移 · 背景快速位移 | V1、V3 | 双层 zoompan 不同 `pzoom` 增量 | GSAP 两层 `x` 位移不同 velocity |
| **A3** | **Alpha Fade 错峰入场** | Q 版立绘一个个 fade in · 错开 0.2-0.5s | V1 intro 3-5s | 多层 `fade=in:st=0.2*N:d=0.4` stagger | GSAP `stagger:0.2` opacity |
| **A4** | **半透明 PIP overlay** | 主角色实体 + 另一角色**半透明大轮廓**(alpha 0.3-0.5) | V4 5.2s 转场 | 双层 `overlay=x=X:y=Y` + `format=yuva444p,geq=a='0.4*A'` | CSS 双层 `opacity:0.4` overlay |
| **A5** | **场景 vfx 层**(火焰/粒子/光晕) | 全片持续叠加 · 增加"活"感 | V4 血红火星 · V3 光晕 · V1 光斑 | 循环粒子 png 序列 `overlay=x='mod(t*100,W)'` · 或 alpha video overlay | Canvas / three.js / Lottie |
| **A6** | **Circular Mask**(圆框蒙版) | 圆形/椭圆蒙版 · 内可 flip/zoom | V2 倒影(f004→f007) | `format=yuva444p,geq='if(gt((X-W/2)^2+(Y-H/2)^2,R^2),0,alpha(X,Y))'` | CSS `clip-path:circle(50%)` |
| **A7** | **Chibi Stack** | 多个 Q 版立绘堆叠展示 · 增加视觉密度 | V1 intro · V4 全片 | 多个 `overlay` 静态叠 | 多个 img 绝对定位 |

### 9.3 大字层动效家族(6 类)

| # | 动效名 | 时长 | 视觉 | 出现在 | FFmpeg 实现 | GSAP 备选 |
|---|---|---|---|---|---|---|
| **B1** | **打字机 / 逐字露出** | 300-600ms | 大字逐字出现 · 卡歌词节拍 · 每字 100-150ms | V4 "上刀山" 逐字 | 多次 `drawtext text='...':enable='between(t,X+N*0.1,end)'` 叠加 | GSAP `SplitText` + `stagger:0.1` |
| **B2** | **错位重复 3 遍** | 全段持续 | 同字复制 3 遍 · 位置偏移 20-40px · alpha 0.5/0.7/1.0 递减 | V1 "听两次" | 3 个 drawtext 位置偏移 + `alpha=0.5/0.7/1.0` | 3 span 绝对定位 · CSS `transform:translate` + `opacity` |
| **B3** | **快闪压层** | 100-200ms | 大字瞬间放大到占屏 30-70% · 200ms 内 | V1 "HEY" · V3 结尾"甲乙丙丁"歌名 | `drawtext=fontsize=200:enable='between(t,X,X+0.2)'` | GSAP `scale:0→1` + `ease.back` 200ms |
| **B4** | **书法慢速淡入** | 500-1000ms | 书法字层缓慢 opacity 0→1 | V3 全片 | `drawtext + alpha='if(gt(t,X),min((t-X)/0.8,1),0)'` | GSAP `opacity` 800ms ease |
| **B5** | **立体粗字块 · 多层阴影** | 静态 | 3D 立体字 · 多层 shadow 叠出厚度 | V4 "On fire" · "天花板" | drawtext 多次调用 · 每次 `x/y` +5px 偏移 · 不同 color 叠加 | CSS `text-shadow: 5px 5px 0 red, 10px 10px 0 black` |
| **B6** | **横竖字混排** | 静态 | 同镜内横字 + 竖字 + 英拼音 | V3、V4 常用 | 多个 drawtext 不同 `angle` | 多 CSS `writing-mode: vertical-rl` |

### 9.4 音画节拍对齐(必须)

**共性规律:切镜 = 音乐鼓点。** 违反 = 拖沓感。

- V1(37 转场 / 38s):**每 1s 一次切镜** · 副歌部分闪切三连(150ms 内 3 次)· 卡副歌鼓点
- V4 rap:**闪切二连**(70-100ms 内 2 次)· 卡 rap 押韵重音
- V2/V3 抒情:**3-5s 一切** · 卡乐句结尾

**实现流程:**
1. Audacity 或 python `librosa` 提取歌曲 onset(鼓点/vocal 起始)时间戳 → 生成 `beat.json`
2. storyboard.yaml 每段 `time: [X, Y]` **强制对齐** beat.json 中的 onset
3. FFmpeg concat 严格按 storyboard 时间(不能因渲染慢自动微调)

### 9.5 特殊 vfx(视频 4 独有 · 玩法 D 可选)

| # | vfx 名 | 视觉 | FFmpeg 实现 |
|---|---|---|---|
| **X1** | **RGB 分离** / chromatic aberration | 字层横向 3-6px 偏移 · R G B 三色分离 | `split=3[R][G][B];[R]lutrgb=g=0:b=0[r];[G]lutrgb=r=0:b=0[g];[B]lutrgb=r=0:g=0[b]` + 各自 `overlay` 位移 |
| **X2** | **VHS 扫描线** | 每 2 行有暗线 · 复古感 | `geq='r(X,Y)*(1-0.15*mod(Y,2)):g(X,Y)*(1-0.15*mod(Y,2)):b(X,Y)*(1-0.15*mod(Y,2))'` |
| **X3** | **胶片颗粒** | 全片持续噪点 · 电影感 | `noise=alls=8:allf=t+u` · 强度 5-10 |
| **X4** | **Bloom / 辉光** | 亮部溢出发光 | `unsharp` + `blur` + `blend=all_mode=addition` 合成 |

### 9.6 实现路线选型(每镜)

按 [SYSTEM.md §4.2](../../docs/SYSTEM.md) 五维打分选:

| 需求 | 优先方案 | 备选 |
|---|---|---|
| 立绘 zoompan / 简单 fade / 静态叠层 | **FFmpeg 原生**(pipeline/p004_video/lib 已有能力) | — |
| 大字打字机 / 错位重复 / 立体阴影 | **FFmpeg drawtext**(足够 · 便宜) | HTML+GSAP 截屏(若需复杂 easing) |
| Motion blur whip / slat slide-in / 圆框 mask | **FFmpeg xfade + geq**(能做) | HTML+GSAP 截屏(复杂动效更快出) |
| Bloom / 粒子系统 / 复杂 vfx | **HTML+GSAP + Canvas**(pipeline/p004_video 已跑通) | AE 手工(极复杂 · 慢) |
| RGB 分离 / VHS / 胶片颗粒 | **FFmpeg lutrgb + geq**(纯滤镜够) | — |

**优先级铁律:** 能 FFmpeg 就 FFmpeg(便宜快)· 复杂动效走 HTML+GSAP 截屏 · **AE 手工只在其他都做不出时用**(违反 [feedback_d05-parallel-agents](feedback_d05-parallel-agents) 60min 目标)。

### 9.7 storyboard.yaml `effects:` 字段(新增)

模板见 `templates/storyboard_template.yaml`,现在增加每段 effects 声明:
```yaml
- slug: solo_01
  time: [3.0, 7.5]
  # ... existing ...
  effects:
    transition_in: T1_vmotion_blur_whip     # 从上段进入本段的转场
    transition_in_duration: 0.15
    portrait_motion: A1_ken_burns            # 立绘全段动效
    portrait_zoom_max: 1.10                  # >= 1.10 才肉眼可见(memory 教训)
    overlays:
      - type: A5_vfx_particles
        asset: assets/vfx/red_sparks.png     # 或 alpha video
        opacity: 0.6
    big_text_effect: B2_offset_repeat_3x     # 大字动效
    beat_align: [3.2, 5.5, 7.0]              # 卡这几个鼓点切镜/大字出现
```

**agent 在 Step 2 前期规划时**必须为每段声明 effects · 未声明视为默认 A1 + B1 + T2(最保守组合)。

---

## 十、参考文件

- 单视频细节分析(含 §动效细节):`analysis/01_love_theme_song.md` · `analysis/02_desert_island.md` · `analysis/03_abcd.md` · `analysis/04_rapper.md`
- storyboard 模板(含 effects 字段):`templates/storyboard_template.yaml`
- 立绘 prompt 模板:`templates/prompt_立绘_template.md`
- 原视频文件(未追踪 git):`/Users/wmzuo/Downloads/听潮阁·礼-*.mp4`(4 条)
- 抽帧供后续对照:`tmp/tingchaoge_analysis/01-04*/f_*.jpg`(134 张)
