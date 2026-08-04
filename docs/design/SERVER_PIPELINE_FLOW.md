# 服务端端到端流程图(网页版制作流程）

> 说明：这是当前多租户服务端（santen/steven 在跑的那套）从**上传物料**到**成片交付**的完整流程。
> 与对话式 `paperdoll-mv-packaging` skill 是**两套独立实现**，此文只画服务端。
> 图用 Mermaid，可在 VS Code / GitHub / 预览器直接渲染。

## 节点图例

```mermaid
flowchart LR
  U["👤 用户操作/拍板点"]:::user
  P["⚙️ 纯程序处理"]:::prog
  L["🧠 LLM 步骤（有提示词）"]:::llm
  I["🎨 出图（图像模型）"]:::img
  V["🎬 出视频（Seedance i2v）"]:::vid
  D{"◇ 分支判断"}:::branch
  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

---

## 一、总览：10 个 stage 主线 + 5 个拍板点

```mermaid
flowchart TD
  A["intake 素材与需求"]:::prog --> B["music 音乐与歌词"]:::llm
  B --> C["story 故事框架"]:::llm
  C --> C_ok{"👤 确认故事？"}:::branch
  C_ok -->|approve| DD["storyboard 分镜工作台"]:::llm
  C_ok -->|request_revision| C
  DD --> DD_ok{"👤 确认分镜？"}:::branch
  DD_ok -->|approve| E["scene_planning 场景组规划"]:::llm
  DD_ok -->|request_revision| DD
  E --> F["scenes 场景与背景"]:::img
  F --> F_ok{"👤 确认背景？"}:::branch
  F_ok -->|approve| G["keyframes 关键帧选择"]:::img
  F_ok -->|request_revision| F
  G --> G_ok{"👤 确认关键帧？"}:::branch
  G_ok -->|approve| H["shots 单镜制作"]:::vid
  G_ok -->|request_revision| G
  H --> J["composite 合成验收"]:::prog
  J --> K["delivery 最终交付"]:::user
  K --> K_ok{"👤 确认外发？"}:::branch
  K_ok -->|approve| DONE["✅ 成片外发"]:::user

  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

> 备注：素材一变（换音频/歌词/加删角色图）→ 后面已确认的 stage 全部作废、状态回退到 music 重跑。
> stage 状态：`locked`（锁）→ `pending`（轮到你做）→ `awaiting_approval`（等你确认）→ `approved`。

---

## 二、第一段：物料进来 → 补齐三桶 → 入库体检

