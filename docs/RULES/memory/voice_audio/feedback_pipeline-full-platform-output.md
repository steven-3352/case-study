---
name: feedback_pipeline-full-platform-output
description: pipeline 必须一键出三平台 mp4 直接落盘 douyin/xhs/weixin — 剪映零手操，M2/M8 走 UI 图内嵌 M3 走 drawtext，别再画剪映 handoff 图纸
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

**规则：** pipeline 必须直接产出 `douyin/video.mp4` + `xhs/video.mp4` + `weixin/video.mp4` 三份可直接外发的 mp4，**任何**"交给剪映做 X"的交接单都是 pipeline 不到位。M2/M8 大字覆盖能烧进 UI PNG 就烧进；M3 三连快切用 ffmpeg drawtext + drawbox 白闪；VO 字幕用 libass 平台化字号（抖音 42 / 小红书 50 / 视频号 42）。

**Why：** W28D02 用户两次追打——
- 第一次「字幕不是自动生成吗？为什么还要我操作？」→ 已固化 `feedback_pipeline-burn-subs`
- 第二次「为什么不直接交付抖音，小红书的最终物料！」→ 本条

用户明说 pipeline 自动化的完整边界是「到平台外发件为止」，不是「到预览件 + 交接单为止」。剪映 handoff 存在本身就说明 pipeline 没做够。

**How to apply：**

**（1）三平台差异化 · 一个脚本 build_platforms_<slug>.py 通吃：**
```python
@dataclass(frozen=True)
class PlatformSpec:
    name: str            # douyin / xhs / weixin
    subs_size: int       # 抖音 42 / 小红书 50 / 视频号 42
    margin_v: int        # 底 margin（大字号要拉大）
    max_cue_chars: int   # 单 cue 最大字数（字号大要收紧）
    max_line_chars: int  # 单行折行阈值
```

**（2）大字覆盖分类处理：**
| 类型 | pipeline 端做法 |
|---|---|
| 时间锚 / CTA 便签 / 静态标签 | **烧进 UI PNG**（Chrome 渲 HTML → PNG）· 不用 drawtext |
| 三连快切 / 快闪 chunk 强调 | **ffmpeg drawtext + drawbox 白闪**（0.05s 满屏 white@1.0）|
| 长句 VO 主字幕 | **libass ASS 内嵌样式**（`ass=<file>` filter · 平台化字号） |

**（3）filter 链组装（`-vf` 单串接 ass + drawbox + drawtext）：**
```
ass='<path>',
drawbox=x=0:y=0:w=1080:h=1920:color=white@1.0:t=fill:enable='between(t,7.40,7.45)',
drawtext=fontfile='/System/Library/Fonts/PingFang.ttc':text='没得写':
  fontsize=96:fontcolor=white:borderw=5:bordercolor=black:
  x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,6.80,7.40)'
```

**（4）验收硬性：**
- 白闪帧 JPEG < 15KB（几乎纯白 · 抽帧 mostly-white 校验）
- 目视三平台各抽 4-6 帧：M3 三段 + 白闪 + 长句子 s3/s5 + CTA s8
- 三平台 mp4 大小相近（±10% 内）· 若 xhs 显著大是字号错了

**（5）文案 + 封面仍手工：** 三平台 `publish.md`（标题/话题/正文/评论区）+ 抖音/小红书封面 mock 由运营 + 视觉设计单独出，**不进 pipeline**。这不是「pipeline 到不了」，而是每平台内容策略需要人工判断。

**（6）已知平台风险登记：** 密 VO 演示型 68.5s 超小红书 60s 优先曝光阈；投后若 xhs 曝光/完播显著低于抖音/视频号，下条要么压时长要么接受这个平台风险。**不因平台限制降 VO 质量。**

**Exception：**
- 出镜真人自录（无 seg_timing）→ 剪映智能识别 + 校对回填 seg_timing，走一次剪映
- 高级动效字（未来若需 · SVG 变形/Motion Blur）→ pipeline drawtext 表现力不够时才回剪映或加 Remotion/Manim 路线

**依赖：** `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`（keg-only · 精简 brew ffmpeg 没编 libass/libfreetype/fontconfig 全用不了）· `/System/Library/Fonts/PingFang.ttc`（macOS 自带 · 中文黑体）

**Related:** [[feedback_pipeline-burn-subs]] · [[feedback_dense-vo-no-bgm-default]] · [[feedback_dense-vo-no-dead-air]] · [[feedback_read-env-example-first]]
