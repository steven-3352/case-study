# Legacy · 旧案例素材与参考文案

> **降级使用**：不作三平台首发默认产出。仅作 B-roll 补充、口吻参考或对内提案。

## 脚本（仍在 repo 根目录）

| 脚本 | 用途 | 首发可用？ |
|------|------|-----------|
| `build_shots.py` | 真实页面/ pin 截图帧 | ✅ 作 B-roll |
| `build_slides.py` | 黑金 11 张架构图 | ❌ 仅素材库 |
| `build_video.py` | Edge TTS 视频草稿 | ❌ 仅内部预览 |

```bash
python3 build_shots.py
python3 build_slides.py
python3 build_video.py
```

## 参考文案（勿直接复制发布）

旧版 `article.md` / `article_c.md` / `voiceover.md` 已删除；口吻与发布结构见 `publish/` 与 `templates/publish_三平台.md`。

| 路径 | 说明 |
|------|------|
| `发布/` | Project-001 三形态图文/视频文案（A/B/C） |
| `voice-clone/` | GPT-SoVITS 声音克隆（已放弃，2026-06-16） |

Phase 1 待发布成品放 `publish/`（空目录占位）。

## 迁移计划

Phase 2 可选：将 build_shots 迁入 `pipeline/render_shots.py`，其余继续归档于此。
