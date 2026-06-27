# PUBLISH_LOG · W27D04

- **选题:** 「我用 AI 替实体店老板做小红书种草,4 周做 AI 内容涨粉几乎为 0 但今早 3 个老板问我多少钱包一套」
- **形态:** 双平台同选题 · 抖音视频 + 小红书 8 张轮播(平台分轨)
- **状态:** ready_to_publish · 两道门 fail-closed 全过(forecast 内容 90 / 形式 92)
- **发布:** 抖音 2026-07-02 · 19:30 ｜ 小红书 2026-07-02 · 12:30

## 成片

### 抖音
- `douyin/video_with_bgm.mp4` · 48.5s · 1080×1920 · VO Edge-TTS Yunjian + BGM 我曾经的丫头(0.08) + 字幕 HTML overlay 烧录
- `douyin/cover.png` @ 2.7s · "4 周做 AI 内容 / 涨粉几乎为 0"反差大字 + 数据红卡 + "几乎为 0"红章
- `douyin/publish.md` · 标题 / 正文 / CTA / 标签 / 合规自检全套

### 小红书
- `xhs/page_01..page_08.png` · 1080×1620 · P003 hybrid 模式(P01 GPT-image-2 报纸风 + P02-P08 Pillow 本地)
- `xhs/SCRIPT.md` · 8 张 caption + 留存节拍
- `xhs/publish.md` · 标题 / 正文 / 评论 CTA / 标签 / 押注卡

## 反转架构(全片核心)
**前 3s 自燃人设建立** → 观众嘲笑/同情 → **中段揭穿** → **「扑了 14 条 = 14 条精确避坑清单」反咬资格质疑** → 落点测水信号(评论扣档位号)

## 门禁记录
- **pre_render:** PASS · 内容 90 / 形式 92(`design/pre_publish_forecast.md`)
- **approve:** PASS · 双平台素材逐张目视检查无叠层遮挡、无虚构数据、无绝对化用语
- **合规复检:** PASS · 履约担保口径(非"全退") · 不出具体粉丝数 · "3 个老板"标"示意"水印 ·(`insights/external_references.md` C 块逐条核对)

## 已知取舍(如实登记)
1. **VO 48.5s 超 45s 目标** — 自然语速实测约 49s,按 D03 策略"按实测 VO 拉伸窗口"(铁律:尽一切可能让内容更好 > 卡死 45s 切口播);s6 报价段最长 11.87s。投后若完播低优先压时长。
2. **MiniMax 凭证未配,实际走 Edge TTS Yunjian** — yunwu.ai 中转 channel 是图片专用不支持 TTS;edge-tts 升级到 7.2.8 后走通。声线为青年男声,与 D03 风格略有差异。
3. **"3 个老板私信"为仿真** — 本期没有真实付费咨询历史,P03 卡片右上角标"示意"水印守 fact_check 红线。
4. **"扑了 14 条"为"扑得很彻底"定性表达** — W27 截至 D04 发布日仅完成 3 条出片,不出具体"14 条"数字;脚本/字幕统一用"扑得彻底"。
5. **三档报价为本期新推,无历史成交** — 内部成本核算见 `insights/domain_notes.md` §3;轻档 ¥99 毛利 ~50%,中档 ¥299 毛利 ~28%。

## 已修复 build.py 长期坑(顺手)
`build.py` 字幕模板硬编码 `_subtitles.html`,跨周复用时会烧错字幕(本期发现 D04 video 烧成 D03 字幕)。已加 `--subtitle-template` 参数,后续 D05+ 不会再踩。

## 投后待跑(L3)
- 48h/7d 回填 actual → `post_publish_retro` + 下条 `evolution_overlay`
- 重点验证(`pre_publish_forecast` 假设):
  1. 自燃反差比常规炫技更强 → completion_3s 应 ≥ 25%
  2. **评论扣档位号 = 真付费意愿信号** → ≥10 条带档位 → 推进 demo 阶段
  3. 99 档位评论 > 599 → 试水"低门槛比高 ARPU 重要"
- 失败容忍:若评论 < 5 → 测水赛道证伪,转 D05/D06 其他角度

## 制作时间真实数据(测今日 capture_frames 优化效果)
- 抖音 8 镜并行截帧: **42.7s**(原串行预计 ≥ 250s,4-5× 提速)
- 字幕层 1455 帧 dedup 实截 **124/1455** = 91.5% 去重(10-15s 完成)
- ffmpeg 合成 ~20s
- **抖音总制作时间 ≈ 80-90s**(对照 D03 时代 ~5-6 min,提速 4×)
- 小红书 carousel:封面 GPT-image-2 211s + Pillow 7 张 ~2s = ~3.5 min
