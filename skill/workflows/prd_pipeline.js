export const meta = {
  name: 'prd_pipeline',
  description: '自足版三层协作 Workflow（不依赖宿主 CLAUDE.md）：加载角色注册表→确定性激活角色→分波次并行产出结构化子PRD→独立验收→汇总复核。强制每个被激活角色由独立 agent 产出可核验的感知目标，防止实现者自己兼任角色、自己验收自己。owns_dims/gates/QG-RAISE-3 注入每个角色 prompt，逼其按「提升3档目标」设计而非只过基准。',
  whenToUse: '任何新选题的正式制作阶段（脚本/风格已与用户对齐、或 blueprint.js 已产出蓝图并经用户一次确认后调用）。args: {totalPRD, projectId, productionTier, formatType, overlays?, executionLogPath?}。production_tier 只影响验收强度（人数/是否锦标赛），角色集合由注册表 + 形态确定性推导，不由 agent 临场判断——这是本 workflow 修复的核心事故（角色被实现者兼任、感知目标从未独立存在）。',
  phases: [
    { title: '读取执行日志', detail: '读 WORKFLOW_EXECUTION_LOG 最近条目的 carry_forward，作为本次角色分派的前车之鉴' },
    { title: '角色激活', detail: '从内嵌注册表按形态确定性推导激活角色集合（不因 tier 减角色），再由 agent 补每个角色的输入切片理由' },
    { title: '角色执行', detail: '按 wave 字段分波次并行，每个角色独立 agent() 产出 subagent_prd_schema 子PRD，注入 owns_dims/gates/QG-RAISE-3' },
    { title: '独立验收', detail: '验收者 ≠ 产出者，只读 acceptance_criteria + 产出摘要 + observable_metric，二元 pass/fail，不锦标赛' },
    { title: '汇总复核', detail: '检查整体是否仍符合总PRD最终结果定义，草拟执行日志条目供主LLM复核后写入' },
  ],
}

