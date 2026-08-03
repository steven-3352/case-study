# PRD-009：Audio-First 素材导入与缺料自动补齐

> **状态**：待实施 · 已按二轮技术评审修订（2026-08-03 · 一轮修 2 P0 + 5 P1 + 2 P2；二轮修 `input_refs` 不可变阻断 + 命名矛盾 + 混合合唱 + 哈希格式 + 计费去重键，见 §2.1.1 与评审记录）（PRD 定稿后须走 `.claude/workflows/prd_pipeline.js`，见 `docs/RULES/02_WORKFLOW.md §四`）
> **优先级**：P1（导入门槛是新用户第一道墙，当前 audio-only / 缺歌词 / 缺角色一律被拒）
> **前置条件**：PRD-008 验收通过（真 provider 链路可用——本 PRD 的听写与做图依赖真 provider）
> **负责模型**：便宜模型实现，Opus 验收
> **解锁**：后续「模板项目 / 一键成片」类需求

---

## 1. 背景与问题陈述

### 1.1 当前状态

用户在「导入项目素材」时，只能上传被系统识别的 4 类文件（audio / lyrics / characters / backgrounds），且必须**同时齐全**才能开工。三道门层层设卡：

1. **导入层静默丢弃**：`import_project_asset`（`mv_platform/application/service.py:1410`）按 `_IMPORT_EXTENSIONS`（`service.py:1323`）白名单归类，扩展名不在册的文件返回 `{"ignored": True}`，用户不知道被吞了。
2. **前端一刀切拒绝**：`job-form` submit（`apps/mv_api/static/app.js:108`）硬校验「恰好一个音频 + 恰好一个歌词 + 至少一张角色图」，否则整批拒绝：
   - `文件夹中需要且只能有一个音频文件`
   - `文件夹中需要且只能有一个歌词文件（xlsx、lrc 或 txt）`
   - `文件夹中没有识别到角色图片`
3. **intake 契约硬要求三件套**：`validate_intake`（`src/mvstudio/director/intake.py:72-88`）要求 audio / lyrics / characters 全部非空；`start_director_intake`（`service.py:3499`）再校验一遍。

### 1.2 问题

真实场景里用户手头常常**只有一首歌**（mp3 / wav），没有现成歌词、更没有角色立绘。这些恰恰是本工具应当**生产**的东西，却被当成**必须由用户提供的前置输入**挡在门外。

### 1.3 能力缺口（实现前必须知道，否则会做出跑不通的东西）

核实全仓后确认，"缺的后面补"当前**不成立**，需新建两块能力：

- **听写歌词**：`FasterWhisperAlignmentPort`（`src/mvstudio/providers/alignment_faster_whisper.py:100-102`）只做「对齐已有歌词」——转写结果须与用户提供的歌词**逐字一致**否则报错。它是对齐器，不是听写器。全仓无「音频 → 歌词」路径。
- **凭空生成角色**：`character_map`（`src/mvstudio/director/drafting.py:598-608`）从用户导入的角色图派生；`structural_planner.py:149` 要求每个角色有 `source_asset`（真实图片文件）。全仓无「无参考图 → LLM 设定 → 做图」路径。

---

## 2. 目标与非目标

### 2.1 设计主线（先读这段，再看规格）

**不改造下游每一层契约，而是"在 intake 前把缺料生成为真实输入文件"，让现有管线原样跑。** 下游消费的是 `inputs/lyrics/` 的歌词文件与 `inputs/characters/` 的角色图文件；只要 intake 执行前这些文件已就位，`validate_intake` 与后续全部环节无需改动。契约改动面因此从「每一层」收缩为「导入放宽 + 入口编排 + 两个新生成执行器」。

### 2.1.1 交接机制:硬门与 staging 改读文件系统桶(二轮评审阻断修复,实现者必读)

**背景阻断**:一轮 PRD 反复写「补齐产物**加入 job `input_refs`**」——核实后确认**做不到**:

- `JobSpec` 是 `@dataclass(frozen=True)`(`contracts.py:72-73`),`input_refs: Tuple[str,...]` 不可变。
- `job_id = "job-" + canonical_hash(request)[:32]`,而 `input_refs` 是 hash 的一部分(`service.py:4472-4474`)——改 refs 等于换 job 身份。
- 仓库只 `INSERT INTO jobs`、**无任何 UPDATE**(`repositories.py:67-70`)——已建的 job 改不了。

而两道硬门(`start_director_intake:3499-3502` / `_start_director_animatic_test:3549-3553`)和 staging 拷贝循环(`:3507-3517`)**都读 `job.input_refs`**。若补齐产物进不了 `input_refs`,intake 仍按建 job 时的 audio-only refs 判定 → 永远拒绝。**这是本 PRD 能否跑通的载重点。**

**定案(用户 2026-08-03 拍板,选项 a)**:硬门与 staging **改为以项目文件系统桶为准,不再以 `job.input_refs` 为准**。

- **判齐标准**:进 intake/animatic 前,读磁盘桶 `inputs/audio/`、`inputs/lyrics/`、`inputs/characters/`:
  - `inputs/audio/` **恰好 1 个**音频文件(唯一硬门,缺则拒)。
  - `inputs/lyrics/` **恰好 1 个**歌词文件(缺则先 materialize;详见 §4.4.1 幂等)。
  - `inputs/characters/` **≥1 个**角色图(缺则先 materialize)。
