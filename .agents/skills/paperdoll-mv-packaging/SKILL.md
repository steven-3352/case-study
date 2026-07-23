---
name: paperdoll-mv-packaging
description: |
  [中文触发] 国风乙 / 古风 / 角色PV / 纸片人立绘卡点 MV 的**包装设计规范**（确定性 motion-graphics 层，非 i2v prompt 层）。当用任意静态立绘/角色卡面做卡点 MV、角色 PV、立绘动效包装、音乐可视化，且要求「立绘像素不变、只做外层包装/动效/卡点」时调此 skill。提供：灵魂三件套 + 五层包装系统（每层含地板/进阶/提升3级三档做法）+ 6 套风格预设库 + 卡点动效字典 + 代码落地接口（gen_paperdoll_pv.py）+ 复用 checklist。
  [EN] Design system for paper-doll (flat 2D portrait) beat-sync music videos / character PVs in the 国风乙 (Chinese otome) aesthetic. Deterministic motion-graphics packaging layer (NOT an i2v/t2v prompt skill). Use when animating static character art into a beat-synced MV where the portrait pixels MUST stay pixel-identical and only the outer packaging / FX / beat-sync changes. Triggers: paper-doll MV, 立绘卡点, character PV, 角色PV, 国风乙 MV, portrait animation, cutout beat-sync, 纸片人动效.
platforms:
  - claude-code
  - cursor
  - codex
---

# 国风乙纸片人卡点 MV · 包装设计规范

> **定位**：把一张（或几张）**静态立绘/角色卡面**做成一条**卡点音乐 MV / 角色 PV**，
> 立绘像素**零改动**（只做仿射变换 + 裁切换景别 + alpha 边缘处理），
> 其余一切（背景、边框、光效、胶片质感、字幕、卡点动效）**全部可设计**。
>
> **本 skill 是「怎么包装」的方法论 + 风格库 + 代码接口，跨选题复用**（skill，不是一次性分镜模板）。
> 与 `video-form-music-video`（i2v/t2v prompt 层）**互补**：那条给"让模型生成一段视频"写 prompt；
> 本条给"用确定性 Python motion-graphics 把不动的立绘卡点动起来"定规范。
>
> 参考实现：`pipeline/voice_room/gen_paperdoll_pv.py`（《明月天涯》纸片人卡点 PV）。

---

## 0. 不可违反的铁律（每套风格、每一帧都适用）

| # | 铁律 | 判据 |
|---|------|------|
| **R1** | **立绘像素零改动** | 只允许：仿射（位移/缩放/旋转）、裁切换景别、alpha 边缘羽化/描边。**禁**：i2v/gpt-image 重画、liquify、改脸改造型、换色、贴滤镜改肤色。立绘身上的深色礼服=人物设定，不算违规。 |
| **R2** | **全暖色板** | 所有背景/包装/光效在暖板内取色：`CREAM #f8f4ea` `GOLD #d4af37` `PEACH #f4c7c7` `ORANGE #ff9a5c` `ROSE #f0aa96` `AMBER #e6af78` `WARM_WHITE #fff6e6` `INK #4a3426`。**禁**蓝紫（Dracula `#bd93f9/#ff79c6/#8be9fd`）、冷蓝调、暖红→冷蓝渐变。 |
| **R3** | **禁 AI 味深色画布** | **禁**自造深色画布（`#0a0e14/#141922` 一类）、Linear/Vercel/Cursor 式冷暗开发者美学。起手一律浅色/暖色。 |
| **R4** | **禁刻意冷渲染** | 古风/温情基调禁白呼气雾、冷蓝调压暗。哪怕"月夜""清冷"氛围也用**暖月光**表达。 |
| **R5** | **真音源卡点** | 卡点时基必须来自**真实音频**的 librosa 节拍分析（`beats.json`），禁合成假 BGM、禁凭感觉硬凑时间码。 |
| **R6** | **palette gate 必过** | 成片抽帧跑 `python3 pipeline/gate_check_palette.py <png>`，H=240~290（蓝紫）占比 >5% 直接 fail。真截屏系统色除外（本场景一般无）。 |