// ═══════════════════════════════════════════════════════════════════
// 内嵌角色注册表（从 roles/registry.yaml 生成 · 改动须同步 · validate.js 校验一致性）
// workflow 沙箱无 fs，无法运行时读 registry.json；此处内嵌镜像保证确定性与零 agent 转写风险。
// 单一事实源仍是 roles/registry.yaml —— 本常量是它的派生镜像。
// ═══════════════════════════════════════════════════════════════════
const ROLE_REGISTRY = [
  // 理解层 4
  { name: '选题深挖师', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-INSIGHT-3FACTS', 'QG-PRD-ACCEPTANCE'], responsibility: '拆透选题——谁、什么场景、烦什么、要什么结果', output_template: 'templates/insights/topic_brief.md' },
  { name: '内核提炼师', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-INSIGHT-3FACTS', 'QG-PRD-ACCEPTANCE'], responsibility: '从调研中抽 3–5 条不可删关键信息 + 1 句价值锚', output_template: 'templates/insights/core_message.md' },
  { name: '领域专家', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '业务逻辑/流程；带货则品类决策链、竞品差异', output_template: 'templates/insights/domain_notes.md' },
  { name: '事实校验员', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '核对数据、SKU、引用；标红不可写；拦截洞察卡没有的卖点', output_template: 'templates/insights/fact_check.md' },
  // 网络调研层
  { name: '网络调研员', group: '调研', wave: 2, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-EXTERNAL-REFS', 'QG-PRD-ACCEPTANCE'], responsibility: '搜公开内容提炼痛点与可引用转述（≥3 URL、≥2 网络原话）', output_template: 'templates/insights/external_references.md' },
  // 核心 10
  { name: '编导', group: '核心', wave: 1, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '选题是否符合主线、形态拆分、验收标准；立项单（钩子+形态分工）', output_template: 'templates/subagent_prd_schema.md' },
  { name: '记者', group: '核心', wave: 2, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '真实性、数据、证据链；小老板原话、痛点佐证、数据点', output_template: 'templates/subagent_prd_schema.md' },
  { name: '纪录片导演', group: '核心', wave: 2, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '故事弧线、改造前后对比；叙事大纲（起承转合+情绪锚点）', output_template: 'templates/subagent_prd_schema.md' },
  { name: '导演', group: '核心', wave: 10, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '镜头语言、节奏、信息密度；分镜表（画面/口播/字幕/时长，出镜含机位）', output_template: 'templates/subagent_prd_schema.md' },
  { name: '摄像/视觉', group: '核心', wave: 10, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D12'], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '画面可拍性、构图、可复用素材；B-roll 列表、截图需求', output_template: 'templates/subagent_prd_schema.md' },
  { name: '编剧', group: '核心', wave: 5, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D19'], gates: ['QG-ANTI-MEDIOCRITY', 'QG-SCRIPT-QUOTES', 'QG-PRD-ACCEPTANCE'], responsibility: 'N 角度抗平庸锦标赛 + 停划裁判 best-of；前 3s 大字钩子', output_template: 'templates/anti_mediocrity_tournament.md' },
  { name: '视觉设计', group: '核心', wave: 8, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D04', 'D09', 'D15'], gates: ['QG-VISUAL-ORIGINALITY', 'QG-PRD-ACCEPTANCE'], responsibility: '版面、色彩、品牌一致性；视觉路线 + 封面 mock 验收', output_template: 'templates/cover_standards.md' },
  { name: '视觉语言策展师', group: '核心', wave: 8, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D04', 'D09', 'D10'], gates: ['QG-PALETTE-NEON', 'QG-VISUAL-ORIGINALITY', 'QG-PRD-ACCEPTANCE'], responsibility: '萃取本条色板/字体/组件/禁用项；候选须含≥1 浅色方案（禁 AI 味深色默认）', output_template: 'templates/design_language.md' },
  { name: '剪辑', group: '核心', wave: 12, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D05', 'D06', 'D14', 'D16', 'D17'], gates: ['QG-MEDIA-BLACK', 'QG-MEDIA-SILENCE', 'QG-DELIVERY', 'QG-PRD-ACCEPTANCE'], responsibility: '时长卡控、三平台规格；抖音 45-60s / 小红书 ≤60s / 视频号 60-90s', output_template: 'templates/subagent_prd_schema.md' },
  { name: '运营/增长', group: '核心', wave: 13, activation: 'always', dual_review: false, translation_layer: false, owns_dims: ['D16'], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '三平台文案 + 评论区埋点 + 私信路径', output_template: 'templates/subagent_prd_schema.md' },
  // 表达/音画层 5
  { name: '留存与互动设计师', group: '表达音画', wave: 4, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D08', 'D15', 'D19'], gates: ['QG-ATTENTION', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '完播节拍、形式切换、互动 CTA；retention_beat_sheet', output_template: 'templates/retention_beat_sheet.md' },
  { name: '动画导演', group: '表达音画', wave: 6, activation: 'video_only', dual_review: false, translation_layer: true, owns_dims: ['D01', 'D02', 'D11', 'D12', 'D13'], gates: ['QG-MOTION-CREATIVE', 'QG-MOTION-FREEZE', 'QG-PRD-ACCEPTANCE'], responsibility: '判定风格 + 逐秒分镜（9 字段）；每 2-4s 必有明确视觉变化；observable_metric 禁写效果名', output_template: 'templates/motion_storyboard.md' },
  { name: '形式策略官', group: '表达音画', wave: 7, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D03', 'D05'], gates: ['QG-FORM-COMPETITION', 'QG-FIVE-DIM', 'QG-FORECAST', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '逐镜比较表达方案，声明数据杠杆、理解成本、制作成本、技术风险', output_template: 'templates/form_competition.md' },
  { name: '动效技术导演', group: '表达音画', wave: 9, activation: 'on_demand', dual_review: true, translation_layer: false, owns_dims: ['D02', 'D03', 'D05', 'D14', 'D18'], gates: ['QG-MOTION-FREEZE', 'QG-MEDIA-BLACK', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '对 GSAP/Three/Web3D/HTML 截帧做可行性/资产/性能/导出审查；接逐秒分镜拆组件任务清单', output_template: 'templates/motion_tech_plan.md' },
  { name: '声音设计师', group: '表达音画', wave: 11, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D06', 'D07', 'D19'], gates: ['QG-MEDIA-HEAD-RMS', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '配音、BGM 情绪、SFX、字幕方案；声音密度 ≥ 画面变化密度', output_template: 'templates/audio_plan.yaml' },
  // 增长复盘层 1（post，不在生产波次）
  { name: '数据复盘官', group: '增长复盘', wave: 'post', activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-FORECAST'], responsibility: '48h/7d 对比 forecast 与 actual，判定问题来源并反哺下条', output_template: 'templates/pre_publish_forecast.md' },
  // 带货扩展 4
  { name: '合规审核', group: '带货扩展', wave: 5, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-COMPLIANCE', 'QG-PRD-ACCEPTANCE'], responsibility: '广告法、绝对化用语、红线、平台规则；红区逐句标注', output_template: 'templates/subagent_prd_schema.md' },
  { name: '选品/商品分析师', group: '带货扩展', wave: 2, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: 'SKU 拆解、卖点、价位、目标人群、竞品对照；选品卡', output_template: 'templates/subagent_prd_schema.md' },
  { name: '消费者声音研究员', group: '带货扩展', wave: 2, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '挖真实槽点和决策路径；原话引用 5-10 条', output_template: 'templates/subagent_prd_schema.md' },
  { name: '销售脚本师', group: '带货扩展', wave: 5, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: ['D19'], gates: ['QG-ANTI-MEDIOCRITY', 'QG-PRD-ACCEPTANCE'], responsibility: '卖货话术、痛点放大、对比、限时福利、口播 CTA（与编剧叙事区分）', output_template: 'templates/anti_mediocrity_tournament.md' },
  // 出镜扩展 2
  { name: '演员/出镜表演指导', group: '出镜扩展', wave: 10, activation: 'format:出镜型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '口语化重写、表情/手势/眼神、节奏、机位建议；表演说明', output_template: 'templates/subagent_prd_schema.md' },
  { name: '造型/服装/场景', group: '出镜扩展', wave: 10, activation: 'format:出镜型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '穿搭、布景、品牌一致性、灯光色温；拍摄清单', output_template: 'templates/subagent_prd_schema.md' },
]

// 图文轮播不产出视频，跳过这些视频专属角色（与 registry.yaml formats.图文轮播.skip_roles 一致）
const CAROUSEL_SKIP = ['声音设计师', '动画导演', '动效技术导演']

// ── 19 维简表（注入 owns_dims 时给 agent 的维度名参照）──
const DIM_LABELS = {
  D01: '运镜', D02: '动效', D03: '特效', D04: '包装', D05: '转场', D06: '卡点', D07: '音频设计',
  D08: '节奏与信息密度', D09: '排版与图形', D10: '色彩与影调', D11: '光影', D12: '景别与构图',
  D13: '一致性', D14: '剪辑逻辑', D15: '视线引导', D16: '平台适配', D17: '无障碍', D18: '工程规范', D19: '情绪曲线',
}

// ── 确定性激活：形态 + overlays 决定角色集合，tier 不减角色 ──
function isVideoFormat(formatType) {
  return formatType !== '图文轮播'
}

function activateRoles(formatType, overlays) {
  const active = new Set([formatType])
  for (const o of (overlays || [])) active.add(o)
  const video = isVideoFormat(formatType)
  const carousel = formatType === '图文轮播'

  const activated = ROLE_REGISTRY.filter(r => {
    if (r.wave === 'post') return false // 发布后单独触发，不进生产波次
    if (carousel && CAROUSEL_SKIP.indexOf(r.name) !== -1) return false
    if (r.activation === 'always') return true
    if (r.activation === 'video_only') return video
    if (r.activation === 'on_demand') return video // 视频默认纳入（形式策略常选 GSAP/Web3D），可 no-op
    if (r.activation.indexOf('format:') === 0) {
      const fmt = r.activation.slice('format:'.length)
      return active.has(fmt)
    }
    return false
  })
  return activated
}

// ── 按 wave 字段分组，升序返回波次数组（每波是角色对象数组）──
function buildWaves(activatedRoles) {
  const byWave = {}
  for (const r of activatedRoles) {
    const w = r.wave
    if (!byWave[w]) byWave[w] = []
    byWave[w].push(r)
  }
  return Object.keys(byWave)
    .map(Number)
    .sort((a, b) => a - b)
    .map(w => byWave[w])
}

// ═══════════════════════════════════════════════════════════════════
// Schemas（与原 prd_pipeline 保持一致）
// ═══════════════════════════════════════════════════════════════════
const SUB_PRD_SCHEMA = {
  type: 'object',
  properties: {
    role: { type: 'string' },
    input_received: {
      type: 'object',
      properties: {
        resources: { type: 'array', items: { type: 'string' } },
        upstream_artifacts: { type: 'array', items: { type: 'string' } },
        known_gaps: {
          type: 'array',
          items: {
            type: 'object',
            properties: { gap: { type: 'string' }, user_decision: { type: 'string' } },
            required: ['gap', 'user_decision'],
          },
        },
      },
      required: ['resources', 'upstream_artifacts', 'known_gaps'],
    },
    deliverable: { type: 'string' },
    perceptual_goal: {
      type: 'object',
      properties: {
        statement: { type: 'string' },
        observable_metric: {
          type: 'string',
          description: '必须是可观察的数值/百分比/可数现象，禁止写"Ken Burns缓推""视差效果"这类效果名术语',
        },
      },
      required: ['statement', 'observable_metric'],
    },
    dims_addressed: {
      type: 'array',
      description: '本产出负责的 19 维维度（D01-D19），每项说明按「提升3档目标」怎么做，不是过基准就行',
      items: {
        type: 'object',
        properties: {
          dim: { type: 'string' },
          raise_3_target: { type: 'string' },
        },
        required: ['dim', 'raise_3_target'],
      },
    },
    implementation_approach: {
      type: 'object',
      properties: {
        method: { type: 'string' },
        why_this_fits_perceptual_goal: { type: 'string' },
      },
      required: ['method', 'why_this_fits_perceptual_goal'],
    },
    alternatives_considered: {
      type: 'array',
      items: {
        type: 'object',
        properties: { option: { type: 'string' }, why_rejected: { type: 'string' } },
        required: ['option', 'why_rejected'],
      },
      minItems: 1,
    },
    known_limitations: {
      type: 'array',
      items: {
        type: 'object',
        properties: { limitation: { type: 'string' }, impact: { type: 'string' } },
        required: ['limitation', 'impact'],
      },
    },
    acceptance_criteria: {
      type: 'array',
      items: {
        type: 'object',
        properties: { criterion: { type: 'string' }, how_to_verify: { type: 'string' } },
        required: ['criterion', 'how_to_verify'],
      },
      minItems: 1,
    },
  },
  required: [
    'role', 'input_received', 'deliverable', 'perceptual_goal',
    'implementation_approach', 'alternatives_considered', 'acceptance_criteria',
  ],
}

const ACCEPTANCE_SCHEMA = {
  type: 'object',
  properties: {
    role: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    reasoning: { type: 'string' },
  },
  required: ['role', 'verdict', 'reasoning'],
}

const INPUT_SLICE_SCHEMA = {
  type: 'object',
  properties: {
    slices: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          role: { type: 'string' },
          why_activated: { type: 'string' },
          input_summary: { type: 'string' },
        },
        required: ['role', 'why_activated', 'input_summary'],
      },
    },
  },
  required: ['slices'],
}

const CONSISTENCY_SCHEMA = {
  type: 'object',
  properties: {
    overall_consistent: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
    log_entry_draft: {
      type: 'object',
      properties: {
        project_id: { type: 'string' },
        role_reasoning_reviewed: { type: 'array', items: { type: 'string' } },
        errors_found: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              role: { type: 'string' },
              what_went_wrong: { type: 'string' },
              root_cause: {
                type: 'array',
                items: { type: 'string', enum: ['flow', 'cognition', 'mechanism'] },
              },
              should_have_done: { type: 'string' },
            },
            required: ['role', 'what_went_wrong', 'root_cause', 'should_have_done'],
          },
        },
        fix_applied: { type: 'string' },
        carry_forward: { type: 'string' },
      },
      required: ['project_id', 'role_reasoning_reviewed', 'errors_found', 'fix_applied', 'carry_forward'],
    },
  },
  required: ['overall_consistent', 'issues', 'log_entry_draft'],
}

// ═══════════════════════════════════════════════════════════════════
// 执行
// ═══════════════════════════════════════════════════════════════════
const totalPRD = (args && args.totalPRD) || ''
const productionTier = (args && args.productionTier) || 'explore'
const formatType = (args && args.formatType) || '演示型'
const projectId = (args && args.projectId) || '未命名项目'
const overlays = (args && args.overlays) || []
const executionLogPath = (args && args.executionLogPath) || 'docs/design/WORKFLOW_EXECUTION_LOG.md'

// ---- Phase 0: 读执行日志 ----
phase('读取执行日志')
const logRead = await agent(
  `用 Read 工具读 ${executionLogPath} 最近 5 条条目的 carry_forward 字段，` +
  '合并成一段简短摘要（不超过 300 字），作为本次新项目角色分派的前车之鉴。' +
  '如果文件不存在或没有条目，返回空字符串。',
  {
    label: '读执行日志',
    schema: { type: 'object', properties: { summary: { type: 'string' } }, required: ['summary'] },
  }
)

// ---- Phase 1: 角色激活（集合由代码确定性推导，agent 只补输入切片理由）----
phase('角色激活')
const activatedRoles = activateRoles(formatType, overlays)
const activatedNames = activatedRoles.map(r => r.name)
log(`形态=${formatType}${overlays.length ? '（叠加：' + overlays.join('、') + '）' : ''} · tier=${productionTier} · 确定性激活 ${activatedRoles.length} 个角色：${activatedNames.join('、')}`)

const sliceResp = await agent(
  '下面是本次已【确定激活】的角色清单（集合已由注册表 + 形态确定，不需要你增删角色，' +
  'production_tier 只影响后续验收强度，不减少角色）。请为每个角色产出 why_activated' +
  '（为什么这条内容需要它）和 input_summary（它应从总PRD里拿到哪部分作为输入）。\n\n' +
  `总PRD：\n${totalPRD}\n\n` +
  `形态=${formatType}，production_tier=${productionTier}。\n` +
  `角色清单（含各自职责）：\n${activatedRoles.map(r => `- ${r.name}：${r.responsibility}`).join('\n')}\n\n` +
  `前车之鉴：${logRead.summary}`,
  { label: '角色输入切片', schema: INPUT_SLICE_SCHEMA, effort: 'high' }
)

const sliceByRole = {}
for (const s of sliceResp.slices) sliceByRole[s.role] = s

// ---- Phase 2: 角色执行（按 wave 分波，波内并行，波间滚动传递已产出摘要）----
phase('角色执行')
const waves = buildWaves(activatedRoles)
const subPRDs = []
let waveIndex = 0
for (const wave of waves) {
  waveIndex += 1
  const producedSoFar = subPRDs.map(s => `【${s.role}】${s.deliverable}`).join('\n')

  const waveResults = await parallel(wave.map(roleObj => async () => {
    const role = roleObj.name
    const slice = sliceByRole[role]
    const guard = roleObj.translation_layer
      ? '⚠️ 本角色是"翻译层"：只描述这一镜/这一段该有什么感觉、变化量级多大，' +
        '禁止阅读或引用任何实现代码（ffmpeg/GSAP/Remotion 等语法），禁止用效果名术语代替可观察描述。'
      : ''
    const dimsText = roleObj.owns_dims.length
      ? '本角色在 19 维打分卡中【负责设计】以下维度（这是设计输入，不是事后验收）：\n' +
        roleObj.owns_dims.map(d => `  · ${d} ${DIM_LABELS[d] || ''}：按「提升3档目标」设计，不是「过基准就行」`).join('\n') +
        '\n务必在 dims_addressed 里逐维写出你的 raise_3_target。\n'
      : ''
    const gatesText = roleObj.gates.length
      ? `本产出须过的质量门（见 quality/quality_registry.md）：${roleObj.gates.join('、')}。\n`
      : ''
    const dualText = roleObj.dual_review
      ? '本角色产出后将走【两名独立评审 ≥90 门】（QG-REVIEWERS/QG-SCORECARD-90），设计时按此强度自我要求。\n'
      : ''
    return agent(
      `你是「${role}」。职责：${roleObj.responsibility}\n${guard}\n` +
      dimsText + gatesText + dualText +
      '\n【QG-RAISE-3 元规则】所有 gate/门/维度基准都是「地板（最低及格）」，不是验收目标。' +
      '每到"我觉得这能过"的时刻，那个"能过"的感觉本身就是"标准定低了"的信号——' +
      '强制把验收目标往上提 3 个档次，按抬高后的标准设计。大模型太容易只做到「及格分」，本条就是防这个。\n\n' +
      `总PRD相关切片：${slice ? slice.input_summary : ''}\n为什么需要你：${slice ? slice.why_activated : ''}\n` +
      `产出落地模板：${roleObj.output_template}\n` +
      `已产出的上游内容摘要：\n${producedSoFar || '（无，本波是第一批产出）'}\n\n` +
      `production_tier=${productionTier}（explore/lightweight 下 alternatives_considered 可只写 1 项；` +
      'full 下需 ≥2 项且来自不同实现家族）。\n' +
      '按 schema 结构化产出：input_received / deliverable / perceptual_goal' +
      '（statement + observable_metric，observable_metric 必须是可观察的数值/百分比/可数现象，' +
      '禁止写"Ken Burns缓推""视差效果"这类效果名术语）/ dims_addressed（负责的维度按提升3档写目标）/ ' +
      'implementation_approach / alternatives_considered（至少1个替代方案+为什么不选）/ ' +
      'known_limitations（允许有局限，诚实写不要隐瞒）/ ' +
      'acceptance_criteria（可操作核验动作，如"抽帧量化位移"，不是"效果好看"这种空话）。',
      { label: `角色执行:${role}`, phase: '角色执行', schema: SUB_PRD_SCHEMA, effort: 'high' }
    )
  }))
  subPRDs.push(...waveResults.filter(Boolean))
  log(`第 ${waveIndex} 波完成：${wave.map(r => r.name).join('、')}`)
}

// ---- Phase 3: 独立验收（验收者 ≠ 产出者）----
phase('独立验收')
const acceptanceResults = await parallel(subPRDs.map(sub => async () => agent(
  `独立验收「${sub.role}」的产出，你没有参与制作，只能看到下面这些信息：\n` +
  `deliverable 摘要：${sub.deliverable}\n` +
  `acceptance_criteria：${JSON.stringify(sub.acceptance_criteria)}\n` +
  `perceptual_goal.observable_metric：${sub.perceptual_goal ? sub.perceptual_goal.observable_metric : ''}\n` +
  `dims_addressed：${JSON.stringify(sub.dims_addressed || [])}\n` +
  '判定这份产出是否达标（二元 pass/fail，不打分不排名，不做锦标赛式比较）。\n' +
  '【QG-RAISE-3】验收基线是「提升3档目标」不是「过基准」：若产出只够到地板、observable_metric 空洞/' +
  '不可核验（只是效果名术语没有量级）、或 dims_addressed 的 raise_3_target 只是复述基准——直接 fail 并说明原因。',
  { label: `独立验收:${sub.role}`, phase: '独立验收', schema: ACCEPTANCE_SCHEMA, effort: 'medium' }
)))

const failedRoles = acceptanceResults.filter(Boolean).filter(v => v.verdict === 'fail')
if (failedRoles.length > 0) {
  log(`独立验收未通过：${failedRoles.map(f => f.role).join('、')}——需退回重做，不能带着 fail 直接交付。`)
}

// ---- Phase 4: 汇总复核 ----
phase('汇总复核')
const consistency = await agent(
  `总PRD：${totalPRD}\n\n` +
  `所有子PRD的deliverable摘要：${JSON.stringify(subPRDs.map(s => ({ role: s.role, deliverable: s.deliverable })))}\n` +
  `独立验收结果：${JSON.stringify(acceptanceResults.filter(Boolean))}\n\n` +
  '检查整体是否仍符合总PRD最初定义的"最终结果长什么样"（不是每个子PRD单独达标就等于整体对，' +
  '子agent组合有"各自达标但拼起来跑题"的风险，要专门检查这个）。\n' +
  '同时草拟一份 WORKFLOW_EXECUTION_LOG 的日志条目（log_entry_draft）：' +
  '列出这次协作执行过程中（不是内容对错，是流程/角色/验收环节本身）发现的问题，' +
  '没有问题就 errors_found 留空数组，但仍要写 carry_forward。' +
  `project_id 用 ${projectId}，` +
  'role_reasoning_reviewed 列出这次实际读了推理栏的角色名单（即 subPRDs 里的所有 role）。',
  { label: '汇总复核', schema: CONSISTENCY_SCHEMA, effort: 'high' }
)

return {
  formatType,
  productionTier,
  activatedRoles: activatedNames,
  subPRDs,
  acceptanceResults,
  failed: failedRoles.map(f => f.role),
  consistency,
}