- **staging**:staging 循环改为遍历这三个磁盘桶的实际文件,而非 `job.input_refs`。
- **`job.input_refs` 语义降级**:对 analyze job,`input_refs` 仅作建 job 时的**信息性快照**(记录用户当时选了什么),**不再是 intake 判齐/取料的事实源**。事实源是磁盘桶。job 身份、hash、幂等 job_id 全部不动——补齐只往磁盘桶写文件,不碰 job 行。
- **`:3501` 的「refs 数 == 三类之和」计数校验**:该校验原意是「refs 里除了三件套没有杂项」。改读磁盘桶后此校验失去对象,**删除**;代之以「三桶各自数量满足上一条判齐标准」。
- **provenance**(§3.3)由编排层写 sidecar,`inspect_intake` 读桶内文件时按 sidecar 标来源——与磁盘桶事实源一致,不依赖 `input_refs`。

**为什么选这条**:最贴合「有什么用什么」——analyze job 本质是「分析这个项目」,项目的料就是磁盘上此刻真实存在的文件;补齐只是把磁盘补足。改动面最小(两道门 + 一个 staging 循环 + 删一条计数校验),不引入新 job / 新路由状态机,intake 后下游读的是 manifest(由 `inspect_intake` 从磁盘桶重建),本就不读 `input_refs`。

### 2.2 目标

1. **导入存全部**：文件夹内任意文件原样进项目，未知类型归 `inputs/materials/` 兜底桶，不再静默丢弃。
2. **唯一硬门 = 音频**：没有正时长音频流 → 拒绝开工（`_probe_audio` 已有此校验）。歌词、角色可缺。
3. **缺歌词自动听写**：新增 Whisper 自由转写能力，音频 → 词级时间戳 → 生成 `.lrc` → 落入 `inputs/lyrics/`。
4. **缺角色自动生成**：LLM 从歌词 + brief 设定 N 个角色 → 复用图片 provider 文生图 → 落入 `inputs/characters/`。
5. **计费可见**：听写、做图走现有费用账本；audio-only 需用户在 intake 阶段显式确认「自动补齐并计费」后才触发，不导入即扣费。
6. **软门提示**：材料不足以直接跑时，前端提示缺什么、将自动补什么，而非报错拒绝。

### 2.3 非目标

- **不改 `validate_intake` 的三件套要求**（补齐后它看到的仍是齐全输入）。`inspect_intake` **允许一处最小改动**：为 manifest 追加 `provenance` 字段（见 §3.3）——这是唯一被授权的 intake **契约**改动。
- **授权的 service 层门改（§2.1.1）**：`start_director_intake` / `_start_director_animatic_test` 的判齐与 staging 改读文件系统桶、删除 `:3501` 计数校验——这是 service 编排层改动（不碰 `intake.py` 契约），为本 PRD 核心机制,已被授权。
- 不做「无音频」项目（纯图片、纯歌词）——那不是音乐视频，超出本工具边界。
- 不做歌词**创作**（作词）——只做「已有歌声 → 转写为歌词文本」。有人声才有词；纯器乐由用户在 intake 阶段手填或跳过（Whisper 对纯器乐会幻觉产词，见 §4.2 质量门）。
- 不做角色**编辑器 UI**（本 PRD 只保证自动生成的角色落成 `source_asset`，人物增删改沿用现有 intake 阶段能力）。
- 不改数据库表结构。
- 不碰 `pipeline/voice_room/`、不碰 `docs/RULES/`。

---

## 3. 数据模型规格

### 3.1 项目目录新增兜底桶

`_PROJECT_DIRECTORIES`（`service.py:145`）追加：

```
"inputs/materials",
```

### 3.2 `import_project_asset` 归类规则变更（`service.py:1410`）

| 情形 | 现状 | 变更后 |
|---|---|---|
| dotfile（`.` 开头） | `{"ignored": True}` | 不变（仍跳过） |
| 扩展名匹配已知 kind | 归该 kind | 不变 |
| 扩展名**未匹配**任何 kind | `{"ignored": True}` 静默丢弃 | 归 `materials` 兜底桶，`ignored=False`，原扩展名保留 |
| `kind_hint` 显式且非法 | 报错 | 不变 |

- `materials` **不做**内容真伪校验（任意类型允许）。
- `backgrounds` **仍做** `_validate_reference_image` 图片真伪校验（它会喂给生成流程，不能是伪装文件）。
- 文件名仍走 sha256 去重 + 净化；目标路径仍锁在项目 `root` 内（现有安全逻辑不动）。

**实现细节（P2，避免撞现有逻辑）**：现流程在 `service.py:1422-1428` 先按扩展名反查 kind，`kind is None` 时 `:1426` 返回 `ignored`；`:1427-1428` 又校验「扩展名必须属于该 kind 的白名单」。materials 兜底须**新增独立分支**：`kind is None` 时不再 return ignored，而是置 `kind="materials"` 并**跳过 `:1427` 的白名单匹配**（materials 不在 `_IMPORT_EXTENSIONS`，若把它塞进白名单反而会误拦其他 kind）。即 materials 是「反查失败后的落桶分支」，不参与 `_IMPORT_EXTENSIONS` 的扩展名匹配。`kind_hint` 显式传非法值时仍报错（不变）。

