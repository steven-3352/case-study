# Local MV Studio · 架构与产品合同

状态：待独立审查  
日期：2026-07-30  
范围：clone 后本地运行的 MV 制作工具，Web / CLI / Codex 三入口共享同一执行内核

## 1. 冻结决策

1. Web 是可选交互入口，不是运行前提。没有浏览器时，用户可用 `mvstudio` CLI 完成同一工作流；Codex 也只调用同一 Application Service。
2. 所有可确定工作优先由 Python 完成：文件扫描、hash、音频探测、schema 校验、状态机、重试、进度、ffmpeg、缓存和 QC 均不调用模型。
3. Job Supervisor 是零 token 组件。它只响应事件、执行队列和记录状态，禁止用模型轮询进度。
4. 低成本模型只处理白名单语义任务；强模型只处理架构、创意总控、冲突、升级和最终独立审查。
5. 本地 Codex CLI 的优势是可以在用户授权范围内读取项目文件、运行工具并产出结构化结果。它并不天然比同模型的 HTTP API 更“聪明”；能力增益来自工具、上下文、sandbox 和可恢复执行。媒体生成仍通过 provider adapter 调用相应服务。
6. 所有入口只提交结构化请求，禁止 Web 传入任意 shell、cwd、环境变量或 Codex flags。
7. 应用源码和内置资源只读；用户项目位于用户工作区的 `projects/<project_slug>/`，应用状态位于 `<workspace>/.mvstudio/`。项目数据、日志、缓存、临时文件和输出不得写入源码仓库。
8. `pipeline/` 是待逐文件分类迁移的 legacy 混合目录，不是新代码、新项目或新输出的落点。完整约束以 [`LOCAL_MV_STUDIO_DIRECTORY_CONTRACT.md`](LOCAL_MV_STUDIO_DIRECTORY_CONTRACT.md) 为准。
9. 首轮实现只交付 M0-M1 基座。旧 `mv_engine`、`mingyue_render.py` 和现有成片路径保持不变，后续通过 adapter 迁移。

## 2. 用户体验

三个入口提供相同能力：创建项目、校验物料、启动阶段、读取事件、取消任务、确认拍板点、重试失败阶段、查看和导出产物。

```text
Web UI ───────┐
mvstudio CLI ─┼─> Application Service ─> Job Supervisor ─> Stage Executors
Codex adapter ┘            │                    │
                           ├─ SQLite events     ├─ deterministic Python
                           └─ Artifact registry ├─ bounded model tasks
                                                └─ media providers
```

Web 通过本机 `127.0.0.1` 的 REST + SSE 使用服务。CLI 默认进程内调用 Application Service；如本地 API 已启动，也可显式使用 API 模式。Codex adapter 只生成或提交同一 `JobRequest`，不得包含渲染分支。

## 3. 业务状态机

```text
intake_pending
  -> intake_validated
  -> maps_generated
  -> story_framework_pending_user
  -> story_framework_approved
  -> visual_score_pending_user
  -> visual_score_approved
  -> keyframes_pending_user
  -> keyframes_approved
  -> generation_pending
  -> generation_partial
  -> generation_approved
  -> compositing_pending
  -> qc_passed
  -> exported
```

任一阶段可进入 `blocked`、`failed` 或 `cancelled`。上游输入、用户选择或合同 hash 变化时，下游版本进入 `superseded`，不得覆盖已经批准的产物。

用户必须在三个位置明确拍板：

- 故事框架：人物关系、情绪推进、能量峰值、结尾回收。
- 视觉总谱：逐镜描述、关键转场、生成与确定性包装的路由。
- 关键帧：可单选一个镜头，也可批量选择多个镜头生成候选；每个高风险镜头最终绑定一个批准版本。

用户未批准时状态保持 `awaiting_approval`/`blocked`，自动流程不得越过门禁。

## 4. 核心输入与产物

项目 intake 最少包含：

- `brief.json`：目标平台、画幅、风格边界、人物定义、隐私与 provider consent。
- 一份 mp3/wav 原曲。
- LRC、带时间歌词或纯文本歌词；纯文本须生成并确认对齐结果。
- 一张或多张人物源图，资产登记为 `source_portrait`。

导演链的 canonical artifacts：

