# 05 · 候选实现清单 · 每一镜五维打分(北极星决策流)

> **没有「默认 pipeline」。** 只有「默认决策流程」:先定这一镜的观众行为,再选实现。
> **本文是 `form_competition` / `form_strategy_meeting` 的候选池来源。** 不在清单内的能力不得作为方案候选;发现清单遗漏当即回填本节,再回 form_competition。

---

## 一、决策流程

```
洞察包 + hook_benchmark(同行怎么停划)
  → retention_beat_sheet(每段:停划 / 看懂 / 互动 主意图)
  → 视觉创意硬门(20→8-12→概念图 · 见 03_VISUAL_CREATIVE_GATE.md)
  → 每一镜:列候选实现 → 五维打分 → 否决项检查
  → 分镜 + audio_plan(音画同拍)
  → pre_publish_forecast(3s/完播/互动区间)→ C/D 禁止外发
  → 渲染(可混用多条 pipeline 于同一成片)
  → 48h 数据 → evolution(改的是「实现」,不是「工具信仰」)
```

---

## 二、每一镜:先标主意图

| 意图 | 观众行为 | 主指标 |
|------|----------|--------|
| **停划** | 拇指停住 | `completion_3s` |
| **看懂** | 不困惑、不中途划走 | `completion_rate` · `avg_watch_s` |
| **互动** | 想评、想收藏、想转发 | 评论率 · 收藏率 |

**未标意图的镜 → 禁止选实现方式。**

---

## 三、候选实现清单(版本化 · 无默认顺序)

> **最后同步**:2026-07-04(P011 · Seedance 2.0 加入 i2v 家族候选)
> **每季度或每次新集成入 `integrations/` 时必须回顾并更新本清单。**

### 3.1 原生 pipeline(`pipeline/`)

| 候选之一 | 脚本 | 用途 |
|------|------|------|
| **真实 B-roll** | `pipeline/p004_video/fetch_broll.py` | 拉 Pexels CC0 免费商用素材 |
| **P001 真实截图风** | `pipeline/render_p001.py --all` | 仿真 B-roll + 三平台视频/图文 |
| **P001 仿真素材** | `pipeline/gen_evidence.py` | Chrome 渲 HTML 出 9:16 满铺帧 |
| **P002 报纸风出图** | `pipeline/p002_carousel_gen.py` | GPT-image-2 整版报纸风轮播 |
| **P004 HTML+GSAP 视频** | `pipeline/p004_video/build.py` | HTML+GSAP 渲染场景 → PNG → mp4 + VO + BGM + 字幕 |
| **P005 带货演示** | `pipeline/p005_belt_video/` | 带货型 |
| **P006 漫画视频** | `pipeline/p006_belt_video_comic/` | 漫画+口播 |
| **P007 漫画图文** | `pipeline/p007_xhs_engine_comic/` | 小红书轮播漫画 GSAP |
| **produce.py 项目演示** | `pipeline/produce.py --id …` | GitHub 项目 → 三平台 mp4+文案+封面 |
| **TTS 配音** | `pipeline/tts/gen_speech.py --script <path>` | `config.yaml provider: edge / minimax / volcengine` |
| **真人出镜**(DECISIONS Q8) | — | 按形态激活 · 数字人暂停 |
| **调研工具** | `agent-reach`(独立 CLI) | 小红书/B 站/Reddit 公开内容 · 消费者声音研究员用 |

### 3.2 外部制作插件(`integrations/`)· 与原生 pipeline 同级候选