### 3.3 补齐来源标记（provenance）

自动生成的输入须可区分于用户上传，写入 intake manifest 附加字段（不破坏现有结构）：

```json
{
  "lyrics": { "...": "...", "provenance": "user_uploaded | auto_transcribed" },
  "characters": [ { "...": "...", "provenance": "user_uploaded | auto_generated" } ]
}
```

`provenance` 缺省视为 `user_uploaded`（向后兼容既有项目）。

**契约边界澄清（回应「不改 intake 契约」的表述）**：`provenance` 是 **manifest 输出字段**，由 `inspect_intake`（`intake.py:342-354` 构造 manifest 处）写入——这是 §2.3 授权的唯一 intake 改动。它**不是 intake 输入字段**：`validate_intake`（`intake.py:72-88`）校验的是入参 `value`（白名单 `{project_id, audio, lyrics, characters}`，`:75`），provenance 不进入参、不碰这个白名单，故 `validate_intake` 零改动。

**provenance 来源**：不由 intake 自行判断，而由 §4.4 编排层在补齐时**显式传入**——编排层知道哪些文件是它刚生成的。传递方式：编排层把补齐产物的相对路径集合写入 job 元数据（sidecar），`inspect_intake` 读取后对匹配路径标 `auto_*`，其余标 `user_uploaded`。这样 intake 无需自己区分来源，也不需要新增入参字段。

---

## 4. 业务逻辑规格

### 4.1 唯一硬门：音频（R-090）

前端 `job-form` 与后端入口均只硬性要求「至少一个音频」。无音频 → 拒绝，文案：`项目需要至少一个音频文件（mp3/wav 等），没有歌曲无法开始`。

### 4.2 听写歌词执行器 `lyrics_transcribe`（R-091）

- **provider 扩展**：`FasterWhisperAlignmentPort` 新增 `transcribe(audio_path) -> [{text, start, end, probability}]` 自由转写方法。现有 `align`（`alignment_faster_whisper.py:71-102`）已在 `:75` 调 `transcribe(..., word_timestamps=True)` 拿到完整转写文本 + 词级时间戳，只是在 `:100-102` 拿它跟用户歌词强制逐字比对后丢弃；新方法**跳过比对**、直接返回转写结果即可。与现有 `align` 并存，互不影响。
- **执行器**：新建 `src/mvstudio/executors/lyrics_transcribe.py`，输入音频 → 词级时间戳 → 合并为行级 `.lrc`（含 `[mm:ss.xx]` 时间标签）→ 原子写入 `inputs/lyrics/<name>-<hash>.lrc`。**幂等见 §4.4 P0-1**（一个音频只听写一次）。
- **产出契约**：生成的 `.lrc` 须能被现有 `_probe_lyrics`（`intake.py:271`）解析为 `alignment_state=aligned`（含时间轴），下游零改动接手。产物 `provenance=auto_transcribed`（§3.3），供前端标注「自动生成·approximate·可人工修改」。

#### 4.2.1 质量门与诚实局限（P1-4，实现者必读）

Whisper 是语音模型，用在**带伴奏的唱歌音频**上有真实局限，不能假设「有音频就能听写出好歌词」。执行器必须内建质量门，不合格宁可**判为「听写不可靠」交人工**，也不把垃圾当合法歌词写进 aligned 合约：

- **纯器乐/间奏会幻觉，不是返回空**：Whisper 对无人声段倾向**编造文本**。因此「空转写 → 报错」的判据不够——必须加**幻觉/人声检测**：如平均词置信度低于阈值、或转写文本高度重复/无意义，判为「无有效人声」，抛可读错误 `音频中未检测到可靠人声，无法自动听写歌词；请手动提供歌词`，**不写产物**。
- **词级时间戳对唱歌不可靠**：拖腔、伴奏干扰使词边界漂移。产物 manifest 标 `alignment_state=aligned` 但须同时标 `approximate=true`，前端提示「时间轴为估计值，可在 intake 阶段修正」。
- **CPU 性能与超时**：`from_env` 默认 `device=cpu / compute_type=int8`（`alignment_faster_whisper.py:27`）。长音频 CPU 慢，`transcribe` 现无超时——执行器必须设**上限时长/超时**，超时进 `blocked` 而非无限挂起。
- **多语种误判**：`language=None` 自动检测可能判错。默认从项目 brief 语言或配置取显式 `language`；无则允许自动检测但在 event 里记录检测结果供审计。
- **置信度阈值**须可配置，写入配置项而非硬编码。

- **无人声**：见上，幻觉检测拦下并给可读错误，不静默写垃圾。
- **事件 + 计费**：走现有 job 事件流；按本地 ASR 成本口径计费（若为本地模型则记 ¥0，仍出 event 供审计）。

### 4.3 角色生成执行器 `character_design`（R-092）

- **执行器**：新建 `src/mvstudio/executors/character_design.py`。
  - 输入：听写/已有歌词 + `brief`。
  - 逐个调用 `OpenAICompatibleImageProvider.generate(prompt, references=(), size=<按画幅>)`（文生图，references 可空，`image_openai.py:50`）→ 原子写入 `inputs/characters/<角色名>-<hash>.png`（**文件名 stem 落名规则见 §4.3.1，与合约绑定强相关，不是自由 `<id>`**）。