```text
brief.json
beats.json
lyrics_timed.json
music_map.yaml
character_map.yaml
story_framework.yaml
visual_score.yaml
asset_plan.yaml
generation_plan.yaml
storyboard.md
shots.yaml
shots.solved.yaml
animatic.mp4
qc_report.json
final.mp4
```

每个 artifact 必须登记 `schema_version`、`artifact_id`、`project_id`、`job_id`、`input_hashes`、`content_hash`、`created_at`、`producer` 和 `status`。批准记录另含 `approved_by`、`approved_at`、`approved_hash`。

## 5. Editorial Shot 与 Generation Clip

`EditorialShot` 是最终剪辑时间轴单位，可以短于 4 秒；`GenerationClip` 是媒体模型提交单位，必须满足 provider 的最短时长，例如 Seedance 2 的 4 秒约束。两者禁止混为同一对象。

```yaml
editorial_shot:
  shot_id: shot_017
  timeline_in_ms: 18420
  timeline_out_ms: 20420
  duration_ms: 2000
  lyric_span: [line_08]
  transition_in: beat_cut
  transition_out: shared_element

generation_clip:
  clip_id: clip_009
  duration_ms: 4000
  source_shot_ids: [shot_017]
  usable_range_ms: [900, 2900]
  head_handle_ms: 900
  tail_handle_ms: 1100
  first_frame_ref: artifact://keyframe_017_a
  last_frame_contract:
    exit_state: subject_faces_right
    shared_element: red_ribbon
```

短镜头的处理优先级：

1. 生成 4 秒以上素材，使用中间稳定区间并保留头尾 handles。
2. 把视觉和动作连续的相邻 editorial shots 合并到一个 generation clip，再在合成层切开。
3. 用批准的首帧/尾帧冻结、确定性 2.5D 或转场占用剩余时长。
4. 只有用户明确选择时才用空白占位；正式导出不得默认黑帧补齐。

`generation_plan.yaml` 必须同时保存 shot 到 clip 的多对多映射、首尾帧连续性合同、选用区间和失败降级方案。

## 6. 分层架构

目录分为应用代码、应用状态和用户项目三类。目标代码采用可安装包，普通用户只通过 Web、CLI 或 Codex 入口使用功能，不修改源码：

```text
apps/
  mv_api/                 # FastAPI REST、SSE，只做协议适配
  mv_cli/                 # mvstudio 命令，只做协议适配
  mv_codex/               # 受控 Codex 任务适配器
src/mvstudio/
  domain/                 # immutable contracts、状态和错误
  application/            # create/submit/approve/cancel/inspect
  infrastructure/         # SQLite、artifact、locks、events
  supervisor/             # 零 token 队列、worker、恢复
  executors/              # Python、Codex、media provider
  engines/                # 可复用确定性渲染能力
  providers/              # image、TTS、video provider adapters
  workflows/              # 产品工作流编排
  resources/              # 随应用发布的只读 schema、模板和默认资源

<user-workspace>/
  .mvstudio/              # SQLite、jobs、cache、service logs
  projects/<project_slug>/
    inputs/               # 用户提供的原料
    creative/             # 可编辑项目合同
    assets/               # 项目专属源素材与生成素材
    outputs/              # animatic、final 和 QC 报告
    .mvstudio/            # 项目级 staging、work 和 logs
```

依赖方向只能是 `interfaces -> application -> domain`；infrastructure 和 executors 实现 application ports。入口层不得 import `mingyue_render`、片级 renderer、multiprocessing 或自行拼 ffmpeg 命令。

当前 `apps/` 与 `mv_platform/` 是 M0-M1 过渡布局；迁入 `src/mvstudio/` 时必须逐模块完成，不能把整个 `pipeline/` 原样搬入包。公共代码、只读 golden fixture、单片项目数据和可清理输出须按目录合同分别归类。

## 7. Job 与事件合同

`JobSpec` 在创建后不可变，至少包含：

```yaml
job_id: job_...
project_id: project_...
operation: analyze | compile | animatic | generate | render | qc | export
input_refs: []
input_digest: sha256:...
pipeline_version: ...
contract_version: ...
model_policy_ref: ...
privacy_consent_ref: ...
requested_outputs: []
idempotency_key: ...
```