> **元规范（提升 3 级）**：本 skill 每一层都给「地板 / 进阶 / **提升3级**」三档。
> 任何时候你觉得"这样够了"，那个"够了"就是标准定低了的信号——强制切到该层的**提升3级**档再验收。
> 依据 memory `feedback_gate-floor-not-target` · `feedback_build-to-reference-not-floor`。

---

## 1. 核心哲学：灵魂三件套（比边框/胶片感更本质）

一条纸片人 MV 好不好看，**第一决定因素不是边框和胶片感，而是立绘有没有「浮起来 + 有重量 + 跟着音乐呼吸」**。
这三件套决定了"纸片人"和"贴图 PPT"的区别：

### ① 描边光 Rim Light —— 让立绘从背景「浮」出来
- **地板**：沿立绘 alpha 边缘描一圈暖金半透明线。
- **进阶**：双层描边——内层暖白（`WARM_WHITE` 2px）+ 外层金色辉光（`GOLD` 高斯模糊 8px，screen 叠加）。
- **提升3级**：描边**跟卡点脉冲**（重拍瞬间描边亮度+粒度 ×2，随 `pulse(t, downbeats)` 衰减）；描边**方向跟主光源**（月盘方向那侧更亮，形成体积感）；出场时描边从一点**扫过整条轮廓**点亮立绘（显影感）。

### ② 投影 Drop Shadow —— 给立绘「重量」
- **地板**：立绘正下方一层柔性暖褐椭圆接触阴影。
- **进阶**：**双阴影**——贴地接触影（硬、小、深）+ 投射影（软、大、偏移向光源反方向）。
- **提升3级**：投影随立绘缩放/位移**实时联动**（push-in 时接触影收紧变深）；卡点缩放瞬间投影**先被压扁再回弹**（果冻物理错觉，纯靠影子形变，立绘不变）。

### ③ 卡点呼吸 Beat-Breathing —— 让立绘「跟着音乐动」
- **地板**：全程 `scale = 1 + 0.012*sin(t*2)` 微呼吸。
- **进阶**：重拍 `scale *= 1 + dbp*0.05` 缩放冲击 + 手持微抖 `shake`。
- **提升3级**：**速度斜坡**——切镜前 6 帧加速冲向下一拍，切镜瞬间急停（punch-in-then-settle）；副歌把呼吸频率对齐 BPM（`sin(t * BPM/60 * π)`），让每一次缩放都精确压在拍点上。

> **落地顺序铁律**：先把三件套做出来看效果，**再**叠边框/胶片感。
> 三件套没做，边框和胶片感只是给"贴图 PPT"化妆——观众照样划走。

---

## 2. 五层包装系统（每层三档做法 + 参数 + 代码接口）

自下而上分 5 层。渲染顺序：`背景 → 立绘（含三件套）→ 前景FX → 字幕 → 遮幅/胶片 → 调色`。

### L1 · 背景场景层（Scene Backdrop）
把立绘放进一个**有纵深的场景**，而不是浮在纯色/渐变上。

| 档 | 做法 |
|---|---|
| 地板 | 暖色竖向渐变 + 中央径向光晕（`make_bg`） |
| 进阶 | + 大月盘（`make_moon`）+ 多层散景视差（`Field(depth)`）+ 移动光轴 god-rays（`light_shafts`）+ 暖云霭（`clouds`） |
| **提升3级** | + **3 层水墨山脊剪影**（远浅近深、视差，`make_ridges`）+ **真实宣纸/水墨纹理**叠底（一张 CC0 宣纸 PNG，`multiply` 15%）+ 背景元素**跟卡点微动**（月盘卡点微亮、山脊卡点微位移）+ **景深虚化**（远层高斯模糊，近层锐利） |

代码接口：`scene_backdrop(t, bg_grad, px_par)` → 现已实现渐变/月/山脊/云；待加：宣纸纹理层、景深分层模糊。

### L2 · 立绘落位与三件套层（见 §1）
代码接口：`place_doll()` + 待加 `rim_light(layer, dbp)`、`drop_shadow(layer, scale)`。