- **产出契约**：生成的角色图须能被 `_probe_character`（`intake.py:298`）识别为合法图片，并作为 `source_asset` 供 `drafting._characters`（`drafting.py:398`）与 `structural_planner`（`structural_planner.py:149`）消费。
- **计费**：图片 ¥0.5/张，走现有费用账本。
- **画幅**：按项目 `resolution` / `canvas` 显式传 `generate(size=...)`（provider 默认 `1024x1536` 竖版，不显式传会忽略项目画幅）。

#### 4.3.1 角色名/数量必须服从歌词绑定合约（P0-2，硬约束）

角色不能让 LLM 随意自选名字/数量——下游有两处硬约束会崩：

- **XLSX 导演合约（binding）场景**：若歌词经 `parse_xlsx_director_sheet`（`intake.py:200-268`）解析、带 `character_names` 且 `characters_are_binding: True`，则 `_bind_director_cast`（`drafting.py:377-394`）要求每个歌词行的角色名**精确命中**角色别名表，否则抛 `MapDraftError`。
  - **规则**：此场景下 `character_design` 生成的角色 `name` 集合**必须直接取自合约 `character_names` 全集**（去重、排除合唱标记，见下），逐一对应，**不允许 LLM 另起名或增减数量**。LLM 只负责为这些既定角色补外观 prompt。
  - **落名/哈希格式（二轮评审定死，blocker #3+#5，实现者照抄不得改动）**：`_bind_director_cast` 的别名表由 `aliases(item)`（`drafting.py:378-381`）= `{item["name"].strip(), Path(source_asset).stem}` 各自再经 `re.sub(r"-[0-9a-f]{10}$", "", value)` 剥尾构成。故自动生成角色图必须满足**两个硬条件**才能命中合约名 `林渊`：
    1. 文件名 stem **必须等于合约角色名**再拼哈希：`<合约角色名>-<hash>.png`（如 `林渊-3f9a2c1b04.png`），**不是** `<id>-<hash>` 或 `C01-<hash>`——否则 stem 剥完是 `C01`，永远命不中 `林渊`。
    2. 哈希段**必须恰好 10 位小写十六进制**（正则 `-[0-9a-f]{10}$`）——须用 `hashlib.<algo>(...).hexdigest()[:10]`（全小写，与导入去重同格式）。位数不对（如 8 位、含大写、含非 hex）→ `re.sub` 不剥 → stem 带尾巴 → 绑定失配。
    3. `brief.characters` 保持为空（见下条），name 由 `_characters`（`drafting.py:398`）默认取 `Path(source_asset).stem` → 剥哈希 → 恰好还原为合约名。三条环环相扣，缺一即崩，(a) 用例专测此链路。
  - **合唱标记排除**：合约 `character_names` 里的合唱标记（如「合」）**不生成独立角色图**——`_bind_director_cast`（`drafting.py:386-387` 附近）对纯「合」有全员映射语义，给它做图反而多出一个绑不上的角色。排除规则见下方「混合合唱」。
- **`brief.characters` 数量绑定**：`_characters`（`drafting.py:401-404`）要求 `brief.characters` 要么为空、要么数量与角色图数量**完全一致**，否则抛「brief character count must match portrait count」。
  - **规则**：`character_design` 生成角色后，若 `brief.characters` 非空则数量必须与生成数一致；建议自动补齐时**保持 `brief.characters` 为空**，让 `_characters` 走「未声明」分支自动派生，规避数量不匹配。
- **听写 LRC（无绑定）场景**：纯 LRC 无 `character_names`，`_bind_director_cast`（`drafting.py:386-387`）遇 `names is None` 直接跳过，不崩——此场景 LLM 可自主设定 1–3 个角色（上界受控，避免失控做图）。
- **混合合唱单元格（二轮评审补，blocker #4）**：`_split_character_names`（`intake.py:188-197`）只对**恰好等于**合唱标记的单元格返回 `["合"]`；`林渊+合` 会被拆成 `["林渊","合"]`。而 `_bind_director_cast` 的全员映射只认**恰好** `["合"]`（`drafting.py` 该分支），混合列里的「合」会被当普通角色名去别名表里找、找不到 → `MapDraftError`。规则：
  - `character_design` 从合约取待生成角色名时，须**先按 `_split_character_names`（`intake.py:188-197`）同一套逻辑拆分每个单元格**，收集所有出现过的名字，**再从全集里剔除合唱标记「合」**，剩余的才是要做图的实拍角色。
    - **落地约束**：当前合唱标记「合」在 `_split_character_names` 里是**硬编码字面量**（`intake.py:192` `if value == "合"`），全仓无 `_CHORUS_MARKERS` 常量。本 PRD 要求 Phase 2 **在 `intake.py` 提取一个模块级常量 `_CHORUS_MARKERS = frozenset({"合"})`**，`_split_character_names` 与 `character_design` 的剔除逻辑**共用同一常量**，避免两处各写一份「合」漂移。此为授权的 `intake.py` 改动（提常量、行为等价，不改契约语义）。
  - 即：`林渊+合`、`合`、`林渊` 三种单元格，去重剔「合」后待生成集合 = `{林渊}`。为「合」单独做图是错的（见上条排除）。
  - **前置断言**：若拆分后出现「合」以外无法归类的合唱/占位标记（合约里出现了 `character_design` 不认识的特殊标记），**抛可读错误交人工**，不猜——`合约含无法识别的角色标记 <x>，请人工确认角色清单`。绝不把不认识的标记当角色名硬做图。
