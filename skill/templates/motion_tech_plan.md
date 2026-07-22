# 动效技术方案 · motion_tech_plan

> 工种：**动效技术导演 / Web 3D 技术导演**（`skill/roles/registry.yaml` → `motion-tech-director`）
> 位置：`design/motion_tech_plan.md`
> 时机：`motion_storyboard.md`（逐秒分镜）之后、render 之前。**使用 GSAP / Three.js / Web 3D / 复杂 HTML 截帧 / 重资产 B-roll 时必跑**（`activation: on_demand`）。
> 目的：接住动画导演的逐秒分镜，对每个动效元素做**可行性、资产清单、性能预算、导出风险**审查，拆成组件级任务清单，防止「分镜写得动、渲染动不了 / 动不出」。
> 负责维度（owns_dims）：**D02 动效 · D03 特效 · D05 转场 · D14 剪辑逻辑 · D18 工程规范**（见 `skill/quality/video_19dim_scorecard.md`；基准是地板，按 `QG-RAISE-3` 提升 3 档目标验收）
> 对应质量门：**`QG-MOTION-FREEZE`**（成片连续像素冻结 >4.00s → fail · 防 PPT 感）· **`QG-MEDIA-BLACK`**（纯黑帧 ≥1.0s → fail）· **`QG-REVIEWERS`** + **`QG-SCORECARD-90`**（双人独立 ≥90）· **`QG-PRD-ACCEPTANCE`**。

## 0. 入口必读（开工前打勾 · fail-closed）

> 流程与门位见 `skill/docs/PROCESS.md`；不过清单不得开工

- [ ] **流程 refs**：`skill/docs/PROCESS.md` 波次表（W9 动效技术导演 · 分镜后 / render 前门位 · dual_review）
- [ ] **质量 refs**：`skill/quality/quality_registry.md`（`QG-MOTION-FREEZE` · `QG-MEDIA-BLACK` · `QG-REVIEWERS` · `QG-RAISE-3`）
- [ ] **维度 refs**：`skill/quality/video_19dim_scorecard.md` D02/D03/D05/D14/D18 的「提升 3 档目标」与「常见踩雷」列
- [ ] **template refs**：本节点已完成 `motion_storyboard.md`（逐秒分镜 · 拆本表「推荐实现方式」字段）· `form_competition.md`（recommended_route）· `design_language.md`（色板/字体资产）
- [ ] **历史成品参考**：同主题最近 1-2 条 `motion_tech_plan.md` 实读（复用组件能力，不复用画面骨架）
- [ ] **能力 refs**：浏览 `skill/` 内相关 `cap-*` 能力目录（渲染 / 截帧 / 素材），确认技术栈落点

**触发词打断**（出现即停）：
- 「先渲了再看动不动得起来」（未做可行性 = D18 踩雷「先出成片后跑 QC」）
- 「Ken Burns 效果名写上就算动效实现了」（效果名≠已实现 · D02 踩雷）
- 「统一 fade 转场省事」（不分情绪一律淡入淡出 · D05 踩雷）
- 「复杂 3D 上去更酷」（观众看不懂就废 · D03/D14 踩雷）

## 1. 结论（技术导演口径）

```yaml
status: draft | pass | fail
content_id:
feasibility_verdict: feasible | feasible_with_downgrade | infeasible   # 整体可行性判定
recommended_stack:                 # 主技术栈（GSAP / Three.js / Web3D / HTML截帧 / Remotion / Manim / 混合）
render_pipeline:                   # 渲染路线（截帧脚本 → PNG 序列 → 编码；或 runtime 直出）
handoff_to:                        # 下一节点：导演 storyboard 合成 / render
decision: proceed_to_render | rewrite_storyboard | downgrade_route | block_render
```

## 2. 逐秒分镜 → 组件级任务清单（核心）

> 拆 `motion_storyboard.md` §3 的每一行「动画动作 / 镜头运动 / 素材需求 / 推荐实现方式」，落成可执行的组件任务。每个动效元素一行，`observable_metric` 对齐 `subagent_prd_schema.md`（禁写效果名，写可观察量级）。

| 分镜时间 | 动效元素 | 实现技术 | 资产依赖 | 预估渲染成本 | 导出格式风险 | observable_metric（可观察量级） |
|---|---|---|---|---|---|---|
| 0:00-0:0X | | GSAP / Three.js / Web3D / HTML截帧 / Remotion / Manim | 字体/模型/纹理/图层/素材 | 帧数 × 单帧耗时 ≈ Xs | 冻帧/黑帧/编码/音轨 | 如「元素 X 3s 内位移 ≥12% 画面宽」 |
| … | | | | | | |

