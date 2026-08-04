# 对话式 MV 生产流程 · 设计文档

> 目标:把现在服务端揉在一起的流程,重构成「纯控制器 + 纯工具 + 文件夹交接」的对话式流水线。
> 每步一个文件夹(上一步 output = 下一步 input),含详细产物、执行日志、用到的提示词副本。
> 本文只做设计与实现方案,不含代码落地。读者先审阅,对齐后再动手。

---

## 〇、三层分离(架构总则)

三样东西各司其职,互不越界:

- **流程控制器(orchestrator)**:只做四件事——读 `state.json` 选下一步、备齐该步输入、调工具、把产物写到该步文件夹并更新 state。**不含任何业务判断、不写提示词、不碰模型。**
- **工具(tool)**:纯函数式。`输入文件 + 参数 → 输出文件`。凡与大模型交互的工具,**提示词是文件参数**传入,工具本身不内嵌提示词。失败返回结构化错误,不抛异常让控制器猜。
- **文件夹交接**:每步一个文件夹。里面固定三类东西——`_input/`(上一步来的软链/拷贝)、产物、`_meta/`(用过的提示词副本 + 执行日志 + 该步 state 片段)。

这样任何一步都能单独复盘「喂了什么、用了哪版提示词、吐了什么」;任何一步都能单独重跑。

### 关键约束(沿用项目铁律)

- 提示词永远中文写、中文改;出图/出视频前由**翻译工具**转英文(角色图例外,纯中文模板直发)。
- 视频是唯一花钱环节:预估 → 用户确认 → 一次性付费锁 → 幂等记账。
- 硬门(禁蓝紫 / 禁 AI 味深色 / palette / 歌词幻觉 / i2v prompt)是**每步产物入下一步前的自动体检**,不过就打回。
- 只在 `pipeline/voice_room/<片名>/` 下读写;不改 `pipeline/mv_engine/`、不改 `docs/RULES/`。

---

## 一、文件夹骨架

```
pipeline/voice_room/<片名>/
  state.json                顶层清单(控制器唯一读懂的业务状态)
  prompts/                  提示词模板(当参数喂给 LLM 工具,可单独改/版本化)
    analysis.director.md
    analysis.lyrics_segment.md
    analysis.character.md
    storyboard.creative.md
    storyboard.quality_review.md
    image.background.md
    image.keyframe.md
    video.motion.md
    translate.md
  logs/                     全局执行日志(按时间)
  00_intake/                物料 + 校验报告
  01_analysis/              音乐/歌词/节拍/人物/故事框架
  02_storyboard/            分镜脚本 + 镜头表 + 背景归组
  03_keyframes/             每镜首帧图(人物+背景)
  04_shots/                 每镜视频 + QC + 成本
  05_delivery/              成片 + 字幕 + 美术字 + 剪辑工程
```

每个步骤文件夹内部固定结构:

```
0X_xxx/
  _input/          上一步产物的软链或拷贝(控制器放进来的)
  _meta/
    prompt_used/   本步实际用过的提示词副本(含翻译前中文 + 翻译后英文)
    log.md         本步执行日志(工具调用、耗时、模型、token、报错)
    step.json      本步 state 片段(status/hash/approval/cost)
  <产物文件...>     见每步详述
```

---

## 二、state.json 结构

控制器唯一需要读懂的业务状态。其余全在文件夹里。

```jsonc
{
  "project": "<片名>",
  "created_at": "...",
  "production_tier": "standard",       // 只降验收强度,不减步骤
  "steps": {
    "00_intake":    { "status": "done",             "hash": "sha256:...", "approved_at": "..." },
    "01_analysis":  { "status": "awaiting_approval", "hash": "sha256:...", "revision": 2 },
    "02_storyboard":{ "status": "pending" },
    "03_keyframes": { "status": "pending" },
    "04_shots":     { "status": "pending" },
    "05_delivery":  { "status": "pending" }
  },
  "cost": {
    "estimated": 0.0,
    "spent": 0.0,
    "confirmed": false,                // 计费确认闸
    "ledger": []                       // 每镜一次性付费记录(幂等)
  }
}
```