- **组合矩阵**（必须都覆盖，见 §7）：

  | 歌词来源 | 角色来源 | 角色名/数量规则 |
  |---|---|---|
  | 用户 XLSX（binding） | 自动生成 | 取自合约 `character_names`，禁自选 |
  | 用户 LRC/TXT | 自动生成 | LLM 自主 1–3 个 |
  | 自动听写 LRC | 自动生成 | LLM 自主 1–3 个 |
  | 任意 | 用户已上传 | 不触发生成 |

### 4.4 入口编排（R-093）

`start_director_intake`（`service.py:3484`）改为**先补齐、后 intake**：

1. 校验 `inputs/audio/` 恰好 1 个音频（唯一硬门，读磁盘桶 §2.1.1）。
2. `inputs/lyrics/` 空 → 触发 `lyrics_transcribe`，产物**只写入 `inputs/lyrics/` 磁盘桶**（不碰 `input_refs`，§2.1.1）。
3. `inputs/characters/` 空 → 触发 `character_design`（依赖步骤 2 的歌词），产物**只写入 `inputs/characters/` 磁盘桶**。
4. 补齐后，调用现有 `director_intake`（契约不变；判齐/取料改读磁盘桶，此时三桶齐全）。

补齐为独立可观测步骤（各自 event + 计费），非静默内联。

#### 4.4.1 幂等：一个音频只补一次（P0-1，硬约束）

听写/做图非确定性，若无守卫，重复触发会往 `inputs/lyrics/`、`inputs/characters/` 按内容 hash 落**新文件**，累积多个 `.lrc` → 直接撞死 §2.1.1 改后的判齐门「`inputs/lyrics/` 恰好 1 个歌词」。规则：

- **补齐前先探测目标桶**：`inputs/lyrics/` 已有任一歌词文件 → 跳过听写，复用现有；`inputs/characters/` 已有任一角色图 → 跳过做图。
- **补齐是「补足到 1 个歌词 + ≥1 角色」，不是「每次都生成」**。重复请求返回已有产物，**不重复计费、不产生新文件**。
- **用户覆盖自动产物的去重（二轮评审补，避免 auto+real = 2 个歌词撞门）**：
  - 判齐与幂等探测都以**磁盘桶文件是否存在**为唯一事实源（§2.1.1),桶里有几个就是几个。
  - 若 `inputs/lyrics/` 已有文件（无论 user_uploaded 还是上一轮 auto_transcribed），本轮**不再听写**——因此正常路径下歌词桶恒为 1 个，不会 auto+real 叠成 2 个。
  - 用户若在补齐**之后**手动上传第二个歌词文件，桶内变 2 个 → 命中 §2.1.1「恰好 1 个歌词」门被拒，前端提示「歌词只能保留一个，请删除多余项」。**替换语义**：用户要用自己的歌词覆盖自动听写产物，须先删除 auto 产物再传（前端读 provenance 提供「删除自动歌词」按钮，见 §6.3）——本 PRD 不做自动择一，避免误删用户文件。
  - 角色桶允许 ≥1，用户追加真角色图与自动产物并存不冲突（下游按全集绑定）。
- 判定「是否已补齐」以**文件是否存在于目标桶**为准（配合 §3.3 provenance 记录哪些是自动产物，供前端与重试逻辑区分）。

#### 4.4.2 失败回滚 / 事务边界（P1-3）

补齐分步写文件，中途失败（如歌词已写、角色做图挂了）会留半成品，叠加幂等探测会导致「重试时歌词被当已补齐、角色仍缺且已计歌词费」。规则：

- 每一步补齐要么**完整成功**、要么**清理本步已写产物**后再置 `blocked`（本步事务性）。
- 已成功的**上游步骤产物保留**（如听写成功、做图失败：保留歌词，清理失败角色的半成品文件，仅角色步置 `blocked`）——重试时听写命中幂等跳过、不重复计费，只重跑做图。
- 计费在**产物落盘成功后**记账，失败已清理的不计费。

#### 4.4.4 计费幂等键必须确定性绑定 `_record_cost`（二轮评审补，blocker #6）

§4.4.1 保证「不重复生成文件」，但**计费去重是独立一层**——即便文件命中幂等跳过、只要重试路径又调了一次 `_record_cost` 且 key 不同,就会重复扣费。核实 `_record_cost`（`service.py:3086-3101`）：`entry_id = "cost-" + canonical_hash({project_id, job_id, step_id, resource_type, metadata})`，落库 `INSERT OR IGNORE INTO cost_entries`。故**只要这五元组确定性，重复记账天然被 `INSERT OR IGNORE` 吞掉**。规则（实现者照此传参）：