### L3 · 边框 / 版式层（Frame & Layout）
**核心原则：不要死框满框**（挤画面、廉价）。用局部装饰。

| 档 | 做法 |
|---|---|
| 地板 | 竖排词牌 + 一条金色竖线（现 `kinetic_text` 的 label 样式） |
| 进阶 | 四角纹样（云纹/回纹 PNG，暖金，低透明）+ 细金线框（非闭合，留气口） |
| **提升3级** | **动态框**——框随卡点**生长/擦除**（笔触从一角画到另一角）；**朱印**（红章 `#c0392b`，盖章瞬间 + 音效同步）；**卷轴/窗棂**边（按风格，见 §3）；框**跟景别联动**（特写用小框、全景去框） |

代码接口：待加 `corner_ornaments()`、`seal_stamp(t)`、`animated_frame(t, style)`。

### L4 · 胶片质感层（Film Texture）
| 档 | 做法 |
|---|---|
| 地板 | 颗粒 `grain` + 暗角 vignette |
| 进阶 | + 漏光 `light_leak` + bloom 辉光 + halation（亮部暖色扩散） |
| **提升3级** | + **竖向胶片划痕 + 尘点**（随机竖线，每几帧刷新）+ **2.35:1 暖褐遮幅**（非纯黑，`INK` 加深）+ **门闪 film-gate flicker**（整体亮度 ±2% 随机抖）+ **双重曝光**（副歌把上一镜立绘半透叠在下一镜，梦幻叠影）+ **化学显影色偏**（暗部偏暖褐、亮部偏奶金，模拟胶片响应曲线） |

代码接口：现有 `grain/light_leak/bloom`；待加 `film_scratches(t)`、`letterbox(arr, ratio)`、`gate_flicker(t)`、`halation(arr)`、`film_curve(arr)`。

### L5 · 字幕 / 排版层（Typography）
古风 MV 的字是**画面的一部分**，不是附加的字幕条。

| 档 | 做法 |
|---|---|
| 地板 | 逐字弹入大标题（宋体，金描边，`kinetic_text`） |
| 进阶 | 竖排词牌 + 副标题渐显 |
| **提升3级** | **歌词卡点字幕**——每句歌词按**人声起音时刻**逐字/逐词显影（笔锋从上到下"写"出来）；**书法笔触入场**（字用毛笔起收笔的 alpha mask 显影）；**关键字放大**（金句里的核心字 ×1.5 + 描金）；**竖排右起**（传统版式）；字**避让立绘**（人物在左则字在右，动态排版） |

代码接口：现有 `kinetic_text`；**待用户提供歌词文本** + 每句时间码（可 librosa onset 辅助定位人声起音）。

---

## 3. 风格预设库（6 套 Style Pack · 立绘像素都不变，只换外层包装）

每套是一个**完整配方**：定位 / 适用气质 / 配色（暖板内）/ 边框 / 胶片 / 光效 / 字幕 / 卡点侧重 / 差异化。
做新片时选 1 套为主，可局部混搭。**所有配色都在 R2 暖板内**，无一例外。

### 风格 A · 电影遮幅·极简 `cinematic-letterbox`
- **一句定位**：克制、高级、留白多，靠光影和运动撑场。最接近现代国乙官方角色 PV。
- **适用气质**：冷峻/矜贵/成熟男主（如西装、长袍、军装）。
- **配色**：主 `CREAM` / 辅 `AMBER` / 强调 `GOLD`，暗部 `INK`。低饱和、大光比。
- **边框**：**2.35:1 暖褐遮幅**，四角极细金线，无满框。
- **胶片**：强——划痕 + 门闪 + halation + 化学色偏拉满。
- **光效**：单一主光（大 god-ray 斜射）+ 强边缘光。粒子极少（一两点飘尘）。
- **字幕**：底部单行极简 + 竖排小词牌。歌词一次一句、淡入淡出。
- **卡点侧重**：**切镜 + zoom-punch + 闪白**为主（少花哨），重拍落在遮幅微开合。
- **差异化**：靠"少"取胜——每镜一个主体、大量负空间。