运行状态为 `queued -> running -> succeeded|failed|blocked|cancelled`，业务阶段作为单独字段，不将两套状态机揉成一个枚举。事件表以 `(job_id, seq)` 唯一，sequence 从 1 单调递增。SSE 通过 `Last-Event-ID` 从 SQLite 补发，内存广播不是事实源。

Supervisor 使用 `spawn` 子进程和白名单 argv。每个 job 有独立 staging 目录；产物完成 schema、hash 和 QC 后才原子发布。重复提交用 `job_id + operation + input_digest + contract_version` 幂等，重试创建新 attempt，不重复提交已有 provider request。

## 8. 模型路由与成本纪律

### 8.1 Python 必做

- 文件枚举、hash、格式/尺寸/时长探测、音频特征和 beat 候选。
- JSON/YAML schema 校验、状态迁移、依赖失效、任务重试和进度汇总。
- ffmpeg 合成、裁切、音轨对齐、黑帧/冻结/响度/时长/画幅 QC。
- 缓存、manifest、artifact registry、日志压缩和 secret 脱敏。

### 8.2 低成本模型事件白名单

- `lyrics.semantic_segment.requested`
- `relationship_map.draft_requested`
- `story_framework.draft_requested`
- `shot_description.expand_requested`
- `prompt.normalize_requested`
- `qc.report_summarize_requested`

每次调用必须记录 `event_type`、`model`、`budget`、`reason`、输入合同 hash 和输出 schema hash。默认模型为配置项，例如 `gpt-5.6-luna`；文档不得假设模型名永远可用，启动时必须 doctor 校验。

### 8.3 强模型升级白名单

- 合同连续两次 schema 失败。
- 歌词、人物关系或用户约束发生不可自动裁决的冲突。
- 隐私、授权或外传范围不明确。
- 视觉总谱或最终验收需要跨镜创意判断。
- 同一媒体任务重试耗尽，证据表明不是瞬时 provider 故障。

升级必须携带 `escalation_reason`、失败证据 digest、attempt count 和预算。建议强模型/审查模型通过配置指定，例如 `gpt-5.6-terra`。

### 8.4 低成本 worker 任务包

便宜模型不得从仓库根目录启动并自动继承全部 `AGENTS.md`、40+ memory 和无关文件。编排器在仓库外的临时工作目录创建只读任务包：

```text
task_packet/
  TASK.md                  # 单一目标和禁止事项
  INPUT_MANIFEST.json      # 文件白名单与 sha256
  CONTRACT.json            # 输入/输出 schema
  ACCEPTANCE.md            # 冻结的验收命令
  refs/                    # 只复制本任务需要的片段
  output/                  # 唯一可写目录
```

worker 必须使用 `--ephemeral`、受限 sandbox、固定 cwd、JSONL 和 output schema。任务包 manifest hash、模型和 CLI 版本进入审计日志。worker 不能提交 git、修改规则、扩大路径或自行降低验收标准。

## 9. 本地 Codex 安全边界

- API 默认只绑定 `127.0.0.1`；公网监听必须是另一个明确产品决策。
- Web 只提交 operation 和结构化参数，服务端将其映射成固定 argv 数组；不调用 shell。
- Codex cwd 指向任务包，不指向仓库根；仅把 allowlisted 输入以只读副本放入 `refs/`。
- 子进程环境变量采用 allowlist，禁止继承 cookies、无关 keys 和用户 shell 环境。
- 路径解析后再次检查 realpath；拒绝 `..`、外部绝对路径、符号链接逃逸、NUL 和未知扩展。
- `source_portrait` 默认不上传。任何媒体外传都要求按 provider 和用途记录 consent。
- stdout、stderr、JSONL 和 provider error 在落盘前脱敏；未知 JSONL 事件可记录但不得导致 false success。

## 10. API 与 CLI

首版 API：

```text
POST /api/v1/projects
POST /api/v1/projects/{project_id}/jobs
GET  /api/v1/jobs/{job_id}
GET  /api/v1/jobs/{job_id}/events
POST /api/v1/jobs/{job_id}/cancel
POST /api/v1/jobs/{job_id}/director/animatic-test
GET  /api/v1/jobs/{job_id}/artifacts
GET  /healthz
GET  /readyz
```

首版 CLI：

