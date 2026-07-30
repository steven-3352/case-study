role: 独立系统架构师

production_tier: full

input_received:
  resources:
    - AGENTS.md
    - docs/RULES/README.md
    - docs/RULES/00_NORTH_STAR.md 至 docs/RULES/11_MV_DIALOGUE_PLAYBOOK.md
    - docs/RULES/decisions/
    - docs/RULES/memory/ 全部文件
    - .agents/skills/paperdoll-mv-packaging/SKILL.md
    - pipeline/mv_engine/
    - pipeline/paperdoll/
    - pipeline/voice_room/mingyue_render.py
    - pipeline/voice_room/mingyue/
    - pipeline/voice_room/paperdoll_engine.py
    - requirements.txt
    - pipeline/requirements.txt
    - .env.example
  upstream_artifacts:
    - docs/design/WORKFLOW_EXECUTION_LOG.md 最近记录
    - templates/design/subagent_prd_schema.md
  known_gaps:
    - gap: 当前没有 FastAPI、SQLite job supervisor、SSE 或统一 Web/CLI/Codex 服务入口
      user_decision: 以本 PRD 设计目标为准，保持只读分析，不在本次实现
    - gap: mv_engine.session 仍使用模块级 _CURRENT 单例
      user_decision: 迁移为显式注入的 JobSession，兼容旧调用但禁止新入口依赖全局状态
    - gap: pipeline/voice_room/mingyue_render.py 固定引用 publish/语音厅、明月天涯、固定音频和字体
      user_decision: 迁移到项目实例目录和声明式 manifest，保留旧片作为 golden reference
    - gap: pipeline/mv_engine/tools/render_cached.py、track.py、mingyue/layouts.py 仍直接 import mingyue_render
      user_decision: 以适配器过渡，最终由 film package 实现 render contract
    - gap: paperdoll skill 已有导演合同和视觉校验器，但缺少 music_map/character_map 到 shots/build_shots 的完整编译链
      user_decision: 分阶段交付，先打通 validated 540p Animatic，再接正式渲染
    - gap: 当前代码中的 paperdoll_engine.py 使用 random，和 MV 引擎无随机数铁律冲突
      user_decision: 统一改为 seed 派生的确定性序列，并纳入原子锁与回归验收

deliverable: |
  一份面向 clone 后本地启动的 MV 制作平台架构子 PRD。

  目标是让 Web、CLI、Codex 三个入口只负责输入契约、提交 job、查看状态和读取产物，
  三者共享同一个 domain/application/core pipeline，不复制渲染逻辑。

  推荐目录：

  ```text
  apps/
    mv_api/
      main.py
      dependencies.py
      routes/
        projects.py
        jobs.py
        artifacts.py
        events.py
      schemas.py
      sse.py
    mv_cli/
      __main__.py
      commands.py
    mv_codex/
      adapter.py
      commands.py

  mv_platform/
    domain/
      brief.py
      manifest.py
      job.py
      events.py
      errors.py
    application/
      create_project.py
      create_job.py
      run_pipeline.py
      inspect_job.py
      cancel_job.py
    infrastructure/
      sqlite.py
      repositories.py
      artifact_store.py
      event_store.py
      locks.py
    supervisor/
      supervisor.py
      worker_process.py
      resource_policy.py

  pipeline/
    mv_engine/                 # 共享确定性渲染核心
    paperdoll/                 # 共享包装能力和探针
    mv_adapters/
      legacy_mingyue.py        # 过渡期旧片适配器
      paperdoll_manifest.py
    voice_room/
      <project_slug>/
        brief.json
        project.yaml
        music_map.yaml
        character_map.yaml
        visual_score.yaml
        asset_plan.yaml
        storyboard.md
        shots.yaml
        shots.solved.yaml
        solver_report.md
        assets/
        build/
        artifacts/
        logs/

  data/
    app.sqlite3
    cache/
      mv_engine/
    jobs/
    projects/

  tests/
    unit/
    integration/
    contract/
    golden/
  ```

  项目实例必须以 `pipeline/voice_room/<project_slug>/` 为唯一内容边界。
  不允许新入口读写 `publish/语音厅` 或使用 `mingyue` 作为默认项目名。
  `publish/` 只作为历史 golden reference 或外部交付目录，不作为运行时工作目录。

