# 待发布成品

> Phase 1 起使用。每条一个目录，从 pipeline/ 复制验收通过的成品。

## 规范

```
publish/{content_id}/
├── douyin.mp4
├── xhs_video.mp4
├── channels.mp4      # 可选
├── carousel/
├── publish.md        # 三平台文案
└── status.yaml       # draft | ready | published
```

## 状态流

```
pipeline 验收通过 → 复制到 publish/ → status=ready → 人工发布 → status=published → 填 metrics.csv
```
