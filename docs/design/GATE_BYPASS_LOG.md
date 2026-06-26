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

### 2026-06-26 · W27D01 · pre_render 带 7 项 render 依赖 fail 进 render（仅出片，不外发）

- **内容/项目：** W27D01「一句话→一支 AI 团队做完一条视频」· 抖音卡通动画 · 脚本 vA-final
- **gate_check(pre_render)：** FAIL（8/15 scorecard pass，7 项 < 90）
- **未过的 7 项：** 记者88 · 内核提炼师89 · 纪录片导演88 · 编剧88(叙事角) · 动效技术导演86 · 动效设计师87 · 编导89
- **判定为何 bypass：** 经 **3 轮独立 Agent 互评**（2/15→7/15→8/15 干净过线），剩余扣分项评审均注明为 **「待 render 抽帧才能确认」**（角色像素一致性、气泡遮挡、VO/BGM 同步、3s 完播实测、信任锚是否被弱化）。Phase A 的 90×15 fail-closed 把像素级标准前置，形成「不 render 不能验、不验不能 render」死锁。
- **授权：** 用户 2026-06-26 拍板「进 render，像素点放 Phase B 关」。
- **边界（铁律）：** 本次 bypass **仅允许 render 出片，禁止外发**。外发前必须：
  1. 抽 6 关键帧复验（hook/吵架/协同/对比/交片/CTA）→ `motion_wow` Phase B 清单
  2. Phase B 双人互评把 7 项重新打到 ≥90
  3. `gate_check(approve)` PASS + `pre_publish_forecast` 非 C/D
- **进化提案（铁律6）：** 建议后续把「角色一致/气泡遮挡/音画同步/完播实测」类像素标准从 pre_render 迁到 post_render，避免该死锁复发（待定，未改 gate）。

（早期：暂无）

---

## 2026-06-24 · 系统升级

**根因：** `week_build` 在 `gates.scorecards_all_pass=true` 时**跳过**校验 → 已修复为 **永远跑 gate_check**。

**新增：** `pipeline/gate_check.py` fail-closed · 证据物 · Phase B 工种硬编码。
