# 内容系统 · 自我进化机制

> **前提：** 提高标准 → 经过多轮测试 → 产出更好（D04 v10→v11 已验证）。  
> 本文定义 **如何持续抬高标准**，而不是一次性改完规则。

## 1. 进化环（每轮必走）

```
用户/数据挑战
    ↓
诚实审计（合规分 vs 效果分）
    ↓
规则/铁律/Rubric 更新
    ↓
gate_check 可执行 enforcement
    ↓
新条目按新标准生产（D05+）
    ↓
发布后 actual vs forecast 复盘
    ↓
import_metrics_48h.py（用户手动 48h JSON）
    ↓
performance.yaml + evolution_apply.py（有数据才跑）
    ↓
evolution_brief.yaml → 下一条 evolution_overlay.md
    ↓
gate_check / 形式重做 / queue 优先级
```

**禁止：** 只改 markdown 口号、不升级 `gate_check.py`、不登记 fail 案例。

## 2. 三级标准（可自我抬高）

| 级别 | 名称 | 含义 | 示例 |
|------|------|------|------|
| L1 | **合规** | 文件齐、互评格式对、scorecard avg≥90 | D04 v10「假 92」 |
| L2 | **效果** | 像素兑现、视觉审计、分析师 forecast pass | D04 v11 approve |
| L3 | **结果** | 发布后 actual 达预估区间 · 反哺下条 | D04 投后待填 |

**进化方向：** L1 流程门槛 → L2 外发决策 → **L3 数据驱动下一条**（`evolution_apply.py`）

详规：`templates/design/topic_evolution_from_data.md`

### 如何继续提高标准？

| 动作 | 下一档可加什么 |
|------|----------------|
| 专属镜 ≥3 → **≥4** | gate `FORM_EXCLUSIVE_MIN` +1 |
| catalog ≤35% → **≤25%** | 分析师 forecast 必写占比 |
| 完播预估 B → **A 档才外发** | forecast 模板加 hard gate |
| 1 条专属 → **每条 1 unexpected** | motion_wow 必填 unexpected 时间点 |
| 抖音单平台 → **三平台形态差异** | 平台策划 scorecard 分项 pass |

**原则：** 每次只抬 **1～2 个可度量阈值**，跑通 1 条（如 D05）再推广全周。

## 3. 触发器（何时启动进化）

| 触发 | 动作 |
|------|------|
| 用户质疑「为什么还像上一条」 | 形式 audit + form_audit 归档 |
| gate PASS 但负责人「不敢外发」 | 效果分重评 · 拆 content/form |
| 分析师 forecast C+ 仍 approved | 加 hard gate · 追责 |
| 发布后 3s/完播低于预估下限 | 更新 REJECT_LOG · Rubric 扣分项 |
| 同 session 批量写 Phase B 分 | scorecard_enforcement 加 readonly Task |
| 新工种空白（如分析师） | 补模板 + gate + multi-agent 流程 |

## 4. 必留产物（经验复用）

| 产物 | 用途 |
|------|------|
| `room/form_audit_{v}.yaml` | 纸面分 vs 诚实效果分 |
| `docs/design/FORM_FAIL_LOG.md` | 形式 fail 与改法 |
| `docs/design/SCRIPT_REJECT_LOG.md` | 脚本 fail |
| `design/pre_publish_forecast.md` | 发布前预估 |
| `design/post_publish_retro.md` | 投后 actual vs 预估 |
| `design/performance.yaml` | 结构化 actual 输入 |
| `publish/{week}/performance_data.yaml` | 周汇总 |
| `publish/{week}/evolution_brief.yaml` | **下一条进化指令** |
| `docs/design/PERFORMANCE_EVOLUTION_LOG.md` | L3 变更日志 |
| `room/discussion.md` Round N | 交锋、取舍、optimization_round |
| `templates/design/*.md` | 铁律/Rubric 沉淀 |

## 5. 版本策略

| 字段 | 含义 |
|------|------|
| `content_version` | 脚本/口播/P0 变更 |
| `storyboard_version` / 形式 vN | 分镜/动效变更（可独立于口播） |
| `form_publish_pass` | 形式门是否可外发 |

**允许：** 口播 v10 + 形式 v11（D04）。**禁止：** 形式 v10 假 approved。

## 6. 多轮测试工作流（D04 示范）

| 轮 | 发生了什么 | 进化产出 |
|----|------------|----------|
| v5 | 假互评 92.5 | scorecard_enforcement · SCRIPT_REJECT_LOG |
| v6–v10 脚本 | 真迭代 91.5 | 内容门 pass |
| v10 形式 | catalog 拼盘仍 90+ | form_audit · 分析师 · visual gate |
| v11 形式 | 7 专属镜 0% catalog | content_form_split_gates · approve |

**下一条目（D05+）应：** 从 Phase A 就拆两道门，不重复 v10→v11 补作业。

## 7. Agent 行为契约

1. **用户提高标准时** → 先更新 Rubric/gate，再生产，不口头答应
2. **发现纸面 pass 与像素不符** → 立即 blocked + 归档，不 patch 过关
3. **每条条目结束** → forecast + 投后填 `performance.yaml` → `evolution_apply.py` → 下条读 `evolution_brief`
4. **每周复盘** → PERFORMANCE_EVOLUTION_LOG + 抬 L2→L3 阈值

## 8. 命令清单

```bash
# 外发前三阶段
python3 pipeline/gate_check.py --id W26D05 --phase pre_render
python3 pipeline/gate_check.py --id W26D05 --phase post_render
python3 pipeline/gate_check.py --id W26D05 --phase approve

# 整周
python3 pipeline/gate_check.py --all --phase approve

# L3 投后进化（须先有 48h 数据）
python3 pipeline/import_metrics_48h.py --status
python3 pipeline/import_metrics_48h.py --file data/W26D04_48h.json
python3 pipeline/evolution_apply.py --id W26D05 --check   # 下条开工前
```

## 9. 相关文件

- 铁律：`.cursor/rules/content-outcome-accountability.mdc`
- 分层：`templates/design/content_form_split_gates.md`
- 门禁：`templates/design/anti_perfunctory_gates.md` · `pipeline/gate_check.py`
- Rubric：`templates/design/scorecard_rubric.md`
- 互评：`templates/design/scorecard_enforcement.md`