perceptual_goal:
  statement: |
    用户从任一入口提交同一份 brief 后，都能看到同一条可追踪的制作进度，
    并在产物目录中获得可播放的粗剪、逐镜验收报告和最终视频；不同 job 的事件、
    帧、缓存链接和失败日志不会互相串写。
  observable_metric: |
    对同一 canonical brief，Web、CLI、Codex 三入口生成的 `brief_sha256`、
    `pipeline_version` 和 `job_spec_sha256` 必须完全一致；同一 job 的 SSE/CLI
    事件序号从 1 单调递增且无重复；并发运行 N=2 个项目时，两个 job 的所有
    `project_root`、`_frames`、`motion.json`、SQLite `job_id` 和最终 artifact
    路径均只包含各自 job 标识，交叉引用数必须为 0；每个正式镜头的预测轨迹
    在任意连续 2 秒窗口内满足中心位移峰值 >= 4% 画面宽，或主体面积变化峰值 >= 8%，
    且跨镜运镜族至少 6 种、转场至少 5 种、任一单一族占比 <= 50%。
    这些是路径、事件、哈希、计数、像素和轨迹数值，不以“动画感”“视差”等效果名作为指标。

implementation_approach:
  method: |
    采用四层架构：

    1. Interface Layer
       - Web：FastAPI REST + SSE。
       - CLI：调用同一 application service，默认输出人类可读文本，可选 JSON。
       - Codex：调用同一 CLI/application contract；不直接 import 渲染细节。
       - 三入口均只提交 `brief.json`、项目 slug、运行选项和取消/查询操作。

    2. Application Layer
       - `CreateProject`：校验输入、建立项目目录、生成 canonical brief。
       - `CreateJob`：创建不可变 job spec，写入 SQLite，返回 job_id。
       - `RunPipeline`：按阶段执行需求契约、导演地图、视觉总谱、Animatic、正式渲染和验收。
       - `InspectJob`：读取状态、阶段、日志游标和 artifact manifest。
       - `CancelJob`：写入 cancel_requested，监督器在阶段边界和 worker 回收点执行取消。

    3. Domain/Infrastructure Layer
       - SQLite 只保存 job 元数据、状态、事件、artifact 索引和错误摘要，不保存帧二进制。
       - SQLite 开启 WAL、foreign_keys、busy_timeout；所有写操作短事务完成。
       - 事件表使用 `(job_id, seq)` 唯一键；SSE 使用 `Last-Event-ID` 断点续传。
       - artifact store 只接受 job-scoped 绝对路径，并生成 sha256、大小、mime、阶段和生成时间。
       - cache store 继续使用 `mv_engine.cache` 的内容寻址 key、原子临时文件和 hardlink/copy fallback。

    4. Execution Layer
       - Supervisor 是唯一允许启动渲染子进程的组件。
       - 每个 job 使用独立的 `spawn` 进程；禁止 fork。
       - job 子进程只接收可序列化 `JobSpec`，自行初始化 `JobSession`、素材缓存和日志。
       - job 内部帧 worker 继续由渲染器按内存上限启动，默认 jobs=4，上限由资源策略限制。
       - 任何任务失败都写入结构化错误事件和 `failure.json`，不得只依赖 stdout。

    FastAPI API 合同：

    ```text
    POST /api/v1/projects
    POST /api/v1/projects/{project_id}/jobs
    GET  /api/v1/jobs/{job_id}
    GET  /api/v1/jobs/{job_id}/events
    POST /api/v1/jobs/{job_id}/cancel
    GET  /api/v1/jobs/{job_id}/artifacts
    GET  /api/v1/artifacts/{artifact_id}
    GET  /healthz
    GET  /readyz
    ```

    SSE 事件至少包括：

    ```json
    {
      "id": "42",
      "event": "stage.progress",
      "data": {
        "job_id": "job_...",
        "stage": "render",
        "status": "running",
        "completed": 128,
        "total": 438,
        "message": "frame batch completed"
      }
    }
    ```

    状态机：

    ```text
    queued
      -> preparing
      -> mapping
      -> visual_score_validated
      -> animatic
      -> awaiting_approval
      -> rendering
      -> validating
      -> succeeded

    queued/preparing/mapping/animatic/rendering/validating
      -> cancel_requested
      -> cancelled

    任意运行态
      -> failed
    ```

    并发隔离规则：

    - `project_id` 是内容隔离边界，`job_id` 是运行隔离边界。
    - 同一个 project 默认只允许一个 active job；显式 A/B 才创建不同 immutable job。
    - 每个 job 使用 `data/jobs/{job_id}/` 临时目录，正式产物发布到项目目录前先完成校验。
    - 禁止模块级 `_PATHS`、`_CURRENT`、`_DOLL`、`_LAYER` 跨 job 共享可变状态。
    - `Session`、素材根、纹理根、输出根、cache root 全部由构造器注入。
    - 共享帧缓存可以跨 job 复用，但 key 必须包含 pipeline version、render config、
      film manifest digest、素材 fingerprint 和完整 shot/item/fx 描述。
    - SQLite 事件只允许 supervisor 写入，worker 通过受控 IPC/队列回传事件。
    - 取消 job 不删除共享缓存，只清理该 job 的临时硬链接和未发布产物。

    从 `mingyue` 迁移：

    - Phase 1：冻结旧片基线。
      - 保留 `pipeline/voice_room/mingyue_render.py` 和 `mingyue/`。
      - 用现有 `render_cached`、`verify_track`、`assert_items` 建立 golden hash、
        motion track、solver report 和 gate report。
    - Phase 2：抽取 film contract。
      - 新建 `FilmManifest`：canvas、fps、audio、assets、textures、fonts、shots、
        palette、lyrics、output slug。
      - 将 `ASSETS`、`TEX`、`GEN`、`OUT`、`WAV`、`FONT_BRUSH`、`_LYR_JSON`
        从模块常量移入 manifest。
      - 将 `render_frame(t, shots, version)` 改为接收 `RenderContext`。
    - Phase 3：消除旧全局依赖。
      - `mv_engine.session.configure()` 保留兼容入口，但新路径使用 `Session(...)`。
      - `paperdoll_engine.PVPaths` 替换模块级 `_PATHS` 读取。
      - `mingyue/layouts.py` 由旧适配器过渡到 `FilmManifest.layout_registry`。
      - `track.py` 只依赖共享 camera/geometry contract，不再 import `mingyue_render`。
    - Phase 4：声明式纸片人项目。
      - 读取 `brief.json`、`music_map.yaml`、`character_map.yaml`、
        `visual_score.yaml`、`asset_plan.yaml`。
      - 编译为 `shots.yaml` 和 `build_manifest.json`。
      - 运行 `validate_visual_score.py`，失败即禁止后续渲染。
    - Phase 5：统一渲染和验收。
      - 使用共享 `mv_engine.render`、`cache`、`track`、`paperdoll.probes`。
      - 旧明月实现只作为 `LegacyMingyueAdapter` 和 golden reference。
      - 达到逐帧 hash、bbox 偏差和 gate report 一致后，才删除新路径对旧模块的依赖。
    - Phase 6：交付入口。
      - Web、CLI、Codex 只消费 application service。
      - 禁止入口直接调用 `mingyue_render.render()` 或 `paperdoll_engine.render()`。

  分阶段交付：

    - M0：可启动骨架
      - clone 后能建立 venv、启动 FastAPI、执行 CLI、访问 healthz。
      - SQLite migration、配置加载和项目目录创建可用。
    - M1：Job supervisor
      - queued/running/succeeded/failed/cancelled 状态机可用。
      - 单 job 可通过 CLI 和 API 创建并查看。
      - SSE 支持实时事件和断线续传。
    - M2：Legacy adapter
      - 明月样段通过 manifest 运行。
      - 输出与当前 golden reference 对齐。
      - 两个并发 job 不发生目录和事件污染。
    - M3：导演编排链
      - 三输入生成 music_map、character_map、visual_score、asset_plan。
      - visual score 校验失败 fail-closed。
      - 540p Animatic 可观看并生成 artifact manifest。
    - M4：正式纸片人渲染
      - 接入共享原子、style pack、poster、background、probes。
      - 完成 frame cache、motion.json、palette gate、motion gate。
    - M5：三入口一致性与发布
      - Web/CLI/Codex 产生相同 job spec。
      - 支持重试、取消、恢复、A/B job 隔离。
      - 最终视频和验收证据都进入项目目录，发布路径由 manifest 决定。

  建议配置：

  ```text
  MV_DATA_ROOT=data
  MV_PROJECT_ROOT=pipeline/voice_room
  MV_CACHE_ROOT=data/cache/mv_engine
  MV_DB_PATH=data/app.sqlite3
  MV_MAX_ACTIVE_JOBS=1
  MV_RENDER_WORKERS=4
  MV_SSE_HEARTBEAT_SECONDS=15
  MV_JOB_TIMEOUT_SECONDS=21600
  MV_FFMPEG_BIN=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
  ```

