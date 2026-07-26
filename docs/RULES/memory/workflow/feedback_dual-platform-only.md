---
name: feedback_dual-platform-only
description: "2026-07-05 起：只做抖音 + 小红书双平台；视频号停做；xhs 视频 or 图文轮播由形式策略官定"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# 双平台规则（2026-07-05 起 · 用户拍板）

## 规则

- **只做**：抖音（Douyin）+ 小红书（Xiaohongshu）
- **停做**：视频号（Weixin Channels）· 不再产出 weixin/ 目录

## Why

用户 2026-07-05 反馈："以后只做抖音、小红书双平台"。原因：
- 视频号增长曲线 & 私域承接效率低于双平台
- 三平台差异化字幕 + 三份发布包外发是纯冗余功
- 精力集中到 2 平台反而能把两条外发做得更精

## How to apply

### 1. pipeline 层

- `pipeline/p004_video/lib/platforms.py` DEFAULT_PLATFORMS 已删 weixin（2026-07-05）
- 新 `pipeline_config.yaml` platforms 段只写 douyin + xhs 两个 key
- 存量条目（W28D01-D03）里的 weixin/ 目录保留不删（历史记录）
- 新条目（W28D04+）**禁**再建 weixin/ 目录

### 2. 小红书形态判定（由形式策略官定 · 每条必判）

xhs 走**视频**还是**7 页图文轮播**，写在 `design/form_strategy.md` "xhs 形态判定" 段：

| xhs 形态 | 数据杠杆首选 | 何时选 |
|---------|-------------|-------|
| 视频（同抖音复用剪辑）| 完播率 · 停留时长 · 播放量 | 强演示 · 强故事弧 · 强情绪冲突 · 主角/工种可见 |
| 7 页图文轮播（P002/P005/P006）| 收藏率 · 划完率 · 保存率 | 强知识 · 强对比表 · 强 SOP · 内容适合"抄下来"而非"看下来" |

**判据**：
- 内容能"截屏收藏"或"按步骤照做" → 图文（收藏率高、评论低但保存高）
- 内容需要"看情绪/看变化/听 VO 理解" → 视频（完播率高、评论互动高）
- 混合型 → 优先视频；图文在 D+2 复盘后 A/B 补一版

### 3. 发布包结构

```
publish/2026-WXX/DXX-XXX/
├── douyin/
│   ├── video_no_bgm.mp4        # ← pipeline 直出
│   └── publish.md              # ← 抖音标题 + 话题 + 首评
├── xhs/                        # 视频版
│   ├── video_no_bgm.mp4
│   └── publish.md
└── xhs/                        # 或 图文版
    ├── 01-07.png               # 7 页轮播
    └── publish.md
```

**禁**：`weixin/` 目录 · `weixin_publish.md` · 三平台 mp4 拷贝

### 4. 存量条目

- W28D01-D03 已发或已跑的 weixin/ 保留 · 不动
- 复盘/迭代时若涉及 W28D01-D03 · 只改 douyin + xhs · weixin 不动

## 违反后果

- 生产层：pipeline_config.yaml 里出现 weixin key → 形式策略官 fail-closed 打回
- 内容层：xhs 直接复用 douyin mp4（未判形态）→ 形式策略官 fail-closed
- 发布层：weixin/ 目录出现在新条目里 → BUILD_NOTES.md 记违规

## 相关 memory

- [[feedback_pipeline-full-platform-output]] · pipeline 三平台差异化字幕（已过时 · 现改双）
- [[feedback_delta-docs-only]] · form_strategy 里 xhs 形态判定只写 delta，不复述形态选型理论
- [[feedback_audience-first]] · xhs 形态选择服务受众成果（收藏 vs 完播），不服务 pipeline 便利
