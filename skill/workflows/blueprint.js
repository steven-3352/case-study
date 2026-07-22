export const meta = {
  name: 'blueprint',
  description: '蓝图即合约 · 预生产 workflow：吃大白话选题描述（可多主题）→ 扩展候选方向+推荐 → 自主跑理解/脚本/风格/形式/分镜（waves 1-10，止于分镜，不进制作）→ 组装人类可读蓝图（逐分镜大白话 + 每镜用哪几维 + 批量待确认项）。返回蓝图后由主 LLM 展示给用户【一次确认】，再调 prd_pipeline.js 无人值守制作。本 workflow 绝不写盘、绝不续跑到制作——这个硬停就是"只确认一次"的结构保证。',
  whenToUse: '用户抛来一个/多个新选题的大白话描述，想让引擎自主设计但先看一眼蓝图再拍板时。args: {briefs:[大白话...] 或 brief:"...", productionTier?, defaults?}。跑完把 blueprint_markdown 展示给用户，用户接受推荐或调整 batched_choices 后，再对每个定稿主题调 prd_pipeline.js。',
  phases: [
    { title: '主题扩展', detail: '每个 brief 扩展 3-5 条候选方向（形态/skin/受众/钩子），各带推荐标记与理由' },
    { title: '自主预生产', detail: '对每个主题的推荐方向跑 waves 1-10（理解→脚本→风格→形式→分镜），止于分镜不进制作' },
    { title: '蓝图组装', detail: '把技术分镜翻译成逐分镜大白话 + 每镜标注 D 维；跨主题汇总 batched_choices' },
  ],
}

