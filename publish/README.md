# 待发布成品

> 引擎最终输出层：每条选题经多 Agent 编排 + `pipeline/` 生产后，验收通过的成品落在此目录，可直接发布。

## 规范

```
publish/{content_id}/
├── insights/                    # 洞察包四件套（必跑）
│   ├── topic_brief.md
│   ├── core_message.md
│   ├── domain_notes.md
│   └── fact_check.md
├── retention_beat_sheet.md      # 视频/强互动图文（必跑）
├── audio_plan.yaml              # 视频必跑
├── douyin.mp4                   # 含 BGM + 字幕（外发版）
├── xhs_video.mp4
├── channels.mp4                 # 可选
├── carousel/
├── publish_三平台.md
├── CHECKLIST_verdict.md         # 验收记录
└── status.yaml                  # draft | ready | published
```

模板来源：`templates/insights/`、`templates/retention_beat_sheet.md`、`templates/audio_plan.yaml`

标杆示例：`publish/P004/`（K1 洞察包 + 节拍表 + 音画方案）

## 状态流

```
洞察包 + 节拍表 + 音画方案
  → pipeline 出片
  → CHECKLIST 验收
  → 复制到 publish/ → status=ready
  → 人工发布 → status=published → 填 metrics.csv
```

## 外发文件约定

| 文件 | 用途 |
|------|------|
| `*_with_bgm.mp4` | **默认外发**（配音 + BGM + 字幕） |
| `p004_K1.mp4` 等裸片 | 工程中间件，不直接发布 |