why_this_fits_perceptual_goal: |
  三入口共用不可变 job spec 和同一 application service，可避免 Web、CLI、Codex
  各自解释 brief、各自拼装路径或各自复制渲染参数。每个 job 的事件序号、artifact
  manifest、预测轨迹和 gate report 都是可观察证据，能直接验证“提交后发生了什么”和
  “最终画面是否真的产生了可量化变化”。

  现有 mv_engine 已经具备相机模型、FRAMING 表、解析式 bbox、H1-H7 求解约束、
  内容寻址帧缓存和 spawn worker 的核心能力，因此服务层应围绕它编排，而不是另写一套
  渲染器。现有 `paperdoll` skill 的三级检查也要求原子、镜头、帧分层，适合映射为
  application stage 和 job artifact。

alternatives_considered:
  - option: 三个入口分别实现一套渲染和任务逻辑
    why_rejected: 会造成 Web/CLI/Codex 的参数、状态、路径和验收口径漂移，无法保证同一 brief 产生同一 job spec，也会复制现有明月硬编码问题。
  - option: 只做 CLI，Web 和 Codex 直接包装 CLI 子进程
    why_rejected: CLI 输出不是稳定的领域 API；SSE、断线续传、结构化 artifact 查询、取消和错误恢复会被文本解析绑架。
  - option: 使用 Redis/Celery 或 PostgreSQL 作为首版 supervisor 后端
    why_rejected: clone 后本地启动需要低依赖；当前任务以单机 macOS、SQLite、spawn 和本地文件产物为主，SQLite WAL 足以支撑 MVP。未来多主机部署再替换 repository/queue adapter。
  - option: 直接把 mv_engine 改成全局无状态函数，不保留 Session
    why_rejected: 素材缓存、路径注入、spawn 初始化和跨 job 隔离都需要运行时上下文；显式 Session 更适合测试和并发隔离。

