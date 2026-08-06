# mv-agent 工作流规范（Codex 执行契约 · 线 G 生成式）

> **这是什么**：mv-agent 六步生成式 MV 流水线的**严格可执行契约**。Codex 读本文即可调度执行,**无需再读 `conductor/` 源码**。
> **人格/话术**见 `AGENTS.md`;**路线分流**(生成式 vs 程序化)见 `docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md`。本文只管:每步输入什么、输出什么、跑哪条命令、怎么校验。
> **工作目录铁规**:所有命令必须在 `mv-agent/` 下执行(`python -m conductor.cli` 依赖此 cwd)。片名 `<name>` 全程一致。

---

## Codex 职责边界(只做这三件,别越界)

1. **流程控制** — 按 §1 主循环发命令(`init`/`run`/`ok`/`reject`),不亲手改文件、不亲手拼 ffmpeg、不替工具算数据。所有实际工作由 `conductor` 脚本完成。
2. **必要结果校验** — 只看 §3 每步「Codex 校验」列的那几项(命令是否停在 awaiting_approval、关键产物是否非空)。**不通读项目源码**、不解析产物内部结构去二次判断,契约里没写的不查。
3. **合理建议** — 命中 §3「合理建议」列的信号时,用大白话给用户一句提醒(如歌词行数偏少、某镜生成失败)。建议而非擅自行动。

**红线**:❌ 不读 `conductor/`、`src/mvstudio/` 源码(本文已固化你需要的全部)· ❌ 不改任何底层代码/引擎 · ❌ 不绕过 CLI 直接调工具函数 · ❌ 不把命令/错误栈甩给用户(念白用大白话)。

---

## 0 · 控制面(全部命令,没有别的)

| 命令 | 作用 | 何时用 |
|------|------|--------|
| `python -m conductor.cli init <name> <项目根>` | 建骨架 + prompts + state.json 于**物料目录**(项目根必填) | 新片第一步 |
| `python -m conductor.cli status <name>` | 打印六步状态 + 花费 | 任何时候查进度 |
| `python -m conductor.cli run <name>` | 一路跑到**下一个等拍板处 / 失败处**停 | 主驱动命令 |
| `python -m conductor.cli next <name>` | 只跑**下一个可执行步骤** | 单步调试 |
| `python -m conductor.cli shot <name> <step> <镜号...>` | **逐镜/子集生成**(仅 `03_keyframes`/`04_shots`),结果增量合并进索引,不动其余镜 | 按需出单张图/单段片,省钱不烧整批 |
| `python -m conductor.cli ok <name> <step>` | 批准某步(awaiting→done) | 用户说"过" |
| `python -m conductor.cli reject <name> <step> "意见"` | 打回(重跑本步 + 下游级联回 pending) | 用户说"改" |

`<step>` ∈ `00_intake 01_analysis 02_storyboard 03_keyframes 04_shots 05_delivery`

**`shot` 镜号写法**(仅 `03_keyframes` / `04_shots`,上游须已 `done`):
`SH003` · `3` · `3-6` / `SH003-SH006`(区间)· `SH003,SH007`(逗号列表)· `all`(全部)· `missing`(还缺的)。
- 结果**增量合并**进本步索引(`keyframes_index.yaml` / `shots_index.yaml`),不覆盖其余镜;索引按分镜原顺序重排。
- `shot` **不推进状态机**:本步仍停在 `pending`/`awaiting_approval`,出满意后照常 `ok <name> <step>` 才算批准。全部失败才落 `rejected`,部分失败仍成功(看 `meta.partial_error` 报的镜号)。
- 典型用法:先 `shot <name> 03_keyframes 3` 试一张看风格,满意再 `shot <name> 03_keyframes missing` 补齐,最后 `ok`。省钱不必一次烧满整批。

---

## 1 · 状态机 + 调度循环(Codex 唯一要懂的编排逻辑)

**每步状态**:`pending → running → awaiting_approval → done`(或失败落 `rejected`)。

**`run` 的行为**(不用自己实现,理解即可):
1. 选第一个 `pending`/`rejected` 且**所有上游 `input_from` 均 `done`** 的步骤,跑它。
2. 跑成功 → 若该步 `approval=True`(六步全是)→ 落 `awaiting_approval`,**停下等拍板**。
3. 跑失败 → 落 `rejected` + 结构化错误,**停下**(不会死循环重试)。
4. 回到 1,直到无可执行步骤。