- **status 取值**:`pending`(没开始)→ `running`(工具执行中)→ `awaiting_approval`(产物出了等拍板)→ `done`(已批)/`rejected`(打回,带意见重跑,revision+1)。
- **hash**:产物内容哈希。控制器据此做幂等跳过 + 检测下游是否需重跑。
- **revision**:返修次数。返修产物版本化存(见 §四)。

---

## 三、控制器 / 工具契约

### 3.1 每步契约(step contract)

每步用一个声明式配置描述,控制器读它就够,不写死逻辑:

```jsonc
{
  "id": "01_analysis",
  "input_from": ["00_intake"],          // 依赖哪些上游文件夹
  "prompts": ["analysis.director.md",   // 需要哪些提示词文件
              "analysis.lyrics_segment.md",
              "analysis.character.md"],
  "tools": ["beat_extract", "llm_analyze"],  // 按序调用的工具
  "outputs": ["music_map.yaml", "beats.json", // 产物清单(供完成判定)
              "lyrics_semantic.json", "character_map.yaml", "story.md"],
  "gate": "qc_analysis",                 // 入下一步前的体检工具(可空)
  "approval": true,                      // 是否需要用户拍板
  "done_when": "all_outputs_exist_and_gate_pass"
}
```

### 3.2 工具契约(tool contract)

```
tool(input_paths[], output_dir, params{}, prompt_file?) -> {
  ok: bool,
  outputs: [path...],
  error?: { code, message, hint },     // 失败结构化返回,不抛异常
  meta?: { model, tokens, cost, elapsed }
}
```

- **纯净**:工具不读 state.json、不知道自己是第几步、不决定下一步。
- **LLM 类工具**:多吃一个 `prompt_file` 参数;提示词是中文就先内部调 `translate` 工具转英文(或由控制器显式串一个翻译步)。
- **确定性工具**(beat_extract / compose / qc):不碰模型,可复现。

### 3.3 控制器主循环(伪代码)

```
loop:
  step = 读 state 选第一个 status ∈ {pending, rejected} 且上游都 done 的步
  若无 → 结束或等用户
  若 done_when 已满足(产物齐 + hash 未变) → 标 done, continue   # 幂等跳过
  status = running
  备齐 _input/(软链上游产物)
  for tool in step.tools:
      res = tool(inputs, out_dir, params, prompt_file)
      写 _meta/log.md
      if not res.ok: status=rejected; 记 error; break
  若配了 gate → 跑 gate 工具; 不过 → rejected
  若 step.approval → status = awaiting_approval(交给用户); 否则 done
```

---

## 四、返修 / 幂等 / 断点续跑

- **返修版本化**:用户打回某步 → 该步 `revision+1`,产物存到 `0X_xxx/_rev/v2/`,当前产物是最新版软链。旧版保留可回滚。
- **返修意见**:打回时写 `_meta/feedback.md`,控制器重跑时把它拼进提示词(作为额外上下文文件参数)。
- **下游失效**:某步 hash 变了 → 控制器把所有依赖它的下游步标回 `pending`(级联重跑),但已花钱的镜(见 §五步5)受付费锁保护不重复扣。
- **断点续跑**:控制器每步先查 `done_when`,满足就跳过。中断后重进直接从第一个未完成步继续。

---

## 五、六步详述(input / output / prompt / tool / gate / approval)

### 步骤 0 · 物料进来 + 校验(00_intake)

- **输入**:用户放进来的音频(1 首)、歌词文件(xlsx 带时间码 / lrc / 纯 txt)、人物图片(0~N)、一段"这首歌想表达什么"的中文意图。
- **工具**:`intake_validate`(确定性)。校验:音频**必须且仅 1 首**、歌词可读、图片格式 OK、意图非空。
- **产物**:
  - `manifest.yaml`——物料清单(路径/时长/歌词类型/人物数)。
  - `validation_report.md`——大白话校验结论:哪些过、哪些缺、歌词是否带时间码。
  - `intent.md`——用户的创作意图原文。
- **gate**:`intake_validate` 本身即闸。音频不是 1 首 → 直接挡;歌词无时间码 → 标记"需在步1做逐字对齐"。
- **approval**:是(用户确认物料无误才放行,这就是你要的"事先严格校验")。
- **提示词**:无(纯程序)。