known_limitations:
  - limitation: 当前仓库没有可直接启动的 FastAPI 应用、数据库 migration 或 supervisor
    impact: M0-M1 需要新增服务代码和测试，不能用当前仓库命令直接验证完整三入口链路
  - limitation: 旧 `mingyue_render.py`、`paperdoll_engine.py` 依赖模块级可变状态和绝对/固定项目路径
    impact: 迁移期间必须保留 legacy adapter；过早删除旧模块会破坏 golden reference
  - limitation: `mv_engine.track` 的部分几何契约仍通过旧 `mingyue_render` 校准
    impact: 迁移时必须逐字节比较预测轨迹和真实轨迹，否则可能出现 gate report 看似通过但轨迹漂移
  - limitation: 当前 `paperdoll_engine.py` 含随机数和片级一次性脚本
    impact: 未完成确定性改造前，不应宣称多 job 可复现或跨入口结果完全一致
  - limitation: SQLite 不适合跨机器高吞吐队列
    impact: 目标范围限定为 clone 后本地单机；未来云端部署需替换 supervisor repository/queue
  - limitation: SSE 不能替代持久化事件
    impact: 客户端断线必须从 SQLite 事件表按 `Last-Event-ID` 补发，不能只依赖内存广播
  - limitation: 540p Animatic 与正式 1080p/1920p 成片的视觉结论不完全等价
    impact: Animatic 只用于早期动态和构图拍板，正式片仍必须运行完整机器门、抽帧和独立验收
  - limitation: 共享 cache 的素材 fingerprint 若只依赖 mtime，存在素材内容未变时间变化或反向覆盖风险
    impact: 正式版必须使用文件 sha256；MVP 至少记录 size、mtime_ns，并在 manifest 变更时失效缓存

