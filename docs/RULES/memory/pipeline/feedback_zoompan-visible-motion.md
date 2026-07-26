---
name: zoompan-visible-motion
description: FFmpeg zoompan 做 Ken Burns 时 zoom_max 定太保守(1.02~1.05)+ 无横向漂移 → 看起来像静态 PPT，不是真的没做动画
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1b8bd492-69a9-47ed-95a9-32ed78edf3ed
---

FFmpeg `zoompan` 滤镜做静态图 Ken Burns 缓推时，`zoom_max` 若只设 1.02~1.05（尤其配合 3-7s 短镜头），单帧增量极小，加上默认 `x=0,y=0` 不居中会偏向左上角漂移，人眼完全看不出变化，成片观感等同 PPT 轮播。

**Why:** D07《明月天涯》方案 C 首版用 zoom_max=1.02~1.05（多人全景镜头刻意收得更保守，避免裁太狠），用户看完直接反馈"没有任何动画，像PPT"。排查发现根因不是滤镜没生效，而是变焦幅度/横向位移量级本身就低于可感知阈值。

**How to apply:** 
- Ken Burns 静图缓推场景，zoom_max 至少给 1.10+（普通单/双人近景可到 1.18），全景/多人镜头最低也要 1.08，不要为了"避免裁太狠"压到 1.02~1.05 这种量级。
- 必须显式居中：`x='(iw-iw/zoom)/2'`、`y='(ih-ih/zoom)/2'`，不要用默认 x=0,y=0（会导致向左上角漂移而非居中放大）。
- 建议叠加横向 pan（`x` 表达式再加 `pan_dir*pan_px*(on/total_frames)` 项），让镜头不是纯粹"呆板放大"而有轻微运镜感；pan_px 按 `slack_px * 0.35` 估算（slack_px = 3840*(1-1/zoom_max)），避免越界。
- 渲染完成后必须实际对比同一镜头首尾两帧（而非只看单帧调色板/黑帧门），才能验证"运动是否肉眼可感知"——纯技术门（gate_check_media/palette）测不出"像 PPT"这类观感问题。

参考实现：`pipeline/client_projects/d07_moon/assemble.py` 的 `_scale_crop_zoompan()`。