**清单自查：**
- [ ] 每个动效元素都指定了实现技术（无「待定」）
- [ ] 每个元素声明了服务哪个数据杠杆（停划/理解/情绪 · D02/D03）
- [ ] 无「装饰性特效无目的声明」（D03 踩雷）
- [ ] 转场逐条声明目的（L-cut 连续感 / match-cut 视觉押韵 / jump-cut 紧迫感 · D05），无「默认统一 fade」

## 3. 可行性审查（按技术栈）

### 3.1 技术栈可行性

| 技术栈 | 用在哪几镜 | 可行 | 卡点/依赖 | 降级路线 |
|---|---|---|---|---|
| GSAP（HTML+时间轴） | | | 浏览器截帧稳定性 / 字体加载 | |
| Three.js / Web 3D | | | GPU / 模型体量 / 光照一致 | 退 2.5D 或预渲染序列 |
| HTML 截帧（Chrome/无头） | | | 截帧节流 / 分辨率 / 字体 | |
| Remotion / Manim | | | 依赖版本 / 渲染时长 | |

### 3.2 每镜降级预案

> 高风险镜头必须有「渲不动/动不出」时的降级路线（换更轻实现 / 预渲染 / 撤镜），对齐生成后诊断的「3 次救不活升级换实现」（`QG-I2V-DIAGNOSE`）。

## 4. 资产清单

| 资产 | 类型 | 来源 / 授权 | 规格（尺寸/格式/色板） | 落地路径 | 就绪 |
|---|---|---|---|---|---|
| | 字体 / 3D 模型 / 纹理 / 图标 / 序列帧 / 音效 | 自造 / cap-image-gen / cap-stock-footage / 授权曲库 | | | ☐ |

**资产自查：**
- [ ] 色板 / 字体来自 `design_language.md`，不新造（D10/D04）
- [ ] 3D 模型 / 纹理体量在性能预算内（见 §5）
- [ ] 授权素材来源合法（禁合成器拼假音效 / 未授权模型）

## 5. 性能预算（`QG-MOTION-FREEZE` 服务项 · D18）

| 项 | 目标 | 本条实测/预估 | 判定 |
|---|---|---|---|
| 输出分辨率 | 1080×1920（9:16） | | |
| 帧率 | 24 / 30 fps（声明） | | |
| 单镜最长连续静止 | **< 4.00s**（`QG-MOTION-FREEZE`） | | |
| 全片渲染时长 | 可接受上限（声明） | | |
| 峰值内存 / GPU | 不超环境上限 | | |
| 1.0× / 1.5× 压测 | 两种时基下动效仍成立（以真实 VO timing 为时基） | | |

> 性能预算不是「能跑就行」——按 `QG-RAISE-3` 抬 3 档：目标是「每 2-4s 明确视觉变化且无一段 >4s 冻结」，不是「刚好不触 freezedetect」。

## 6. 导出风险审查（成片机器门前置 · D18）

| 风险 | 检测 | 对应门 | 缓解 |
|---|---|---|---|
| 连续冻帧 >4.00s | freezedetect | `QG-MOTION-FREEZE` | 加中间关键帧 / 拆镜 |
| 纯黑帧 ≥1.0s | blackdetect | `QG-MEDIA-BLACK` | 补转场帧 / 检查渲染丢帧 |
| 接缝闪烁 / 方向反向 | 逐帧目视 + 抽帧 | D05 / D14（帧锁接缝铁律） | 接缝两端用相邻真实渲染帧，不用原始静帧 |
| 编码 / 音轨 / 规格失败 | Phase B 前跑机器 QC（ffprobe） | D18 | 冻结 render，先修再出 |
| 输出路径互覆 | 按 content_id/scene_id 隔离 | D18 | 独立输出目录 |

**工程规范自查（D18）：**
- [ ] Phase B 前先跑机器 QC（不是先出成片后跑）
- [ ] 成片 SHA-256 记录于 scorecard（MP4 变化即失效重审）
- [ ] 输出路径按 content_id/scene_id 隔离，临时文件清理
- [ ] 优先逐场景增量重渲；全片重渲登记为技术债

## 7. 进入 render 的条件

- [ ] §2 组件级任务清单完整，每元素有实现技术 + observable_metric（禁效果名）
- [ ] §3 每个高风险镜头有降级预案
- [ ] §4 资产全部就绪或有替代
- [ ] §5 性能预算全绿，含 1.0×/1.5× 压测
- [ ] §6 导出风险逐条有缓解，机器 QC 前置到位
- [ ] 双人独立评审 ≥90（`QG-REVIEWERS` + `QG-SCORECARD-90`），notes ≥40 字（`QG-NOTES-40`）
- [ ] 产出以 `subagent_prd_schema.md` 结构化返回，走 `QG-PRD-ACCEPTANCE` 二元独立验收

任一项未完成：`status: fail`，禁止 render。

## 8. 联签

- [ ] 动效技术导演 · 可行性 + 性能 + 导出风险审查完成
- [ ] 独立评审 A（≥90）
- [ ] 独立评审 B（≥90）