acceptance_criteria:
  - criterion: clone 后可完成本地初始化并启动 API
    how_to_verify: |
      ```bash
      git clone <repo-url> case-study
      cd case-study
      python3 -m venv .venv
      . .venv/bin/activate
      pip install -r requirements.txt
      python3 -m pip install fastapi uvicorn
      uvicorn apps.mv_api.main:app --host 127.0.0.1 --port 8787
      curl -fsS http://127.0.0.1:8787/healthz
      curl -fsS http://127.0.0.1:8787/readyz
      ```
      预期：两个 endpoint 返回 JSON，进程不依赖 `publish/语音厅` 才能启动。

  - criterion: 三入口提交同一 brief 得到同一规范化 job spec
    how_to_verify: |
      ```bash
      python3 -m apps.mv_cli create-job --brief fixtures/brief.json --json
      curl -fsS -X POST http://127.0.0.1:8787/api/v1/jobs \
        -H 'content-type: application/json' \
        --data @fixtures/brief.json
      python3 -m apps.mv_codex submit --brief fixtures/brief.json --json
      ```
      读取三个响应中的 `brief_sha256`、`pipeline_version`、`job_spec_sha256`；
      三组值必须完全一致。

  - criterion: SQLite job 状态机和事件顺序正确
    how_to_verify: |
      ```bash
      python3 -m pytest tests/integration/test_job_state_machine.py -q
      sqlite3 data/app.sqlite3 \
        "select job_id,seq,event_type from job_events order by job_id,seq;"
      ```
      每个 job 的 seq 从 1 开始、连续递增、无重复；非法状态迁移必须返回 409。

  - criterion: SSE 支持实时订阅和断线续传
    how_to_verify: |
      ```bash
      curl -N http://127.0.0.1:8787/api/v1/jobs/<job_id>/events
      curl -N -H 'Last-Event-ID: 10' \
        http://127.0.0.1:8787/api/v1/jobs/<job_id>/events
      ```
      第二次连接必须从 seq=11 开始补发，并最终收到 terminal event。

  - criterion: 两个并发 job 完全隔离
    how_to_verify: |
      ```bash
      python3 -m pytest tests/integration/test_concurrent_job_isolation.py -q
      find data/jobs -maxdepth 3 -type f | sort
      ```
      测试启动两个不同 project、不同素材和不同输出名的 job；检查文件内容中的
      `job_id`、`project_id`、manifest digest 和 SQLite event job_id，交叉引用数必须为 0。

  - criterion: supervisor 使用 spawn，且资源上限生效
    how_to_verify: |
      ```bash
      python3 -m pytest tests/integration/test_supervisor_spawn.py -q
      python3 -m apps.mv_cli doctor --json
      ```
      失败条件包括检测到 fork、worker 数超过配置上限、取消后 worker 未回收、
      或单进程 RSS 超过资源策略阈值。

  - criterion: 明月 legacy adapter 与 golden reference 对齐
    how_to_verify: |
      ```bash
      python3 -m pipeline.mv_engine.tools.assert_items
      python3 -m pipeline.mv_engine.tools.verify_track \
        --truth-root .cache/mv_engine/baseline --version a b
      python3 -m pipeline.paperdoll.probes selftest
      ```
      预期：items contract 通过；预测轨迹中心偏差 p95 < 0.2%W、max < 1%W；
      预测轨迹与真实轨迹的 gate report 逐字一致；paperdoll 探针及 8 个反例符合预期。

  - criterion: 声明式导演链 fail-closed
    how_to_verify: |
      ```bash
      python3 .agents/skills/paperdoll-mv-packaging/scripts/validate_visual_score.py \
        pipeline/voice_room/<project_slug>/visual_score.yaml
      python3 -m apps.mv_cli run --project pipeline/voice_room/<project_slug> \
        --stage animatic
      ```
      删除一个必填字段后，校验命令必须非 0，job 状态必须为 failed/blocked，
      且不得生成正式背景、i2v、正式帧或 final.mp4。

  - criterion: 540p Animatic 产物完整且可播放
    how_to_verify: |
      ```bash
      python3 -m apps.mv_cli run \
        --project pipeline/voice_room/<project_slug> \
        --stage animatic
      ffprobe -v error -show_entries stream=width,height,r_frame_rate \
        -of default=noprint_wrappers=1 \
        pipeline/voice_room/<project_slug>/build/animatic.mp4
      ```
      必须生成 `music_map.yaml`、`character_map.yaml`、`visual_score.yaml`、
      `asset_plan.yaml`、`shots.yaml`、`keyframes_preview.png` 和 `animatic.mp4`；
      540p 视频可被 ffprobe 读取，帧率与 manifest 一致。

  - criterion: 正式渲染具备缓存、运动轨迹和原子产物
    how_to_verify: |
      ```bash
      python3 -m apps.mv_cli run \
        --project pipeline/voice_room/<project_slug> \
        --stage render
      test -f pipeline/voice_room/<project_slug>/build/motion.json
      test -f pipeline/voice_room/<project_slug>/build/index.json
      python3 -m pipeline.mv_engine.tools.frame_digest \
        pipeline/voice_room/<project_slug>/build
      ```
      冷跑产生完整帧和 index；热跑只计算 key 并 hardlink/copy；
      任意 PNG 不得出现半写文件；`motion.json` 即使 100% cache hit 也必须生成。

  - criterion: 正式镜头满足单镜可见变化和跨镜多样性
    how_to_verify: |
      ```bash
      python3 -m pipeline.gate_check_motion \
        pipeline/voice_room/<project_slug>/build/motion.json
      python3 -m pipeline.paperdoll.probes shot \
        pipeline/voice_room/<project_slug>/build/frames \
        --track pipeline/voice_room/<project_slug>/build/motion.json
      python3 -m pipeline.gate_check_palette \
        --declared "<manifest.palette_gate_arg>" \
        pipeline/voice_room/<project_slug>/build/frames/*.png
      ```
      任何连续 2 秒窗口必须有跨镜切换，或主体中心位移峰值 >= 4%画面宽，
      或主体面积变化峰值 >= 8%；同时验证运镜族、转场族和版式分布，不允许
      单一手法超过 50%。所有门必须 fail-closed。

  - criterion: 失败、取消和重试不会污染项目目录
    how_to_verify: |
      ```bash
      python3 -m pytest tests/integration/test_cancel_retry_cleanup.py -q
      ```
      取消 job 后状态为 cancelled，worker 已回收，临时目录可清理，共享 cache 保留；
      重试生成新的 job_id 和 job_spec，不覆盖旧 job 的 artifact manifest 或事件。

  - criterion: 三入口不包含渲染分支逻辑
    how_to_verify: |
      ```bash
      rg -n "mingyue_render|paperdoll_engine|render_frame|multiprocessing|ffmpeg" \
        apps/mv_api apps/mv_cli apps/mv_codex
      ```
      入口层不得直接 import 片级渲染器、启动 worker 或拼接 ffmpeg 命令；
      这些调用只能出现在 application/supervisor/pipeline adapter 层。

  - criterion: 交付证据可独立复核
    how_to_verify: |
      ```bash
      python3 -m apps.mv_cli inspect <job_id> --json
      python3 -m apps.mv_cli artifacts <job_id>
      sha256sum pipeline/voice_room/<project_slug>/build/final.mp4
      ```
      输出必须包含 job spec digest、source asset fingerprints、pipeline code digest、
      render config、motion gate、palette gate、probe 和最终 artifact sha256。
      验收者只需读取这些产物和 `acceptance_criteria`，不依赖实现者口头说明。