```mermaid
flowchart TD
  UP["👤 上传文件 POST /assets"]:::user --> CLS["⚙️ 按后缀分类落桶<br/>audio/lyrics/characters/backgrounds"]:::prog
  CLS --> CHK["⚙️ 齐备度检查 material-status"]:::prog
  CHK --> MAT["👤 点『确认计费并自动补全』<br/>POST /materialize confirm_billing=true"]:::user

  MAT --> billing{"◇ confirm_billing?"}:::branch
  billing -->|false| E422["❌ 422 需确认计费"]:::branch
  billing -->|true| audio{"◇ 音频恰好 1 个?"}:::branch
  audio -->|否| E400["❌ 400 no_audio 中止"]:::branch
  audio -->|是| lyr{"◇ 歌词桶空?"}:::branch

  lyr -->|空| TR["⚙️ 自动转写 ASR<br/>音频 → transcript.lrc"]:::prog
  lyr -->|非空| chr{"◇ 角色桶空?"}:::branch
  TR --> trok{"◇ 转写可用?"}:::branch
  trok -->|provider没配/挂了| E423["❌ 423 转写不可用"]:::branch
  trok -->|词密度>8/s| E409["❌ 409 幻觉门"]:::branch
  trok -->|OK| chr

  chr -->|空| GENC["🎨 从歌词抽名 → 每人出一张立绘<br/>模板:简洁人物肖像…中国风写实白底半身"]:::img
  chr -->|非空| INTAKE["⚙️ start_director_intake<br/>三桶齐 → 提交入库"]:::prog
  GENC --> INTAKE

  INTAKE --> PROBE["⚙️ 入库体检 _probe_lyrics"]:::prog
  PROBE --> ltype{"◇ 歌词类型?"}:::branch
  ltype -->|xlsx 导演表| A_CT["aligned_director_contract<br/>人物+时间权威绑定 · 不用对齐"]:::prog
  ltype -->|lrc 有时间戳| A_LRC["aligned · 不用对齐"]:::prog
  ltype -->|txt 纯文本| A_REQ["alignment_required"]:::prog
  A_REQ --> ALIGN["⚙️ 本地 Whisper 逐字对齐<br/>转写文本须与歌词完全一致"]:::prog

  A_CT --> DONE1["→ 进第二段 导演编排"]:::prog
  A_LRC --> DONE1
  ALIGN --> DONE1

  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

> 另有一条独立的 LLM 角色分析链路（网页多轮对话 `POST /fill/characters/analyze`）：读歌词前 8000 字，
> 让"MV 导演助手"识别人物、末尾吐 JSON。与上面自动物料化的"从 xlsx 抽名"是两条不同的路。
> 转写 provider 选择链：**先本地 faster-whisper（MVSTUDIO_WHISPER_MODEL）→ 再远端网关**，逐个试，前面失败就 fall through。

---

## 三、第二段：导演编排（语义分析 → 分镜 → 创意 → 审批发布）

```mermaid
flowchart TD
  IN["⚙️ 入库产物<br/>intake + 带时间码歌词 + brief"]:::prog --> ENTRY{"◇ 走哪条入口?"}:::branch
  ENTRY -->|run_director_plan 主路径| DM
  ENTRY -->|offline_test| DM
  ENTRY -->|mvp_test| DM
  ENTRY -->|resume 断点续跑| CRE

  DM["🧠 draft_maps 语义草图（2 枪 LLM）"]:::llm --> DM1["🧠 枪1 歌词语义分段<br/>lyrics.semantic_segment.requested"]:::llm
  DM --> DM2["🧠 枪2 人物关系草图<br/>relationship_map.draft_requested"]:::llm
  DM1 --> MAPS["⚙️ 产出 music_map.yaml + character_map.yaml<br/>lyrics_semantic.json + beats.json"]:::prog
  DM2 --> MAPS

  MAPS --> STRUCT["⚙️ 结构分镜 plan_structural_score<br/>纯程序 · 不花钱 · 出 visual_score.yaml"]:::prog
  STRUCT --> mode{"◇ 出创意分镜?"}:::branch
  mode -->|offline / mvp:跳创意| COMP
  mode -->|plan:走创意| CRE

  CRE["🧠 创意规划 draft_creative_score"]:::llm --> CRE1["🧠 每镜 1 枪 逐镜视觉创意<br/>visual_score.creative_draft_requested"]:::llm
  CRE1 --> CRE2["🧠 全片 1 枪 质检抬三档<br/>visual_score.quality_review_requested"]:::llm
  CRE2 --> COMP

  COMP["⚙️ 编译打包 compile_package<br/>硬校验:时间轴无缝+能量起伏+多人物有关系镜<br/>出 storyboard.md + shots.yaml + animatic.mp4"]:::prog
  COMP --> APP["👤 approve 审批（哈希盖章）"]:::user
  APP --> PUB{"◇ publish 发布<br/>目标已存在且不同?"}:::branch
  PUB -->|系统发布过的| OVER["覆盖（记 superseded）"]:::prog
  PUB -->|用户手改的 + preserve=true| KEEP["跳过 · 保留用户版"]:::prog
  PUB -->|用户手改的 + preserve=false| CONF["❌ 冲突 不覆盖"]:::branch
  PUB -->|不存在| NEW["新建发布"]:::prog
  OVER --> DONE2["→ 进第三段 图像生成"]:::prog
  KEEP --> DONE2
  NEW --> DONE2

  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

> LLM 发送机制：system = 系统词+任务词拼接（尾部追加 "Return one JSON object only…"），
> temperature=0、json_object、流式；中文提示词先经翻译器翻英文再发。
> `run_director_plan` 发布用 `supersede=true, preserve_user_edits=true`（保护用户手改）；mvp 用默认 false/false。

---

## 四、第三段：图像生成（背景 / 关键帧共用出图引擎）

