---
name: candidate_families
type: motion_tech
last_updated: 2026-07-22
source_projects:
  - publish/语音厅 (v3 · 2026-07-22)
tags: [motion, tech, family, illustration, animation, i2v]
reuse_scope: 涉及静态立绘/角色美术 → 动态呈现的所有选题 · 技术家族选型参考
freshness_horizon: 90d
---

# 动态元素候选池 · 静态立绘的动画技术家族

## 摘要

**8 个动态元素候选 × 5 个技术家族**（zoompan / SVG 拆件 / Live2D / i2v / 粒子层）· 每个候选标明可行家族 + 风险等级 · 供动效技术导演在给定物料/预算/时间下选型。

---

## 1 · 8 个动态元素候选（D1-D8）

| # | 动态元素 | 建议技术家族 | 用在哪 | 风险等级 |
|---|---|---|---|---|
| **D1** | 从画外飞进来的声波（横向切入 → 撞到 CV 胸前扩散） | SVG 拆件 + GSAP timeline 或 粒子层 | 每位 CV 亮相瞬间 · 强化"发声者"符号 | 低 |
| **D2** | 麦克风指示灯（红点）呼吸闪烁 | SVG 拆件 + CSS animation 或 GSAP 简单循环 | 每位 CV 出场时叠在角落作"开麦中"信号 | 极低 |
| **D3** | 耳机中央 EQ 波形随 WAV 节拍抖动 | SVG 路径 + WAV 频谱数据驱动（或后期 fake 假频谱） | 前 3s 或末段收束 · 强化"耳机党氛围" | 低 |
| **D4** | 4 条不同颜色的波形从画面 4 边汇入中央并叠合 | SVG 或 canvas 波形 + GSAP timeline | 15-35s 4 声叠合高潮 · 视觉锚"真同框" | 中 |
| **D5** | 立绘头发/衣摆的微飘动（cy 披风飘 / 轩珩汉服袖飘 / 中里毅衣领轻扬 / 诺兰纹身若隐若现） | **i2v**（seedance/grok-imagine）或 SVG 遮罩形变（AE 类） | 逐位亮相中段 · 打破"立绘静态感" | **高**（i2v 幻觉风险） |
| **D6** | 立绘外扩的光晕/剪影双重曝光（暗色底 + 高光边） | 高幅度 zoompan + 遮罩合成 或 AE 双重曝光 | 4 声叠合时 4 人剪影叠影 · 强化"群像感" | 中 |
| **D7** | 粒子从 CV 嘴部/胸口散开（声音扩散可视化） | 粒子层（three.js / canvas / AE 粒子插件） | 每位 CV 声音出来的瞬间 · 呼应 S2 波形 | 中 |
| **D8** | **4 种专属飘落元素**（竹叶/花瓣/光粉尘/火星） · 各人独立配置 | SVG 或 粒子层 | 逐位亮相或过渡段 · **4 CV 视觉差异化关键**（对治 v2"都长一样"） | 低-中 |

---

## 2 · 技术家族对比

| 家族 | 优势 | 风险 | 项目内已用 |
|---|---|---|---|
| **zoompan** | ffmpeg 原生 · 低成本 · 稳定 | **天花板已知**（v3 事故 log）：低 zoom（<1.15x）在小 plate 上位移物理上到不了 10% 屏高 · 相机运动不能替代"角色真动" | `pipeline/p004_video/` · v1/v2 版本 |
| **SVG 拆件 + GSAP** | 逐镜可控性最高 · 无 AI 幻觉 · 项目 8 个 GSAP skills 已装 | 需美术拆图 · 每个动作需手工设计 · 时间投入高 | `.agents/skills/gsap-*/` 8 个 skill |
| **Live2D** | 角色骨骼动画 · 表情丰富 · 圈层专业感 | 需 Live2D 模型（美术投入）· 项目未装 | 未使用 |
| **i2v**（Seedance / grok-imagine-video） | 立绘"真动"效果 · 时间投入低 | **幻觉风险高**：脸崩/相机不动/AI 味 · 需 `i2v-video-diagnose` skill 逐帧诊断 · 3 次救不活需换路线 | `pipeline/p011_seedance_i2v/` · `.agents/skills/i2v-video-diagnose/` · 相关 memory 大量 |
| **粒子层**（canvas / AE） | 声波/星尘/粒子扩散效果强 · 情绪叠加自然 | 需性能优化 · 高粒子数会拉低 FPS · 项目未沉淀 pipeline 工具 | 部分单帧用 |

