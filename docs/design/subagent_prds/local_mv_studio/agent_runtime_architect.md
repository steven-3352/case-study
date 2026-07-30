```yaml
role: 安全架构师 / 本地 Agent 执行架构师
production_tier: full

input_received:
  resources:
    - AGENTS.md
    - docs/RULES/07_ENVIRONMENT.md
    - docs/RULES/08_ASSETS_LIFECYCLE.md
    - templates/design/subagent_prd_schema.md
    - docs/RULES/README.md、00-11 规则、decisions/、memory/ 全部文件
    - 本机 /opt/homebrew/bin/codex
    - 本机 codex exec --help 输出
    - 本机 ~/.codex/config.toml 与 default.rules
    - 仓库 pipeline/、integrations/、assets/、templates/、tests/ 目录
    - 仓库 .env.example，仅确认 provider 配置形态，不读取或复述凭证值
  upstream_artifacts:
    - docs/design/WORKFLOW_EXECUTION_LOG.md
    - pipeline/README.md
    - pipeline/CHECKLIST.md
    - pipeline/gpt_image_client.py
    - pipeline/p011_seedance_i2v/gen_video.py
    - pipeline/gen_video_frames.py
    - pipeline/tts/gen_speech.py
    - docs/RULES/05_PIPELINE_CANDIDATES.md
  known_gaps:
    - gap: 当前仓库没有现成的本地 Web Job API、统一 Job Supervisor 或 Codex JSONL 解析器
      user_decision: 未提供；按新增独立 adapter/service 层设计，不修改现有 pipeline
    - gap: 当前受限环境无法完成一次真实 codex exec，会话初始化因权限失败
      user_decision: 未提供；JSONL 采用版本兼容解析，并以 fixtures 和安装环境实测作为上线前门禁
    - gap: provider API 的异步任务字段、下载 URL 和 webhook 规范不统一
      user_decision: 未提供；统一抽象为 submit/poll/download，禁止 provider 细节泄漏到 Supervisor

deliverable:
  - 本地 Web 服务调用 Python Codex CLI 及媒体 API 的安全执行架构
  - 确定性 Python、低成本模型、强模型和媒体 provider 的路由规则
  - 无 token Job Supervisor 的状态机、队列、重试和恢复策略
  - Codex exec JSONL 事件兼容层与 output-schema 约束
  - sandbox、approval、路径白名单、环境变量白名单、日志和隐私控制
  - provider adapter 接口、测试矩阵与二元验收标准

perceptual_goal:
  statement: >
    对同一输入事件，服务应始终先完成可确定的本地处理；只有事件规则明确要求时才调用低成本模型；
    只有发生可审计的升级条件时才调用强模型或媒体 API。用户可从 Job 状态、事件日志和产物清单
    判断任务正在运行、失败、重试、升级或完成，且不会看到凭证、未授权本地文件或未声明的外传。
  observable_metric: >
    1. 相同输入、版本和配置的确定性任务，输出 JSON digest 100% 一致；
    2. Job Supervisor 的单元测试中模型调用计数始终为 0，Supervisor 仅执行队列、锁、超时、
       重试、状态转移和日志压缩；
    3. 低成本模型调用必须命中 allowlisted event_type，调用记录包含 model、budget、reason，
       未命中率为 0；
    4. 强模型升级必须包含 allowlisted escalation_reason，缺少原因时升级请求率为 0；
    5. 每个 Job 都有单调状态序列和最终 terminal 状态，重复 webhook、进程重启和重复提交不产生
       重复副作用；
    6. 安全测试中路径穿越、符号链接逃逸、未授权环境变量、未同意的媒体上传和 secret 原文日志
       泄露全部为 0；
    7. JSONL 中未知事件不使 Job 崩溃，已支持事件的解析成功率为 100%。

implementation_approach:
  method: >
    新增一个仅本机监听的 Python Web Service，分为 API、Job Store、Supervisor、Deterministic
    Executor、Codex Executor、Media Provider Adapter、Policy/Redaction、Artifact Registry 七层。
    Web API 只接受结构化 Job 请求，不接受任意 shell 字符串；所有子进程使用 argv 数组启动。
  architecture:
    request_layer:
      - 默认绑定 127.0.0.1，禁止公网监听
      - 请求包含 job_id、event_type、input_refs、operation、requested_outputs、privacy_consent、
        model_policy 和 asset_policy
      - 拒绝任意 command、任意 cwd、任意 env、任意 URL 转发
      - 使用 SQLite 或等价本地持久化 Job 状态、幂等键、重试次数和审计摘要
    job_state_machine:
      states:
        - accepted
        - policy_checked
        - deterministic_running
        - model_queued
        - model_running
        - media_queued
        - media_running
        - qa_running
        - completed
        - blocked
        - failed
        - cancelled
      rules:
        - 状态转移由 Python 状态机白名单控制
        - 每次转移写入 sequence、timestamp、reason、artifact_refs
        - 使用 job_id + operation + input_digest 做幂等键
        - 崩溃恢复时将 running 状态重新归队，但不重复提交已有 provider_request_id
    deterministic_executor:
      responsibilities:
        - 文件枚举、hash、尺寸/时长/格式读取
        - YAML/JSON schema 校验
        - ffprobe、图像尺寸、音频时长、palette 和黑帧等确定性检查
        - asset_log、manifest、路径归一化、缓存命中判断
        - provider 请求参数构造与响应字段提取
      rule: >
        能通过标准库、现有 Python library、ffprobe 或现有 pipeline 完成的工作，不调用模型。
    codex_executor:
      command_template:
        - codex
        - exec
        - --json
        - --ephemeral
        - --sandbox
        - read-only
        - --cd
        - /Users/wmzuo/Documents/project/case-study
        - --output-schema
        - /approved/schema/path.json
      controls:
        - 不使用 --dangerously-bypass-approvals-and-sandbox
        - 不把用户输入直接拼接为 shell command
        - prompt 通过 stdin 或受控参数传入，并限制长度、文件引用和任务类型
        - 环境变量使用显式 allowlist，只向子进程传入 Codex 所需认证配置
        - 默认禁止写仓库；需要写入时只能写入预先创建的 job staging 目录
        - 使用 --ephemeral，避免不必要的本地会话持久化
        - 由于当前 codex exec 未暴露 --ask-for-approval，approval 不作为安全边界；
          安全边界由外层 policy、sandbox、cwd、路径白名单和 argv 校验提供
    jsonl_contract:
      purpose: >
        将 codex exec --json stdout 按事件解析，而不是把整段 stdout 当作最终文本。
      supported_events:
        - type: thread.started
          fields:
            thread_id: string
        - type: turn.started
          fields: {}
        - type: item.started
          fields:
            item: object
        - type: item.completed
          fields:
            item: object
        - type: turn.completed
          fields:
            usage:
              input_tokens: integer
              cached_input_tokens: integer
              output_tokens: integer
        - type: turn.failed
          fields:
            error: object
        - type: error
          fields:
            message: string
      parser_rules:
        - 每行独立 JSON parse；空行忽略
        - 保存 event_type、event_id、thread_id、turn_id、sequence 和 received_at
        - 未知 event_type 记录为 unknown_event，不阻塞已知事件处理
        - item 只提取允许的 agent_message、reasoning 摘要、command_execution 状态和错误字段
        - 不把 reasoning 原文写入普通业务日志
        - turn.completed 的 usage 作为成本与升级判断输入；缺失时标记 usage_unknown
        - 进程 exit code、stderr、JSONL terminal event 三者必须共同决定成功
        - output-schema 只约束最终模型响应，不替代 JSONL 事件解析
      normalized_result:
        schema_version: "1"
        status: success | failed | blocked | usage_unknown
        thread_id: string|null
        output: object|null
        usage:
          input_tokens: integer|null
          cached_input_tokens: integer|null
          output_tokens: integer|null
        events_seen: integer
        stderr_digest: string|null
        raw_log_ref: string|null
    low_cost_model_policy:
      triggers:
        - structured_field_extraction
        - short classification
        - provider response normalization fallback
        - ambiguous but low-impact metadata labeling
        - draft prompt linting
        - bounded asset description
      constraints:
        - 固定 allowlist model，不接受请求方任意 model 字符串
        - 固定 max_output_tokens、timeout、retry 和 prompt template
        - 必须使用 JSON output-schema
        - 单 Job、单 event、单 provider 设置 token budget
        - 失败只返回 blocked 或转入升级判定，不静默改用强模型
    strong_model_escalation:
      conditions:
        - 低成本模型 schema 校验连续失败两次
        - 任务涉及外部公开发布、事实性陈述、版权/隐私或高风险合规判断
        - 低成本模型输出与确定性检查冲突
        - 媒体 provider 重试上限达到且需要改变策略
        - 视觉创意、叙事或跨镜方案需要多候选判断
        - 需要读取多个上游角色产物并形成结构化决策
        - 质量门禁失败且确定性修复不能解决
      requirements:
        - escalation_reason 必须是枚举值
        - 附带失败证据 digest、attempt_count、qa_results 和预估成本
        - 强模型仍受相同路径、隐私、输出 schema 和日志规则约束
        - 强模型不能直接修改验收器输入以制造 pass
    media_provider_abstraction:
      interface:
        - validate_capabilities(request) -> CapabilityReport
        - submit(request, idempotency_key) -> ProviderJob
        - poll(provider_job_id) -> ProviderStatus
        - download(provider_job_id, destination) -> Artifact
        - cancel(provider_job_id) -> CancelResult
        - redact_error(response) -> SafeError
      adapters:
        - image_provider: 对接仓库现有 GPT image client/config
        - video_provider: 对接 grok/Seedance 类异步 submit-poll-download 流程
        - tts_provider: 对接 pipeline/tts 的 provider 配置和 strict_provider 语义
        - broll_provider: 对接公开素材 API，但必须记录来源与授权
      rules:
        - provider 名称和 endpoint 由服务端 registry 配置，不能由客户端任意代理
        - provider 失败不自动静默换 provider
        - 切换 provider 必须写入 reason、attempt、成本和 asset_log
        - 上传前检查 privacy_consent、asset source_type、文件大小、MIME 和目的地
        - 生成素材必须区分 generated_fact、synthetic_visual、public_reference、real_private 和 hybrid
    supervisor:
      token_cost: 0
      responsibilities:
        - 拉取队列、租约、超时、心跳、重试、退避、取消、恢复
        - 调用 Deterministic Executor 和已授权 Adapter
        - 根据事件规则排队模型任务
        - 汇总状态和 artifact refs
      prohibited:
        - 生成自然语言计划
        - 改写 prompt
        - 选择未注册 provider
        - 解释 QA 结果
        - 代替模型做开放式创意决策
      scheduling:
        - SQLite lease 或文件锁保证单 Job 单执行者
        - 外部 API 使用指数退避和 Retry-After
        - 每个 provider 独立并发上限
        - 媒体任务与模型任务分别限流
        - supervisor heartbeat 不调用 LLM
    artifact_and_asset_policy:
      paths:
        - repository_root: /Users/wmzuo/Documents/project/case-study
        - job_staging: repository_root/.local_jobs/<job_id>/
        - project_assets: 仅允许请求声明的项目目录
        - public_assets: 仅允许 assets/broll/catalog.yaml 等登记路径
      rules:
        - 所有路径 realpath 后必须仍位于 allowlist 根目录
        - 拒绝 ..、绝对外部路径、NUL 字节、未知扩展名和符号链接逃逸
        - 输出先写 staging，再原子 rename 到已批准目录
        - 不允许写 docs/RULES/、pipeline/mv_engine/ 或 AGENTS.md
        - 资产清理只能按明确 job/project 目录执行
        - 每个产物记录 sha256、source_type、provider、prompt_digest、cost、license 和 consent_ref
    privacy_and_logging:
      privacy_notice:
        - 明确告知哪些文件会上传到哪个 provider、用途、保留时间和删除方式
        - real_private 素材必须脱敏后才能外传
        - 用户拒绝 consent 时只能执行本地确定性任务
        - 默认不发送完整仓库、.env、git metadata、聊天记录或无关资产
      logging:
        - 结构化 JSONL，字段分为 audit、operational、provider_usage 三类
        - secret、Authorization、API key、cookie、个人电话号码、邮箱和私信正文先脱敏
        - stdout/stderr 只保留长度受限摘要、sha256 和 artifact ref
        - 大日志按 Job 分片并 gzip/zstd 压缩；原始媒体不进入日志
        - 原始 provider 响应只存受控 staging，设置 TTL，默认不入 Git
        - 日志记录模型、provider、token usage、延迟、重试和失败原因，但不记录 secret
        - 日志压缩不能破坏状态序列、错误码、成本和审计链
    web_api:
      endpoints:
        - POST /v1/jobs
        - GET /v1/jobs/{job_id}
        - GET /v1/jobs/{job_id}/events
        - POST /v1/jobs/{job_id}/cancel
        - GET /v1/artifacts/{artifact_id}
        - GET /v1/health
      rules:
        - localhost only；若需要局域网访问，必须显式配置绑定地址和 bearer token
        - 请求体大小、文件大小、并发数、队列长度和单 Job 成本均有限制
        - 不返回凭证、原始 provider headers 或未脱敏错误
        - 所有 mutation 要求 idempotency-key
        - 文件下载只允许 artifact registry 中的已完成产物

why_this_fits_perceptual_goal: >
  把“是否需要模型”变成确定性事件路由，把“是否成功”变成状态机和机械 QA，把“是否可外传”
  变成 consent、来源和路径门禁。这样低成本模型只处理不可避免的语义判断，Supervisor 不消耗
  token，媒体 provider 的异步差异被 adapter 隔离；用户可观察到真实状态和产物，而不是只看到
  “pipeline 跑通”或模型返回一段看似完整的文本。

alternatives_considered:
  - option: 让 Python Web 服务直接调用 OpenAI/媒体 SDK，并在服务内实现所有业务逻辑
    why_rejected: >
      会把 provider 认证、异步状态、重试和业务流程耦合在一起；难以统一 Codex CLI sandbox、
      JSONL、路径白名单和升级审计，也会重复现有 pipeline 的 provider 逻辑。
  - option: 让 Codex CLI 作为总控 Agent，自主读取仓库、执行 shell、调用媒体 API
    why_rejected: >
      Supervisor 会消耗 token，且安全边界依赖模型自律；无法保证确定性任务不调用模型，也无法
      对任意 shell、cwd、env、上传文件和媒体副作用做严格白名单控制。
  - option: 使用云端队列/托管 Agent 作为 Job Supervisor
    why_rejected: >
      增加外传面和长期凭证暴露面，不符合当前本地仓库和本机 Codex CLI 的部署边界；网络服务中断
      时也不利于本地素材恢复和审计。
  - option: 只解析 Codex 最后一条文本，不解析 JSONL 事件
    why_rejected: >
      无法可靠区分 thread、turn、item、失败、usage、stderr 和未知事件；会丢失成本、重试、取消
      和部分完成状态，不能形成可恢复的 Job 审计链。

known_limitations:
  - limitation: 当前环境未能成功启动真实 codex exec
    impact: >
      JSONL 字段需以目标机器安装版本的 fixtures 和一次最小 dry-run 最终确认；解析器必须容忍
      未知事件和字段缺失。
  - limitation: codex exec 当前帮助输出未提供逐次 approval 参数
    impact: >
      不能把用户审批当作执行安全边界；必须依赖外层 allowlist、sandbox、cwd、argv 和环境变量
      控制，敏感任务默认 blocked。
  - limitation: provider 的异步 API 返回字段和错误语义不统一
    impact: >
      adapter 需要为每个 provider 编写 contract test；未通过 contract test 的 provider 不得进入
      production registry。
  - limitation: 本地 Web 服务无法替代用户对真实私域素材上传的授权判断
    impact: >
      consent 只能证明用户确认了声明，不能证明素材本身拥有合法授权；asset_log 必须保留来源和
      授权证据。
  - limitation: 低成本模型仍可能产生事实错误或错误分类
    impact: >
      事实、合规、隐私和发布相关判断不得只依赖低成本模型；必须走确定性校验、强模型升级或人工
      blocked。
  - limitation: 日志压缩和脱敏可能降低调试完整性
    impact: >
      需要使用不可逆 digest、受控 raw_log_ref 和短期 TTL 原始日志，在隐私与可复盘性之间取平衡。
  - limitation: 现有仓库包含多种历史 provider 变量命名和中转 URL 约定
    impact: >
      adapter registry 必须显式映射变量，不得猜测 endpoint；环境初始化阶段遵守 .env.example 和
      最近姊妹脚本核对规则。

acceptance_criteria:
  - criterion: 确定性优先
    how_to_verify: >
      使用固定 fixture 连续提交 100 次相同 Job，比较状态序列、路由决策和 artifact manifest 的
      sha256；要求完全一致且模型调用计数为 0。
  - criterion: Supervisor 零 token
    how_to_verify: >
      注入 fake Codex、fake media provider 和 token meter，运行队列、租约、超时、重试、恢复和取消
      测试；Supervisor 的 model/token counter 必须始终为 0。
  - criterion: 低成本事件触发
    how_to_verify: >
      对每个 allowlisted event_type 和 10 个未登记 event_type 做 contract test；只有前者进入
      low-cost model queue，后者必须 deterministic handled 或 blocked。
  - criterion: 强模型升级
    how_to_verify: >
      构造 schema 连续失败、事实冲突、隐私风险、QA 失败和重试耗尽 fixture；每次升级都必须含
      allowlisted escalation_reason、失败证据 digest、attempt_count 和成本预算。
  - criterion: Codex JSONL 解析
    how_to_verify: >
      用 thread.started、turn.started、item.started、item.completed、turn.completed、turn.failed、
      error、未知事件和损坏行 fixtures 测试；已知事件 100% 归一化，未知事件只记录不崩溃，损坏行
      使 Job blocked 或 failed 而不是 false success。
  - criterion: output-schema 约束
    how_to_verify: >
      给 Codex Executor 一个只允许结构化 JSON 的 schema，分别注入合法响应、额外字段、缺字段和
      非 JSON 响应；只有合法响应可进入下游，其他情况必须记录 schema_error 并按升级策略处理。
  - criterion: sandbox 和命令边界
    how_to_verify: >
      审计实际 argv，确认每次 Codex 调用包含 --json、--ephemeral、--sandbox、固定 --cd 和批准的
      --output-schema；提交 shell 注入、任意 cwd、--add-dir 外路径和危险 flag fixture，全部拒绝。
  - criterion: 路径白名单
    how_to_verify: >
      测试 ..、绝对外部路径、符号链接、硬链接、NUL 字节、未知扩展名和 staging 外写入；所有案例
      必须 blocked，正常 project_assets 和 job_staging 路径必须可用。
  - criterion: 环境变量和 secret
    how_to_verify: >
      给子进程注入包含 API key、cookie、无关环境变量的父环境，比较子进程实际环境和 allowlist；
      检查 stdout、stderr、provider error、compressed log，任何 secret 原文出现即 fail。
  - criterion: 隐私提示与 consent
    how_to_verify: >
      分别提交无 consent、拒绝 consent、同意指定 provider、real_private 未脱敏和 synthetic_visual
      请求；未同意或未脱敏请求不得发生网络上传，已同意请求的审计事件必须记录 provider、目的、
      asset source_type 和 consent_ref。
  - criterion: provider 抽象
    how_to_verify: >
      使用 fake image、video、tts、broll adapters 验证相同 submit/poll/download/cancel 接口；
      provider 返回不同 task_id、job_id、id、request_id、超时和 4xx/5xx 时均能归一化，未知 provider
      必须拒绝。
  - criterion: 幂等、恢复和重试
    how_to_verify: >
      重复 POST、重复 webhook、Supervisor 进程在 submit 后退出、provider 超时和网络重连场景各
      运行 50 次；要求不重复收费提交、不重复写最终产物，恢复后最终状态唯一且可审计。
  - criterion: 日志压缩和可复盘
    how_to_verify: >
      生成超过日志阈值的 Codex stdout/stderr 和 provider 响应，检查压缩文件可解压、sequence 不丢、
      secret 已脱敏、raw_log_ref 可定位且 TTL 清理只删除原始重资产，不删除 manifest、asset_log、
      状态摘要和 QA 结果。
  - criterion: 媒体资产生命周期
    how_to_verify: >
      对 real_private、public_reference、generated_fact、synthetic_visual、hybrid 五类 fixture
      生成 asset_log；核验 source_type、provider、prompt_digest、成本、授权和落盘路径齐全，
      清理任务只删除项目专属重资产，不删除长期设计文档和公共代码。
  - criterion: 独立验收
    how_to_verify: >
      由不同进程读取最终 manifest、状态日志和 QA 产物，不读取 implementation_approach，执行
      二元 pass/fail；验收目标必须在首次运行前冻结，禁止修改 verifier 输入或降低阈值制造 pass。
  - criterion: 本地 Web E2E
    how_to_verify: >
      在 127.0.0.1 启动服务，使用 fake providers 完成“事件接收 → 确定性处理 → 低成本模型 →
      媒体任务 → QA → artifact registry”；验证 GET 状态、事件流、取消、重启恢复、错误响应和
      artifact 下载均符合 schema，且服务不监听公网地址。
```