# ad-agent 工作流规范（执行契约 · 广告/视频创作）

> **这是什么**：ad-agent 六步生成式流水线的**严格可执行契约**。调度方读本文即可执行，**无需再读 `conductor/` 源码**。
> **人格/话术**见 `AGENTS.md`。本文只管：每步输入什么、输出什么、跑哪条命令、怎么校验。
> **工作目录铁规**：所有命令必须在 `ad-agent/` 下执行（`python -m conductor.cli` 依赖此 cwd）。片名 `<name>` 全程一致。

---

## 职责边界（只做这三件，别越界）

1. **流程控制** — 按 §1 主循环发命令（`init`/`run`/`ok`/`reject`/`shot`），不亲手改文件、不亲手拼 ffmpeg、不替工具算数据。所有实际工作由 `conductor` 脚本完成。
2. **必要结果校验** — 只看 §3 每步「校验」列那几项（命令是否停在 awaiting_approval、关键产物是否非空）。**不通读源码**、不解析产物内部结构去二次判断。
3. **合理建议** — 命中 §3「合理建议」列的信号时，用大白话给用户一句提醒。建议而非擅自行动。

**红线**：❌ 不读 `conductor/` 源码 · ❌ 不改任何底层代码 · ❌ 不绕过 CLI 直接调工具函数 · ❌ 不把命令/错误栈甩给用户（念白用大白话）。

**保真铁规**：产品原图像素一律不重绘。display 展示帧是"原图 paste 到 AI 背景上"，产品区 = 原始字节，100% 保真。这是本工具存在的意义，任何时候不得妥协。

---

## 0 · 控制面（全部命令，没有别的）

| 命令 | 作用 | 何时用 |
|------|------|--------|
| `python -m conductor.cli init <name> <项目根>` | 建骨架 + prompts + state.json 于**物料目录**（项目根必填） | 新片第一步 |
| `python -m conductor.cli status <name>` | 打印六步状态 | 任何时候查进度 |
| `python -m conductor.cli run <name>` | 一路跑到**下一个等拍板处 / 失败处**停 | 主驱动命令 |
| `python -m conductor.cli next <name>` | 只跑**下一个可执行步骤** | 单步调试 |
| `python -m conductor.cli shot <name> <step> <镜号...>` | **逐镜/子集生成**（仅 `03_keyframes`/`04_shots`） | 按需出单张图/单段片，省钱 |
| `python -m conductor.cli ok <name> <step>` | 批准某步（awaiting→done） | 用户说"过" |
| `python -m conductor.cli reject <name> <step> "意见"` | 打回（重跑本步 + 下游级联回 pending） | 用户说"改" |

`<step>` ∈ `00_intake 01_analysis 02_storyboard 03_keyframes 04_shots 05_delivery`

**`shot` 镜号写法**（仅 `03`/`04`，上游须已 `done`）：`SH003` · `3` · `3-6` · `SH003,SH007` · `all` · `missing`。结果增量合并进索引，不动其余镜；不推进状态机，满意后照常 `ok` 才算批准。

---

## 1 · 状态机 + 调度循环

**每步状态**：`pending → running → awaiting_approval → done`（或失败落 `rejected`）。

**主循环**：`init → run → [读产物转述用户 → 用户 ok/reject] → run → … → 05_delivery done`
- 每次 `run` 停在 awaiting_approval，就读该步产物、用大白话转述、等用户拍板。
- 用户认可：`ok <name> <step>` 然后再 `run`。
- 用户要改：`reject <name> <step> "<具体意见>"` 然后再 `run`（下游已批准步骤级联重置为 pending，自动重跑）。

---

## 2 · 前置条件（开工前一次性核验）

```bash
python --version                                   # 需 3.10+
python -c "import yaml, dotenv; from PIL import Image"   # 核心依赖
test -f .env || echo "缺 .env（复制 .env.example 填 API Key）"
which ffmpeg ffprobe                               # 03/04/05 需要
```

**.env 必填项**：