| 候选之一 | 位置 | 用途 | 门禁 |
|------|------|------|------|
| **OpenMontage** | `integrations/openmontage/` | 视频合成 runtime(Remotion / HyperFrames / FFmpeg / undecided) | **每条必跑** `design/openmontage_brief.md` 判断 enabled/disabled/blocked,未跑不得进 storyboard |
| **Grok video** | `integrations/openmontage/openmontage.env.example` · `grok-imagine-video` | i2v 候选 · 相机运动天花板 | 走 OpenMontage brief;详见 memory `feedback_camera-motion-vs-i2v-ceiling` |
| **Seedance 2.0 i2v/t2v** | `pipeline/p011_seedance_i2v/gen_video.py` | 与 grok-imagine 并列的 i2v 家族候选 · `doubao-seedance-2-0` 云雾中转 · 生产可用 640 行 · CLI 单段/yaml 批量双模式 · 重试+并发+恢复+后置 QA | **必须与 grok-imagine 打分选**,不得因"新集成"或"更酷"默认走它;详见 memory `project_p011-seedance-i2v-candidate` |
| **未接入的视频模型候选** | Kling / Runway / Luma / Wan / HunyuanVideo / Veo | 需要时手工接;prompt 工程都走 `.agents/skills/i2v-video-prompt/` | 见 `04_CONTENT_CONSTRAINTS.md §15 i2v prompt 硬门` |
| **视频 prompt 工程 skill** | `.agents/skills/i2v-video-prompt/` | **通用 · 与具体视频模型解耦** · 任何 i2v/t2v 场景强制调用 | CLAUDE.md/AGENTS.md 有硬门(见 `04 §15`) |
| **GPT-image-2** | 直接 API · 云雾中转 | 报纸风外,也可用于任意需静态生成的画面 | 走 form_competition 打分 |

### 3.3 Web 3D / 高级动效候选

- **Three.js** — 少数镜、非默认
- **Canvas / SVG** — 覆盖层、打点、翻牌
- **GSAP**(项目已装 8 个 skill · `.agents/skills/gsap-*/`) — 网页动效 → 录屏当 B-roll · Before-After 对比 · 交互式作品集

---

## 四、GPT-image-2 API(报纸风首选)

- **中转**:tonbirds(`GPT_IMAGE_BASE_URL=https://us.tonbirds.com/v1`)
- **尺寸**:1024×1536 原生 → 升采样 1080×1620
- **单张耗时**:60-130s,需 4 次重试 + 5s 退避
- **中文标题渲染质量高**,正文长段落约 5% 乱码(可接受)
- **不适合**:精确文字排版、可编辑版面、品牌 logo
- **并发**:降到 `GPT_IMAGE_WORKERS=2`(503 无可用渠道 = 并发过高,不是模型名问题)

依据:memory `gpt-image-2-api` · `feedback_gpt-image-model-fallback`

---

## 五、五维打分(1–5,加权求和;最高分 wins)

| 维度 | 权重 | 问什么 |
|------|------|--------|
| 停划力 | 首镜 ×2,其余 ×1 | 0–3s 能否压住信息流? |
| 看懂速度 | ×2 | 一屏一信息?3s 内能懂? |
| 节奏变化 | ×1 | 支撑 5–8s 一切?中段会不会塌? |
| 互动钩子 | ×1 | 有没有「想评一句」的钉子? |
| 信任/证据 | ×1 | Q9:真实画面是否更强? |
| 交付风险 | ×0.5 | 新管线会不会导致**更差赶工版**? |

**否决项(不看分数)**:
- chaos 用 AI 假手机
- 字挡信息
- 带货合规红线
- forecast C/D

---

## 六、平局时的 tie-breaker

| 情况 | 倾向 |
|------|------|
| 停划/看懂/互动主要靠字与节拍 | GSAP / DOM |
| 同一信息真实界面更有冲击力 | P001 / B-roll(常胜过动效) |
| 必须真 3D 空间,2D 明显假 | Three.js(少数镜,非默认) |
| 轮播收藏动机(清单/漫画故事) | P007 / P002(看本条形态) |
| 带货需摸产品/看脸 | 真人(Q8) |
| 五候选差不多 | **已有管线**(少赶工 = 少毁片) |

**整条片可混用**:chaos 实拍 + 中段 P001 录屏 + OpenMontage 段 + 末段 GSAP CTA。

**`pipeline/p004` 是分镜里若干镜的渲染器之一,不是「视频默认路线」。同理,OpenMontage / P001 / GSAP 也都不是"默认"。**

---

## 七、接到「该用哪种方式?」只问四问

