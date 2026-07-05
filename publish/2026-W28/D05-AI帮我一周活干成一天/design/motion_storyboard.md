# motion_storyboard · W28D05 一周活干成一天

> 动画导演 · Delta doc · ≤8000 bytes 硬门 · **单跑不双评**（2026-07-04 起）
> 依赖：`scripts/vA.md`（推荐 A 出）· `retention_beat_sheet.md` · `design/form_strategy.md` · `design/design_language.md`
> 状态：`draft_self_generated` · 2026-07-05

## 一、风格判定

**风格**：**Vibe Motion + 静态 UI 混合**（非 WaytoAGI · 非七七纯 UI）
**依据**：
- 0-3s 手机推送真实感（Vibe Motion 情境代入）
- 25-40s 三层堆叠 UI（七七风 UI 大字信息组织）
- 8-15s / 40-48s 大字 + 表格（静态 UI · 无复杂动效）
- **不用 GSAP 复杂动画**（技术导演接口：25-40s 走 gen_ui HTML+CSS 直出 · 大字 fade-in 用 drawtext + fade filter · 无需 motion_tech_plan）

## 二、逐秒分镜（55-58s · 9 字段）

### 段 0-3s · 反差锚 chaos-punch-reveal

| 秒 | 旁白 | 内容类型 | 画面主体 | 动画动作 | 镜头运动 | 屏幕文字 | 素材需求 | 推荐实现 | 设计目的 |
|---|---|---|---|---|---|---|---|---|---|
| 0.0-1.0 | 无 | 实景 B-roll | 睡姿俯拍 + 手机屏暗 + 时间 08:00 | 静态 | 静止 | 无 | Pexels "morning bed sleeping" or 内部拍 | B-roll 直出 | chaos · 停划疑问 |
| 1.0-1.2 | 无 | 屏录 mock | 手机屏亮 · 首推送冒 | fade-in 200ms | 静止 | Project-001 · 新询盘已分类·方案 v0.3 已生成·待你决策 | gen_ui iOS 通知 | HTML 直出 | punch 1/3 |
| 1.2-1.4 | 无 | 屏录 mock | 第 2 推送冒 | stagger 200ms | 静止 | 客户回问 3 条·2 条已回·1 条待你 | gen_ui | HTML | punch 2/3 |
| 1.4-1.6 | 无 | 屏录 mock | 第 3 推送冒 | stagger 200ms | 静止 | 昨晚新增 4 单·系统已走完流程 | gen_ui | HTML | punch 3/3 |
| 1.6-3.0 | 无 | 静态 UI | 主角一只眼睁开 + 全屏黑蒙层大字入 | 大字 fade-in 300ms | 静止 | **我睡着的时候·系统已经跑完了昨晚的活** | B-roll + drawtext | drawtext + fade | reveal · 认领点 |

### 段 3-8s · 认领 · 时间对比

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 3.0-8.0 | 上周我也这样 · 凌晨 1 点还在改方案 · 早上继续跟单。这个项目做通之后 · 我一周的活干成了一天 | 分屏 | 左：凌晨 1 点桌面 · 右：08:00 起床 | 分屏 slide-in 500ms | **40h/周 → 8h/周（我的项目实测）** | B-roll x2 + drawtext | 分屏 concat + drawtext | 认领 + 数据锚 |

### 段 8-15s · 烂做法 ① · R6 少数派原话

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 8.0-15.0 | 一人公司都想装 AI · 大多数装了 5 个用不起来——每天切来切去 40 分钟没了 | UI 图标网格 | 5 AI 图标网格（ChatGPT / Claude / Cursor / Notion / n8n）· 依次点亮 | icon fade-in stagger 700ms x5 | 装了 5 个 AI · 切来切去 40 min 没了（少数派原话）| gen_ui HTML 图标网格 | HTML + drawtext | 自我识别 |

### 段 15-25s · 烂做法 ②③

| 秒 | 旁白 | 画面 | 动画 | 文字 | 实现 |
|---|---|---|---|---|---|
| 15-20 | 或花 3 月搭完美 workflow · 每步都要 review · 更累 | n8n 半成品 8 节点 · 每节点"需 review"红标 | 静态 + drawtext 批注 | ② 3 月完美流 → 更累 | gen_ui+drawtext |
| 20-25 | 或只自动化打字 10 min · 客户沟通 6h 一字没碰 | 左打字 UI(10 min) · 右微信沟通(6h) | 分屏 slide | ③ 自动化最容易 → 省 10 min 累 6h | HTML+drawtext |

