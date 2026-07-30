role: 业务流程与数据契约设计师
production_tier: full

input_received:
  resources:
    - AGENTS.md
    - docs/RULES/README.md 及 docs/RULES/00-11、decisions、memory
    - .agents/skills/paperdoll-mv-packaging/SKILL.md
    - .agents/skills/paperdoll-mv-packaging/references/director-orchestration.md
    - .agents/skills/paperdoll-mv-packaging/assets/visual-score.template.yaml
    - templates/design/subagent_prd_schema.md
    - pipeline/mv_engine/ 及现有 gate_check、缓存、渲染、QC 能力
    - docs/design/WORKFLOW_EXECUTION_LOG.md
  upstream_artifacts:
    - 当前仓库已有导演规则、视觉总谱模板和校验器
    - 当前仓库未发现本次指定项目的确定性 brief、歌曲、歌词和立绘输入
  known_gaps:
    - gap: 未提供具体音频、歌词、人物立绘、目标画幅和发布平台
      user_decision: 由运行时 intake 补齐；缺失时状态保持 blocked，不允许生成
    - gap: music_map、character_map 自动生成器及 visual_score 到渲染 shots 的编译器尚未完整接入
      user_decision: 本 PRD 定义契约和状态，不假设实现已存在
    - gap: 关键帧多选、i2v 生成、逐镜诊断与最终合成入口未形成统一幂等任务协议
      user_decision: 由本 PRD 作为后续实现边界

