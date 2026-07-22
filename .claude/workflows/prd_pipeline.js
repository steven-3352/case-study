export const meta = {
  name: 'prd_pipeline',
  description: '用户-主LLM-子Agent 三层协作 Workflow：PRD拆解→角色执行→独立验收→汇总复核，强制每个被激活角色由独立agent产出可核验的感知目标，防止实现者自己兼任角色、自己验收自己',
  whenToUse: '任何新项目/新选题的正式制作阶段（PRD 已与用户对齐后调用）。args 需要 totalPRD/projectId/productionTier/formatType。production_tier 只影响验收强度（人数/是否锦标赛），不减少被激活的角色数量——这是本 workflow 要修复的核心事故（动画导演角色被实现者自己兼任、感知目标从未独立存在）。',
  phases: [
    { title: '读取执行日志', detail: '读 WORKFLOW_EXECUTION_LOG.md 最近条目的 carry_forward，作为本次角色分派的前车之鉴' },
    { title: 'PRD拆解', detail: '按 CLAUDE.md 角色清单 + production_tier 判定本次激活哪些角色，拆出每个角色的输入切片' },
    { title: '角色执行', detail: '按依赖顺序分波次并行执行，每个角色独立 agent() 产出 subagent_prd_schema 结构化子PRD' },
    { title: '独立验收', detail: '验收者与产出者是不同的 agent() 调用，只读 acceptance_criteria + 产出摘要，二元判定 pass/fail，不锦标赛' },
    { title: '汇总复核', detail: '检查整体是否仍符合总PRD的最终结果定义，草拟执行日志条目供主LLM复核后写入' },
  ],
}

// ---- 角色分波次目录（对应 CLAUDE.md 核心工作流程 21 通用角色）----
// 每一波内角色可并行；波与波之间保留粗粒度依赖顺序——
// 后一波的 prompt 会拿到前面所有波次已产出的 deliverable 滚动摘要，不是纯装饰性排序。
const ROLE_WAVES = [
  ['网络调研员'],
  ['选题深挖师'],
  ['内核提炼师', '领域专家', '事实校验员'],
  ['编导'],
  ['记者', '纪录片导演'],
  ['留存与互动设计师'],
  ['编剧'],
  ['视觉设计', '视觉语言策展师'],
  ['形式策略官'],
  ['动画导演'],
  ['动效技术导演', '声音设计师'],
  ['导演（执行）', '摄像/视觉'],
  ['剪辑', '运营/增长'],
]

const EXTENDED_ROLE_WAVES_ECOMMERCE = [
  ['合规审核', '选品/商品分析师', '消费者声音研究员'],
  ['销售脚本师'],
]

const EXTENDED_ROLE_WAVES_ONCAMERA = [
  ['演员/出镜表演指导', '造型/服装/场景'],
]

// 翻译层角色：只描述感知目标，禁止阅读实现语法/代码——
// 这次事故的根因就是实现者把"效果名字"当成了"效果已实现"，
// 让动画导演这类角色接触到 ffmpeg/GSAP 代码只会诱导它重复这个错误。
const TRANSLATION_LAYER_ROLES = ['动画导演']

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