---

## 3 · 选型决策树

```
需要"角色本身动起来"（表情/动作）？
├─ 是 → 有 Live2D 模型？
│       ├─ 有 → 用 Live2D
│       └─ 无 → i2v（生成后必过 i2v-video-diagnose 诊断 · 3 次上限）
└─ 否 → 需要"角色附近有动效"（声波/粒子/光晕）？
        ├─ 是 → SVG 拆件 + GSAP（可控性高） 或 粒子层（视觉冲击强）
        └─ 否 → zoompan（相机推拉·底图微推·转场）
```

**红线**：
- ❌ **zoompan 单独用不能达 v3 立项要求**（"绚丽转场·快节奏"必须叠加其他家族）· v1 事故复盘直接证明
- ❌ **i2v 不做诊断直接上**（幻觉率高 · 崩粉风险大）
- ❌ **SVG 拆件用 PNG 立绘**（PNG 不可拆 · 需要美术出 layered PSD/SVG）

---

## 4 · 通用踩坑记录

### zoompan 位移公式（v3 事故复盘沉淀）

`dy ≈ H × (z_avg - 1) × py_sweep`

- 低 zoom（<1.15x）+ 小 plate → 竖向位移只有 ~60px · 无论 py 参数如何都到不了 190px
- 要位移就得**抬 zoom** 或 **加大 plate 余量**

### zoompan 掉帧 bug

- `-loop 1 -t + d=1` 会掉帧（4.5s 只出 3.77s/113 帧）
- 必须 `-i + d=n`（单帧输入）

### i2v 3 次救不活升级

- 生成完 → 用 `.agents/skills/i2v-video-diagnose/` 7 类归因诊断
- minimal-edit（只改 1-2 变量）迭代 3 次
- 仍崩 → 升级换路线（换模型/换实现/撤镜/换 B-roll）

### CJK 字体重影

- 苹方无真 900 字重 · Chrome faux-bold 会涂抹重影
- 已装思源黑体 Heavy
- font-family 用 `"SF Pro Text","Source Han Sans SC","PingFang SC"`
- 详见 memory `cjk-bold-font-ghosting-fix`

---

## 5 · 独立验收工具

`publish/语音厅/qa_motion2.py`（v2 沉淀） · 单镜位移探针 + 跨镜多样性硬约束（**核心复用资产**）：

- 单镜位移探针：FFT 相位相关求全局像素位移 · 二元底线 190px(10%屏高)/12pt · 副歌镜 AND 双过
- 跨镜多样性硬约束：运镜去重 ≥6 · 转场去重 ≥5 · 版式去重 ≥5 · 相邻不重复 · 无单一手法过半 ≤11/22

**验收协议**：任何多镜视频都要过这两层 · 缺一层 = 只保证单镜合格 = v2 事故"逐镜合格但整片单一"重现。

---

## 溯源

- 抽自 `publish/语音厅/insights/domain_notes.md` §4.3（动态元素候选）
- 技术家族对比 + 踩坑记录抽自：
  - `docs/design/WORKFLOW_EXECUTION_LOG.md`（3 条事故记录）
  - memory `feedback_zoompan-visible-motion` `feedback_camera-motion-vs-i2v-ceiling` `cjk-bold-font-ghosting-fix`
  - `.agents/skills/i2v-video-diagnose/` skill
- 验收工具：`publish/语音厅/qa_motion2.py`（v2 版本沉淀）