deliverable:
  summary: >
    定义从物料 intake 到最终导出的一条可恢复、可审计、fail-closed 的
    纸片人 MV 生产流程。流程顺序为：
    intake → audio_lyric_alignment → relationship_story_approval →
    visual_score_approval → keyframe_selection → generation_clip_generation →
    compositing_qc → export.
  state_machine:
    states:
      - intake_pending
      - intake_validated
      - maps_generated
      - story_framework_pending_user
      - story_framework_approved
      - visual_score_pending_user
      - visual_score_approved
      - keyframes_pending_user
      - keyframes_approved
      - generation_pending
      - generation_partial
      - generation_approved
      - compositing_pending
      - qc_failed
      - qc_passed
      - exported
      - blocked
      - superseded
    transitions:
      - from: intake_pending
        to: intake_validated
        when: brief、音频、歌词、源立绘和画幅契约校验通过
      - from: intake_validated
        to: maps_generated
        when: beats.json、lyrics_timed.json、music_map.yaml、character_map.yaml 生成成功
      - from: maps_generated
        to: story_framework_pending_user
        when: 原始故事框架和关系推进包可读
      - from: story_framework_pending_user
        to: story_framework_approved
        when: 用户确认人物功能、关系、能量峰值和结尾回收
      - from: story_framework_approved
        to: visual_score_pending_user
        when: visual_score.yaml、asset_plan.yaml、generation_plan.yaml 生成且结构校验通过
      - from: visual_score_pending_user
        to: visual_score_approved
        when: 用户确认视觉总谱、关键转场和 i2v 使用范围
      - from: visual_score_approved
        to: keyframes_pending_user
        when: 每个 editorial shot 生成至少 2 个关键帧候选
      - from: keyframes_pending_user
        to: keyframes_approved
        when: 用户为每个需生成或高风险 shot 选择唯一候选
      - from: keyframes_approved
        to: generation_pending
        when: generation_plan 与已选首帧绑定且所有资产来源合法
      - from: generation_pending
        to: generation_partial
        when: 至少一个 generation clip 完成，其他任务可并行恢复
      - from: generation_partial
        to: generation_approved
        when: 所有 clip 通过逐镜诊断和首尾帧连续性检查
      - from: generation_approved
        to: compositing_pending
        when: 2.5D、i2v、字幕、音频和转场输入齐全
      - from: compositing_pending
        to: qc_passed
        when: media、motion、palette、字幕、音轨、时长和哈希 QC 全部通过
      - from: qc_passed
        to: exported
        when: 平台导出包生成且最终文件哈希登记
      - from: any
        to: blocked
        when: 必填输入缺失、用户未拍板、来源不合法或任一硬门失败
      - from: any
        to: superseded
        when: 上游版本变更导致下游 artifact_hash 不再匹配
  stages:
    - id: S0_intake
      input:
        - brief.json
        - 原始音频 mp3/wav
        - LRC 或纯文本歌词
        - source_portrait 立绘
      output:
        - normalized brief.json
        - asset manifest
        - input hashes
      user_decision:
        - 画幅、平台、时长裁切策略
        - 人物名称、身份、关系和禁用内容
      boundary:
        - 源立绘只允许仿射、裁切和 alpha 处理
        - 不接受生成图冒充 source_portrait
    - id: S1_audio_lyric_mapping
      input:
        - brief.json
        - 真实音频
        - lyrics source
      output:
        - beats.json
        - lyrics_timed.json
        - music_map.yaml
      user_decision:
        - 无需拍板，除非歌词对齐置信度低于 0.9 或段落识别冲突
      boundary:
        - 一级/二级/三级 cues 必须来自音频分析或歌词时间
        - 禁止凭感觉填写时间码
    - id: S2_character_relationship_mapping
      input:
        - source_portrait manifest
        - 人物资料
        - lyrics_timed.json
        - music_map.yaml
      output:
        - character_map.yaml
        - 原始故事框架
        - appearance budget
      user_decision:
        - 确认主视角、角色导演功能、关系冲突、首次介绍和高潮群像
      boundary:
        - character_map 只描述叙事功能和关系，不描述包装参数
        - 多角色片必须有首次介绍、关系镜、群像和高潮后回收
    - id: S3_visual_score_compilation
      input:
        - music_map.yaml
        - character_map.yaml
        - 原始故事框架
        - asset manifest
      output:
        - visual_score.yaml
        - asset_plan.yaml
        - generation_plan.yaml
        - storyboard.md
      user_decision:
        - 确认视觉总谱、每镜导演任务、转场共享元素、i2v 范围
      boundary:
        - visual_score 是 editorial shot 层，不是视频模型任务清单
        - 每镜一个主要导演任务和一个 primary_action
        - 未通过 validate_visual_score.py 不得生成正式资产
    - id: S4_keyframe_selection
      input:
        - visual_score.yaml
        - asset_plan.yaml
        - 背景候选
        - 源立绘及合法补姿势候选
      output:
        - keyframe_candidates/{shot_id}/{candidate_id}.png
        - keyframe_selection.yaml
      user_decision:
        - 每个高风险 editorial shot 选择候选或退回重绘
      boundary:
        - 候选必须保存 prompt、provider、seed、source_refs、candidate_hash
        - 中文歌词和标题由合成层排版，不依赖图像模型生成
    - id: S5_generation_clip
      input:
        - keyframe_selection.yaml
        - generation_plan.yaml
        - i2v prompt
      output:
        - generation_clips/{clip_id}.mp4
        - generation manifest
        - per-frame diagnostic report
      user_decision:
        - 仅在连续三次诊断失败或需改变技术路线时介入
      boundary:
        - editorial shot 可由 2.5D、静态、确定性合成或 i2v 完成
        - generation clip 是实现资产，不等同于 editorial shot
        - 每个 generation clip 最短 4.0 秒；更短的视觉事件必须在合成层裁切或由静态帧实现
    - id: S6_compositing
      input:
        - approved editorial shot list
        - 2.5D renders
        - approved generation clips
        - audio and timed lyrics
      output:
        - intermediate video
        - subtitle track
        - audio mux manifest
      user_decision:
        - 无；仅遇到不可修复的内容或关系错误才回退
      boundary:
        - 转场不得随机套用
        - 首尾帧共享元素必须与 visual_score 一致
        - 字幕层位于最上层，源立绘不可被长期遮挡
    - id: S7_qc_export
      input:
        - canonical intermediate video
        - QC configuration
        - target platform profiles
      output:
        - qc_report.json
        - final mp4 variants
        - final hashes
        - delivery manifest
      user_decision:
        - 外发拍板
      boundary:
        - 黑帧、冻结、静音、音轨、时长、分辨率、帧率、字幕安全区、调色和终片哈希必须通过
        - 终片字节变化会使旧验收自动失效

  schema_contracts:
    brief.json:
      owns:
        - project_id
        - title
        - canvas
        - fps
        - target_platforms
        - duration_policy
        - audience
        - source_inputs
        - constraints
      excludes:
        - shot timing
        - character relationship decisions
        - rendering parameters
    music_map.yaml:
      owns:
        - duration
        - bpm
        - sections
        - energy
        - level_1_2_3_cues
      excludes:
        - character assignment
        - asset paths
        - visual effects
    character_map.yaml:
      owns:
        - character identity
        - director_function
        - traits
        - symbols
        - relationships
        - appearance_budget
      excludes:
        - camera parameters
        - prompt text
        - generated asset metadata
    visual_score.yaml:
      owns:
        - editorial shot timeline
        - purpose
        - leverage
        - characters
        - lyric mapping
        - composition
        - primary_action
        - beats
        - first_frame
        - last_frame
        - transition_out
        - technique
        - assets.use
        - assets.missing
      excludes:
        - provider credentials
        - generation seed
        - final render cache key
    asset_plan.yaml:
      owns:
        - source_type
        - asset_role
        - source_refs
        - used_by
        - required_by
        - identity_checks
        - provenance
        - status
      excludes:
        - editorial meaning
        - user approval state
        - final clip QC result
    generation_plan.yaml:
      owns:
        - clip_id
        - editorial_shot_id
        - first_frame_ref
        - last_frame_target
        - duration
        - model
        - prompt_ref
        - motion_constraints
        - retry_policy
        - output_hash
      excludes:
        - changing story purpose
        - changing character relationship
        - replacing visual_score approval
    keyframe_selection.yaml:
      owns:
        - shot_id
        - candidate_id
        - selected_hash
        - selection_status
        - reviewer
        - decision_timestamp
      excludes:
        - modifying source portrait
        - silently changing shot composition
  shot_model:
    editorial_shot:
      definition: >
        面向导演和剪辑的叙事单元，具有完整语义、音乐区间、人物关系、
        首尾帧和转场契约；可以由多个 generation clip、静态帧或 2.5D 段落组成。
      duration:
        - 按音乐与语义确定
        - 低能量通常 4-8 秒
        - 高能量通常 0.75-2 秒或由连续镜内事件构成
    generation_clip:
      definition: >
        面向生成模型的执行单元，只负责一个可生成的连续动作或状态变化。
      duration:
        - minimum: 4.0
        - recommended: 4.0-6.0
        - editorial_trim_allowed: true
      relationship:
        - 一个 editorial shot 可对应零个、一个或多个 generation clips
        - 一个 generation clip 不得跨越两个不连续 editorial shot
  frame_contract:
    first_frame:
      required:
        - shot_id
        - clip_id
        - asset_hashes
        - character_ids
        - composition_anchor
        - color_context
        - readable_subject
      rule: 生成首帧必须与前一镜尾帧或指定共享元素一致
    last_frame:
      required:
        - exit_state
        - transition_shared_element
        - subject_position
        - occlusion_level
        - frame_hash
      rule: 尾帧必须明确如何进入下一镜，不允许只写“自然结束”
    transition_contract:
      types:
        - hard_cut
        - occlusion_cut
        - action_match
        - dissolve
        - flash_white
        - light_wipe
        - bridge_shot
        - none
      rules:
        - 非终镜必须有 shared_element
        - 相邻镜至少共享颜色、主体、意象、空间或运动方向之一
        - 不连续且无法共享元素时必须插入 1-2 秒 bridge shot
  idempotency:
    task_key: >
      sha256(project_id + stage_id + artifact_version + normalized_input_hashes +
      config_hash + code_version)
    rules:
      - 相同 task_key 已有完整 artifact 和 manifest 时直接复用
      - 输出先写临时文件，完成后原子替换
      - manifest 记录 input_hash、output_hash、schema_version、tool_version、status
      - 同一 task_key 禁止覆盖已批准 artifact
      - 上游 hash 变化只使受影响下游进入 superseded
      - 失败任务保留 failure manifest，可从最近成功 checkpoint 恢复
      - 并行任务必须使用 project_id/shot_id/clip_id 命名空间
    recovery:
      - 从最后一个 approved checkpoint 继续
      - 只重跑 hash 失效的 shot 或 clip
      - generation 失败三次后切换到确定性 2.5D、补图或 bridge shot
      - 不通过修改验收输入或降低阈值恢复任务
  acceptance_gates:
    - gate: contract
      metric: 所有必填字段存在，枚举和引用可解析
    - gate: director
      metric: visual_score 总分不低于 80，单项不低于该项满分 60%
    - gate: timing
      metric: editorial shot 覆盖全片，时间间隙和重叠不超过 50ms
    - gate: relationship
      metric: 多角色片至少 1 个关系镜、1 个高潮群像、1 个高潮后回收镜
    - gate: motion
      metric: 任意连续 2 秒窗口内主体位置变化至少为画幅宽 4%，或主体面积变化至少 8%，否则必须切镜或增加可见构图事件
    - gate: diversity
      metric: 不允许相邻镜人物与景别完全重复；任一单一运镜、转场或版式不得超过全片 50%
    - gate: generation
      metric: 每个 generation clip 时长至少 4 秒，逐帧检查幻觉、角色一致性、画面尺寸和首尾帧
    - gate: media
      metric: 0 黑帧、0 异常静音、无超过 4 秒冻结、音频完整、规格匹配目标平台
    - gate: release
      metric: 内容门、形式门、机器 QC、独立终片验收和 pre_publish_forecast >= B 全部通过