```text
mvstudio doctor --json
mvstudio project create --brief <path> --json
mvstudio job submit --project <id> --operation <op> --json
mvstudio job inspect <job_id> --json
mvstudio job events <job_id> --follow
mvstudio job cancel <job_id>
mvstudio job director-animatic-test <job_id> --json
```

The structural Animatic action requires an operation=animatic Job with one
project audio input, one timed LRC input, and one or more project character
images. It writes runtime files only under <workspace>/.mvstudio/jobs/<job_id>
and publishes the explicitly non-approved preview to
projects/<slug>/outputs/structural_animatic_<job_id>.mp4.

同一 canonical brief 从 Web、CLI 和 Codex 提交时，`brief_sha256`、`pipeline_version` 和 `job_spec_sha256` 必须一致。

## 11. 交付里程碑

- M0 可启动骨架：配置、domain contracts、SQLite migration、health/ready、CLI doctor。
- M1 Job Supervisor：提交、事件、SSE、取消、恢复、artifact registry，使用 fake executor 完成 E2E。
- M2 Legacy adapter：先通过目录合同门禁，再冻结只读明月 golden，提供显式 Session 和 canvas，验证两个并发 job 零串写且源码树零写入。
- M3 导演编译器：三输入到 maps、story framework、visual score、generation plan 和 540p Animatic。
- M4 正式生成与合成：关键帧选择、provider adapters、逐镜诊断、转场和 final QC。
- M5 三入口产品化：Web 工作台、重试/版本比较、导出包和完整本地安装体验。

每个里程碑独立验收；前一里程碑未通过，不得把下一里程碑的代码混入同一任务。

M2 的额外前置门禁见 [`LOCAL_MV_STUDIO_DIRECTORY_CONTRACT.md`](LOCAL_MV_STUDIO_DIRECTORY_CONTRACT.md)：默认工作区必须位于仓库外，显式把源码根设为工作区必须 fail-closed，公共能力不得继续写入 `pipeline/voice_room` 或片名目录。

## 12. M0-M1 冻结验收

1. `python3 -m pytest tests/mv_platform -q` 全部通过。
2. API 可在 `127.0.0.1` 启动，`/healthz` 返回 alive；SQLite migration、写目录和 worker 初始化都正常时 `/readyz` 才返回 ready。
3. CLI 和 API 提交同一 fixture，三个 digest 完全一致。
4. fake executor 跑通 `queued -> running -> succeeded`，事件 sequence 连续且重启后可补发。
5. 取消运行中 job 后 worker 被回收，状态唯一为 `cancelled`；临时产物不进入 artifact registry。
6. 重复提交同一幂等键不会产生第二次副作用；失败重试保留旧 attempt 和证据。
7. Supervisor 的模型/token counter 恒为 0。
8. 两个并发 fake jobs 的 staging、事件、artifact 和日志交叉引用为 0。
9. 安全 fixtures 中 shell 注入、路径穿越、符号链接逃逸、未授权 env 和 secret 日志全部被拒绝或脱敏。
10. `rg -n "mingyue_render|paperdoll_engine|render_frame|multiprocessing|ffmpeg" apps/mv_api apps/mv_cli apps/mv_codex` 无入口层业务实现命中。

## 13. 已知限制

- M0-M1 只证明本地任务平台成立，不代表导演编译器或正式 MV 已完成。
- SQLite 目标是单机本地，不支持多机队列；未来可替换 repository 和 queue adapter。
- 本地 Codex 仍可能产生错误结构化结果，所有输出必须经过 schema 和独立验收。
- 540p Animatic 只用于结构拍板，不能代替正式分辨率的视觉、palette、motion 和 media gates。
- 现有 `mv_engine` 存在固定 canvas、模块全局 session 和明月硬编码；必须在 M2 以 golden adapter 渐进迁移。

## 14. 来源子 PRD

- `docs/design/subagent_prds/local_mv_studio/system_architect.md`
- `docs/design/subagent_prds/local_mv_studio/workflow_contract_designer.md`
- `docs/design/subagent_prds/local_mv_studio/agent_runtime_architect.md`

主文档冲突裁决：业务状态与 job 运行状态分离；Web 可选但 API 作为 Web 的本地服务；CLI 不依赖 API 进程；首轮不迁移渲染引擎；低成本 worker 使用仓库外精简任务包。
