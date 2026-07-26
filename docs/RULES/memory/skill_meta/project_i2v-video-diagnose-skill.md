---
name: i2v-video-diagnose-skill
description: "视频生成后单镜诊断闭环 skill(.agents/skills/i2v-video-diagnose/);补 15 步流程\"渲染→验收\"之间\"这条为什么崩、怎么最小代价救\"的缺口"
metadata: 
  node_type: memory
  type: project
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**事实:** 2026-07-20 建 `.agents/skills/i2v-video-diagnose/SKILL.md`,补齐项目 15 步流程里"渲染 → 验收"之间的**单镜内环诊断层**。此前诊断力量集中在①事前 `gate_check_*.py` 门禁 和 ②投后 `evolution_apply.py`/`post_publish_retro.md`,中间"这条镜为什么崩、怎么最小代价救、要不要放弃"的层是空白。

skill 内容:
- **7 类失败 taxonomy**:幻觉/伪影 · 角色崩 · 动作不自然 · 相机运动看不出 · 光影/色调错 · 物理错 · AI 味重
- **4 步标准动作**:视觉扫描(30s) → 7 类归因(1min) → minimal-edit 只改 1-2 变量(1min) → 登记 VIDEO_ITERATE_LOG.md
- **迭代上限**:同 slug 最多迭代 3 次;3 次救不活升级换路线(换模型/换实现/撤镜),不许无限迭代
- **6 类"救不活信号"**:出现即直接换路线,不再瞎改 prompt

**Why:** 2026-07-20 用户用 "Fable 5 + Seedance 分工架构" 对本项目做架构评审,结论是 5 步流程里项目 4 步已覆盖甚至更细(洞察层 4/拆分镜/prompt 层/渲染),唯独第 5 步"生成后诊断迭代"缺失。按用户新学的"stub 不能拖"教训,立刻补齐 skill · 不留 TODO · 加 CLAUDE.md 硬门强制触发。

**How to apply:**
- **触发场景**:视频生成完不满意 · 幻觉/伪影 · palette gate fail · 用户说"这段不对/重生/改一下"
- **和 i2v-video-prompt 主门分工**:主门管"写";本 skill 管"生成后判定 + 迭代"—— 顺序是主门(prompt)→ 渲染 → 本 skill(诊断)→ 迭代主门 → 再渲染
- **不做的事**:不做事前门禁(gate_check.py 系列)· 不做投后复盘(evolution_apply)· 不做选实现方式(SYSTEM §4.2)
- **和已有 memory 硬绑**:[[feedback_camera-motion-vs-i2v-ceiling]](3 次救不活换 i2v 路线)· [[feedback_no-neon-palette]](palette 类问题)· [[feedback_no-exaggerated-cold-atmosphere]](冷渲染)· [[feedback_anti-ai-visual]](AI 味类)· [[feedback_zoompan-visible-motion]](相机看不出)
- **登记新失败模式**:诊断中发现的新失败特征,反哺 skill §一 taxonomy;或写入 `docs/design/SCRIPT_REJECT_LOG.md` / `FORM_FAIL_LOG.md`
- **相关**:[[feedback_i2v-video-prompt-skill-mandatory]] · [[project_video-form-skills-full-install]] · [[project_p011-seedance-i2v-candidate]]