perceptual_goal:
  statement: >
    任何执行者都能沿着已批准的数据契约恢复生产，并能从成片反查
    音乐、歌词、人物关系、镜头、资产、生成任务和 QC 结论；观众在前 3 秒
    能识别世界与主要人物，随后能看到关系推进而非角色轮播。
  observable_metric: >
    100% editorial shot 可追溯到至少一个 section、lyric/cue、character_id、
    first_frame、last_frame 和 transition_shared_element；100% generation clip
    可追溯到一个 editorial shot 且时长 >= 4.0 秒；相同 task_key 重跑不产生新字节；
    任意 2 秒窗口至少满足一次 4% 画幅宽位置变化、8% 主体面积变化或明确切镜；
    前 3 秒至少出现一次可识别主体变化。

implementation_approach:
  method: >
    采用版本化 YAML/JSON 契约加状态机编排。以 brief、music_map、
    character_map 为叙事输入，以 visual_score 作为 editorial shot 的唯一导演事实源，
    以 asset_plan 管理来源，以 generation_plan 管理模型执行，以 manifest/hash 管理幂等、
    恢复和验收对象。2.5D 优先承担可确定的立绘包装；i2v 只承担有机动作和必要的连续变化。
  why_this_fits_perceptual_goal: >
    分离 editorial shot 与 generation clip 可防止模型生成任务反过来重写故事；
    首尾帧契约把转场从事后特效变成上游数据；输入输出 hash、原子写入和 checkpoint
    让失败恢复不会污染已批准版本；独立 QC 直接量化观众可见的运动、连续性和媒体质量。