| 变量 | 用于步骤 | 缺失后果 |
|------|---------|---------|
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | 01 / 02 | `llm_config` / `storyboard_failed` |
| `GPT_IMAGE_BASE_URL` / `GPT_IMAGE_API_KEY` / `GPT_IMAGE_MODEL` | 03 | `image_config` |
| `SEEDANCE_BASE_URL` / `SEEDANCE_API_KEY` / `SEEDANCE_MODEL` | 04（仅生成镜/i2v 展示镜） | `video_config` |

**小样省钱**：`export AD_MAX_SHOTS=2` → 02 起镜头数封顶 2，贯穿 03/04/05。正式出片前 `unset`。

**自动化跳分镜拍板**：`export MVSTUDIO_STORYBOARD_AUTO_APPROVE=1` → 03_keyframes 完成后不停在 awaiting，直接进 04（自动化/批处理场景用；交互场景**别设**，故事板拍板是省钱防线）。

**成本分层**：00（读图，免费）· 01/02（LLM 付费）· 03（图像付费）· 04（Seedance 付费 · 但 static/ken_burns 展示镜走 ffmpeg 免费）· 05（ffmpeg 免费）。

---

## 3 · 每步契约

> 通用：每步产物落 `<项目根>/<step>/`；上游产物自动拷进 `<step>/_input/`；日志在 `<step>/_meta/log.md`。产物齐即视为完成，失败则 `<step>` 落 `rejected` + `error={code,message,hint}`。
> 📍 **项目根**：`init <片名> <项目根>`，项目根 = 用户原始物料所在目录，必填。

### 00_intake · `intake_validate` — 收物料 + 校验（本地免费）

- **前置输入**：`00_intake/request.yaml`（首次 `run` 自动生成模板并停下报 `need_materials`）。字段：`aspect_ratio`（9:16/16:9/1:1）· `brief`（文本文件路径）或 `brief_text`（内联）· `images`（≥1 张，每个 `path`+`name`+可选 `role`）。
- **产物**：`manifest.yaml`（图片清单+尺寸+摘要 / 文本 / 画幅）· `validation_report.md` · `brief.md`。
- **校验**：`run` 停在 awaiting → 成功；读 `validation_report.md` 确认画幅、图片数+尺寸、文本字数。
- **失败码**：`need_materials` · `bad_image`/`no_image` · `no_brief`。

### 01_analysis · `llm_analyze` — 需求理解书（付费 · LLM）

- **输入**（自 00）：`manifest.yaml` + `brief.md`
- **命令**：`ok <name> 00_intake` → `run <name>`
- **产物**：`requirements.md`（需求理解书，人可读 · **这是关键拍板点**）· `requirements.yaml`（用途/卖点/人群/基调/CTA/时长）。
- **校验**：读 `requirements.md` 转述，**主动问"这个方向对吗？不对告诉我哪里改"**。
- **提示词**：`analysis.requirements.md`（改完 `reject 01_analysis "调提示词"` → `run`）。
- **失败码**：`missing_intake` · `llm_config` · `analysis_failed`。

### 02_storyboard · `llm_storyboard` — 故事 + 逐镜分镜（付费 · LLM）

- **输入**（自 01+00）：`requirements.yaml` + `manifest.yaml`
- **命令**：`ok <name> 01_analysis` → `run <name>`
- **产物**：`story.md`（故事线）· `storyboard.md`（逐镜表，标🖼展示/🎬生成）· `shots.yaml`（每镜 `type`/`motion`/`duration`/`product_ref`/`image_prompt`/`video_prompt`/`overlay_text`）。
- **校验**：读 `storyboard.md` 表格展示，报镜头总数 + 展示镜/生成镜各几个。
- **合理建议**：`AD_MAX_SHOTS` 生效（镜头被截）→ 提醒"当前小样只出 N 镜"；问"哪镜想改"。
- **失败码**：`no_requirements` · `storyboard_failed` · `no_shots_drafted`。

### 03_keyframes · `gen_keyframe` — 首帧 + 展示帧（付费 · 图像）