### 风格 B · 古画卷轴·水墨 `ink-scroll`
- **一句定位**：最"国风"、装饰最满，宣纸水墨 + 卷轴装裱。
- **适用气质**：文人/侠客/古装（书生、剑客、王侯）。
- **配色**：主 宣纸米黄 `#efe0b0` / 辅 墨褐 `INK` / 强调 朱砂 `#c0392b` + `GOLD`。
- **边框**：**卷轴上下轴杆 + 窗棂/回纹侧边**，四角云纹。可做"展开卷轴"入场。
- **胶片**：中——宣纸纤维纹理叠底 + 淡墨晕，少划痕（古画不是胶片）。
- **光效**：柔和散射（阴天古画感），水墨晕开转场（笔刷擦除）。
- **字幕**：**竖排书法右起** + 朱印。歌词用毛笔笔锋逐字"写"出。
- **卡点侧重**：**水墨晕开/笔刷擦除转场** + 印章盖章卡点 + 花瓣/落叶随拍飘。
- **差异化**：转场全用水墨笔触，字全书法，最强东方装帧感。

### 风格 C · 朱砂工笔·浓彩 `gongbi-vermilion`
- **一句定位**：传统重彩工笔，浓艳、华丽、金碧辉煌。
- **适用气质**：华服/皇室/神话（凤冠、金甲、仙君）。
- **配色**：主 `PEACH`+`ROSE` / 辅 朱砂 `#c0392b` / 强调 **真金 `GOLD` 描金拉满**。饱和高。
- **边框**：**描金重彩框** + 缠枝纹 + 宝相花四角，可满框（本风格允许，因风格本就华丽）。
- **胶片**：弱——工笔要清透，只留极淡颗粒 + 金粉飘落粒子。
- **光效**：**金粉/流光**为主（大量暖金粒子 + 流光线条），bloom 拉高。
- **字幕**：描金宋体 + 花钿装饰。歌词逐字描金显影。
- **卡点侧重**：**金粉爆发 + 流光扫过 + 描金脉冲**，重拍金光炸开。
- **差异化**：最"贵"最满，金色和粒子密度最高。

### 风格 D · 现代国乙·杂志 `modern-magazine`
- **一句定位**：无框满画幅 + 大字排版冲击，年轻、快、短视频卡点感。
- **适用气质**：都市/现代 AU/时尚（西装、街头、校园）。
- **配色**：主 `WARM_WHITE` / 辅 `ORANGE` / 强调 `GOLD`。干净高对比。
- **边框**：**无边框**，靠大字排版分割画面（英文/拼音大字压边）。
- **胶片**：中——轻颗粒 + 漏光，无遮幅（要满画幅）。
- **光效**：光效 + 粒子为主，节奏猛。
- **字幕**：**超大字卡点弹入** + 中英混排 + 关键词高亮。歌词大字快切。
- **卡点侧重**：**最猛**——每拍一个视觉变化，whip / RGB 错位（慎用，保持暖）/ 速度线 / 大字弹入 / 频闪切镜。
- **差异化**：最快最猛，排版即设计，最像抖音爆款卡点。

### 风格 E · 暖金梦幻·琉璃 `dream-glow`
- **一句定位**：梦幻、柔焦、光晕流动，唯美耽美向。
- **适用气质**：温柔/病弱/精灵系男主（白衣、羽翼、花海）。
- **配色**：主 `WARM_WHITE`+`PEACH` / 辅 `AMBER` / 强调 `GOLD`。**全暖，绝不碰冷色**（梦幻≠冷，用暖金梦幻）。
- **边框**：柔性光晕虚化边（vignette 加强）+ 星芒装饰，无硬框。
- **胶片**：柔——强 bloom + 强 halation + 柔焦（整体轻高斯），少颗粒。
- **光效**：**光斑 bokeh + 星芒 flare + 花瓣雨**为主，一切都在发光。
- **字幕**：细体 + 柔光描边，歌词柔和渐显。
- **卡点侧重**：**光斑脉冲 + 柔性缩放呼吸 + 花瓣随拍**，卡点靠光而非硬切。
- **差异化**：最柔最梦幻，全画面发光，适合抒情段/副歌。