### 步骤 1 · LLM 分析 → 导演规划 + 故事框架(01_analysis)

- **输入**:`00_intake` 全部产物。
- **工具(按序)**:
  1. `beat_extract`(确定性,**新增独立工具**)→ `beats.json`(逐拍时间码,驱动后面每镜时长)。
  2. `lyric_align`(确定性,仅当歌词无时间码)→ 用本地 faster-whisper 逐字对齐,补出时间码。
  3. `llm_analyze`(LLM)→ 两枪:歌词语义分段 + 人物关系;再综合出导演规划 + 故事框架。
- **产物**:
  - `beats.json`——每拍/每小节时间点。
  - `lyrics_semantic.json`——歌词分段(主歌/副歌/桥段 + 情绪标签 + 时间码)。
  - `music_map.yaml`——曲式结构、情绪曲线、能量起伏。
  - `character_map.yaml`——人物设定 + 人物间关系。
  - `story.md`——**故事框架**(大白话:讲什么故事、几个主要段落、视觉基调)。
- **提示词**:`analysis.lyrics_segment.md`、`analysis.director.md`、`analysis.character.md`。
- **gate**:`qc_analysis`——查故事框架是否覆盖全曲时间轴、情绪曲线是否有起伏、多人物是否给了关系。
- **approval**:是(故事框架是全片地基,必须拍板)。

### 步骤 2 · 故事 → 分镜脚本 + 背景规划 + 提示词(02_storyboard)

- **输入**:`01_analysis` 全部。
- **工具(按序)**:
  1. `plan_structural`(确定性)→ 按 beats + 歌词分段切镜,定每镜起止时间,出镜头骨架。
  2. `llm_creative`(LLM)→ 逐镜写视觉创意(中文导演词);再一枪全片质检抬档。
  3. `scene_group`(确定性,**独立层**)→ 把镜头按"能否共用同一张背景"归组,产出 `scene_groups.yaml`。
- **产物**:
  - `shots.yaml`——镜头表(每镜:id / 起止时间 / 所属场景组 / 中文导演词 / 涉及人物)。
  - `storyboard.md`——大白话分镜脚本(逐镜讲画面)。
  - `scene_groups.yaml`——背景归组(哪些镜共用一张背景 master)。
  - 每镜中文导演词单独存 `shots/<id>/director_zh.md`。
- **提示词**:`storyboard.creative.md`、`storyboard.quality_review.md`。
- **gate**:`qc_storyboard`——时间轴无缝拼接、每镜有导演词、多人物镜有关系交代。
- **approval**:是。

### 步骤 3 · 关键帧:人物 + 背景 → 首帧图(03_keyframes)

- **输入**:`02_storyboard` + `00_intake` 的人物图。
- **工具(按序)**:
  1. `translate`(LLM)→ 中文导演词 + 本镜上下文 → 一句英文出图 prompt。
  2. `gen_background`(图像)→ 每个场景组出 1 张背景 master(**严禁画人**,参考图只借画风)。
  3. `gen_character`(图像,独立链路)→ 人物定妆图当**角色锚点**(纯中文模板直发,不走翻译)。
  4. `gen_keyframe`(图像)→ 每镜首帧:第一张参考=背景 master,其余参考=人物锚点,合出完整首帧。
- **产物**:
  - `scene_groups/<gid>/background_master.png`——每组背景。
  - `characters/<cid>/anchor.png`——角色锚点。
  - `shots/<id>/keyframe_candidates/`——首帧候选图。
  - `shots/<id>/keyframe_selected.png`——用户选定的首帧。
  - `shots/<id>/_meta/prompt_used/`——中文导演词 + 翻译后英文 prompt。
- **提示词**:`image.background.md`、`image.keyframe.md`、`translate.md`。
- **前置门**:场景规划未批 / 无 background_master → 挡住不出关键帧。
- **gate**:`qc_image`——禁蓝紫、禁 AI 味深色、palette gate、背景不含人、关键帧不加文字/水印。
- **approval**:是(用户逐镜选定首帧;也允许 `import` 直接上传自己做的成品首帧)。

### 步骤 4 · 每镜视频(04_shots)