- **输入**（自 02+00）：`shots.yaml` + `manifest.yaml`
- **命令**：`ok <name> 02_storyboard` → `run <name>`（整批）· 或 `shot <name> 03_keyframes <镜号>`（逐镜省钱）
- **做什么**：generated 镜→AI 画首帧；**display 镜→AI 生成背景 + 产品原图 PIL paste（像素不动，100% 保真）**。画完后自动拼一张 `storyboard_grid.png`（镜头≥2 时），让用户一屏看完再决定要不要花钱进 04_shots（i2v 最贵）。
- **产物**：`keyframes_index.yaml` + `SH###_keyframe.png`（按画幅）+ `storyboard_grid.png`（分镜拼图 · N 张 keyframe 网格 + 镜号/时长字幕 · 拍板锚点，单镜片跳过）。
- **校验**：读"生成 X/总 Y"，**指向 `<项目根>/03_keyframes/storyboard_grid.png` 让用户拍板**；单镜时无此文件，直接指 `SH001_keyframe.png`。
- **合理建议**：`storyboard_grid.png` 缺失（`meta.storyboard_grid=None` · 镜头 <2）→ **不是错误**，直接指第一张 keyframe。
- **失败码**：`no_shots` · `image_config` · `keyframe_failed`（全失败才算）。

### 04_shots · `gen_video` — 每镜视频（生成镜付费 · 展示镜免费）

- **输入**（自 03）：`keyframes_index.yaml` + png
- **命令**：`ok <name> 03_keyframes` → `run <name>` · 或 `shot <name> 04_shots <镜号>`
- **做什么**：generated/i2v 镜→Seedance i2v（慢，先提醒用户）；**static/ken_burns 展示镜→ffmpeg 本地出片，不花钱不调服务**。
- **产物**：`shots_index.yaml` + `SH###.mp4`。
- **校验**：读"生成 X/总 Y"，逐镜报 `SH###.mp4`+来源（seedance/static/ken_burns）。
- **合理建议**：若有 i2v 镜，提醒"这几镜要跑 Seedance，慢，先忙别的"。
- **失败码**：`no_keyframes` · `video_config`（有 i2v 镜但没配 Seedance）· `video_failed`。

### 05_delivery · `compose` — 合成交付（本地免费 · ffmpeg）

- **输入**（自 04+00+01）：`shots_index.yaml`+mp4 · `manifest.yaml`
- **命令**：`ok <name> 04_shots` → `run <name>`
- **做什么**：按分镜顺序拼接 · 归一到画布 · 叠卖点/CTA 文字（.ass 烧入）。当前版本无音频。
- **产物**：`final.mp4`（用户画幅）· `overlay.ass` · `delivery_report.md`。
- **校验**：读 `delivery_report.md`，指向 `final.mp4`，报时长/画幅/镜头数/文字处数。
- **失败码**：`no_videos` · `normalize_failed` · `concat_failed` · `mux_failed`。

---

## 4 · 打回与级联

- 用户说"改"→ **先追问哪里不对**，再 `reject <name> <step> "<具体意见>"`。逐镜问题写 `reject <name> 03_keyframes "SH003: <反馈>"`。
- `reject` 效果：本步 revision+1、意见落 `<step>/_meta/feedback.md`、**下游所有非 pending 步骤级联重置为 pending**。
- 打回后 `run <name>` 自动从被打回步骤重跑。

---

## 5 · 一屏速查

```
cwd: ad-agent/           片名 <name> 全程一致
六步: 00_intake → 01_analysis → 02_storyboard → 03_keyframes → 04_shots → 05_delivery
主循环: init → run →(读产物转述→ok/reject)→ run → … → 05 done
关键拍板: 01 需求理解书（先确认方向）· 02 分镜（确认镜头）
保真: display 展示帧 = 产品原图 paste 到 AI 背景，像素不改
付费步: 01 02 03 · 04(仅生成镜/i2v)   免费: 00 05 · 04(static/ken_burns)
省钱: export AD_MAX_SHOTS=2   正式出片前 unset
画幅: 9:16 / 16:9 / 1:1（1:1 的 i2v 镜按 9:16 出片再填充到方画布）
```
