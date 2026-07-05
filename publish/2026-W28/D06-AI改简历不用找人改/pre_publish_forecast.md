# pre_publish_forecast · W28D06

> 平台表现分析师 · 自跑 · 2026-07-05
> 判据：`docs/SYSTEM.md §1.0` 铁律 0 audience-first · `templates/design/completion_rate_north_star.md`
> 状态：`draft_self_generated` · 双平台（抖音视频 + 小红书轮播）

## 一、整体判定

- **抖音 predicted grade**: **B+ (87–90)**
- **小红书 predicted grade**: **A- (88–91)**（7 页轮播 · 收藏动机强 · 求职圈小红书池大）
- **可外发**: ✅ 双平台 render_gate PASS · palette gate PASS（10 UI + 7 carousel = 17/17）· CTA ship gate PASS
- **风险**: 60.64s 略超 60s 抖音甜区（+0.64s）· 简历示例真实感依赖排版而非真截图

## 二、抖音 forecast 拆解（B+ · 88）

### completion_3s（预估 55–62%）

| 项 | 得分 | 备注 |
|---|---|---|
| 反差钩子 简历盖「已读不回」红戳 | ★★★★☆ 88 | 求职党秒懂「已读不回」的窒息感 · memory contrast-hook-3s 落地 |
| 首屏停划设计 | ★★★★ 86 | 「投了很多份·已读不回」90pt 血红大字 · 一句话戳痛点 |
| **净分** | **87** | VO 从 0s 覆盖 · 无沉默钉子（seg s1 start 0.0） |

### completion_rate（预估 44–50%）

| 段 | 得分 | 备注 |
|---|---|---|
| 3–8s 花钱改也没用 punch | 88 | 「不是文笔·花钱改照样没面试」认知缺口 |
| 8–14s HR 视角扫描线 | 86 | 「只有几秒」机制锚 · amber 扫描带 |
| 14–17.5s 三处预告 | 85 | 悬念钩 · 引出下三段 |
| **17.5–43s 三处硬伤对照** | 90 | **本片主体** · before/after + 对照句卡 + ATS 8 格 · 收藏+完播双贡献 |
| 43–49s 三处一改收束 | 88 | 「两回事」情绪落点 |
| 49–55s 边界价值锚 | 89 | 「被看到是不花钱的第一步」+「数字填真的别编」反造假边界 |
| 55–60.6s CTA | 85 | 私信「发我简历」· 求职焦虑重 · 私信意愿预估最高 |
| **净分** | **88** | |

### 观众成果 · audience-first 三要素

- **内容共鸣** ★★★★★ 91 · 「投了很多份已读不回」直击求职党真实窒息场景
- **强观赏性** ★★★★☆ 84 · 每 2–4s 视觉变化（10 场景 · 扫描线/分屏/对照卡/清单卡多形态）· sfx 31/31 已补
- **强内容** ★★★★★ 92 · 三处硬伤 + 具体改法（可复现）· 数据口径严谨（几秒到几十秒 · 禁 6 秒）

### 综合 · **B+ 88**

## 三、小红书 forecast 拆解（A- · 89 · 7 页轮播）

- **收藏预估** 8–11%（P5 对照句卡「负责社群运营→从 0 搭 3000 人转化涨 40%」可长按截图照抄 · P4/P6 亦 saveable）
- **完播预估** 60–66%（xhs 用户更耐心 · 7 页节奏适配）
- **评论预估** 2–3%（「投了多少份/面试几个」公开自查门槛低）
- **收藏动机核心**：P5 句式模板「把负责 X 改成 用什么方法·做出什么数字」= 可直接照抄的方法卡
- **净分 89 (A-)**

## 四、观众成果预警（audience-first 硬门自检）

| 硬门 | 状态 | 备注 |
|---|---|---|
| 内容共鸣（真实情绪/场景） | ✅ | 投了很多份已读不回 · 付费改简历踩坑 |
| 强观赏性（每 2–4s 变化 · 声音密度 ≥ 画面） | ✅ | 多形态 UI + sfx 31/31 events applied（0 gap · vs D05 gap 已修复） |
| 强内容（真材实料 · 可复现） | ✅ | 三处硬伤 + 具体改法 + 句式模板 |

## 五、对比 D03/D04/D05 差异化（H6 门禁）

| 维度 | D04 帮想选题 | D05 一周活干成一天 | D06 AI 改简历 |
|---|---|---|---|
| skin | 中腰部创作者 | 一人公司 | 求职党·投了没回音 |
| 核心 | 5 问 seed prompt | 三层顺序·60/20/20 | HR 视角 3 处硬伤对照 |
| 情感锚 | 焦虑/枯竭 | 疲惫/想解放 | 焦虑/去焦虑（HR 视角戳破） |
| CTA | 私信「账号方向」 | 私信「项目+卡点」 | 私信「发我简历」脱敏 |
| 视觉族群 | 屏录 + WaytoAGI 表 | 三层堆叠 dark theme | 暖白纸面 + 扫描线/分屏/对照卡 |
| 主色 | — | 全黑卧室 | 暖白纸面 #f5f0e6 |
| **H6 结论** | | | **暖白纸面 vs D05 全黑 · 扫描线/分屏对照 vs 三层堆叠 · 无族群重叠 · PASS** |

## 六、门禁签字

- [x] 内容 gate: pass_dual_review（编剧+ vA/vB · 新 session 双评 ≥90）
- [x] form gate: pass_dual_review（形式策略官 · A92 / B91.7 · 6 硬门全过）
- [x] motion_storyboard: pass_single_run（Q11 · 无 GSAP · 纯 CSS 扫描帧）
- [x] audio: pass_self_generated（voice male-qn-jingying-jingpin · sfx ~31 events）
- [x] TTS 前置估算: pass（估算 → MiniMax 实发 60.64s · scene 已 sync seg_timing）
- [x] palette: pass（10 UI PNG + 7 carousel PNG = 17/17 · 蓝紫 0.00% · 无 Dracula 色）
- [x] CTA ship gate: pass（seg 60.64s vs plan 60.97s · Δ=−0.33s · CTA 不裁）
- [x] audience_first_3q: 3/3 pass（sfx 已补 · 强观赏性满足）
- [x] xhs form: 7 页轮播首选（form_strategy 判定 · 非 fallback）

## 七、下步

- 用户 D+2 / D+7 数据回填 → 触发数据复盘官（`design/post_publish_retro.md`）
- 若抖音 completion_3s < 55% → 复盘「已读不回」钩子 vs 同行热门钩子
- 若 xhs 收藏 < 8% → 复盘 P5 对照句卡版式（是否需更大字/更强截图引导）
- 若三处硬伤主体段（17.5–43s）完播 > 90% → skin 复用（求职党 → 其他垂类简历/作品集结构）