### 风格 F · 水墨留白·禅意 `zen-void`
- **一句定位**：极致留白、单色水墨、大道至简，高级冷淡但暖调。
- **适用气质**：出尘/宗师/隐士（道袍、僧衣、白发）。
- **配色**：主 宣纸 `CREAM` / 辅 淡墨 `INK`（低透明）/ 强调 一点朱砂 `#c0392b`。近单色。
- **边框**：无框，超大留白，立绘偏置一侧（黄金分割）。
- **胶片**：极弱——宣纸纹理 + 一点墨晕，几乎无颗粒。
- **光效**：极简，一道淡光 + 偶尔一片落叶。
- **字幕**：极简竖排书法，一次一字，大量停顿。
- **卡点侧重**：**慢**——靠呼吸和留白节奏，卡点用极轻的位移 + 墨点晕开，重拍才一次大动作。
- **差异化**：反其道而行——用"静"和"空"制造高级感，节奏最慢，适合前奏/间奏/收尾。

> **一周形式 A/B 用法**：这 6 套天然是 6 种"视觉语汇"，可直接对应周维度 7 天差异化（见 CLAUDE.md 周形式 A/B 规则）。
> 同一角色同一立绘，套不同 Style Pack 出 6 版，是零新增素材的"完全不同形式"，可归因哪套数据最好。

---

## 4. 卡点动效字典（Beat → Effect 映射 · 可复用）

时基来自 `load_beats()`：`beats`（全部拍）、`downbeats = beats[::2]`（重拍）、`drop`（副歌/高潮，手动或 onset-strength 峰值标）。

| 拍类型 | 触发 | 动效候选（按强度） | 参数锚 |
|---|---|---|---|
| **弱拍** every beat | `pulse(t, beats, 0.14)` | 描边微脉冲 · 粒子闪烁 · 呼吸微缩放 | scale +2% |
| **重拍** downbeat | `pulse(t, downbeats, 0.22)` | zoom-punch · 闪白 · 手持抖 · 投影压弹 · 月盘微亮 | scale +5%, flash 0.15 |
| **切镜点** shot 边界（落在 downbeat） | `lt < 0.16` | 闪白 / 光扫切 swipe / zoom-blur match-cut / 水墨晕开（B风格） | 0.16s 转场 |
| **drop / 副歌炸点** | 手标时间码 | 粒子中心爆发 · 速度线放射 · 描边全亮 · 大字弹入 · 双重曝光叠影 · 遮幅开合 | 全 FX 叠加 |
| **间奏 / 留白** | 低能量段 | 慢呼吸 · 落叶/花瓣飘 · 光轴缓移（F风格靠这个撑） | 一切放慢 |
| **人声起音** onset | librosa onset | 歌词逐字显影 · 字锋写出 | 对齐 onset 时刻 |

**卡点铁律**：切镜点**必须**落在 `downbeats` 上（不能落在拍间）；重动效**必须**压在拍点±1 帧内，否则"卡点"就散了。
现有实现：`place_doll` 用 `dbp` 驱动缩放/抖动；`render_frame` 用 `bp/dbp` 驱动闪白/zoom-blur；转场用 `lt<0.16` + `shot.trans`。

---

## 5. 落地映射（gen_paperdoll_pv.py · 现状 / 待实现 / Style Pack schema）

### 5.1 已实现（v3）
`load_beats` 节拍缓存 · `full_doll/prep_layer`（含 `_feather_edges` 裁切羽化）· `scene_backdrop`（渐变/月/山脊/云/视差）· `Field`（散景/花瓣视差）· `streaks/bloom/grain/light_leak/light_shafts` · `place_doll`（push_in/pull_out/dutch/orbit/whip/montage + slam/pop/slide 入场 + rays/mirror/whip 拖影 + shake）· `kinetic_text`（逐字弹入 + 竖排词牌）· `render_frame`（转场 flash/swipe/zoomblur + 卡点闪白/zoom-blur + 分段调色 + bloom/grain/vignette）。