- **输入**:`03_keyframes` 每镜选定首帧 + `shots.yaml` 时长。
- **计费前置**:`cost_estimate`(确定性)→ 按总秒数预估价 → 用户 `confirm_billing`。未确认不开跑。
- **工具(按序)**:
  1. `translate`(LLM)→ 中文运动描述 → 英文运动 prompt。
  2. `gen_video`(视频,Seedance **i2v-only**)→ 选定首帧当第一帧,按 prompt 生成该镜动态。固定 `generate_audio=False`、`watermark=False`,无负向提示词。
- **产物**:
  - `shots/<id>/shot.mp4`——该镜视频。
  - `shots/<id>/qc_report.md`——该镜体检结论。
  - `shots/<id>/cost.json`——该镜花费。
- **提示词**:`video.motion.md`、`translate.md`。
- **付费锁 + 记账**:每镜一次性付费锁(重跑不重复扣);账本 `INSERT OR IGNORE` 幂等写入 `state.cost.ledger`。
- **gate**:`qc_video`——运动合理、首帧一致、无崩坏;不过退回不计成品。
- **approval**:是(逐镜验收)。

> **统一记账口径**:本设计**只保留一条视频路径**(等价服务端"路径B 契约式"),
> 消除现服务端 A/B 两路口径不一致的历史遗留。单价、锁、账本、质检全程一致。

### 步骤 5 · 合并 + 字幕 + 美术字 + 剪辑(05_delivery)

- **输入**:`04_shots` 全部镜视频 + `00_intake` 音频 + `01_analysis` 歌词时间码。
- **工具(按序,全确定性)**:
  1. `compose`→ 按 shots.yaml 时间码拼接所有镜。
  2. `mux_audio`→ 混入原曲音轨。
  3. `render_subtitle`→ 按歌词时间码烧字幕。
  4. `render_arttext`→ 美术字/标题(可选,按需)。
  5. `finalize`→ 输出成片 + 剪辑工程文件。
- **产物**:
  - `final.mp4`——最终成片。
  - `subtitle.ass`——字幕。
  - `project.edl`(或等价工程文件)——可回编辑的剪辑工程。
  - `delivery_report.md`——大白话交付说明(时长/镜数/总成本)。
- **提示词**:无(纯程序)。
- **gate**:`qc_delivery`——音画同步、时长匹配、字幕对齐。
- **approval**:是(最终验收)。

---

## 六、工具清单(纯工具 · 一览)

| 工具 | 类型 | 输入 → 输出 | 提示词参数 | 花钱 |
|---|---|---|---|---|
| `intake_validate` | 确定性 | 物料 → manifest + 校验报告 | 无 | 否 |
| `beat_extract` | 确定性 | 音频 → beats.json | 无 | 否 |
| `lyric_align` | 确定性(本地 whisper) | 音频+歌词 → 带时间码歌词 | 无 | 否 |
| `llm_analyze` | LLM | intake → music_map/character_map/story | 是(3 个) | 是(便宜) |
| `plan_structural` | 确定性 | analysis → 镜头骨架 | 无 | 否 |
| `llm_creative` | LLM | 骨架 → 逐镜中文导演词 | 是(2 个) | 是(便宜) |
| `scene_group` | 确定性 | shots → 背景归组 | 无 | 否 |
| `translate` | LLM | 中文 prompt → 英文 prompt | 是(1 个) | 是(便宜) |
| `gen_background` | 图像 | 英文 prompt → 背景图 | (英文已备) | 是 |
| `gen_character` | 图像 | 中文模板 → 角色锚点 | 是(直发) | 是 |
| `gen_keyframe` | 图像 | 英文 prompt+参考图 → 首帧 | (英文已备) | 是 |
| `cost_estimate` | 确定性 | shots → 预估价 | 无 | 否 |
| `gen_video` | 视频(i2v) | 首帧+英文 prompt → mp4 | (英文已备) | **是(贵)** |
| `compose`/`mux_audio`/`render_subtitle`/`render_arttext`/`finalize` | 确定性 | 镜+音+词 → 成片 | 无 | 否 |
| `qc_*`(各门) | 确定性 | 产物 → 通过/打回 | 无 | 否 |

---

## 七、如何实现(落地方案)