**Codex 主循环**:
```
init → run → [读产物转述用户 → 用户 ok/reject] → run → … → 05_delivery done
```
- 每次 `run` 停在 awaiting_approval,就读该步产物、用大白话转述、等用户拍板。
- 用户认可:`ok <name> <step>` 然后再 `run`。
- 用户要改:`reject <name> <step> "<具体意见>"` 然后再 `run`(下游已批准步骤会被级联重置为 pending,自动重跑)。

---

## 2 · 前置条件(开工前一次性核验)

```bash
python --version                                   # 需 3.10+
python -c "import yaml, dotenv, faster_whisper"    # 核心依赖(缺→ pip install -r requirements.txt)
test -f .env || echo "缺 .env(复制 .env.example 填 API Key)"
which ffmpeg ffprobe                               # 05_delivery / 00_intake 需要
```

**.env 必填项**(键名遵循 `mv_platform.control_plane.ENV_MAP`):

| 变量 | 用于步骤 | 缺失后果 |
|------|---------|---------|
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | 01 / 02 | `llm_config` / `storyboard_failed` |
| `GPT_IMAGE_BASE_URL` / `GPT_IMAGE_API_KEY` / `GPT_IMAGE_MODEL` | 03 | `image_config` |
| `SEEDANCE_BASE_URL` / `SEEDANCE_API_KEY` / `SEEDANCE_MODEL` | 04 | `video_config` |
| (whisper 模型) | 00(仅 txt/xlsx/兜底) | 自动发现本地 medium,无需填 |

**小样省钱**:`export MV_MAX_SHOTS=2` → 02 起镜头数封顶 2,贯穿 03/04/05。正式出片前 `unset`。

**成本分层**:00(ffprobe+whisper 本地免费)· 01/02(LLM 付费)· 03(图像付费)· 04(Seedance 付费,最慢)· 05(ffmpeg+PIL 本地免费)。

---

## 3 · 每步契约(跑前念白 / 输入 / 命令 / 产物用途 / 校验 / 建议)

> 通用:每步产物落 `<项目根>/<step>/`;上游产物自动拷进 `<step>/_input/`;日志在 `<step>/_meta/log.md`。产物**齐全即视为完成**(控制器按文件是否存在判定),失败则 `<step>` 落 `rejected` 且 `error={code,message,hint}`。
> 📍 **项目根约定(owner 2026-08-05 · 见 `docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1`)**:凡 `init` 都是新项目,`<项目根>` = **用户原始物料所在目录**,**必填**。`init <片名> <项目根>` 把骨架/产物建在物料目录,并把「片名→项目根」记入 `projects/_registry.json`;缺参数直接报错,绝不落回 `mv-agent/projects/`。之后 `status/run/ok/reject <片名>` 按片名走注册表,用法不变。
> **念白格式**:CLI 的 `run`/`next` 已自动打印"跑前(脚本+用途)/跑后(产物+用途)/提示词标注",**直接转述,别另编**。下面每步的「跑前念白/产物用途」就是这些数据,列出便于你转述。

### 00_intake · 脚本 `intake_validate` — 收物料 + 校验 + 歌词时间码(本地免费)

- **跑前念白**:"这步用 `intake_validate`:收下你的音乐/歌词/人物图,校验格式齐不齐,再用本地 whisper 给歌词打时间码。不花钱。"
- **前置输入**:`projects/<name>/00_intake/request.yaml`(`init` **不建**此文件;首次 `run` 时若缺失/未填 `audio`,`intake_validate` 生成模板并停下报 `need_materials`,等用户填)。字段:
  - `audio`(必填,`.wav/.mp3/.aac/.m4a/.flac/.ogg`)
  - `lyrics`(可选,`.lrc` 最准 / `.txt` 一行一句 / `.xlsx` 表格 / 留空走 whisper 兜底)
  - `lyrics_column`(仅 xlsx:列字母如 `"B"` 或表头名;留空自动挑 CJK 占比最高列)
  - `intent`(一句话创作意图)· `characters`(≥1 个,每个 `path`+`name`,`.png/.jpg/.jpeg/.webp`)
- **命令**:`python -m conductor.cli run <name>`
- **产物用途**:`manifest.yaml`(物料清单:音频 path+digest+时长 / 歌词来源+method+行数 / intent / characters)· `lyrics_timed.json`(歌词时间码 `{version,entries:[{start_seconds,text}]}`)· `intent.md`(创作意图人可读)· `validation_report.md`(校验报告:各项 ✅)
- **Codex 校验**:① `run` 停在 `00_intake` awaiting → 成功;停在 rejected → 读 `error.message` 转述。② 读 `validation_report.md` 一次,确认音乐时长、歌词行数+来源(method)、人物数、意图都在。**仅此,不解析 json 细节。**
- **合理建议**:歌词 method=`whisper`(用户没给词,是听音识别)→ 提醒"歌词是机器听出来的,可能有错字,要更准就给 .lrc/.txt";歌词行数明显偏少(如 <5)→ 提醒可能没识别全。
- **失败码**:`need_materials`(request 没填全)· `bad_audio`(音频缺失/格式不支持)· `bad_character`/`no_character`(人物图缺失或 0 个)· `probe_failed`(ffprobe 挂)· `lyrics_timing_failed`/`no_lyrics`(时间码为空)。