- **`job_id`**：补齐复用**同一个 materialize job**的 id（§2.1.1 不新建 job），重试时 job_id 不变——这是去重成立的前提。
- **`step_id`**：必须**确定性、与音频/角色内容绑定**，不得含时间戳/随机数/自增序号。约定：
  - 听写：`step_id = "materialize:lyrics:" + <音频内容 hash 前 10 位>`。
  - 做图：`step_id = "materialize:character:" + <角色名或其确定性序号>`（每个角色一条,名字取自 §4.3.1 落名）。
- **`resource_type`**：听写 `"asr"`,做图 `"image"`（与现有账本口径一致）。
- **`metadata`**：只放**确定性内容**（如音频 hash、角色名、画幅、provider 名）,**禁放**耗时、时间戳、请求 id 等每次不同的字段——否则 hash 变、去重失效。
- **记账时机**：§4.4.2 已定「产物落盘成功后才记账」;配合上面确定性 key,「落盘成功 → 记账」这条边即使重试也只入库一次。
- 测试 (b)/(d) 用桩 provider 计次 + 对账 `cost_entries` 行数断言零重复(§7.2)。

#### 4.4.3 animatic 路径同样接补齐（P1-2）

`_start_director_animatic_test`（`service.py:3549`）有与 intake **完全相同**的「1 audio + 1 lyrics + characters」硬门（`:3549` / `:3553`）。只补 `start_director_intake` 的话，audio-only 项目走到 animatic 仍被拒。规则：animatic 入口共用同一「补齐前置」——进入 animatic 前**读磁盘桶**（§2.1.1）判齐，三桶未齐先走 §4.4 补齐（幂等，通常此时已补过、直接命中跳过），再走改读磁盘桶后的 animatic 判齐。animatic 的门与 staging 一并按 §2.1.1 改读磁盘桶、删 `:3553` 计数校验（与 intake 同一套）。

### 4.5 显式计费确认（R-094，P1-5 时序定稿）

audio-only（或任何触发自动补齐的情形）：前端在进入补齐前要求用户点击「确认自动补齐并计费」。未确认不触发 provider 调用。已齐全三件套的项目：行为完全不变，无需确认。落地规格（不留给实现阶段）：

- **契约二选一，本 PRD 定为：独立 `POST /api/v1/jobs/{id}/materialize` 路由**（见 §5.2）。理由：补齐是有成本、可失败、可重试的独立步骤，独立路由让「确认→补齐→intake」三态清晰，SSE 进度和失败重试都挂在这一步，不把计费副作用塞进 `director/intake` 的语义里。
- **`confirm_billing` 落点**：请求体 `{"confirm_billing": true}`。服务端在**任何 provider 调用之前**校验该标记；缺失或为 false → 直接返回「需确认计费」错误，**零 provider 调用**（用桩 provider 断言零调用，见 §7.2）。
- **校验方**：`service` 层的 materialize 入口校验，不依赖前端自觉。
- **时序**：`materialize`(confirm_billing) → 补齐（幂等，§4.4.1）→ 成功后 `director/intake`（此时三件套齐全）。若项目已齐全，前端不显示确认按钮、直接走 intake，materialize 可跳过。

---

## 5. API 变更规格

### 5.1 现有路由变更

- `POST /api/v1/projects/{id}/assets`（`service.py:670`）：未知类型不再 `ignored`，返回 `{"ignored": false, "kind": "materials", ...}`。
- `POST /api/v1/jobs/{id}/director/intake`：内部编排为「补齐 → intake」，对外契约不变（仍返回 job 状态）。补齐进度经 SSE `events` 流推送。

### 5.2 新增路由（已定稿，非二选一）

- `POST /api/v1/jobs/{id}/materialize`：显式触发缺料补齐（配合 R-094 的确认按钮）。请求体 `{"confirm_billing": true}`。返回补齐 job 状态；补齐进度经 SSE `events` 流推送。
  - 服务端在任何 provider 调用前校验 `confirm_billing`（§4.5）；未确认 → 返回「需确认计费」错误、零 provider 调用。
  - 幂等（§4.4.1）：重复调用命中已有产物则直接返回、不重复生成/计费。
  - 失败回滚（§4.4.2）：本步失败清理本步半成品后置 `blocked`，保留已成功的上游产物。
  - `director/intake` 与 `director/animatic-test` 入口**读磁盘桶判齐**（§2.1.1）：三桶未齐时先要求走完 `materialize`（前端驱动），不在 intake/animatic 内部隐式触发计费。
  - materialize 复用**当前 job 的 id**（不新建 job），产物只写磁盘桶、不改 job 行（§2.1.1）——这是计费幂等键成立的前提（§4.4.4）。

### 5.3 `allowed_stages` / workflow 返回值

- intake 阶段 `data` 增加 `pending_materialization`（缺哪些料）与各料 `provenance`，供前端渲染软门提示与「自动生成」标记。
- `pending_materialization` **由后端读磁盘桶计算**（§2.1.1：`inputs/lyrics/` 空 → 缺歌词，`inputs/characters/` 空 → 缺角色），**不从 `input_refs` 推断**——前端只消费此字段，不自行比对 `input_refs`。

---

## 6. 前端规格

### 6.1 导入对话框（`apps/mv_api/static/index.html:81-82`）

- 文件夹选择器说明与 `folder-summary` change 文案（`app.js:109`）改为：**整个文件夹按现有内容导入为项目原始材料，有什么用什么；缺歌词/角色会在开工时自动补齐（计费）。**