alternatives_considered:
  - option: 直接以 ffmpeg/Python 分镜参数驱动整片，不设中间导演契约
    why_rejected: >
      会把包装参数误当叙事决策，无法表达歌词语义、人物关系和用户拍板点，
      也无法可靠区分“代码调用了效果”和“观众看得见效果”。
  - option: 全片交给 i2v，按歌曲段落生成长视频后再剪辑
    why_rejected: >
      角色一致性、首尾帧控制、歌词对齐和失败恢复不可控；超过 4 秒的生成单元
      不能替代 editorial shot 的关系与能量编排。
  - option: 只用静态关键帧和统一 2.5D 包装
    why_rejected: >
      可确定但无法稳定表现转身、抬手、消散等有机动作；会把所有镜头压成同一
      视觉语法，增加电子相册和全程同能量风险。

known_limitations:
  - limitation: 本次没有具体音频、歌词和立绘，无法生成真实时间码和人物关系结论
    impact: 所有 map 和 shot 只能在运行时由真实输入实例化
  - limitation: 现有仓库已有 visual_score 校验器，但自动导演编译器和一键 final 入口仍缺失
    impact: 契约可作为实现边界，当前不能宣称端到端自动完成
  - limitation: i2v 供应商可能改变模型能力、时长限制或输出格式
    impact: generation_plan 必须记录 provider capability，失败时回退到确定性合成
  - limitation: 视觉多样性指标不能完全替代独立人工观感验收
    impact: 仍需由非产出者执行最终二元 pass/fail 审核
  - limitation: 复杂关系镜可能需要额外补姿势图
    impact: 补图增加身份一致性检查、成本和返工路径

acceptance_criteria:
  - criterion: PRD 字段可被 schema 解析，且 observable_metric 含明确数量级
    how_to_verify: 检查 role、production_tier、input_received、deliverable、perceptual_goal、implementation_approach、alternatives_considered、known_limitations、acceptance_criteria 均存在
  - criterion: 状态机覆盖正常、失败、恢复和上游变更
    how_to_verify: 用测试事件依次验证 intake 缺失、用户拒绝、单 clip 失败、上游 hash 变化和重复 task_key
  - criterion: 五类核心契约边界无循环依赖
    how_to_verify: 对 brief、music_map、character_map、visual_score、asset_plan、generation_plan 逐字段检查 owner 与 excludes
  - criterion: editorial shot 与 generation clip 可一对多映射且 clip 最短 4 秒
    how_to_verify: 构造一个 2 秒 editorial shot 映射 4 秒 generation clip，验证合成层允许裁切而 generation 层拒绝短于 4 秒
  - criterion: 首尾帧契约可阻止无动机转场
    how_to_verify: 删除非终镜 shared_element 或 last_frame.exit_state，schema 校验必须 fail
  - criterion: 重跑不会覆盖批准结果
    how_to_verify: 使用相同 task_key 重跑并比较 output_hash；修改输入后验证旧 artifact 标记 superseded 并生成新版本
  - criterion: QC 对最终 canonical MP4 生效
    how_to_verify: 修改 MP4 字节后重新运行 QC，验证旧验收哈希失效；注入黑帧、冻结、静音或规格错误时必须 fail-closed
  - criterion: 独立验收只依据产物与验收标准
    how_to_verify: 让独立 reviewer 不读取 implementation_approach，仅检查导出的 shot、clip、QC report 和本 PRD acceptance_criteria