const ROLE_ACTIVATION_SCHEMA = {
  type: 'object',
  properties: {
    production_tier_used: { type: 'string', enum: ['explore', 'lightweight', 'full'] },
    activated_roles: {
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
  required: ['production_tier_used', 'activated_roles'],
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

// ---- Phase 0: 读执行日志 ----
phase('读取执行日志')
const logRead = await agent(
  '读 docs/design/WORKFLOW_EXECUTION_LOG.md 最近 5 条条目的 carry_forward 字段，' +
  '合并成一段简短摘要（不超过 300 字），作为本次新项目角色分派的前车之鉴。' +
  '如果文件不存在或没有条目，返回空字符串。',
  {
    label: '读执行日志',
    schema: { type: 'object', properties: { summary: { type: 'string' } }, required: ['summary'] },
  }
)

// ---- Phase 1: PRD拆解 ----
phase('PRD拆解')
const totalPRD = (args && args.totalPRD) || ''
const productionTier = (args && args.productionTier) || 'explore'
const formatType = (args && args.formatType) || '演示型'
const projectId = (args && args.projectId) || '未命名项目'

const activation = await agent(
  '读 CLAUDE.md 的"核心工作流程"章节（21 个通用角色 + 带货 4 扩展 + 出镜 2 扩展）和"形态对照"表。\n' +
  `总PRD如下：\n${totalPRD}\n\n` +
  `production_tier=${productionTier}，形态=${formatType}。\n` +
  '按 CLAUDE.md 形态对照表判定本次要激活哪些角色（不因 production_tier 而减少角色数量，' +
  'production_tier 只影响后续验收强度，不影响这一步的角色列表）。' +
  '每个角色给出 why_activated（为什么这条内容需要它）和 input_summary（它将拿到总PRD里的哪部分）。\n' +
  `前车之鉴：${logRead.summary}`,
  { label: 'PRD拆解', schema: ROLE_ACTIVATION_SCHEMA, effort: 'high' }
)

// activation agent 返回的 role 名常带英文/别名后缀（如「选题深挖师 (Topic Deep-Digger)」、
// 「动画导演 / Motion Planner (🆕)」、「形式策略官 / 视觉策略官 (…)」），与 ROLE_WAVES 的
// 规范短名不精确相等。此前用精确相等匹配 → 全部角色被静默过滤 → 角色执行/独立验收两 phase 空转。
// 改为「activation 返回名 startsWith 规范短名」的归一化匹配，键一律用规范短名。
const allWaveRoles = ROLE_WAVES
  .concat(EXTENDED_ROLE_WAVES_ECOMMERCE, EXTENDED_ROLE_WAVES_ONCAMERA)
  .reduce((acc, w) => acc.concat(w), [])
const matchActivation = (canonical) =>
  activation.activated_roles.find(a => (a.role || '').startsWith(canonical))
const activatedRoleNames = {}
const activationByRole = {}
for (const canonical of allWaveRoles) {
  const a = matchActivation(canonical)
  if (a) { activatedRoleNames[canonical] = true; activationByRole[canonical] = a }
}
log(`本次激活 ${Object.keys(activatedRoleNames).length} 个角色（已归一化匹配）：${Object.keys(activatedRoleNames).join('、')}`)

// ---- Phase 2: 角色执行（分波次，波内并行，波间滚动传递已产出摘要）----
phase('角色执行')
let waves = ROLE_WAVES
if (formatType === '带货型') waves = waves.concat(EXTENDED_ROLE_WAVES_ECOMMERCE)
if (formatType === '出镜型') waves = waves.concat(EXTENDED_ROLE_WAVES_ONCAMERA)

const subPRDs = []
let waveIndex = 0
for (const wave of waves) {
  waveIndex += 1
  const rolesInWave = wave.filter(r => activatedRoleNames[r])
  if (rolesInWave.length === 0) continue

  const producedSoFar = subPRDs.map(s => `【${s.role}】${s.deliverable}`).join('\n')

  const waveResults = await parallel(rolesInWave.map(role => async () => {
    const a = activationByRole[role]
    const isTranslationLayer = TRANSLATION_LAYER_ROLES.indexOf(role) !== -1
    const guard = isTranslationLayer
      ? '本角色是"翻译层"：只描述这一镜/这一段该有什么感觉、变化量级多大，' +
        '禁止阅读或引用任何实现代码（ffmpeg/GSAP/Remotion 等语法），禁止用效果名术语代替可观察描述。'
      : ''
    return agent(
      `你是「${role}」。\n${guard}\n` +
      `总PRD相关切片：${a ? a.input_summary : ''}\n为什么需要你：${a ? a.why_activated : ''}\n` +
      `已产出的上游内容摘要：\n${producedSoFar || '（无，本波是第一批产出）'}\n\n` +
      `production_tier=${productionTier}（explore/lightweight 下 alternatives_considered 可以只写 1 项；` +
      'full 下需要 ≥2 项且来自不同实现家族）。\n' +
      '按 schema 结构化产出：input_received / deliverable / perceptual_goal' +
      '（statement + observable_metric，observable_metric 必须是可观察的数值/百分比/可数现象，' +
      '禁止写"Ken Burns缓推""视差效果"这类效果名术语）/ implementation_approach / ' +
      'alternatives_considered（至少1个替代方案+为什么不选）/ known_limitations（允许有局限，诚实写不要隐瞒）/ ' +
      'acceptance_criteria（可操作核验动作，比如"抽帧量化位移"这类，不是"效果好看"这种空话）。',
      { label: `角色执行:${role}`, phase: '角色执行', schema: SUB_PRD_SCHEMA, effort: 'high' }
    )
  }))
  subPRDs.push(...waveResults.filter(Boolean))
  log(`第 ${waveIndex} 波完成：${rolesInWave.join('、')}`)
}

// ---- Phase 3: 独立验收（验收者 ≠ 产出者）----
phase('独立验收')
const acceptanceResults = await parallel(subPRDs.map(sub => async () => agent(
  `独立验收「${sub.role}」的产出，你没有参与制作，只能看到下面这些信息：\n` +
  `deliverable 摘要：${sub.deliverable}\n` +
  `acceptance_criteria：${JSON.stringify(sub.acceptance_criteria)}\n` +
  `perceptual_goal.observable_metric：${sub.perceptual_goal ? sub.perceptual_goal.observable_metric : ''}\n` +
  '判定这份产出是否达标（二元 pass/fail，不打分不排名，不做锦标赛式比较）。' +
  '如果 observable_metric 本身写得空洞/不可核验（比如只是效果名术语没有量级），直接 fail 并说明原因。',
  { label: `独立验收:${sub.role}`, phase: '独立验收', schema: ACCEPTANCE_SCHEMA, effort: 'medium' }
)))

const failedRoles = acceptanceResults.filter(Boolean).filter(v => v.verdict === 'fail')
if (failedRoles.length > 0) {
  log(`独立验收未通过：${failedRoles.map(f => f.role).join('、')}——需要退回重做，不能带着 fail 直接交付。`)
}

// fail-closed 断言：角色执行 / 独立验收任一空手，就不许进汇总（否则汇总 agent 空转，
// 反而伪装出一份"看似复核过"的日志）。这是 wf_41d5ccea 那次角色名匹配 bug 暴露的教训。
const acceptedCount = acceptanceResults.filter(Boolean).length
const activatedCount = Object.keys(activatedRoleNames).length
if (subPRDs.length === 0 || acceptedCount === 0) {
  throw new Error(
    `[fail-closed] 角色执行/独立验收空手，拒绝进汇总：` +
    `激活 ${activatedCount} 角色，落盘子PRD ${subPRDs.length} 份，验收结果 ${acceptedCount} 份。` +
    `检查 activation 返回的 role 名是否与 ROLE_WAVES 归一化匹配失败。`
  )
}
if (subPRDs.length < activatedCount) {
  log(`⚠️ 子PRD ${subPRDs.length} 份 < 激活 ${activatedCount} 角色，有角色执行掉队，汇总时须核查缺哪几个。`)
}

// ---- Phase 4: 汇总复核 ----
phase('汇总复核')
const consistency = await agent(
  `总PRD：${totalPRD}\n\n` +
  `所有子PRD的deliverable摘要：${JSON.stringify(subPRDs.map(s => ({ role: s.role, deliverable: s.deliverable })))}\n` +
  `独立验收结果：${JSON.stringify(acceptanceResults.filter(Boolean))}\n\n` +
  '检查整体是否仍符合总PRD最初定义的"最终结果长什么样"（不是每个子PRD单独达标就等于整体对，' +
  '子agent组合有"各自达标但拼起来跑题"的风险，要专门检查这个）。\n' +
  '同时草拟一份 WORKFLOW_EXECUTION_LOG.md 的日志条目（log_entry_draft）：' +
  '列出这次协作执行过程中（不是内容对错，是流程/角色/验收环节本身）发现的问题，' +
  '没有问题就 errors_found 留空数组，但仍要写 carry_forward（哪怕是"这次顺利，继续保持XX"）。' +
  `project_id 用 ${projectId}，` +
  'role_reasoning_reviewed 列出这次实际读了推理栏的角色名单（即 subPRDs 里的所有 role）。',
  { label: '汇总复核', schema: CONSISTENCY_SCHEMA, effort: 'high' }
)

return {
  activation,
  subPRDs,
  acceptanceResults,
  consistency,
}