### 5.2 待实现（按优先级 · 对应各层"提升3级"）
1. **三件套**（§1，最高优先）：`rim_light(layer, dbp, light_dir)` · `drop_shadow(layer, scale, light_dir)` · 速度斜坡 easing。
2. **Style Pack 参数化**（§3）：把 6 套配方做成可切换 preset，一个 `--style` 参数出不同版本。
3. **胶片提升3级**（L4）：`film_scratches` · `letterbox(2.35)` · `gate_flicker` · `halation` · `film_curve`。
4. **歌词字幕**（L5，需用户给词 + 时间码）：`lyric_typography(line, onset_times, style)`。
5. **边框提升3级**（L3）：`corner_ornaments` · `seal_stamp` · `animated_frame` · 水墨擦除转场 `ink_wipe`。
6. **背景提升3级**（L1）：宣纸纹理叠底 · 景深分层模糊。

### 5.3 Style Pack schema（建议 dataclass，落到代码里）
```python
@dataclass(frozen=True)
class StylePack:
    name: str
    palette: dict          # {main, aux, accent, ink} 全在暖板内
    frame: str             # none / letterbox / scroll / gilded / corner_only
    film: str              # heavy / medium / soft / paper
    light: str             # single_ray / diffuse / gold_dust / bokeh_glow / minimal
    type_style: str        # minimal / calligraphy_vertical / big_type / gilded / zen
    beat_bias: str         # cut_punch / ink_wipe / gold_burst / max_kinetic / glow_pulse / slow
    letterbox_ratio: float # 0=off, 2.35, 1.85...
    grain_amp: float
    bloom_strength: float
    particle_density: float
```
6 套 = 6 个 `StylePack` 实例；`render_frame` 读 `pack` 决定各层参数。这样"多种风格"在**一份代码 + 一组 preset**里全覆盖，符合"skill≠template"（配方复用，非克隆分镜）。

---

## 6. 复用 Checklist（做一条新国风乙 MV / 角色 PV）

1. **素材**：拿到立绘 → rembg 抠透明 PNG → `full_doll` 硬化 alpha（去 matte）。**立绘像素此后零改动**。
2. **音源**：真实音频 → `load_beats` 出 `beats.json`（BPM/beats/downbeats）。标 drop/副歌时间码。**禁合成假 BGM**。
3. **选风格**：从 §3 六套选 1 套为主（按角色气质），必要时局部混搭。确认配色全在暖板内。
4. **三件套先行**（§1）：先把描边光 + 投影 + 卡点呼吸做出来看效果，**再**叠其余包装。
5. **分镜**：按 `Shot` 排镜，切镜点**落在 downbeats**，最长 3s 一镜，景别靠裁切换（全景/半身/特写/局部）。**禁**从上一条克隆分镜。
6. **五层包装**（§2）：逐层叠，每层瞄**提升3级**档，不是地板档。
7. **卡点动效**（§4）：按 beat 字典绑定，重动效压拍点±1 帧。
8. **字幕**（§5）：有歌词则逐字/逐词 onset 对齐显影。
9. **验收**：抽帧跑 `gate_check_palette.py`（暖板）+ 目视三件套/景别丰富度/卡点是否对齐 + 立绘保真核验。**每道"觉得能过"先自问能否再提3级**。
10. **命名外发**：有 BGM `*_with_bgm.mp4` / 密 VO 无 BGM `*_no_bgm.mp4`；16:9 出，按平台适配。

---

## 附：与其他 skill / 铁律的关系
- **本 skill**（确定性 motion-graphics 包装）↔ `video-form-music-video`（i2v/t2v prompt）：前者立绘不变、后者生成新画面，选路由看"能不能改立绘"——国风乙立绘卡点默认走**本 skill**。
- 立绘身份保真、暖板、禁 AI 味：见 memory `project_voice-room-paperdoll-pv` · `feedback_no-neon-palette` · `feedback_no-ai-visual-dark-canvas` · `feedback_no-exaggerated-cold-atmosphere`。
- "抬高3级"元规范：`feedback_gate-floor-not-target` · `feedback_build-to-reference-not-floor`。
- skill≠template：`feedback_skill-vs-template-distinction`——本文是方法/配方/字典（复用），不是某条片子的具体分镜（一次性）。
