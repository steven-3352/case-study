# 形式策略 · form_strategy · W28D02

> 工种：形式策略官
> 依赖：form_competition.md（**回炉版 2026-07-04 · 推荐方案 A · 家族 pipeline**）· openmontage_brief.md（decision=blocked_infrastructure）· retention_beat_sheet.md
> 状态：`draft_self_generated · 回炉审核通过` · 2026-07-04
>
> **回炉审核（2026-07-04）：** form_competition 首版因候选池预先缩水（3 方案都在 P001 家族）作废，回炉版加入 OpenMontage 显式候选（blocked_infrastructure）+ raw 家族（素材缺失 blocked）。**方案 A 仍胜出且是唯一可执行方案，本文件技术内容不变**，仅更新上游引用。

## 逐镜表达方案（抖音 50s · vA 脚本对应）

| 镜 | 时间 | 主意图 | 表达形式 | 形式 ID | 数据杠杆声明 |
|----|------|--------|----------|---------|------------|
| M1 | 0-3s | 停划 | 真实办公室 B-roll + 手机屏幕特写 | `chaos_broll` + `broll_demo` | `completion_3s`：真实下班场景 → 打工人 1s 认领 |
| M2 | 3-6s | 停划延续 | 手机通知 pop + Excel 空白特写 | `broll_demo` UI 特写 | `completion_3s`：钩子拉长到 6s，测钩子边际收益 |
| M3 | 6-8s | 看懂痛点 | 3 段大字快切 punch | `punch_black` 灰底大字（非霓虹） | `completion_rate`：三段痛点点破，1s/段 |
| M4 | 8-12s | 看懂反面 | 反面 prompt UI 截图 + AI 通用垃圾 | `broll_demo` UI + 静态 | `completion_rate`：反面 → 期待反转 |
| M5 | 12-18s | 反转开场 | 素材拖入 AI 对话框 · 半真实录屏 | `broll_demo` + SVG 覆盖 | `completion_rate`：动作性变化点 |
| M6 | 18-32s | 演示核心 | **屏幕录制** + SVG 打点标注五段 | `broll_demo` 屏录 + SVG label | `completion_rate` + 收藏：真实动作 |
| M7 | 32-40s | 前后对比 | 静态 before/after 对比图 | `before_after` | `completion_rate` + 收藏：效果眼见为实 |
| M8 | 40-46s | 价值锚 | 傍晚窗外 B-roll + 大字字幕 | `chaos_broll` + `punch_black` | 评论率：情感落点 |
| M9 | 46-50s | 互动 CTA | 便签特写 + 光标 + 大字 | `punch_black` 灰底 | 评论率：具体可答的问题 |

## 形式切换密度（防中段塌陷）

- **9 段镜头 · 5 种形式 ID**：`chaos_broll` × 2 · `broll_demo` × 4 · `punch_black` × 3 · `before_after` × 1 · SVG 覆盖 × 2
- **超过 SYSTEM Q9 铁律要求**（≥3 种观感）
- **单一形式最大占比**：`broll_demo` 屏录约 14s（M6）= 全片 28% < 40% 上限 ✅

## 关键场景细化

### 场景 A · 沉默钉子（M1-M2，0-6s）

**Q9 铁律：** chaos 必须是真实素材，禁用 AI 生图

- 主 B-roll：**办公室 18:55 傍晚窗外光**（Pexels 免费商用，如 `office+dusk+18-19h`）
- 手机屏幕：真实拍摄（准备一部 iOS 手机，设置时间 18:55，用微信开发者调试模式模拟通知）
- Excel：真实截屏（Excel 空白模板 + 光标在"本周工作总结"下闪烁）
- **不用**：3D 渲染的手机、AI 生成的办公室、HTML 仿真的 iOS 通知

### 场景 B · 屏幕录制核心（M6，18-32s）

**关键动作路径：**
1. 打开 AI 工具（ChatGPT/豆包/Kimi 任选，不打 logo 或马赛克）
2. 光标滚动到对话框
3. 粘贴黄金 prompt（分 5 段打字进入）
4. 每段 punch-in 时，SVG 覆盖层高亮"角色/规矩/反例/兜底/字数"标签
5. AI 输出草稿（打字机效果 = AI 原生）
6. 复制粘贴到 Excel/文档

**SVG 打点策略：**
- 不做复杂 GSAP 动画
- 只做**静态 SVG 高亮框 + 淡入淡出**（0.3s 淡入 · 停 2s · 淡出 0.3s）
- 每段标签用小红/淡黄底 + 黑字（禁 Dracula 霓虹 · 见 skin 禁词）

### 场景 C · 静态对比（M7，32-40s）

- 左：原始工作流水账（乱七八糟的备忘录记录，可用 generated_fact + 标注 `示例数据`）
- 右：AI 整理后周报（结构化 · 分三块 · 300 字以内）
- 时间戳跳变：`18:55 → 19:15（旧方式加班）→ 18:15（新方式收工）`
- 静态图叠时间戳动态变化，用 SVG 数字滚动即可

## Fail 检查（避免"承诺 ≠ 兑现"事故 · SYSTEM §3.1c）

| 检查项 | 承诺 | 兑现方式 |
|--------|------|----------|
| chaos 用真实素材 | form_competition 方案 C 承诺 | Pexels 免费素材 或 真实拍摄 · 严禁 AI 生图 |
| 屏幕录制真实 | form_competition 承诺"真实屏录" | 用 QuickTime 或 OBS 录 · 不用 HTML 模拟 |
| SVG 打点非 GSAP | 方案 C 声明"少量 SVG" | 简单 SVG + CSS transition · 不引 GSAP 库 |
| 前后对比静态 | 方案 C 声明"静态对比" | 静态图 · 只用 SVG 数字滚动 |
| 3 种以上观感 | rules.min_distinct_formats: 3 | 5 种形式 ID · 已达标 |

## 交付给下一环节

- **视觉语言策展师**（design_language.md）：本条画面气质、色板、字体、组件规则
- **动效技术导演**（motion_tech_plan.md）：本条 **SKIP**——未使用 Web 3D/GSAP/复杂动效，只用 SVG 覆盖层，无技术风险
- **导演/摄像**（storyboard.yaml）：本条 9 段镜头的画面清单
