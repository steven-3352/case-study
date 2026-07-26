---
name: feedback_no-synth-bgm
description: "禁止用 ffmpeg aevalsrc/sine 谐波/棕噪合成假装是 BGM —— 用户判定为\"噪音不是 BGM\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9454e7a7-84bb-426d-88ad-0485259de3b7
---

不要用 `aevalsrc=sin(...)` / 多频率谐波叠加 / brown noise 拼"BGM"。用户 2026-06-27 W27D05 直接判:**"什么叫 BGM？现在这个是噪音"**。

**Why:** 工程合成的 sine + noise 本质是工程信号不是音乐,没有旋律/节奏/和声进行,在视频里只听到嗡嗡底噪,反而显得低质。我连续合成 `_bgm_drone.mp3` / `_bgm_warmpad.mp3` / `_bgm_lofi.mp3` 三轮,每轮都更"丰富"但仍被否定 —— 因为不是音乐源的问题,是路线错。

**How to apply:**
- 视频要 BGM,只走两条路:① 用户提供 mp3/m4a 文件 ② 用 剪映(macOS 工具栈自带,见 CLAUDE.md)加抖音生态官方 BGM 库,合规零风险
- 项目里 D04 的 `audio_plan.yaml` 写了 `我曾经的丫头.mp3` 但**文件根本不存在**,D04 published 视频也是 channels=1 的裸 VO —— 这条作为历史伪门禁记下来,不是可复用模式
- 网络下载 Pixabay/archive.org/freepd 在当前环境被防火墙挡(403/timeout),不要再尝试
- 如果 publish 前确实没拿到真 BGM:**就发裸 VO + 字幕**(明确登记"BGM 待补"),不要发合成噪音冒充 BGM
- 关联 [[feedback_read-env-example-first]]:在确认没有可用资源前,先看项目 .env / 工具栈 / 姊妹文件,再决定路线
