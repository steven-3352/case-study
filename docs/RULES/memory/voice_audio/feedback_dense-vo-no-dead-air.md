---
name: feedback_dense-vo-no-dead-air
description: "参考视频（WaytoAGI/七七/浙大猫学长）的密 VO 无 BGM 结构 — 全片零死区，禁\"沉默钉子\"设计"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

W28D02 v1 犯了"沉默钉子"错误——storyboard M1 设计 0-3s"只有环境音+VO 停顿"，M2 设计 3-6s kick+大字，全靠视觉挑起前 6s；结果 preview_no_bgm.mp4 前 6s 是**-193 dB 纯数字静音**（用 `anullsrc` 填的），观众直接以为视频坏了。

**规则：** 视频前 6s 禁"仅环境音/仅 sting/仅大字"设计；VO 必须从 0s 开始覆盖到 8s 后的第一个自然停顿。

**Why：** 参考 `/Users/wmzuo/Downloads` 三支密 VO 无 BGM 视频：
- WaytoAGI 《如何用 Claude 以 10 倍速度学》(234s, 576×1024)
- 七七《设计学专业就业》(227s, 1022×576)
- 浙大猫学长《vibe+git=无限动画》(181s, 540×720)

前 10s 实测 RMS -13 到 -23 dB，全片无 3s+ 的死区。观众预期"打开视频就有声音"，前 6s 静默 = 划走。

**How to apply：**
- 编剧写脚本时，`s1/s2` 必须有 VO 文本，禁"（沉默）（环境音）"占位
- 若 storyboard 出现"env: 环境音"设计，声音设计师必须**在同一时段配 VO**，不能只有环境音
- gen_vo_*.py 严禁 `anullsrc` 生成静音段；若某段无 VO，直接不生成，不是填 anullsrc
- 参考视频响度基准：VO RMS 目标 **-16 到 -20 dB**（用 `loudnorm=I=-16:TP=-1.5:LRA=11`），发布前 `ffmpeg astats` 验前 6s 不得 <-25 dB
- 大字/kick sting/环境音都是**叠在 VO 上的第二层**，不是替代 VO

**Exception：** 出镜型（真人开场留白 1-2s 看镜头）可有 ≤2s 静默；演示/知识/带货型无此例外。

**Related:** [[feedback_contrast-hook-3s]] · [[feedback_pre-node-checklist]]
