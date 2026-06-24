# 生产流水线

> Phase 0 全人工 · Phase 1 半自动 · 按顺序执行，不跳步
>
> 本目录是引擎的**渲染与组装层**（SYSTEM §2 Layer 3）。上游见 `docs/SYSTEM.md` · 工种细则见 `CLAUDE.md`。

**用语：** `pipeline/*/templates/*.html` 是**渲染场景**（截帧画布），不是可套用的标准内容模板。每条选题单独分镜；可新建场景或重写，禁止克隆上一条。见 [templates/README.md](../templates/README.md)。

## 通用产线（新）：输入任意项目 → 三平台短视频

一条命令，从 GitHub 仓库（demo 可选）自动产出抖音/小红书/视频号的
30–60s 竖屏配音字幕 mp4 + 标题/正文/标签/封面：

```bash
.venv/bin/pip install -r pipeline/requirements.txt      # 首次
# 有 demo（界面项目）：截真实页面
python3 pipeline/produce.py --id P002 \
    --github https://github.com/owner/repo \
    --demo   https://demo.example.com \
    --note   "一句话定位（可选）"
# 无 demo / 非界面项目：author 自己整理 evidence 素材（终端/代码/对话/数据/笔记）
python3 pipeline/produce.py --id P003 --github https://github.com/owner/lib
```

author 先把项目想透再写：痛点（谁的什么痛点）、解决了什么、前3秒钩子、各平台互动钩子，
都落进 `content.yaml` 的 `topic` / `interaction` 字段。

阶段（各步独立可跑，产物存在则跳过，`--force` 全量重跑）：

| 步骤 | 脚本 | 产出 |
|------|------|------|
| ① 抓原料 | `ingest.py` | `projects/{id}/context.md` |
| ② 写脚本文案 | `author.py`（调 Claude API） | `research.md` `plan.md` `content.yaml` |
| ③ 真实截图 | `shoot.py`（有 demo 才截；无则全回落） | `projects/{id}/shots/*.png` |
| ④ 渲染 | `render.py`（Ken Burns + xfade + 字幕叠层 + 封面） | `publish/{id}/{平台}/video.mp4` `cover.png` |
| ⑤ 发布文案 | `write_publish.py` | `publish/{id}/{平台}/publish.md` |

约束与现有一致：9:16、demo_only 不出镜、去 AI 味（自然 TTS + persona 口语 + 真实截图优先）。
配音 provider 可插拔，见 `pipeline/tts/config.yaml`（edge 保底 / volcengine / minimax）。  
**API 凭证**：仓库根目录 `.env`（模板见 `.env.example`），`pipeline/env_loader.py` 在脚本启动时自动加载。
凭证走 `ANTHROPIC_API_KEY` 或 `ant auth login`。渲染内核统一在 `render_core.py`。

素材来源：
- 有 demo → `source=shot` 截真实页面，缺失时回落卡片。
- 无 demo / 非界面 → `source=evidence`，author 给出 `evidence_kind`（terminal/code/chat/metric/note）
  + `detail`，render 画成像真实截图的体裁卡（macOS 窗口外壳），不是甩一行字。

---

## P001 单案例流水线（既有）


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