### 01_analysis · 脚本 `llm_analyze` — LLM 导演规划 + 故事框架(付费 · LLM)

- **跑前念白**:"这步用 `llm_analyze`:把歌词/音乐/人物/意图交给 LLM,产出导演规划和故事框架。会调用付费模型。"
- **输入**(自 00):`manifest.yaml` + `lyrics_timed.json`
- **命令**:`ok <name> 00_intake` → `run <name>`
- **产物用途**:`story.md`(故事框架人可读总览)· `beats.json`(音乐节拍/段落数据)· `lyrics_semantic.json`(歌词逐行语义分段)· `music_map.yaml`(音乐结构地图:时长/段落)· `character_map.yaml`(人物关系与导演功能)· `title_card.yaml`(标题卡/艺术字数据契约)
- **提示词**(想调创意在此改,`projects/<name>/prompts/`):`analysis.director.md` · `analysis.lyrics_segment.md` · `analysis.character.md`。改完 `reject <name> 01_analysis "调提示词"` → `run`。
- **Codex 校验**:`run` 停在 `01_analysis` awaiting → 成功;读 `story.md` 转述即可。不校验 json/yaml 内部。
- **合理建议**:转述后主动问"这个故事方向对吗?不对告诉我哪里改"。
- **失败码**:`missing_intake`(上游产物缺)· `audio_moved`(音频原路径失效)· `llm_config`(服务没配→提示填 `.env` 的 `LLM_*`)· `analysis_failed`(LLM 调用失败→查额度/地址)。

### 02_storyboard · 脚本 `llm_storyboard` — 逐镜分镜脚本(付费 · LLM)

- **跑前念白**:"这步用 `llm_storyboard`:按音乐段落逐镜拆分镜脚本,规划每镜画面和动作。会调用付费模型。"
- **输入**(自 01):`music_map.yaml` + `character_map.yaml`
- **命令**:`ok <name> 01_analysis` → `run <name>`
- **产物用途**:`storyboard.md`(分镜脚本人可读逐镜表)· `shots.yaml`(镜头列表:每镜 `id`/`section_id`/`duration`(4~15s)/`first_frame`/`primary_action`/`image_prompt`/`video_prompt`)· `scene_groups.yaml`(场景组:哪些镜共用背景)
- **规则**:镜头数 = 音乐段落数,受 `MV_MAX_SHOTS` 封顶。
- **提示词**:`storyboard.creative.md` · `storyboard.quality_review.md`
- **Codex 校验**:`run` 停在 `02_storyboard` awaiting → 成功;读 `storyboard.md`,表格展示(最多 10 镜),报镜头总数。
- **合理建议**:若 `MV_MAX_SHOTS` 生效(镜头数被截)→ 提醒"当前是小样模式只出 N 镜,正式出片要我解除限制就说";问"哪个镜头想改"。
- **失败码**:`no_sections`(上游 music_map 无段落→回 01 查)· `storyboard_failed`(LLM 挂)。

### 03_keyframes · 脚本 `gen_keyframe` — 逐镜首帧图(付费 · 图像)

- **跑前念白**:"这步用 `gen_keyframe`:拿你的人物图当参考,给每个镜头画一张竖版首帧图(9:16)。逐张生成,按镜头数量花图像费。"
- **输入**(自 02+00):`shots.yaml` + `manifest.yaml`(取人物图作参考)
- **命令**:`ok <name> 02_storyboard` → `run <name>`(整批出图)· 或 `shot <name> 03_keyframes <镜号...>`(逐镜/子集出图,省钱按需)
- **产物用途**:`keyframes_index.yaml`(首帧图索引:每镜 `id`/`keyframe`(png 名)/`duration`/`video_prompt`/`digest`)+ `SH###_keyframe.png`(每镜一张 · 9:16 · 1024x1536)
- **Codex 校验**:`run` 停在 `03_keyframes` awaiting → 成功;从 CLI 输出/`meta` 读"生成 X/总 Y"。指向 `projects/<name>/03_keyframes/` 让用户看图。**不逐张打开图判断质量**(那是用户的事)。
- **合理建议**:X<Y(部分失败,`meta.partial_error`)→ 明说"有 N 张没出来,要重试就 reject 报镜号";让用户"哪张不满意报镜号我重做"。
- **失败码**:`no_shots`(上游无 shots)· `image_config`(服务没配→提示 `GPT_IMAGE_*`)· `keyframe_failed`(**全部**失败才算 rejected;部分失败仍 ok)。