```mermaid
flowchart TD
  SP["👤 场景规划 suggest（本身不出图）<br/>LLM 把镜头按共用背景归组"]:::llm --> SPA["👤 approve<br/>下发 scene_group_id 到镜头"]:::user

  SPA --> BGREQ["🎨 背景生成 请求"]:::img
  BGREQ --> TRANS["🧠 出图 prompt 由 LLM 翻译产出<br/>中文导演词 + 这镜全部上下文 → 一句英文 prompt"]:::llm
  TRANS --> BGGEN["🎨 出背景图（不含人物）<br/>硬约束:参考图只借画风 严禁画人"]:::img
  BGGEN --> BGSEL["👤 选定 background master<br/>写进该组所有镜头"]:::user

  BGSEL --> kfgate{"◇ 关键帧前置门"}:::branch
  kfgate -->|scenes未approve / 无background_master_id| KFBLOCK["❌ 拦住"]:::branch
  kfgate -->|都齐| KFROUTE{"◇ 关键帧来路?"}:::branch

  KFROUTE -->|generate 模型出| KFTRANS["🧠 LLM 翻译出 prompt<br/>第一张参考=背景 其余=人物锚点"]:::llm
  KFTRANS --> KFGEN["🎨 出关键帧候选（背景+人物完整首帧）<br/>禁改画风/加人/文字/水印"]:::img
  KFROUTE -->|import 用户上传成品| KFIMP["👤 上传自己做的首帧"]:::user

  KFGEN --> KFSEL["👤 select 选定关键帧候选"]:::user
  KFIMP --> KFSEL
  KFSEL --> DONE3["→ 进第四段 视频生成<br/>选中关键帧当 i2v 首帧"]:::prog

  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

> 出图引擎固定 n=1（一次一张），有参考图走 images.edit、无参考图走 images.generate。
> 角色图是另一条独立链路，不走翻译，纯中文模板直发。

---

## 五、第四段：视频生成 + 成本记账

```mermaid
flowchart TD
  KF["⚙️ 选中关键帧（i2v 首帧）+ shots.yaml"]:::prog --> path{"◇ 走哪条视频路径?"}:::branch

  path -->|路径A generate_shot_video| A1["🎬 单镜出片（宽松）"]:::vid
  path -->|路径B start_seedance_shot| B1["🎬 契约出片（严格）"]:::vid

  A1 --> ATR["🧠 LLM 翻译出运动 prompt<br/>video.shot.generate_requested"]:::llm
  ATR --> AGEN["🎬 Seedance i2v 首帧→动<br/>0.8/秒 · 不进账本 · 无重复付费锁<br/>体检不阻断（只提示）"]:::vid
  AGEN --> ADONE["产出该镜 mp4"]:::prog

  B1 --> BLOCK{"◇ 一次性付费锁<br/>这镜已付过?"}:::branch
  BLOCK -->|已付| BSKIP["跳过付费 · 直接复用"]:::prog
  BLOCK -->|没付| BTR["🧠 LLM 翻译出运动 prompt"]:::llm
  BTR --> BGEN["🎬 Seedance i2v 锁定 9:16 / 720p<br/>0.6/秒 · 进账本 · 硬体检不过就退回"]:::vid
  BGEN --> BQC{"◇ 硬质检过?"}:::branch
  BQC -->|不过| BFAIL["❌ 退回 不计成品"]:::branch
  BQC -->|过| BLEDGER["⚙️ 记账 INSERT OR IGNORE（幂等·同镜不重复扣）"]:::prog
  BSKIP --> BDONE["产出该镜 mp4"]:::prog
  BLEDGER --> BDONE

  ADONE --> FIN["⚙️ 合成 + 交付<br/>按时间码拼镜 + 混音轨 → 成片"]:::prog
  BDONE --> FIN
  FIN --> OUT["🎬 最终 MV 成片"]:::vid

  classDef user fill:#e8b84b,stroke:#8a6d1f,color:#222
  classDef prog fill:#d9d2c5,stroke:#8a8072,color:#222
  classDef llm fill:#7bb0e0,stroke:#2f5f8a,color:#fff
  classDef img fill:#8ec98e,stroke:#3f7a3f,color:#222
  classDef vid fill:#c98ec1,stroke:#7a3f72,color:#fff
  classDef branch fill:#e6a07a,stroke:#8a4f2f,color:#222
```

> **Seedance 只有 i2v**（必须给首帧），没有纯文生视频分支、没有负向提示词；
> 固定 `generate_audio=False`、`watermark=False`。
> **两条视频路径记账口径不一致**（历史遗留，值得留意）：
>
> | | 路径A generate_shot_video | 路径B start_seedance_shot |
> |---|---|---|
> | 单价 | 0.8/秒 | 0.6/秒 |
> | 进成本账本 | 否 | 是 |
> | 重复付费锁 | 无 | 有（一次性锁） |
> | 质检 | 非阻断（只提示） | 硬门（不过退回） |
> | 尺寸 | 跟随请求 | 锁死 9:16 / 720p |

---

## 六、三个容易踩的点（复盘用）

1. **materialize 是"入口门"不是"合成步"**：它只负责把音频/歌词/人物三个桶补齐并触发入库，
   硬前提是**必须且仅有 1 条音频**（否则 400 no_audio）；`confirm_billing=false` → 422；
   转写不可用 → 423；歌词幻觉 → 409。它不产出任何画面。
2. **两条视频路径口径不一致**（见上表）——同一个片子走 A 和走 B，扣费与质检行为不一样。
3. **出图 / 出视频的英文 prompt 都是 LLM 现翻的**：用户永远只写中文导演词，
   系统内部先过"翻译器"LLM 转英文再发给图像/视频模型；角色图是例外（纯中文模板直发）。
