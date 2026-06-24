# 门禁绕过 / 偷工登记

> 工具 `gate_check.py` FAIL 仍标 approved、或 `--force` 外发 → 登记于此。

---

## 规则

| 行为 | 后果 |
|------|------|
| 手填 `gates.*=true` 但 gate_check FAIL | 无效；verdict 须改 blocked |
| `week_build --force` | 仅调试；**登记下方，不可外发** |
| 同 Agent 产出 + 自评 scorecard pass | scorecard 无效，须独立 Agent 重评 |

---

## 登记

（暂无）

---

## 2026-06-24 · 系统升级

**根因：** `week_build` 在 `gates.scorecards_all_pass=true` 时**跳过**校验 → 已修复为 **永远跑 gate_check**。

**新增：** `pipeline/gate_check.py` fail-closed · 证据物 · Phase B 工种硬编码。