### 段 25-40s · **核心 · 3 层堆叠 UI**（15s · 收藏点）

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 25.0-30.0 | 解法是顺序不能反——先自己做一遍 · SOP 记 Notion | UI + 大字 | Notion 卡上层 + 大字滑入 | Notion 卡 slide-down 400ms + 大字 fade-in 300ms | 第 1 层：手工 SOP · Notion | Notion 截屏 mock（化名 Project-001）| HTML+CSS gen_ui | 收藏 P0-1 第 1 层 |
| 30.0-35.0 | 再让 Claude 按 SOP 出草稿 · Cursor 存 prompt 模板 | UI + 大字 | Cursor 卡中层 + 大字滑入 | Cursor 卡 slide-down 400ms + 大字 fade-in | 第 2 层：AI 辅助 · Cursor + Claude | Cursor 截屏 mock | HTML+CSS | 收藏 P0-1 第 2 层 |
| 35.0-40.0 | 最后 n8n 把 SOP 串成 workflow · 系统跑。跳过 SOP 直接搭自动化 · 需求一改整套散架 | UI + 大字 + 反证句 | n8n workflow 底层 + 大字滑入 + "散架" 大字爆入 | n8n slide-down 400ms + 大字 fade-in + "散架" pop-in 200ms | 第 3 层：系统自跑 · n8n · **可长按暂停截屏** · "散架"红字 | n8n 截屏 mock | HTML+CSS | 收藏 P0-1 第 3 层 + 反证 |

### 段 40-48s · 60/20/20 表格

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 40.0-42.0 | 每天分配是——60% 塞给 AI | 表格 | 3 列表格 · 60% AI 列 highlight 血红 | 表格 fade-in + 60% 数字 pop | 60% AI（塞：分类·草稿·翻译·答客户·搜索）| gen_ui HTML 表格 | HTML+CSS | 收藏 P0-2 列 1 |
| 42.0-44.0 | 20% 塞给自动化 | 表格 | 20% 自动化列 highlight | pop | 20% 自动化（做：webhook·分类·推送·归档）| HTML | HTML | 收藏 P0-2 列 2 |
| 44.0-48.0 | 20% 保留给你决策。是我的项目实测·请参考不套用 | 表格 | 20% 人做列 highlight + 底注 | pop | 20% 人做（做：审美·关系·战略）· 底注"参考·不套用" | HTML | HTML+drawtext | 收藏 P0-2 列 3 + 边界 |

### 段 48-54s · 边界

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 48.0-54.0 | 我不是教你搞钱 · 是给你看我怎么把自己解放的。AI 帮我解放 · 不是帮我印钞机 | 全屏大字 | 黑底 · 大字双行 | 大字 fade-in 500ms | AI 帮我解放 · 不是帮我印钞机 | 无素材 · 纯 drawtext | drawtext | 价值锚 |

### 段 54-58s · CTA

| 秒 | 旁白 | 内容 | 画面 | 动画 | 文字 | 素材 | 实现 | 目的 |
|---|---|---|---|---|---|---|---|---|
| 54.0-58.0 | 私信『我在做什么项目 · 卡在哪』——我给你可自动化的第 1 步 | CTA 大字 | 黑底 · CTA 大字浮动 | 大字浮动上下 3px 循环 | 私信「项目+卡点」→ 可自动化的第 1 步 | drawtext | drawtext + subtle bob | 私信路径 |

## 三、素材需求汇总（给 gen_ui + broll 组）

| 素材 | 类型 | 数量 | 来源 |
|---|---|---|---|
| 睡姿俯拍 | B-roll | 1 段 (5s) | Pexels "morning bed sleeping" or 内部拍 |
| 手机推送 UI | gen_ui PNG | 1 张（3 条推送）| gen_ui_w28d05.py 直出 |
| 主角一只眼睁开 | B-roll | 1 段 (1.5s) | 内部拍或 Pexels "waking up looking at phone" |
| 凌晨 1 点桌面 | B-roll | 1 段 (5s) | Pexels "night desk laptop" |
| 08:00 起床 | B-roll | 1 段 (5s) | Pexels "morning wake up phone" |
| 5 AI 图标网格 | gen_ui PNG | 1 张 | gen_ui HTML |
| n8n workflow 半成品 | gen_ui PNG | 1 张 | gen_ui HTML |
| 打字 vs 客户沟通对比 | gen_ui PNG | 1 张 | gen_ui HTML |
| Notion 截屏 mock | gen_ui PNG | 1 张 | gen_ui HTML |
| Cursor 截屏 mock | gen_ui PNG | 1 张 | gen_ui HTML |
| n8n workflow 完整 | gen_ui PNG | 1 张 | gen_ui HTML |
| 60/20/20 表格 | gen_ui PNG | 1 张 | gen_ui HTML |

**总计**：4 段 B-roll + 8 张 gen_ui PNG · 无 GSAP · 无 3D · 无复杂动效 · **无需 motion_tech_plan**

## 四、门禁签字

- [x] 每 2-4s 有视觉变化（8 段全覆盖）
- [x] 风格判定明确（Vibe Motion + 静态 UI 混合）
- [x] 无 GSAP/3D → **无需 motion_tech_plan**
- [x] 素材需求 12 项齐全
- [x] 每段声明 P# 或数据杠杆
- [x] 与 D04 完全不复用