1. 这一镜主意图是停划、看懂还是互动?
2. 真实素材/B-roll 能否更强?(能 → 优先证据,别动效硬撑)
3. 换实现,forecast 里 3s/完播/互动区间会不会上移?
4. 换实现会不会导致赶工烂版?(会 → 用稳管线做好版)

---

## 八、候选池完整性铁律(form_competition 门禁)

| 铁律 | 说明 |
|---|---|
| ❌ 3 个方案**不得同家族** | 不能都是 P001 变体 / 都是 P004 变体 / 都是 OpenMontage 变体 |
| ❌ 候选池不得**预先缩水** | 列候选前必须回来读本清单 |
| ❌ 发现候选被"默认习惯"排除 | 立即打断,回本节重列(如"就走 P004 吧") |

**清单本身可能过期。** 出现"我脑子里的默认路线是 X"时立即警觉——是不是清单缺了新能力?回本节校对再决策。

依据:memory `feedback_no-default-tech-stack`

---

## 九、渲染路由(禁止全周 render.py · 禁静态冒充动效)

| render_route | pipeline | 适用 |
|--------------|----------|------|
| `render_evidence` | `pipeline/render.py` | Ken Burns 证据卡 · **每周最多 1 天** · **禁相邻** |
| `p004_gsap` | `pipeline/p004_video/build.py` | punch/pain/compare 等 GSAP 动效视频 |
| `p007_comic` | `p007_xhs_engine_comic/capture_carousel.py` | 漫画 GSAP 轮播(非静态排版) |
| `p002_newspaper_gpt` | `p002_carousel_gen.py` | 仅当需插画且仍走 GSAP/动效验收 |

**动效铁律**:抖音必须 `video.mp4`;小红书轮播须 P007 漫画 GSAP 或等价动效 pipeline;禁 PPT 分屏、禁纯静态报纸风、禁 `light_split` 抖音封面。

---

## 十、D08 复用检查 · 先定画面任务,不定技术路线

新选题进入视频生产前,必须先写一张"画面任务表",再选能力:

| 位置 | 必填 | 不合格信号 |
|------|------|------------|
| 首镜 | 场景锚点 + 冲突大字 | 只有抽象背景/只有标题 |
| 痛点镜 | 具体工作现场或具体对象 | 只用概念卡解释 |
| 方案镜 | 方案被拆成动作/职责/流程 | 只写 AI 很强 |
| 证据镜 | 看板、录屏、真实素材、可核验结构 | 假装后台、数字无边界 |
| 变化镜 | 与前一镜不同视觉语法 | 连续同类卡片 |
| CTA | 低成本具体评论动作 | "你怎么看"式空泛问题 |

通过这张表后才允许决定使用 Pexels、GSAP、Three、录屏、真人、P001/P004 等能力。**能力选择的理由必须写成"更有利于哪一个目标",不能写成"默认用某技术"。**

---

## 十一、p004_video/lib config-driven 架构

W29+ 每条走 `pipeline_config.yaml` + `run_pipeline.py --step all`;W28D01-D06 保 golden reference;D03 修的 4 个 bug 已写入 lib。

依据:memory `p004-lib-config-driven`

---

## 十二、TTS 时长前置估算

`audio_plan` 写完必跑 `estimate_duration.py`;≥30% 溢出 fail 改稿;D03 s2/s10 溢出若前置就能避免 M7 挤压。

依据:memory `tts-estimate-duration-pre-synth`

---

## Source Map

- 原 `CLAUDE.md §候选实现清单`(常用入口 + 铁律)
- 原 `docs/SYSTEM.md §4.1 能力全景`
- 原 `docs/SYSTEM.md §4.2 实现方式选型(北极星决策流)`
- 原 memory:`feedback_no-default-tech-stack` · `p004-lib-config-driven` · `feedback_camera-motion-vs-i2v-ceiling` · `feedback_gpt-image-model-fallback` · `gpt-image-2-api` · `tts-estimate-duration-pre-synth` · `project_p011-seedance-i2v-candidate`