### 04_shots · 脚本 `gen_video` — 逐镜 i2v 视频(付费 · 最慢)

- **跑前念白(必说慢)**:"这步用 `gen_video`:把每张首帧图交给 Seedance 跑成视频片段(9:16/720p)。这步最慢,N 个片段大概要 X~X 分钟,你先忙别的。"
- **输入**(自 03):`keyframes_index.yaml` + 同目录 png
- **命令**:`ok <name> 03_keyframes` → `run <name>`(整批出片)· 或 `shot <name> 04_shots <镜号...>`(逐镜/子集出片,最慢最贵更该按需)
- **产物用途**:`shots_index.yaml`(视频片段索引:每镜 `id`/`video`(mp4 名)/`duration`/`video_sha256`)+ `SH###.mp4`(每镜一段 · Seedance · 9:16/720p/该镜 duration 秒)
- **Codex 校验**:`run` 停在 `04_shots` awaiting → 成功;从 `meta` 读"生成 X/总 Y";逐镜报 `SH###.mp4`+时长。**不播放视频判断内容**。
- **合理建议**:X<Y(部分失败)→ 明说哪几镜没出、可 reject 重试;让用户"有问题的报镜号"。
- **失败码**:`no_keyframes`(上游无关键帧)· `video_config`(服务没配→提示 `SEEDANCE_*`)· `video_failed`(**全部**失败才算)。

### 05_delivery · 脚本 `compose` — 合成交付(本地免费 · ffmpeg+PIL)

- **跑前念白**:"这步用 `compose`:把所有片段按时间码拼起来,铺上音乐、烧进字幕、叠上开场/结尾大标题艺术字,出成片。本地合成,不花钱。"
- **输入**(自 04+00+01):`shots_index.yaml`+mp4 · `manifest.yaml`(音频路径)· `lyrics_timed.json` · `title_card.yaml`
- **命令**:`ok <name> 04_shots` → `run <name>`
- **内部流程**(理解即可,`compose` 全自动做):标题卡→PNG · 每段归一化(720x1280/30fps/h264/无音轨)· concat · 铺音乐(延迟片头卡 3s 对齐)· 烧 `.ass` 字幕。
- **产物用途**:`final.mp4`(最终成片 9:16/720p)· `subtitle.ass`(字幕,已烧入成片)· `title_cards.json`(大标题艺术字 spec)· `delivery_report.md`(交付报告:时长/规格/清单)
- **Codex 校验**:`run` 停在 `05_delivery` awaiting → 成功;读 `delivery_report.md`,指向 `final.mp4`,报镜头数/字幕行数/有无片头尾卡。批准后全片完成。
- **合理建议**:报告显示"缺音频"→ 提醒 00 的音频路径可能已移动;字幕 0 行 → 提醒歌词时间码没进来。
- **失败码**:`no_videos`(上游无片段)· `normalize_failed`(归一化全挂→查 ffmpeg/镜头 mp4)· `concat_failed` · `mux_failed`(终混失败→查 ffmpeg/字幕字体)。

---

## 4 · 打回与级联(Codex 必须遵守)

- 用户说"改"→ **先追问哪里不对**,再 `reject <name> <step> "<具体意见>"`。逐镜问题写成 `reject <name> 03_keyframes "SH003: <反馈>"`。
- `reject` 效果:本步 revision+1、意见落 `<step>/_meta/feedback.md`、**下游所有非 pending 步骤级联重置为 pending**(已批准的下游会重跑,不会丢上游成果)。
- 打回后 `run <name>` 即自动从被打回步骤重跑。

---

## 5 · 一屏速查

```
cwd: mv-agent/           片名 <name> 全程一致
六步: 00_intake → 01_analysis → 02_storyboard → 03_keyframes → 04_shots → 05_delivery
主循环: init → run →(读产物转述→ok/reject)→ run → … → 05 done
付费步: 01 02 03 04    免费步: 00 05    最慢: 04(先提醒用户)
省钱: export MV_MAX_SHOTS=2   正式出片前 unset
每步失败 → rejected + {code,message,hint};产物齐 → 自动视为完成
```

