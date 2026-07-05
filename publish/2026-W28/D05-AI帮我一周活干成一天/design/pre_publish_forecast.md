# pre_publish_forecast · W28D05

> 平台表现分析师 · 自跑 · 2026-07-05
> 判据：`docs/SYSTEM.md §1.0` 铁律 0 audience-first · `templates/design/completion_rate_north_star.md`
> 状态：`draft_self_generated` · 双平台（抖音 + 小红书）

## 一、整体判定

- **抖音 predicted grade**: **B+ (87-90)**
- **小红书 predicted grade**: **B (83-86)**（video fallback · 若 carousel 则 A-）
- **可外发**: ✅ 双平台 render_gate PASS · palette gate PASS · CTA ship gate PASS
- **风险**: 60.22s 略超 60s 抖音甜区 · sfx 层 gap（0/29 events applied）· xhs 走 video fallback（非 form_strategy 首选 carousel）

## 二、抖音 forecast 拆解（B+ · 88.5）

### completion_3s（预估 55-60%）

| 项 | 得分 | 备注 |
|---|---|---|
| 反差钩子 chaos-punch-reveal | ★★★★☆ 88 | 睡姿 broll + 3 声推送 + 大字 reveal · memory contrast-hook-3s 落地 |
| 首屏停划设计 | ★★★★ 85 | "我睡着的时候系统跑完了昨晚的活" 90pt 大字 · 一人公司群体秒懂 |
| **风险** | | 前 3s 无 VO（1.6s 后才起字幕）· 沉默钉子风险（memory dense-vo-no-dead-air 已警告） |
| **净分** | **86** | |

### completion_rate（预估 42-48%）

| 段 | 得分 | 备注 |
|---|---|---|
| 3-8s 时间对比认领 | 90 | 分屏 40h→8h 情感共鸣双落 |
| 8-25s 三坑批判 | 85 | R6/R3 原话锚 · 有实感 |
| **25-40s 三层堆叠 UI** | 92 | **本片最重镜** · 收藏动机 + 完播贡献 |
| 40-48s 60/20/20 | 88 | 参考不套用 · 反教条 |
| 48-54s 反印钞机 | 90 | 反变现话术 · 边界锚 |
| 54-58s CTA | 85 | 私信「项目+卡点」· 转化路径清晰 |
| **净分** | **88** | |

### 观众成果 · audience-first 三要素

- **内容共鸣** ★★★★☆ 89 · 一人公司凌晨改方案痛点直击
- **强观赏性** ★★★★ 82 · 每 2-4s 视觉变化（10 场景 60s = 6s/场景平均 · 略慢）· sfx 缺失扣分
- **强内容** ★★★★★ 92 · 三层顺序 + 60/20/20 + 反印钞机 = 高信息密度 · 可复现

### 综合 · **B+ 88.5**

## 三、小红书 forecast 拆解（B 83-86）

### 若走 video fallback（本条实际交付）

- **完播预估** 60-65%（xhs 用户更耐心）
- **收藏预估** 4-6%（三层堆叠 UI + 60/20/20 表格 = 收藏点）
- **评论预估** 1.5-2.5%（"项目+卡点" 关键词回复门槛低）
- **净分 84**

### 若走 form_strategy 首选 · 7 页 carousel（挂起 D06 补）

- **收藏预估** 7-10%（P4/P5/P6 三页 collectible）
- **完播预估** 55-60%
- **净分 89 (A-)**
- **差距 · 5 分** = video 未展开 P6 Project-001 结构 · 未把 P4/P5 做成 saveable 版式

## 四、观众成果预警（audience-first 硬门自检）

| 硬门 | 状态 | 备注 |
|---|---|---|
| 内容共鸣（真实情绪/场景） | ✅ | 一人公司凌晨改方案 · Project-001 化名结构 |
| 强观赏性（每 2-4s 变化 · 声音密度 ≥ 画面） | ⚠️ | 视觉 OK · **sfx 层 gap · 29 事件 0/29 · 声音密度不足** |
| 强内容（真材实料 · 可复现） | ✅ | 三层顺序 · 60/20/20 · Project-001 结构 |

**风险 · sfx gap**：memory sfx-layer-required 强调"密 VO 型 BGM 可 off 但 sfx 不 off"· 本条 sfx 缺失是首次系统性 gap · 若数据不达标应作为 D+2 复盘重点

## 五、对比 D03/D04 差异化（H6 门禁）

| 维度 | D03 陪练英语 | D04 帮想选题 | D05 一周活干成一天 |
|---|---|---|---|
| skin | 学英语 · 92% 不敢开口 | 中腰部创作者 · 想不出下条 | 一人公司 · 想解放自己 |
| 核心 | 角色卡 = AI 陪你说 | 5 问 · account_seed prompt | 三层顺序 · 60/20/20 |
| 情感锚 | 孤独/怯懦 | 焦虑/枯竭 | 疲惫/想解放 |
| CTA | 评论关键词 4 选 1 | 私信「账号方向」5 条选题 | 私信「项目+卡点」可自动化第 1 步 |
| 视觉族群 | Vibe Motion 角色卡主 | Vibe Motion 屏录 62% + WaytoAGI 表 21% | Vibe Motion + 静态 UI 混合 · 3 层堆叠为核心 |
| **H6 结论** | | | **无视觉族群重叠 · 无节拍复用 · PASS** |

## 六、门禁签字

- [x] 内容 gate: pass_dual_review（编剧+ vB · 92/85）
- [x] form gate: pass_dual_review（形式策略官 · 92/92）
- [x] motion_storyboard: pass_single_run（Q11）
- [x] audio: pass_self_generated（voice + sfx events 定义）
- [x] TTS 前置估算: pass（79.5% 利用率 · 3 warn ≤27% · 无 fail）
- [x] palette: pass（9 张 UI PNG · 无 Dracula 色）
- [x] CTA ship gate: pass（seg 60.22s vs plan 60.22s · Δ=0）
- [⚠️] audience_first_3q: 2/3 pass · 强观赏性因 sfx gap 未满
- [⚠️] xhs form: video fallback · 非 form_strategy 首选（挂起 D06）

## 七、下步

- 用户 D+2 / D+7 数据回填 → 触发数据复盘官
- 若 completion_3s < 55% → 复盘 sfx gap 影响 · 首推补 sfx 层重发
- 若 xhs 收藏 < 4% → 触发 carousel 生成器 D06 优先级 P0
- 若 25-40s 三层堆叠 UI 段完播 > 90% → skin promptization 复用（Project-001 → 其他一人公司项目结构）
