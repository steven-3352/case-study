---
name: reference_paperdoll-mv-packaging-skill
description: 国风乙/古风纸片人立绘卡点MV·角色PV 的可复用包装设计规范 skill 位置与用途；做此类片先读它
metadata: 
  node_type: memory
  type: reference
  originSessionId: 06a8b37e-f7bd-4cc2-b536-59332e6c038a
---

做**国风乙 / 古风 / 角色PV / 纸片人立绘卡点 MV**（立绘像素不变、只做外层包装+动效+卡点）时，先读可复用规范：
`.agents/skills/paperdoll-mv-packaging/SKILL.md`

**内含（跨选题复用的方法论，不是某条片的分镜）：**
- **R1–R6 铁律**：立绘像素零改动 / 全暖色板 / 禁AI味深色 / 禁冷渲染 / 真音源卡点 / palette gate
- **灵魂三件套**（比边框胶片感更本质）：描边光 rim-light + 投影 drop-shadow + 卡点呼吸 beat-breathing
- **五层包装系统**：背景场景 / 立绘三件套 / 边框版式 / 胶片质感 / 字幕排版——**每层给 地板/进阶/提升3级 三档**做法+参数+代码接口
- **6 套风格预设库**（全暖板内）：A 电影遮幅极简 · B 古画卷轴水墨 · C 朱砂工笔浓彩 · D 现代国乙杂志 · E 暖金梦幻琉璃 · F 水墨留白禅意（天然可当周形式 A/B 的 6 种视觉语汇）
- **卡点动效字典**：beat/downbeat/切镜/drop/间奏/人声onset → 动效映射
- **代码落地**：映射到 `pipeline/voice_room/gen_paperdoll_pv.py` 现状/待实现 + `StylePack` dataclass schema（6套=一份代码+一组preset）
- **复用 checklist**：素材→音源→选风格→三件套先行→分镜→五层→卡点→字幕→验收→外发
- **§9 七阶段前置对话流程**（2026-07-27 加）：**需求对话（−1）→ 物料预处理（0）→ 创意矩阵多选（①）→ 分镜（②）→ 小样两拍（③ 静帧拼图 + draft 动态粗剪）→ 后台自主成片（④）→ 终审（⑤）**。套路 = 前置对话填满**需求契约** `brief.json` → 用户拍板 → agent 无干预跑完。多视频默认「同素材多风格 A/B」。多角色须补「立绘↔歌词段映射」。设计模式见 [[intake-contract-autonomous]]。

**Why:** 2026-07-23 用户要求"多套风格都要、自提升3级、落地文档以后国风乙MV/角色PV参照使用"，据此建此规范。
**How to apply:** 收到国风乙/古风立绘卡点MV/角色PV 需求 → 读此 skill 选风格 + 按五层提升3级档做 + 三件套先行。参考实现见 [[project_voice-room-paperdoll-pv]]。关联 [[feedback_gate-floor-not-target]] [[feedback_skill-vs-template-distinction]] [[feedback_no-neon-palette]]。
