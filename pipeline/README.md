# 生产流水线

> Phase 0 全人工 · Phase 1 半自动 · 按顺序执行，不跳步
>
> 本目录是引擎的**渲染与组装层**（BLUEPRINT Layer 3）。上游为 `queue/topics.yaml` 选题 + `CLAUDE.md` 多 Agent 工种编排（采料、脚本、分镜、合规、文案）；下游为 `publish/` 发布包。

## 流程图

```
queue/topics.yaml (approved)
        │
        ▼
⓪ 多 Agent 编排 ── CLAUDE.md 工种清单（编导/记者/编剧/导演/合规/运营…）
        │            产出：调研笔记、脚本三版、分镜、发布文案草稿、合规清单
        ▼
① 脚本 ── templates/script_*.md
        │
        ▼
② 声音 ── pipeline/tts/gen_speech.py → speech.mp3
        │
        ▼
③ ~~数字人~~（暂停）── 跳过
        │
        ▼
④ B-roll 拼接 ── assets/broll/catalog.yaml（全屏演示）
        │
        ▼
⑤ 剪辑 ── 剪映 → 三平台版本
        │
        ▼
⑥ 图文衍生（可选）── carousel/
        │
        ▼
⑦ 发布文案 ── templates/publish_三平台.md
        │
        ▼
⑧ CHECKLIST 验收（含 insights + 节拍表 + audio_plan）
        │
        ▼
⑨ 发布（Phase 1+）→ ops/metrics.csv
```

## 阶段说明

| 步骤 | Phase 0 | Phase 1 | Phase 2+ |
|------|---------|---------|----------|
| ⓪ 多 Agent 编排 | 人工串行扮演各工种 | Agent 并行辅助 | 半自动编排 |
| ① 脚本 | 人工 | AI 草稿+人工改 | gen_script.py |
| ② 声音 | Edge TTS（gen_speech.py） | 同左或 SaaS 原生音 | 同左 |
| ③ 数字人 | **暂停** | — | — |
| ④ B-roll | 从 catalog 选 | 同左 | 自动匹配（可选） |
| ⑤ 剪辑 | 剪映手动 | 剪映模板 | ffmpeg 批量裁切 |
| ⑥ 图文 | 手动拼 | 同左 | 模板脚本 |
| ⑦ 文案 | 人工 | AI 草稿+人工改 | 同左 |
| ⑧ 验收 | CHECKLIST | 同左 | 同左 |
| ⑨ 发布 | **不发布** | 人工 | 人工 |

## 输出目录规范

```
pipeline/{content_id}/
├── script.md
├── speech.mp3              # gen_speech.py 产出
├── avatar_raw.mp4
├── douyin.mp4
├── xhs_video.mp4
├── channels.mp4          # 视频号，可选
├── carousel/             # 01.png ...
├── publish.md
└── feedback.md           # 路人测试反馈
```

## 时长与构图硬约束

- **全屏演示**：录屏 / 数据 / 系统页面 / 真实截图（100% 画面）
- **无人物出镜**：真人、数字人、小窗、画中画均不做
- **口播 + 字幕**：Edge TTS 配音，字幕叠在主画面上
- **视频比例**：**9:16（1080×1920）** 图文+视频统一，见 `screen_dims.CANVAS_W/H`
- 抖音 45–60s，小红书视频 ≤60s，视频号 60–90s
- 前 3s 冲突钩子 = **大字字幕** + 演示画面

详见 `persona/persona.yaml` → `video_layout`、`docs/DECISIONS.md` Q8。

## 相关文档

- 验收清单 → `CHECKLIST.md`
- **经验沉淀 / 数据复盘** → `docs/LESSONS.md`
- 空跑样例 → `dry-run-001/`
