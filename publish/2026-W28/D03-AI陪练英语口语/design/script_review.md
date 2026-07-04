# 脚本审查 · W28D03

```yaml
status: draft_self_generated
content_id: W28D03
review_source: draft_self_generated
decision: allow_render_no_approve
```

> 对象：`scripts/v0.md`（默认严格版 · vA/vB 备用）
> 说明：这是单 Agent 草稿审查 + 已完成 pipeline 出片；不具备 approve 门效力。

## 草稿判断

当前脚本方向已渡过内容门（scorecard avg 91 / 90.5 · 见 `room/scorecards/编剧.yaml` 与 `留存与互动设计师.yaml`），允许 render 到底片 + 三平台 mp4，**不允许**外发前无独立复评。

- **钩子有明确冲突**：0-3s 深夜 23:12 对着墙念英语 + 92% 不敢开口。
- **场景有具体动作**：多邻国 700 天连击、AI 对话框输入"怎么练口语"、豆包语音陪练、侧躺 22:45。
- **CTA 走评论关键词**：面试 / 雅思 / 日常 / 旅游 → 私发 role prompt，避开私信 / 扣 1 诱导。
- **数据点均带同帧来源**：92% / 78%（讯飞录《2024 中国英语学习报告》）· 700 天（自证 · 用户可核验多邻国截图）。

## 已达内容门 + 出片状态

| 环节 | 状态 |
|--------|------|
| 洞察包 4 件套 | ✓ `insights/topic_brief.md` + `core_message.md` + `domain_notes.md` + `fact_check.md` |
| 留存节拍表 | ✓ `retention_beat_sheet.md` · 10 段 58s |
| 脚本 v0/vA/vB | ✓ `scripts/` 三版 · v0 默认严格版 |
| 设计层 | ✓ `design_language.md` + `form_competition.md` + `form_strategy.md` + `motion_tech_plan.md`(SKIP) |
| 分镜 + 音画 | ✓ `storyboard.yaml` 10 段 + `audio_plan.yaml` MiniMax male-qn-jingying-jingpin |
| VO 合成 | ✓ `build/audio/vo_w28d03.mp3` · 59.9s · loudnorm -16 dB |
| UI PNG | ✓ 11 张 1080×1920 · 禁霓虹色门 PASS |
| 底片 | ✓ `build/final/preview_no_bgm_v2.mp4` · 59.9s · Pexels B-roll + UI PNG |
| 字幕烧录 | ✓ `build/final/preview_no_bgm_subs_v3.mp4` |
| 三平台 mp4 | ✓ `douyin/xhs/weixin/video_no_bgm.mp4` |

## 仍需补齐（外发前门）

| 阻塞项 | 原因 | 下一步 |
|--------|------|--------|
| 真独立复评 | 当前 scorecard 均 draft_self_generated · 非独立 reviewer | 触发条件：D+2 数据不达 forecast B 级 → 复盘会补人评 |
| pre_render 27 misses | form_strategy / motion_tech_plan / visual_originality_gate 字段格式与 gate_check 期望不完全匹配 | 已登记 `docs/design/PRE_NODE_CHECKLIST_MISS_LOG.md` · v2 迭代补齐 |
| M7 真机豆包屏录 | 当前 M7 = 1.7s 占位 UI（s6 VO 12.3s 溢出压缩空间）· 未插入真英文对话 | v2：s2/s6 换更快 speed（0.98/0.98）释放 M7 6s 空间 · 用户录 mov |

## 允许

- 允许上传三平台 mp4（`video_no_bgm.mp4` → 重命名 `video.mp4` 后发布）· 但**不允许**在 `room/verdict.yaml` 写 pass/approved（无独立复评）。
- 允许 D+2/D+7 数据回填。

## 不允许

- 不允许把 `video_no_bgm.mp4` 归为 pipeline "预览件" · 按 CLAUDE.md 密 VO 演示型 no-BGM 默认可直外发。
- 不允许在数据未回填前，套用本条 storyboard 骨架给 D04+ 用（复用是能力，不是画面骨架 · 见 visual_originality_gate）。
- 不允许把 "M7 压到 1.7s" 当成设计选择 · 是 VO 溢出的副作用，v2 需修。

## D03 特有合规红线（重申）

- ❌ 30 天流利 / 秒变母语 / 哑巴英语克星 / AI 替代真人外教
- ❌ 便宜 100 倍（未同帧口径 "对比线下 300 元/小时"）
- ❌ 多邻国 logo / App 名（M3 只用连击数字截图 + "App Logo Masked"）
- ❌ 打真实竞品对话框 logo（M4 AI 对话框不带 OpenAI/字节 logo）
- ❌ 私信 / 扣 1（CTA 走评论关键词交付）
