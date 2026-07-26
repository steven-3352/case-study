---
name: feedback_dense-vo-no-bgm-default
description: 密 VO 演示/知识型默认无 BGM — BGM 从硬门下调为形态条件件，密 VO 已把氛围撑满，硬加只会盖 VO
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

**规则：** 密 VO 演示/知识型视频**默认不加 BGM**；BGM 从"音画硬门"下调为"形态条件件"。

**判定标准（`audio_plan.yaml` bgm.enabled=auto 时）：**
- **默认 off**：VO 覆盖率 ≥85% + 无 3s+ 死区 + 形态 ∈ {演示型, 知识型}
- **默认 on**：稀疏 VO（覆盖率 <85% 或有 3s+ 环境音段）/ 出镜型 / 情感叙事型 / 带货型

**Why：** 用户在 W28D02 v2 交付后拍板（2026-07-04）：
- 参考 `/Users/wmzuo/Downloads` 三支密 VO 无 BGM 视频（WaytoAGI《Claude 10 倍学》、七七《设计学专业就业》、浙大猫学长《vibe+git=无限动画》）全片无 BGM，观感一样好——因为 **VO 密度已经把整体氛围撑满**，硬加 BGM 只会盖 VO 或喧宾夺主。
- 剪映音乐库里合适的密 VO 铺底 BGM 极难找（W28D02 试过 lo-fi/极简钢琴/ambient piano 都盖 VO），花时间选曲 ROI 低。
- 用户原话：「以后就不用 BGM 这个环节，参照刚刚的 3 个示例视频，没有 BGM 整体效果也不错」。

**How to apply：**
- 声音设计师产出 `audio_plan.yaml` 时，**默认写 `bgm.enabled: off`**（若判定为密 VO 演示/知识型），并在 notes 写「密 VO 已撑满，无 BGM」
- 强制 on 需说明依据（如：本条是情感叙事、需要情绪推动）
- 剪映交接单不再写「BGM 曲风推荐关键词」段（若 enabled=off），直接标「无 BGM，字幕 + 三平台导出即可」
- `pipeline/p004_video/build_*.py` 输出 `*_no_bgm.mp4` 直接落 `douyin/video.mp4` / `xhs/video.mp4` / `weixin/video.mp4`——**不再是"预览件"**
- SYSTEM §3.3 表述已改：硬门 = VO + 字幕，BGM 是条件件

**Exception：**
- 出镜型 / 带货型 / 情感叙事型 / 稀疏 VO（长 pause + 环境音） → 仍需 BGM（否则死气沉沉）
- 投后数据显示"无 BGM"版完播/收藏显著低于同形态"有 BGM"参考 → 单条回退加 BGM，并升级到形式策略会重议

**Related:** [[feedback_dense-vo-no-dead-air]] · [[feedback_no-synth-bgm]] · [[feedback_ai-voice-known-gap]]
