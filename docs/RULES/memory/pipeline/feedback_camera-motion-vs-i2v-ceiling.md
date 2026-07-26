---
name: camera-motion-vs-i2v-ceiling
description: "纯 FFmpeg zoompan(相机运动)和 i2v AI 生成(画面内容运动)是两种不同技术天花板；调参数解决不了\"画面内容不动\"的问题"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1b8bd492-69a9-47ed-95a9-32ed78edf3ed
---

D07《明月天涯》方案 C 第二轮反馈("人物背景都不动,样品背景还有动效")揭示：即使 [[zoompan-visible-motion]] 里描述的"zoom_max 太保守"问题已修复(居中+加大变焦+横向 pan)，用户仍反馈"没有任何动画"。根因不是参数还不够大，而是**纯 FFmpeg 相机运镜(zoompan/pan)只能移动"取景窗口"，不能让画面内容本身动**——静态插画的头发、衣袍、雨丝、云雾、灯笼这些像素永远不变，只是被裁切窗口挪来挪去；这在观众感知上和真正的"画面在动"(内容形变/位移)是两回事，前者做到极限也会被识别为"包装过的静态图"。

**Why:** D06《一弦入江湖》同类武侠 MV 之所以有真实动效，是因为全部 34 镜过了 `grok-imagine-video` i2v(image-to-video)生成，让 AI 重新生成"内容真的在动"的视频，而不是相机绕着静态图缩放平移。这是两种完全不同、不可互相替代的技术方案，价格/耗时也不同（i2v 每段约 60-90s API 生成 + 下载，且有约 50% 概率出现幻觉伪影需要二次生成，见下）。

**How to apply:**
- 客户/用户反馈"背景/画面不会动"且已确认 zoompan 参数(zoom_max/pan)已经调到位仍无效 → 不要继续调参数，直接判断是"相机运动天花板"问题，需要升级到 i2v 技术路线。
- 升级前用 AskUserQuestion 让用户拍板范围(全量 i2v / 部分 i2v / 维持纯运镜)，因为 i2v 有真实的时间和 API 成本，不能替用户决定加量。
- i2v 生成后必须逐个抽帧目视 QA(首/中/尾三帧)：grok-imagine-video 对"雾/云"类描述容易幻觉出卡通化的扇贝形云朵、对"水波纹"类描述容易幻觉出圆形气泡状光斑——这些是需要重新生成的伪影，不是能接受的"风格"。QA 通过标准：连贯性(内容轮廓不能变形)、无新增几何形状、无人物剪影/文字/水印混入。
- prompt 写法教训：与其描述"活跃/翻涌/漂移"这类强动作词，不如写"very slight/subtle/minimal parallax shift only, do not invent new shapes, preserve exact original composition"——弱化幅度描述反而降低了模型乱加内容的概率，见 `pipeline/client_projects/d07_moon/gen_bg_motion.py` 的 v2 prompt（MOTION_QA 常量与逐场景 motion_prompt）。
- i2v 视频结果只能通过本地代理(如 127.0.0.1:7890 Clash/V2Ray)下载(host 是 `vidgen.x.ai`)，直连超时是预期行为不是 bug；下载函数应"先直连、失败再退化走代理"而不是假设代理一定在跑。
- 集成回 FFmpeg 时间轴：i2v 生成的视频已经有真实动效，不要再叠加 zoompan/pan("画蛇添足")，只需 scale+fps 归一化到画布规格即可。

参考实现：`pipeline/client_projects/d07_moon/gen_bg_motion.py`（i2v 生成脚本）+ `assemble.py` 的 `build_bg_motion_clip()`（消费 i2v mp4，不再叠加相机运动）。
