---
name: no-cheap-procedural-background
description: "严禁廉价背景——PIL 平滑渐变+高斯模糊多边形堆出来的\"程序化\"背景一眼廉价，背景必须与立绘同插画级"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c1075b53-4425-4e4d-ab2a-ebd66cd0f73e
---

**规则：以后严格禁止廉价背景效果。** 具体指用 PIL 基元（线性/径向渐变、blur 过的多边形山脊、blur 的圆点散景、雾气横带）堆叠出来的"程序化平滑"背景——不管叠多少层、加多少 rim/落影/视差，只要底子是平滑矢量渐变+高斯模糊，就是一眼廉价，判 fail。

**触发案例：** 语音厅《明月天涯》纸片人 PV，`gen_paperdoll_pv.py` 的 `make_bg()`（暖琥珀→暖沙渐变+月光核+blur 沙丘山脊）。用户看第一版扁平 cream 渐变说"很low，廉价、平面"；我加了月光核/背光rim/落影/差速视差/前景散景重渲，用户看了仍判"廉价"，下硬令严禁此类效果。

**Why：** 立绘是插画级（国乙精细立绘），背景是 PIL 平滑渐变+blur 多边形，二者材质等级不匹配 → 背景像"廉价程序化占位图"，把整片拉低。平滑矢量+高斯模糊本身就是"合成/廉价"信号，同 [[feedback_anti-ai-visual]] 的"AI 味"同源。加再多包装层也救不回底子的廉价。

**How to apply：**
- 做任何视频/图文背景，**默认不许用"PIL 渐变+blur 形状"当背景底子**。背景必须达到与前景（立绘/主体）同一材质等级。
- 贵路子（用户 2026-07-25 拍板默认路线）：**背景图直接用 gpt-image-2 生成最终效果**——比现搓 PIL 又省事、又省时、效果好（插画级，与立绘同级）。生成一张背景 plate，立绘+卡点动效叠其上；需景深/调色包装时把 plate 喂 `backgrounds.py::photoreal_location`（读真实 plate 做暗角/调色）。备选：真实摄影散景 plate / 实拍空镜 / 真宣纸绢纹金箔纹理打底。
- gpt-image-2 落地约束：走 tonbirds 中转、按 [[gpt-image-2-api]]（1024×1536 原生→升采样；横屏 PV 需横向尺寸如 1536×1024）；调前必读 `.env.example` + 抄姊妹脚本（[[feedback_read-env-example-first]]）；503 是并发不是模型名（[[feedback_gpt-image-model-fallback]]，`GPT_IMAGE_WORKERS=2`）；prompt 全暖、禁蓝紫（[[feedback_no-neon-palette]]）、禁 AI 味深色画布（[[feedback_no-ai-visual-dark-canvas]]）、温馨禁冷渲染。
- 判据自查：把背景单独抽出来看，像不像"随手用代码画的渐变"？像 → 廉价 → 换 gpt-image-2 生成/真素材。细节密度、材质真实感、而非"层数多"才是贵的来源。
- 与 [[feedback_build-to-reference-not-floor]] 同源：别搓程序化近似去够底线，第一版就照真参考的材质等级建。与 [[feedback_gate-floor-not-target]]：背景"能看"不是目标，"和立绘一个级别"才是。