### 6.2 `job-form` submit（`app.js:108`）

- 删除三条硬拒绝，改为仅校验「至少一个音频」。
- 所有文件照常逐个 POST 导入（未知类型现由后端存为 `materials`）。
- analyze 的 `input_refs` 仅取 `audio` / `lyrics` / `characters`（排除 `backgrounds` / `materials`）。**注意**：改后 `input_refs` 只是建 job 时的信息性快照（§2.1.1），intake/animatic 判齐与取料以磁盘桶为准；前端不再依赖 `input_refs` 反推「是否齐全」，而是读后端返回的 `pending_materialization`（§5.3）。
- 齐全 → 照旧建任务并 intake；不齐 → 建任务但进入「待补齐」态，展示缺料清单 + 「确认自动补齐并计费」按钮。

### 6.3 intake 阶段展示

- 自动生成的歌词/角色打 `自动生成` 标记（读 `provenance`），提示用户可在此阶段替换或增删（沿用现有 intake 能力）。

---

## 7. 测试用例规格

### 7.1 单元测试（`tests/mv_platform/unit/test_prd009_auto_materialization.py`）

基础：
- 导入 `.txt` / `.mp4` 等未知类型 → 落 `inputs/materials/`、`ignored=False`、文件确实存在。
- 伪装 png 存 `backgrounds` 仍报 `reference image is invalid`（回归，不受影响）。
- `lyrics_transcribe`：给定含人声音频（或桩 provider）→ 产出合法 `.lrc`，`_probe_lyrics` 解析为 `aligned`。
- `character_design`：给定歌词 + brief（桩 LLM + 桩图片 provider）→ 产出 N 张合法图片，`_probe_character` 通过，可作 `source_asset`。
- 入口编排：audio-only job → 补齐 → `validate_intake` 通过。
- 无音频 → 硬门报错。

覆盖评审指出的真风险点（P1-6，缺一不可）：
- **(a) XLSX binding + 自动角色（P0-2）**：用户传带 `character_names` 的 XLSX 导演合约、缺角色图 → `character_design` 生成的角色名取自合约全集、文件名 stem == 合约名 + 10 位小写 hex（§4.3.1）→ `_bind_director_cast`（`drafting.py:377`）绑定命中、不抛 `MapDraftError`；反向断言「LLM 自选名 / `C01-<hash>` 落名 / 哈希非 10 位」任一都会崩，证明三条落名规则各自必要。
- **(a2) 门改读磁盘桶（blocker #1）**：audio-only 建 job（`input_refs` 仅含 audio）→ materialize 只往 `inputs/lyrics/`、`inputs/characters/` 写文件、**不改 job 行** → `start_director_intake` 读磁盘桶判齐通过（断言 job 的 `input_refs` 仍是建 job 时的单 audio、未被改动，且 intake 不因此被拒）；反向断言「若判齐仍读 `job.input_refs` 则被拒」，证明门必须改读磁盘桶。
- **(a3) 混合合唱单元格（blocker #4）**：合约含 `林渊+合` / `合` / `林渊` 三种单元格 → `character_design` 拆分剔「合」后待生成集合 = `{林渊}`、不为「合」做图 → 绑定命中不崩；含未识别标记的单元格 → 抛可读错误交人工（不硬做图）。
- **(b) 重复触发幂等（P0-1 + blocker #6）**：连续两次 `materialize` → `inputs/lyrics/` 仍只有一个 `.lrc`、`inputs/characters/` 不新增重复角色、第二次**零 provider 调用**（桩 provider 计次断言）；且**对账 `cost_entries` 行数不增**——同一 `job_id + 确定性 step_id`（§4.4.4）使 `_record_cost` 的 `INSERT OR IGNORE` 吞掉重复，断言两次 materialize 后听写/做图各自只有一条 cost entry。
- **(c) 纯器乐幻觉（P1-4）**：给定无人声/低置信度转写 → 质量门拦下、抛「未检测到可靠人声」、**不写歌词产物**（断言 `inputs/lyrics/` 为空）。
- **(d) animatic 路径 audio-only（P1-2）**：audio-only 项目走 `director/animatic-test` → 经补齐前置后通过 `:3549` 校验，不被拒。
- **(e) 半途失败可干净重试（P1-3）**：听写成功、做图失败 → 角色半成品被清理、歌词保留、job `blocked`；重试 → 听写命中幂等跳过（不重复计费）、只重跑做图、成功后齐全。
- **(f) `brief.characters` 数量绑定**：`brief.characters` 非空且与生成角色数不一致 → 复现 `_characters`（`drafting.py:401-404`）的报错；自动补齐保持 `brief.characters` 为空则通过。
- **(g) provenance 落 manifest（P1-1）**：自动产物在 intake manifest 标 `auto_transcribed` / `auto_generated`，用户上传标 `user_uploaded`；且 `validate_intake` 入参白名单未被 provenance 污染（回归）。

### 7.2 API 契约测试（`tests/mv_platform/contract/test_prd009_api.py`）