// ═══════════════════════════════════════════════════════════════════
// 内嵌角色注册表镜像（从 roles/registry.yaml 派生 · 与 prd_pipeline.js 同源）
// 沙箱无 fs/import，两 workflow 各内嵌一份；validate.js 校验两份镜像 == registry.json。
// ═══════════════════════════════════════════════════════════════════
const ROLE_REGISTRY = [
  { name: '选题深挖师', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-INSIGHT-3FACTS', 'QG-PRD-ACCEPTANCE'], responsibility: '拆透选题——谁、什么场景、烦什么、要什么结果', output_template: 'templates/insights/topic_brief.md' },
  { name: '内核提炼师', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-INSIGHT-3FACTS', 'QG-PRD-ACCEPTANCE'], responsibility: '从调研中抽 3–5 条不可删关键信息 + 1 句价值锚', output_template: 'templates/insights/core_message.md' },
  { name: '领域专家', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '业务逻辑/流程；带货则品类决策链、竞品差异', output_template: 'templates/insights/domain_notes.md' },
  { name: '事实校验员', group: '理解', wave: 3, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '核对数据、SKU、引用；标红不可写；拦截洞察卡没有的卖点', output_template: 'templates/insights/fact_check.md' },
  { name: '网络调研员', group: '调研', wave: 2, activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-EXTERNAL-REFS', 'QG-PRD-ACCEPTANCE'], responsibility: '搜公开内容提炼痛点与可引用转述（≥3 URL、≥2 网络原话）', output_template: 'templates/insights/external_references.md' },
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
  { name: '留存与互动设计师', group: '表达音画', wave: 4, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D08', 'D15', 'D19'], gates: ['QG-ATTENTION', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '完播节拍、形式切换、互动 CTA；retention_beat_sheet', output_template: 'templates/retention_beat_sheet.md' },
  { name: '动画导演', group: '表达音画', wave: 6, activation: 'video_only', dual_review: false, translation_layer: true, owns_dims: ['D01', 'D02', 'D11', 'D12', 'D13'], gates: ['QG-MOTION-CREATIVE', 'QG-MOTION-FREEZE', 'QG-PRD-ACCEPTANCE'], responsibility: '判定风格 + 逐秒分镜（9 字段）；每 2-4s 必有明确视觉变化；observable_metric 禁写效果名', output_template: 'templates/motion_storyboard.md' },
  { name: '形式策略官', group: '表达音画', wave: 7, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D03', 'D05'], gates: ['QG-FORM-COMPETITION', 'QG-FIVE-DIM', 'QG-FORECAST', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '逐镜比较表达方案，声明数据杠杆、理解成本、制作成本、技术风险', output_template: 'templates/form_competition.md' },
  { name: '动效技术导演', group: '表达音画', wave: 9, activation: 'on_demand', dual_review: true, translation_layer: false, owns_dims: ['D02', 'D03', 'D05', 'D14', 'D18'], gates: ['QG-MOTION-FREEZE', 'QG-MEDIA-BLACK', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '对 GSAP/Three/Web3D/HTML 截帧做可行性/资产/性能/导出审查；接逐秒分镜拆组件任务清单', output_template: 'templates/motion_tech_plan.md' },
  { name: '声音设计师', group: '表达音画', wave: 11, activation: 'video_only', dual_review: true, translation_layer: false, owns_dims: ['D06', 'D07', 'D19'], gates: ['QG-MEDIA-HEAD-RMS', 'QG-REVIEWERS', 'QG-PRD-ACCEPTANCE'], responsibility: '配音、BGM 情绪、SFX、字幕方案；声音密度 ≥ 画面变化密度', output_template: 'templates/audio_plan.yaml' },
  { name: '数据复盘官', group: '增长复盘', wave: 'post', activation: 'always', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-FORECAST'], responsibility: '48h/7d 对比 forecast 与 actual，判定问题来源并反哺下条', output_template: 'templates/pre_publish_forecast.md' },
  { name: '合规审核', group: '带货扩展', wave: 5, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-COMPLIANCE', 'QG-PRD-ACCEPTANCE'], responsibility: '广告法、绝对化用语、红线、平台规则；红区逐句标注', output_template: 'templates/subagent_prd_schema.md' },
  { name: '选品/商品分析师', group: '带货扩展', wave: 2, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: 'SKU 拆解、卖点、价位、目标人群、竞品对照；选品卡', output_template: 'templates/subagent_prd_schema.md' },
  { name: '消费者声音研究员', group: '带货扩展', wave: 2, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '挖真实槽点和决策路径；原话引用 5-10 条', output_template: 'templates/subagent_prd_schema.md' },
  { name: '销售脚本师', group: '带货扩展', wave: 5, activation: 'format:带货型', dual_review: false, translation_layer: false, owns_dims: ['D19'], gates: ['QG-ANTI-MEDIOCRITY', 'QG-PRD-ACCEPTANCE'], responsibility: '卖货话术、痛点放大、对比、限时福利、口播 CTA（与编剧叙事区分）', output_template: 'templates/anti_mediocrity_tournament.md' },
  { name: '演员/出镜表演指导', group: '出镜扩展', wave: 10, activation: 'format:出镜型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '口语化重写、表情/手势/眼神、节奏、机位建议；表演说明', output_template: 'templates/subagent_prd_schema.md' },
  { name: '造型/服装/场景', group: '出镜扩展', wave: 10, activation: 'format:出镜型', dual_review: false, translation_layer: false, owns_dims: [], gates: ['QG-PRD-ACCEPTANCE'], responsibility: '穿搭、布景、品牌一致性、灯光色温；拍摄清单', output_template: 'templates/subagent_prd_schema.md' },
]

const CAROUSEL_SKIP = ['声音设计师', '动画导演', '动效技术导演']
const BLUEPRINT_LAST_WAVE = 10 // 预生产止于分镜（wave 10），不进制作 waves 11-13

const DIM_LABELS = {
  D01: '运镜', D02: '动效', D03: '特效', D04: '包装', D05: '转场', D06: '卡点', D07: '音频设计',
  D08: '节奏与信息密度', D09: '排版与图形', D10: '色彩与影调', D11: '光影', D12: '景别与构图',
  D13: '一致性', D14: '剪辑逻辑', D15: '视线引导', D16: '平台适配', D17: '无障碍', D18: '工程规范', D19: '情绪曲线',
}

function isVideoFormat(formatType) {
  return formatType !== '图文轮播'
}

// 确定性激活：形态决定角色集合，tier 不减角色（与 prd_pipeline 同逻辑）
function activateRoles(formatType, overlays) {
  const active = new Set([formatType])
  for (const o of (overlays || [])) active.add(o)
  const video = isVideoFormat(formatType)
  const carousel = formatType === '图文轮播'
  return ROLE_REGISTRY.filter(r => {
    if (r.wave === 'post') return false
    if (carousel && CAROUSEL_SKIP.indexOf(r.name) !== -1) return false
    if (r.activation === 'always') return true
    if (r.activation === 'video_only') return video
    if (r.activation === 'on_demand') return video
    if (r.activation.indexOf('format:') === 0) return active.has(r.activation.slice('format:'.length))
    return false
  })
}

// 按 wave 分组升序；预生产只保留 wave ≤ BLUEPRINT_LAST_WAVE
function buildPreProductionWaves(activatedRoles) {
  const byWave = {}
  for (const r of activatedRoles) {
    if (typeof r.wave !== 'number' || r.wave > BLUEPRINT_LAST_WAVE) continue
    if (!byWave[r.wave]) byWave[r.wave] = []
    byWave[r.wave].push(r)
  }
  return Object.keys(byWave).map(Number).sort((a, b) => a - b).map(w => byWave[w])
}

// ═══════════════════════════════════════════════════════════════════
// Schemas
// ═══════════════════════════════════════════════════════════════════
const TOPIC_EXPANSION_SCHEMA = {
  type: 'object',
  properties: {
    candidates: {
      type: 'array',
      minItems: 2,
      items: {
        type: 'object',
        properties: {
          direction_id: { type: 'string' },
          one_line: { type: 'string', description: '这条方向一句话说清是什么内容' },
          format: { type: 'string', enum: ['演示型', '知识型', '带货型', '出镜型', '图文轮播'] },
          overlays: { type: 'array', items: { type: 'string', enum: ['出镜型'] }, description: '可叠加形态，一般为空' },
          skin: {
            type: 'object',
            properties: {
              audience: { type: 'string' },
              persona_anchor: { type: 'string' },
              tone: { type: 'string' },
            },
            required: ['audience', 'persona_anchor', 'tone'],
          },
          hook: { type: 'string', description: '前 3s 钩子的大白话描述' },
          why: { type: 'string', description: '为什么这条值得做/它的差异点' },
          recommended: { type: 'boolean' },
        },
        required: ['direction_id', 'one_line', 'format', 'skin', 'hook', 'why', 'recommended'],
      },
    },
    recommended_id: { type: 'string' },
    recommendation_rationale: { type: 'string' },
  },
  required: ['candidates', 'recommended_id', 'recommendation_rationale'],
}

// 预生产每个角色的产出（比 prd_pipeline 的 SUB_PRD 精简：蓝图阶段只需可读摘要 + 负责维度）
const PREPROD_SUB_SCHEMA = {
  type: 'object',
  properties: {
    role: { type: 'string' },
    deliverable: { type: 'string', description: '这个角色的产出摘要（供下游与蓝图组装用）' },
    dims_addressed: {
      type: 'array',
      items: {
        type: 'object',
        properties: { dim: { type: 'string' }, raise_3_target: { type: 'string' } },
        required: ['dim', 'raise_3_target'],
      },
    },
    open_decisions: {
      type: 'array',
      description: '需要用户拍板的分叉点（没有则空数组）',
      items: {
        type: 'object',
        properties: {
          question: { type: 'string' },
          options: { type: 'array', items: { type: 'string' }, minItems: 2 },
          recommended_option: { type: 'string' },
          rationale: { type: 'string' },
        },
        required: ['question', 'options', 'recommended_option', 'rationale'],
      },
    },
  },
  required: ['role', 'deliverable', 'dims_addressed'],
}

// 蓝图组装：把技术分镜翻译成逐分镜大白话 + 每镜 D 维
const BLUEPRINT_SCHEMA = {
  type: 'object',
  properties: {
    topic_title: { type: 'string' },
    style_summary: { type: 'string', description: '整条风格一句话（用户能想象出画面质感）' },
    final_direction: {
      type: 'object',
      properties: {
        format: { type: 'string' },
        audience: { type: 'string' },
        hook: { type: 'string' },
        production_tier: { type: 'string', enum: ['explore', 'lightweight', 'full'] },
      },
      required: ['format', 'audience', 'hook', 'production_tier'],
    },
    shots: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        properties: {
          shot_no: { type: 'number' },
          duration_s: { type: 'number' },
          plain_language: { type: 'string', description: '大白话：这一镜最终画面长什么样、发生什么，用户读完能想象出来，不许写效果名术语' },
          vo_line: { type: 'string', description: '这一镜的口播（无则空字符串）' },
          dims_used: {
            type: 'array',
            description: '这一镜用到的 19 维维度 + 各自在本镜起什么作用',
            items: {
              type: 'object',
              properties: {
                dim: { type: 'string' },
                what_it_does: { type: 'string' },
              },
              required: ['dim', 'what_it_does'],
            },
          },
        },
        required: ['shot_no', 'duration_s', 'plain_language', 'dims_used'],
      },
    },
    known_risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['topic_title', 'style_summary', 'final_direction', 'shots'],
}

// ═══════════════════════════════════════════════════════════════════
// 预生产：对单个主题的定稿方向跑 waves 1-10，返回 subPRDs + 收集的待决点
// ═══════════════════════════════════════════════════════════════════
async function runPreProduction(topicTitle, direction, tier) {
  const formatType = direction.format || '演示型'
  const overlays = direction.overlays || []
  const activated = activateRoles(formatType, overlays)
  const waves = buildPreProductionWaves(activated)
  const subPRDs = []
  const openDecisions = []
  let waveIndex = 0

  for (const wave of waves) {
    waveIndex += 1
    const producedSoFar = subPRDs.map(s => `【${s.role}】${s.deliverable}`).join('\n')
    const results = await parallel(wave.map(roleObj => async () => {
      const role = roleObj.name
      const guard = roleObj.translation_layer
        ? '⚠️ 本角色是"翻译层"：只描述这一镜/这一段该有什么感觉、变化量级多大，禁止引用任何实现代码（ffmpeg/GSAP/Remotion 等语法），禁止用效果名术语代替可观察描述。'
        : ''
      const dimsText = roleObj.owns_dims.length
        ? '你在 19 维打分卡中【负责设计】：' +
          roleObj.owns_dims.map(d => `${d} ${DIM_LABELS[d] || ''}`).join('、') +
          '。每维按「提升3档目标」设计（不是过基准就行），并在 dims_addressed 里逐维写 raise_3_target。\n'
        : ''
      const gatesText = roleObj.gates.length ? `须过的质量门：${roleObj.gates.join('、')}。\n` : ''
      return agent(
        `你是「${role}」。职责：${roleObj.responsibility}\n${guard}\n` + dimsText + gatesText +
        '\n【QG-RAISE-3】所有 gate/维度基准都是"地板"，不是目标。"我觉得这能过"的感觉本身=标准定低了的信号，' +
        '强制把目标往上提 3 档再设计。大模型太容易只做到及格分，本条防这个。\n\n' +
        `主题：${topicTitle}\n定稿方向：${JSON.stringify(direction)}\n` +
        `production_tier=${tier}\n` +
        `已产出的上游摘要：\n${producedSoFar || '（无，本波第一批）'}\n\n` +
        '这是【预生产/蓝图阶段】：产出你这一环的设计结论摘要（deliverable），供下游和蓝图组装使用；' +
        '不要写制作代码。若有需要用户拍板的分叉，写进 open_decisions（每项带推荐 + 理由）；没有就留空数组。' +
        `产出落地模板参考：${roleObj.output_template}`,
        { label: `预生产:${role}`, phase: '自主预生产', schema: PREPROD_SUB_SCHEMA, effort: 'high' }
      )
    }))
    for (const r of results.filter(Boolean)) {
      subPRDs.push(r)
      for (const d of (r.open_decisions || [])) {
        openDecisions.push({ topic: topicTitle, role: r.role, ...d })
      }
    }
    log(`[${topicTitle}] 预生产第 ${waveIndex} 波完成：${wave.map(r => r.name).join('、')}`)
  }
  return { subPRDs, openDecisions, formatType, overlays }
}

// ═══════════════════════════════════════════════════════════════════
// 蓝图 markdown 渲染（在 JS 里确定性组装，不额外花 agent）
// ═══════════════════════════════════════════════════════════════════
function renderBlueprintMarkdown(topics, batchedChoices) {
  const L = []
  L.push('# 制作蓝图（合约） · 请确认')
  L.push('')
  L.push('> 下面是引擎为每个主题自主设计的蓝图。你可以逐镜看，也可以直接过。')
  L.push('> **确认后进入无人值守制作**：过程中的机器门 / 质量门 / 闭环上限照常运行（那不是人工干预），')
  L.push('> 只有闭环预算耗尽才会回来找你，而不是发残次品。')
  L.push('')

  if (batchedChoices.length) {
    L.push('## ⬛ 需要你拍板的点（已集中在此 · 每项带推荐）')
    L.push('')
    batchedChoices.forEach((c, i) => {
      L.push(`**${i + 1}. [${c.topic}]（${c.role}）${c.question}**`)
      c.options.forEach(o => {
        const star = o === c.recommended_option ? ' ⭐推荐' : ''
        L.push(`   - ${o}${star}`)
      })
      if (c.rationale) L.push(`   > 推荐理由：${c.rationale}`)
      L.push('')
    })
    L.push('> 不回复即视为全部采纳 ⭐推荐项。')
    L.push('')
  } else {
    L.push('## ⬛ 需要你拍板的点')
    L.push('')
    L.push('无分叉——各主题方向清晰，可直接确认进入制作。')
    L.push('')
  }

  topics.forEach((t, ti) => {
    const b = t.blueprint
    L.push('---')
    L.push('')
    L.push(`## 主题 ${ti + 1}：${b.topic_title}`)
    L.push('')
    L.push(`- **形态**：${b.final_direction.format}　**受众**：${b.final_direction.audience}　**生产档**：${b.final_direction.production_tier}`)
    L.push(`- **钩子**：${b.final_direction.hook}`)
    L.push(`- **风格**：${b.style_summary}`)
    if (t.alternatives && t.alternatives.length) {
      L.push(`- **其他候选方向**：${t.alternatives.map(a => a.one_line).join('；')}`)
    }
    L.push('')
    L.push('### 逐分镜（大白话 + 每镜用哪几维）')
    L.push('')
    b.shots.forEach(s => {
      L.push(`**镜 ${s.shot_no}（${s.duration_s}s）**：${s.plain_language}`)
      if (s.vo_line) L.push(`　口播：「${s.vo_line}」`)
      const dims = (s.dims_used || []).map(d => `${d.dim} ${DIM_LABELS[d.dim] || ''}（${d.what_it_does}）`)
      if (dims.length) L.push(`　用到的维度：${dims.join(' · ')}`)
      L.push('')
    })
    if (b.known_risks && b.known_risks.length) {
      L.push('### 已知风险')
      b.known_risks.forEach(r => L.push(`- ${r}`))
      L.push('')
    }
  })

  L.push('---')
  L.push('')
  L.push('确认方式：回复「全部按推荐做」，或指出要调整的编号/主题。确认后我对每个定稿主题调 `prd_pipeline.js` 无人值守制作，交付可发布内容 + publish.md。')
  return L.join('\n')
}

// ═══════════════════════════════════════════════════════════════════
// 执行
// ═══════════════════════════════════════════════════════════════════
const briefs = (args && args.briefs) || (args && args.brief ? [args.brief] : [])
const defaults = (args && args.defaults) || {}
const defaultTier = (args && args.productionTier) || defaults.productionTier || 'explore'

if (!briefs.length) {
  log('未收到任何 brief（args.briefs 或 args.brief）。请传入至少一条大白话选题描述。')
  return { error: 'no briefs', topics: [], blueprint_markdown: '', batched_choices: [] }
}

// ---- Phase 1: 主题扩展（每个 brief 并行）----
phase('主题扩展')
const expansions = await parallel(briefs.map((brief, i) => async () => agent(
  '你是编导。把下面这条大白话选题描述扩展成 3-5 条【不同角度】的候选方向，' +
  '每条声明 format（演示型/知识型/带货型/出镜型/图文轮播）、skin（受众/人设锚/话术方向）、hook（前3s钩子）、why（差异点），' +
  '并标记 recommended（恰好 1 条为 true），给出 recommended_id 和 recommendation_rationale。\n' +
  '候选之间要真的不同角度（不是同一条的措辞变体）。\n\n' +
  `选题描述：${brief}\n` +
  (defaults.audience ? `默认受众倾向：${defaults.audience}\n` : ''),
  { label: `主题扩展:${i + 1}`, phase: '主题扩展', schema: TOPIC_EXPANSION_SCHEMA, effort: 'high' }
)))

// ---- Phase 2: 自主预生产（对每个主题的推荐方向跑 waves 1-10）----
phase('自主预生产')
const topics = []
const batchedChoices = []

for (let i = 0; i < briefs.length; i++) {
  const exp = expansions[i]
  if (!exp) { log(`主题 ${i + 1} 扩展失败，跳过。`); continue }
  const rec = exp.candidates.find(c => c.direction_id === exp.recommended_id) ||
              exp.candidates.find(c => c.recommended) || exp.candidates[0]
  const alternatives = exp.candidates.filter(c => c !== rec)
  const topicTitle = rec.one_line

  // 把"选哪条方向"本身作为一个 batched choice（有其他候选时）
  if (alternatives.length) {
    batchedChoices.push({
      topic: topicTitle,
      role: '编导',
      question: `主题方向选择（brief：${briefs[i].slice(0, 30)}…）`,
      options: exp.candidates.map(c => c.one_line),
      recommended_option: rec.one_line,
      rationale: exp.recommendation_rationale,
    })
  }

  const tier = rec.production_tier || defaultTier
  const pre = await runPreProduction(topicTitle, rec, tier)
  for (const d of pre.openDecisions) {
    batchedChoices.push({
      topic: d.topic, role: d.role, question: d.question,
      options: d.options, recommended_option: d.recommended_option, rationale: d.rationale,
    })
  }

  // ---- Phase 3: 蓝图组装（把技术分镜翻译成逐镜大白话 + 每镜 D 维）----
  const preSummary = pre.subPRDs.map(s =>
    `【${s.role}】${s.deliverable}` +
    (s.dims_addressed && s.dims_addressed.length
      ? `\n  负责维度：${s.dims_addressed.map(d => `${d.dim}(${d.raise_3_target})`).join('；')}`
      : '')
  ).join('\n')

  const blueprint = await agent(
    '你是蓝图组装官。把下面这轮预生产的所有角色产出，翻译成一份【用户能看懂的逐分镜蓝图】。\n' +
    '要求：\n' +
    '1. 每个分镜 plain_language 用大白话写"最终画面长什么样、发生什么"，用户读完能在脑子里想象出画面——' +
    '禁止写"Ken Burns""视差""match-cut"这类效果名术语，要写成"镜头缓缓推近老板的手，桌上文件从模糊变清晰"这种。\n' +
    '2. 每个分镜 dims_used 标注这一镜用到了 19 维里的哪几维，each 写 what_it_does（这一维在本镜起什么作用）。\n' +
    '3. style_summary 一句话让用户想象出整条质感。final_direction 带 production_tier。\n' +
    '4. known_risks 诚实写预生产暴露的风险。\n\n' +
    `主题：${topicTitle}\n定稿方向：${JSON.stringify(rec)}\ntier：${tier}\n\n` +
    `预生产产出汇总：\n${preSummary}`,
    { label: `蓝图组装:${topicTitle}`, phase: '蓝图组装', schema: BLUEPRINT_SCHEMA, effort: 'high' }
  )

  topics.push({
    brief: briefs[i],
    chosen_direction: rec,
    alternatives,
    tier,
    formatType: pre.formatType,
    overlays: pre.overlays,
    subPRDs: pre.subPRDs,
    blueprint,
  })
  log(`主题 ${i + 1} 蓝图完成：${topicTitle}（${blueprint.shots.length} 镜）`)
}

const blueprintMarkdown = renderBlueprintMarkdown(topics, batchedChoices)

return {
  topics,
  batched_choices: batchedChoices,
  blueprint_markdown: blueprintMarkdown,
  next_step: '把 blueprint_markdown 展示给用户 → 用户一次确认（接受推荐或调整）→ 对每个定稿主题调 prd_pipeline.js（args: {totalPRD, projectId, productionTier, formatType, overlays}）无人值守制作。blueprint.js 到此为止，绝不自动续跑制作。',
}
