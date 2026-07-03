# 防应付机制 · 可执行门禁清单

> 与 `.cursor/rules/content-outcome-accountability.mdc` 同级。**口号无效，以下任一项不满足 = blocked。**

## 1. 双人互评 · 90 分门禁

| 规则 | 执行 |
|------|------|
| 每工种 ≥2 名 **独立** Agent 互评 | `room/scorecards/{工种}.yaml` |
| `review_mode: independent` | **每位 reviewer 必填**，缺则 gate FAIL |
| 不同角度 | 两位 `angle` 不得相同 |
| 禁止自评/假分身 | 产出者不得评自己；禁止 `编剧审校-A` / `子 Agent` |
| notes 实质 | pass 时 ≥40 字 + 扣分项；禁止套话式「微扣(-7)」 |
| 通过线 | 每位 **score ≥ 90**，**avg ≥ 90**（89 = fail） |
| 汇总 | **`gate_check.py --phase approve` PASS** |

详规：`templates/design/scorecard_enforcement.md`

## 1b. 物理隔离 · 禁止同 Agent 自评

| 规则 | 执行 |
|------|------|
| 产出与打分分离 | 写 `scripts/` 的 Agent **不得**写同工种 scorecard pass |
| 打分 Agent | **独立** Task · `readonly: true` · 只读 artifact + rubric |
| 分差 >5 | discussion 须写交锋/取舍 |

## 1c. 证据物（Phase B · gate_check 验）

| 文件 | 要求 |
|------|------|
| `design/vo_listen_notes.md` | content_version + mp4 时间戳 |
| `design/pre_publish_forecast.md` | 平台表现分析师 · 形式 go/no-go · **approve 必填** |
| `design/form_strategy.md` | 形式策略官 · 逐镜表达方案竞争 · **pre_render/approve 必填** |
| `design/design_language.md` | 视觉语言策展师 · DESIGN.md 参考本地化为 token/组件/逐镜约束 · **pre_render/approve 必填** |
| `design/motion_tech_plan.md` | 动效技术导演 · Web 3D/GSAP/复杂 HTML 动效可行性审查 · 触发时必填 |
| `design/cover_review.md` | mtime ≥ video.mp4；@ 与 content.yaml 一致 |
| `design/motion_wow.md` | Phase B **无 `[ ]`** |
| `room/discussion.md` | Round 6+ · mp4/听/像素 · 有交锋 |
| `room/form_audit_{v}.yaml` | 纸面分与效果分差 >5 时 **必填** |

## 1d. 内容 vs 形式两道门（D04 起 · 全系统）

| 门 | 通过条件 | 不通过 |
|----|----------|--------|
| 内容 | script_review + 编剧 90+ | 禁止 TTS |
| 形式 | 视觉审计 + forecast pass + 形式 scorecard 90+ | 禁止外发 |

详规：`templates/design/content_form_split_gates.md`

## 1e. 形式层硬门槛（gate_check approve 验）

| 指标 | 阈值 |
|------|------|
| 专属 template | ≥3 |
| catalog 时长 | ≤35% |
| 同 template 重复 | ≤1 镜 |
| 48s+ 不同 template | ≥6 |

## 1f. 形式策略会（gate_check pre_render + approve 验）

| 规则 | 执行 |
|------|------|
| `form_strategy.md` 必填 | 缺失 = 禁止 storyboard 定稿 / render |
| 逐镜字段 | 须含镜头任务、候选表达、数据杠杆、推荐方案 |
| 候选表达 | 至少比较 3 类能力（如实拍、2D UI、消息流、GSAP、Three/Web 3D、截图、字幕） |
| 数据杠杆 | 必须声明服务 3s、完播、理解、收藏、评论、互动或停划 |
| 禁止理由 | “默认用 / 为了快 / 更酷 / 沿用上一条 / 套用” = FAIL |
| 高级动效 | 出现 Web 3D / Three / GSAP / 复杂 HTML / 风险雷达等，必须有 `motion_tech_plan.md` |
| **注意力引导（折入 · 硬门）** | form_strategy 须含 `单焦点`/`时刻类型`/`加料不加赢家`；时刻分型 ≥2 类；单焦点声明 ≥3 处。详规 `templates/design/attention_guidance_system.md` |

## 1g. 视觉语言策展（gate_check pre_render + approve 验）

| 规则 | 执行 |
|------|------|
| `design_language.md` 必填 | 缺失 = 禁止 storyboard 定稿 / render |
| 参考来源 | 须说明 DESIGN.md / 成熟视觉系统来源与选择理由 |
| 色板 | 至少 4 个 hex 色值，并声明 canvas/surface/ink/accent 等角色 |
| 字体层级 | 须有字号/字重/行高或明确替代规则 |
| 组件规则 | 须覆盖卡片、CTA、标签、表格/字段等本条会用的组件 |
| 逐镜应用 | 至少 3 行，说明每镜/页使用哪些 token、焦点路径与禁用项 |
| 禁止口号 | 只写“高级感 / 产品感 / 干净一点 / 参考一下” = FAIL |

## 1h. L3 投后进化（数据驱动下一条）

| 步骤 | 产出 | 命令 |
|------|------|------|
| 首次登录 | `ops/platform_sessions/*.json` | `fetch_platform_metrics.py --login douyin` |
| 自动拉 actual | performance.yaml + metrics.csv | `fetch_platform_metrics.py --sync --id …` |
| 合并进化 | `evolution_brief.yaml` | 自动触发 evolution_apply |
| 下条 overlay | `design/evolution_overlay.md` | D05+ 形式开工前 |
| 变更日志 | `docs/design/PERFORMANCE_EVOLUTION_LOG.md` | 自动追加 |

详规：`templates/design/topic_evolution_from_data.md`

## 2. 产出顺序（禁止颠倒）

洞察包 → 三版脚本+90+ → script_review → storyboard+motion_wow → scorecard 90+ → render → Phase B 证据+复评 → **gate_check(approve)** → approved

## 3–8. （三版 / 原话≥4 / 创意 / 脚本 / 讨论室 / 反例）

见 `templates/design/script_standards.md` · `scorecard_rubric.md`

## 9. 工具门禁（fail-closed）

```bash
python3 pipeline/gate_check.py --id W26D04 --phase pre_render   # TTS/render 前必 PASS
python3 pipeline/gate_check.py --id W26D04 --phase approve
python3 pipeline/week_build.py --render   # 自动 pre_render 门禁
```

## 9b. 有成本工序 · TTS / gpt-image / render

| 工序 | 成本 | 允许条件 |
|------|------|----------|
| TTS（MiniMax/Edge） | 有 | `gate_check(pre_render) PASS` |
| gpt-image | 有 | 同上 + 视觉工种 90+ |
| P004 build / render.py | 有 | 同上 |

**铁律：全 Phase A scorecard 90+ + script_review pass → 才开工。** `audio_plan.yaml` 须标 `not_started`。

## 10. 变更级联作废

见 `pipeline/gate_check.py` · `INVALIDATE_MAP`