分层落地,每层可独立测。建议实现顺序自底向上:

### 7.1 目录与状态层(先做,无外部依赖)

- 写 `orchestrator/state.py`:读写 `state.json`、步骤状态机、hash 计算、级联失效。
- 写 `orchestrator/layout.py`:建/校验文件夹骨架、`_input/` 软链、`_meta/` 落盘。
- **可先跑通"空转"**:所有工具用 stub(只写占位产物),验证控制器主循环、幂等跳过、返修版本化、断点续跑全对。

### 7.2 工具层(逐个实现,契约统一)

- 定 `tools/base.py`:统一签名 `run(input_paths, output_dir, params, prompt_file=None) -> ToolResult`。
- **确定性工具优先**:`intake_validate`→`beat_extract`→`plan_structural`→`scene_group`→`compose` 等。这些不花钱、可复现,先跑通骨架。
- **复用现有实现**:`beat_extract`/`lyric_align`/合成类可直接调 `src/mvstudio/` 与 `pipeline/mv_engine/` 里已有的确定性能力(**只调用不修改**,需要新原子就起草 PR 给 owner)。
- **LLM/图像/视频工具**:各包一个 provider 适配,复用现服务端的 `from_env` provider 接口。提示词一律走 `prompt_file` 参数,内部按需先调 `translate`。

### 7.3 提示词层(从现服务端搬)

- 把 `prompt_catalog.py` 里的 9 条中文 system+task 提示词导出成 `prompts/*.md` 独立文件,当模板。
- 这样提示词脱离代码,用户/你可直接改文件调风格,不用碰工具。

### 7.4 编排配置层(声明式)

- 每步一个 `steps/0X_xxx.json`(§3.1 契约)。控制器读配置驱动,新增/调整步骤改 JSON 不改代码。
- 全流程串成 `pipeline.json`(步骤顺序 + 依赖图)。

### 7.5 对话式外壳(最后)

- 用一个 skill 把控制器包成对话式:用户说"下一步"→ 控制器跑下一步 → 产物给用户看 → "过"或"打回带意见"。
- 拍板点、计费确认、逐镜选帧都通过对话完成;skill 只翻译"用户意图 ↔ 控制器动作",不含业务逻辑。

### 7.6 落地里程碑

1. **M1 空转骨架**:控制器 + state + 文件夹 + stub 工具,全流程能跑通(不出真产物)。
2. **M2 确定性链路**:intake/beats/结构分镜/归组/合成 真实现,能出无 AI 生成的骨架成片。
3. **M3 LLM 链路**:分析/创意/翻译接真模型,出中文导演词 + 英文 prompt。
4. **M4 出图链路**:背景/角色/关键帧真出图 + QC 门。
5. **M5 出视频 + 交付**:i2v 出镜 + 计费锁 + 合成成片。
6. **M6 对话外壳**:skill 包壳,端到端对话式跑一支真片。

---

## 八、和现服务端的关系

- **不是推翻重写**:确定性能力(beats/对齐/合成/mv_engine 原子)、provider 适配、提示词内容全部复用。
- **变的是编排方式**:从"service.py 揉逻辑"变成"控制器读声明式配置 + 纯工具 + 文件夹交接"。
- **修正的历史遗留**:统一视频记账为单条路径(消除 A/B 口径不一致)。
- **新增的独立关注点**:beats 独立工具、背景归组独立层、角色锚点链路、每步 QC 门前置、顶层 state + 返修版本化。

---

## 九、待你拍板的开放项

1. **视频路径**:是否同意只保留一条(契约式)统一口径?(我倾向:是)
2. **返修粒度**:打回是整步重跑,还是允许逐镜(如只重跑第 7 镜)?逐镜更省钱但控制器更复杂。
3. **角色锚点**:是否强制每个人物都要定妆图?没有图的人物怎么办(纯文字设定 vs 必须补图)?
4. **对话外壳**:新写一个 skill,还是扩现有 `paperdoll-mv-packaging` skill?(两者实现独立,建议新写)
5. **落地起点**:先做 M1 空转骨架给你看流程跑通,还是先把某一段(如分析段)做深做透?

> 本文只做设计,未写任何代码。请审阅,尤其 §九 五个开放项——定了我再动手。
