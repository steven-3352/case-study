---
name: feedback_no-default-tech-stack
description: "生产层实现选型不属于自主拍板范围；出现\"就走 P004/P001 吧\"这类默认路径念头立即警觉，回 SYSTEM §4.2 候选实现清单重列"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

case-study 项目：**生产层技术选型不属于「自主拍板」范围**。出现「就走 P004 吧」「用 P001 gen_evidence 拼一个」「HTML+GSAP 是我的默认路线」这类念头，立即警觉，属于**候选池预先缩水**——是一次错误的心智固化。

**Why:** 2026-07-04 用户抛出 W28D02 生产环节，我从"用户没素材"直接跳到"用 fetch_broll + gen_speech + HTML 仿真 + ffmpeg 拼一个"，脑子里的候选池被预先缩水到 P001/P004 家族的 3 个变体。等到 form_competition 五维打分时看似公平选择，其实 OpenMontage / Grok video / GPT-image-2 从未进过候选池。

**用户原话（教学式复盘）：**
- 「既然默认技术栈心智固化是干扰，要不要清理掉？」
- 用户没让我删 P001/P004，而是让我识别「候选池预先缩水」这个动作本身

**根因（我犯的错）：**
1. 把 P001/P004 当作"已知路线"，脑子里跳过了 SYSTEM §4.2 "无默认 pipeline" 铁律
2. 没读姊妹条（W28D01）的 design/ 目录，遗漏了 W28D01 已经跑过 openmontage_brief 的事实
3. 把 memory「自主推进 · 其他工种环节自己拍板」过度扩展到"技术选型也自主"—— 但技术选型是**门禁级决策**，不是工种执行

**How to apply:**

1. **每次进 form_competition 前，强制读**：
   - `docs/SYSTEM.md §4.2 候选实现清单`（版本化，最新集成能力都在）
   - 姊妹条最近 1-2 条的 `design/openmontage_brief.md` + `design/form_competition.md`
   - `integrations/` 全目录 `ls`（看有没有新集成的能力）

2. **写候选方案时的自查动作**：
   - 3 个方案是否都是同家族变体？如是 → **打断**，重列
   - `integrations/` 目录里的 OpenMontage / Grok video / GPT-image-2 是否被并列考虑？如无 → **打断**，回 §4.2 清单
   - 有没有出现"就走 X 吧"这类默认路径念头？如有 → **打断**，回 §4.2

3. **openmontage_brief.md 是每条必跑的门禁**：
   - 无论最终 enabled/disabled/blocked，判断本身**必须做**
   - decision: disabled 也要写清楚"为什么不启用"的理由（W28D01 就是这么做的）
   - 未跑 openmontage_brief 就写 form_competition 结论 = **门禁绕过**

4. **触发词清单**（出现即回 SYSTEM §4.2）：
   - 「就走 P004 吧」/「就走 P001 吧」/「就用 GSAP 拼一个」
   - 「用姊妹条的 gen_vo_dNN.py 抄」（抄没错，但抄之前先做本条 openmontage_brief 判断）
   - 「fetch_broll + gen_speech + HTML 仿真 + ffmpeg 拼一个」（这句话本身 = 已经缩水到 P001/P004）
   - 「XX 是本项目主路径」/「XX 是默认路线」（**本项目没有默认路线**）

**关联：**
- [[feedback_read-env-example-first]] — 接手项目第一动作；本条是它的深化（不只读 .env，还要读 SYSTEM §4.2 清单 + 姊妹 design/）
- [[feedback_autonomous-data-driven]] — 自主推进；本条明确划边界（工种执行属于自主，技术选型属于门禁）
- [[feedback_multi-role-collab]] — 多工种协作；本条是它的补丁（工种协作 ≠ 单模型跳过门禁）

**反例（不要这么做）：**
- ❌ form_competition 3 方案都是 P001 变体（方案 A/B/C 只是不同镜头组合，实现家族相同）
- ❌ form_competition 3 方案都是 P004 变体
- ❌ 跳过 openmontage_brief 直接写 form_competition
- ❌ 说「OpenMontage 太重了不适合本条」但没跑 brief 就写这句
- ❌ 从 fetch_broll 开始跑（那是 pipeline 一角），却没做 SYSTEM §4.2 五维打分
- ❌ 把 CLAUDE.md「流水线入口」表格当作全部候选池（那只是常用入口摘要，完整清单在 SYSTEM §4.2）

**清理干扰的三层机制（2026-07-04 L1+L2+L3+L4 一次性完成）：**

- **L1 · 清单升级**：`SYSTEM §4.2` 候选清单补 OpenMontage / Grok video / GPT-image-2 / Remotion / HyperFrames；版本化
- **L2 · 表述纠正**：`CLAUDE.md`「流水线入口」改为「候选实现清单（无默认顺序）」；`templates/README.md` 补"候选池预先缩水"反例；`assets/formats/catalog.yaml` 每条 `pipeline` → `pipeline_candidates`
- **L3 · 门禁前置**：`templates/design/form_competition.md` 加"候选池完整性自查 §3"+ "跨家族 3 方案" 强制 + openmontage_brief 前置门禁
- **L4 · memory**：即本条

**不做的事：**
- ❌ 不删 P001/P004（能力是能力，别烧仓库）
- ❌ 不把 OpenMontage 设成新默认（那是把干扰换个名字）
- ❌ 不写"永远先跑 OpenMontage brief"教条（brief 本来就要每条跑，不需要把 OpenMontage 特殊化）
