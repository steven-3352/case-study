# D02 · pipeline 三平台直出说明（v4 · 无剪映）

> **2026-07-04 变更**：本条起，剪映交接单**作废**。三平台 mp4 由 pipeline 一次跑完直接落盘，人工零手操。
> 依据：CLAUDE.md 铁律「pipeline 直出」· memory `feedback_pipeline-full-platform-output`

## 交付路径（直接外发）

| 平台 | 路径 | 时长 | 尺寸 | 编码 | 字幕字号 |
|---|---|---|---|---|---|
| **抖音** | `douyin/video.mp4` | 68.50s | 1080×1920 | H.264 + AAC | 42pt |
| **小红书** | `xhs/video.mp4` | 68.50s | 1080×1920 | H.264 + AAC | **50pt**（滑动阅读放大） |
| **视频号** | `weixin/video.mp4` | 68.50s | 1080×1920 | H.264 + AAC | 42pt |

**⚠️ 已知风险**：小红书视频 >60s 会掉推荐流优先级（1-6-60 曝光机制里 60s 是分档线）。本条 VO 精确 68.5s，不改语速；若投后 xhs 完播/曝光显著低，下条起要么压到 60s 以内，要么接受这个平台风险。

## 生产链路（人工只运行一条命令）

```
seg_timing_w28d02.json         ← 从 gen_vo_w28d02.py 精确 VO 时序
        ↓
gen_vo_w28d02.py              ← MiniMax TTS 8 段合成 · loudnorm -16 dB
        ↓
build_w28d02_preview.py       ← Chrome 渲 UI + PNG → 无字幕底片 preview_no_bgm_v2.mp4
        ↓
build_platforms_w28d02.py     ← 【本步】烧字幕 + M3 大字 + 三平台差异化导出
        ↓
{douyin,xhs,weixin}/video.mp4  ← 外发件
```

**一键命令**：

```bash
cd pipeline/p004_video && python3 build_platforms_w28d02.py
```

## Pipeline 烧进 mp4 的元素（不用剪映做的清单）

| 元素 | 来源 | 位置 | 时序 |
|---|---|---|---|
| **VO 主字幕** | `seg_timing_w28d02.json` → ASS + libass | 底部 · MarginV 200/220 | 15 cues · 0-68.5s 全覆盖 |
| **M3 三连快切「没得写→写不出→占私人时间」** | ffmpeg drawtext + drawbox | 屏幕中心 · 96pt 白字黑描边 5px | 6.80-7.40 / 7.45-8.05 / 8.10-8.70s |
| **M3 间隔 白闪** | ffmpeg drawbox 满屏 white@1.0 | 全屏 | 7.40-7.45 / 8.05-8.10s（0.05s / 帧半） |
| **M2「18:55·周五」时间锚** | `01_iphone_lockscreen_1855.png`（UI 图内已含） | UI 图内 | 3.69-6.80s |
| **M8 CTA「评论你的岗位」便签** | `12_cta_note.png`（UI 图内已含） | UI 图内 | 64.26-68.50s |
| **VO 音频（loudnorm -16 dB）** | MiniMax speech-2.8-turbo | 全片 | 0-68.5s |

## 三平台文案（还需要人工写）

**pipeline 不做**：三平台标题、话题、正文描述、评论区埋点、私信路径。这三份文案由运营/增长工种在 `templates/publish_三平台.md` 里单独写，然后：

- 抖音：`douyin/publish.md`
- 小红书：`xhs/publish.md`（含 8 张轮播独立 → 待做）
- 视频号：`weixin/publish.md`

**封面 mock** 也由视觉设计单独出（抖音 1 张 + 小红书首页 1 张），不走 pipeline。

## 外发前 checklist（最后目视一遍）

- [x] 三份 mp4 已 pipeline 直出并入库 douyin/xhs/weixin
- [x] VO 主字幕：15 cues 精确对齐 · 底部不遮画面主体
- [x] M3 三段大字「没得写/写不出/占私人时间」+ 两次白闪已烧进
- [x] BGM 环节按新规则跳过（密 VO 演示型 · `feedback_dense-vo-no-bgm-default`）
- [ ] QuickTime 播放三份 mp4：字幕清晰、无叠层、VO 全程覆盖、M3 三段字刺激但不遮画面
- [ ] 抖音文案 · 小红书文案 · 视频号文案（三平台独立，禁跨平台复用）
- [ ] 抖音封面 · 小红书首页封面（独立 mock）
- [ ] 小红书 8 张轮播（`storyboard.yaml → xhs_carousel`）—— 独立于 mp4

## 内容禁事项（外发前最后一眼）

- ❌ **禁跨平台 mp4 复用**（W26 教训 · 已通过 pipeline 三平台差异化字号规避）
- ❌ **禁虚假效果承诺**：「月薪翻倍」「老板必然夸」「效率提升 80%」
- ❌ **禁站队骂老板**：共情 OK，不做「老板都是傻 X」
- ❌ **禁教你摸鱼**：定位"用 AI 干实事"，不是划水内容
- ❌ **禁点名真实公司/客户**：无 阿里/京东 logo，无真客户数据
- ❌ **禁 Dracula 霓虹色**：#bd93f9 / #ff79c6 / #8be9fd 一律不用
- ❌ **禁合成 BGM**：本条无 BGM，不适用

## 完工后回填

发布后 48h + 7d，回来把三平台的 播放/完播/点赞/收藏/评论 数据填到：
`design/post_publish_retro.md`

数据复盘官会自动生成 `evolution_overlay.md`，喂给 D03。

## 剪映 什么时候还会用到

只有以下情况才需要 open 剪映：
1. 出镜型真人自录（无 seg_timing 精确时序）→ 剪映智能字幕 + 校对，然后回填 seg_timing 供 pipeline 复用
2. 用户在剪映里想调整字幕样式/CTA 位置 → 导入副产物 `vo_w28d02.srt` 或 `vo_w28d02.ass`，改后重新导出
3. pipeline drawtext 表现力不够（未来若加入更复杂动效字）→ 从剪映导出 mp4，或让 pipeline 支持更多 filter

**当前 D02 都不属于以上任一情况，剪映不用开。**