- 未知类型 assets 上传返回 `kind=materials, ignored=false`。
- `POST /materialize` 未带 `confirm_billing`（或为 false）→ 返回「需确认计费」错误，**桩 provider 计次断言零调用**。
- `POST /materialize` 带 `confirm_billing=true` → 触发补齐、返回 job 状态。
- 重复 `POST /materialize` → 第二次命中幂等、零 provider 调用、无重复计费（对账费用账本）。
- SSE `events` 流出现补齐进度事件（听写、做图各自 event）。
- `director/intake` 与 `director/animatic-test` 在 `input_refs` 未齐三类时，返回引导「先 materialize」而非隐式触发计费。

### 7.3 浏览器 E2E（`tests/e2e/test_prd009_browser.py`）

- 选一个只含 mp3 的文件夹 → 建项目 → 出现「确认自动补齐并计费」→ 确认后进 intake，歌词与角色带「自动生成」标记。

---

## 8. 验收标准

1. audio-only 文件夹可一路走到 intake 完成，歌词、角色均自动补齐为真实输入文件。
2. 无音频文件夹被硬门拒绝，文案明确。
3. 未知类型文件全部落 `inputs/materials/`，无静默丢弃。
4. 自动补齐前有显式计费确认（独立 `/materialize` 路由 + `confirm_billing`），未确认零 provider 调用。
5. 既有「三件套齐全」项目行为完全不变（回归）。
6. `provenance` 正确区分用户上传与自动生成，且未污染 `validate_intake` 入参白名单。
7. **幂等（P0-1）**：重复触发补齐不产生重复歌词/角色文件、不重复计费。
8. **角色绑定（P0-2）**：XLSX binding 歌词 + 自动角色，绑定命中不崩；`brief.characters` 数量约束不被违反。
9. **animatic 路径（P1-2）**：audio-only 项目走 animatic 同样经补齐后通过，不被 `:3549` 硬门拒。
10. **失败回滚（P1-3）**：补齐半途失败清理本步半成品、保留上游产物，重试可干净完成、不重复计费。
11. **Whisper 质量门（P1-4）**：纯器乐/低置信度被拦下不写垃圾歌词；长音频有超时；产物标 `approximate` 供人工修正。
12. **门改读磁盘桶（blocker #1）**：materialize 只往磁盘桶写文件、不改 job 行；intake/animatic 判齐与 staging 均以磁盘桶为事实源，`:3501`/`:3553` 计数校验已删；audio-only job 补齐后一路通过。
13. **落名/哈希格式（blocker #3+#5）**：自动角色文件名 stem == 合约角色名、哈希恰好 10 位小写 hex，绑定命中；格式错误的反向用例证明规则必要。
14. **混合合唱（blocker #4）**：`林渊+合` 等混合单元格拆分剔「合」正确；未识别标记交人工不硬做图；`_CHORUS_MARKERS` 常量单一事实源。
15. **计费幂等键（blocker #6）**：`_record_cost` 的 `step_id`/`metadata` 确定性、`job_id` 复用同一 materialize job，重复记账被 `INSERT OR IGNORE` 吞掉，对账零重复。
16. 全部 7.x 测试通过（含 §7.1 的 (a)/(a2)/(a3)/(b)–(g) 风险点用例）。

---

## 9. 废弃与归档说明

- 保留 `backgrounds` 图片真伪校验；`materials` 为纯兜底桶，二者语义不同，不合并。
- 后端 intake 三件套校验**不删**——前端软门是体验层，后端补齐后仍走原校验，双保险。

---

## 10. 实施顺序建议（给便宜模型 · 定稿后走 Workflow 编排）

1. **Phase 0** 导入放宽（§3.1 / §3.2 / §6.1 / §6.2）——独立可验收，先落地解决「静默丢弃」。
2. **Phase 1** `lyrics_transcribe`（§4.2 + provider `transcribe`），**质量门（§4.2.1）与 Phase 1 同批交付，不得后补**——没有幻觉检测的听写会把垃圾写进 aligned 合约，比不做更糟。
3. **Phase 2** `character_design`（§4.3，依赖 Phase 1 的歌词），**角色绑定规则（§4.3.1 P0-2）是 Phase 2 的验收前置**。
4. **Phase 3** 入口编排 + 计费确认（§4.4 / §4.5 / §5 / §6.3）。**本阶段的载重改动是「门改读磁盘桶」（§2.1.1 blocker #1）——两道硬门 + staging + 删计数校验必须先落地，否则补齐的文件进不了 intake，整条链跑不通。** 幂等（§4.4.1 P0-1）、回滚（§4.4.2）、计费幂等键（§4.4.4 blocker #6）同为核心非补充；animatic 路径（§4.4.3）与 intake 同批处理。
5. **Phase 4** 测试补全（§7）+ 回归。

> **跨阶段硬约束提醒**：blocker #1（门改读磁盘桶）是 Phase 3 的地基,先于编排;两个 P0（幂等、角色绑定）横跨 Phase 2/3;落名/哈希（blocker #3+#5）在 Phase 2、混合合唱（blocker #4）在 Phase 2、计费幂等键（blocker #6）在 Phase 3。实现时别当各阶段的收尾项——它们决定了功能能否跑通，须在对应阶段一开始就设计进去。

> **治理**：本 PRD 定稿后进入执行，须调用 `.claude/workflows/prd_pipeline.js`，每个被激活工种独立 `agent()` 产出、独立验收，禁止主 LLM 一人从需求直写实现（`docs/RULES/02_WORKFLOW.md §四`）。
