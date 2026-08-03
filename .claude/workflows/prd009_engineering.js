export const meta = {
  name: 'prd009_engineering',
  description: 'PRD-009 Audio-First 自动补料 工程实施 — 独立角色 agent() 分工 → 独立验收，满足 §四 四条件',
  phases: [
    { title: '读执行日志', detail: 'WORKFLOW_EXECUTION_LOG.md carry_forward 摘要' },
    { title: '架构守门', detail: '读 PRD-009 全文，逐条核实 6 项 blocker 已覆盖' },
    { title: 'Phase 0 实施', detail: '_PROJECT_DIRECTORIES + import_project_asset 未知类型入 materials 桶' },
    { title: 'Phase 1+2 实施', detail: 'FasterWhisper transcribe() 质量门 ‖ _CHORUS_MARKERS + character_design 命名三规则' },
    { title: 'Phase 3a 门改造', detail: 'blocker-1 优先：service.py 两道门改读磁盘桶，删 :3501/:3553 计数校验' },
    { title: 'Phase 3b 编排+计费', detail: 'materialize 四步编排 §4.4 + _record_cost 幂等键 §4.4.4' },
    { title: 'Phase 3c API+前端', detail: 'POST /api/v1/jobs/{id}/materialize 端点 + 文件夹上传 UI' },
    { title: 'Phase 4 测试', detail: '§7.1 用例 a/a2/a3/b + 逆向断言' },
    { title: '独立验收', detail: '4 维验收者 ≠ 实现者，二元 PASS/FAIL' },
    { title: '汇总复核', detail: '整体一致性 + 执行日志草稿' },
  ],
}

// ─── Schema ──────────────────────────────────────────────────────────────────

const ARCH_SCHEMA = {
  type: 'object',
  required: ['role', 'constraints_verified', 'risks', 'go'],
  properties: {
    role: { type: 'string' },
    constraints_verified: {
      type: 'array',
      minItems: 6,
      items: {
        type: 'object',
        required: ['blocker_id', 'section', 'verdict', 'reason'],
        properties: {
          blocker_id: { type: 'string' },
          section: { type: 'string' },
          verdict: { type: 'string', enum: ['COVERED', 'PARTIAL', 'MISSING'] },
          reason: { type: 'string' },
        },
      },
    },
    risks: { type: 'array', items: { type: 'string' } },
    go: { type: 'boolean' },
  },
}

const IMPL_SCHEMA = {
  type: 'object',
  required: ['role', 'prd_sections_read', 'files_changed', 'constraints_respected', 'blockers_hit', 'done'],
  properties: {
    role: { type: 'string' },
    prd_sections_read: { type: 'array', items: { type: 'string' } },
    files_changed: {
      type: 'array',
      items: {
        type: 'object',
        required: ['path', 'change_type', 'summary'],
        properties: {
          path: { type: 'string' },
          change_type: { type: 'string', enum: ['MODIFY', 'NEW_FILE', 'DELETE_LINES', 'ADD_LINES'] },
          summary: { type: 'string' },
          key_additions: { type: 'string' },
        },
      },
    },
    constraints_respected: { type: 'array', items: { type: 'string' } },
    blockers_hit: { type: 'array', items: { type: 'string' } },
    done: { type: 'boolean' },
  },
}

const ACCEPT_SCHEMA = {
  type: 'object',
  required: ['role', 'target_phase', 'verdict', 'checks'],
  properties: {
    role: { type: 'string' },
    target_phase: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'FAIL', 'PARTIAL'] },
    checks: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        required: ['criterion', 'result', 'note'],
        properties: {
          criterion: { type: 'string' },
          result: { type: 'string', enum: ['PASS', 'FAIL', 'SKIP'] },
          note: { type: 'string' },
        },
      },
    },
    fail_reasons: { type: 'array', items: { type: 'string' } },
  },
}

// ─── Workflow 正文 ─────────────────────────────────────────────────────────────
// §四 要求 1：先读执行日志
phase('读执行日志')
const logSummary = await agent(
  `读 /home/ubuntu/case-study/docs/design/WORKFLOW_EXECUTION_LOG.md 全文。
提取：①最近两次运行的 carry_forward 要点；②曾出现的 errors_found 模式及修复方法；
③曾用过的工程角色名（排除内容创作角色如编剧/动画导演）。
返回纯文本，不超过 500 字。`,
  { label: '执行日志摘要', phase: '读执行日志' }
)
log(`执行日志摘要：${String(logSummary).slice(0, 400)}`)

// 架构守门人 — 独立读 PRD-009 全文，逐条核实 6 项 blocker
phase('架构守门')
const archResult = await agent(
  `你是「架构守门人」，角色只读不写，不做任何代码修改。

读以下文件（全文）：
- /home/ubuntu/case-study/docs/design/PRD-009-AUDIO-FIRST-AUTO-MATERIALIZATION.md
- /home/ubuntu/case-study/mv_platform/domain/contracts.py（JobSpec 定义）
- /home/ubuntu/case-study/mv_platform/application/service.py 行 140-165、1315-1435、3080-3110、3480-3570
- /home/ubuntu/case-study/src/mvstudio/director/intake.py 行 185-200

逐条核实 6 项 blocker 在 PRD 正文中的覆盖情况：
blocker-1: input_refs 不可变→门改读磁盘桶 §2.1.1
blocker-2: 角色文件命名矛盾→§4.3.1 三规则（stem==角色名，10位小写hex，brief.characters留空）
blocker-3: 混合合唱 林渊+合→_CHORUS_MARKERS 常量，两处共用
blocker-4: hash 格式未锁定→hexdigest()[:10] 恰好10位
blocker-5: 计费去重键未定义→§4.4.4 step_id/metadata 确定性规则
blocker-6: 用户覆盖去重→桶严格1文件 + 前端删除按钮（provenance 标记）

输出 ARCH_SCHEMA。go=true 仅在全部6项 COVERED 且无 P0 风险时成立。`,
  { label: '架构守门人', phase: '架构守门', schema: ARCH_SCHEMA }
)

if (!archResult?.go) {
  const missing = (archResult?.constraints_verified ?? [])
    .filter(c => c.verdict !== 'COVERED')
    .map(c => `  ${c.blocker_id}[${c.verdict}] §${c.section}: ${c.reason}`)
    .join('\n')
  log(`⛔ 架构守门未通过，停止实施:\n${missing}`)
  return { status: 'ARCH_BLOCKED', archResult }
}
log(`✅ 架构守门 PASS — 6 项 blocker 全部 COVERED，开始实施`)

// ── Phase 0：导入放宽（独立实现者）──────────────────────────────────────────
phase('Phase 0 实施')
const p0 = await agent(
  `你是「Phase 0 实现者」。任务：放宽导入门，未知文件类型写入 materials 桶而非静默丢弃。

先读：
- PRD-009 §3.1 §3.2 §6.1 §6.2
- /home/ubuntu/case-study/mv_platform/application/service.py 行 140-165（_PROJECT_DIRECTORIES）
  和行 1315-1435（_IMPORT_EXTENSIONS + import_project_asset）

执行以下代码改动（用 Edit 工具直接写入文件，不是仅描述）：
1. _PROJECT_DIRECTORIES（约行 145）：在现有条目中增加 "inputs/materials" 条目
2. import_project_asset unknown-ext 分支（约行 1420-1430）：
   将 {"ignored": True} 路径改为写入 inputs/materials/{filename}，
   并在返回值中带 bucket="inputs/materials"，不再返回 ignored=True
3. 不改 _IMPORT_EXTENSIONS whitelist（whitelist 保持原样）
4. 不改 JobSpec、不改 job_id、不改任何 gate 逻辑

完成后返回一段纯文本，说明你做了哪些改动。`,
  { label: 'Phase 0 实现者', phase: 'Phase 0 实施' }
)
if (p0?.blockers_hit?.length) log(`⚠️ Phase 0 新 blocker: ${p0.blockers_hit.join('; ')}`)
log(`Phase 0 done=${p0?.done}，改动文件: ${(p0?.files_changed ?? []).map(f => f.path).join(', ')}`)

// ── Phase 1 + Phase 2：并行实施（不同文件，无冲突）─────────────────────────
phase('Phase 1+2 实施')
const [p1, p2] = await parallel([
  // Phase 1：歌词转录（FasterWhisper transcribe 新方法）
  () => agent(
    `你是「Phase 1 实现者」。任务：为 FasterWhisperAlignmentPort 增加 transcribe() 方法。

先读：
- PRD-009 §4.1 §4.2 §4.2.1
- /home/ubuntu/case-study/src/mvstudio/providers/alignment_faster_whisper.py（全文）

执行改动（用 Edit 工具）：
1. 在 FasterWhisperAlignmentPort 类中新增 transcribe(self, audio_path, language="zh") 方法
   - 调用 faster_whisper model.transcribe()，不传 reference transcript
   - 返回原始 segments 列表（list[Segment]）和 detected_language
2. §4.2.1 质量门：转录后检测 word_count vs audio_duration_s；
   若 word_count / duration_s > 8.0（幻觉阈值），在返回值中标 hallucination_risk=True
3. 不改已有 align() 方法签名和逻辑
4. 不改 intake.py 或 service.py

完成后返回纯文本，说明做了哪些改动。`,
    { label: 'Phase 1 实现者', phase: 'Phase 1+2 实施' }
  ),
  // Phase 2：合唱标记常量 + character_design 命名规则
  () => agent(
    `你是「Phase 2 实现者」。任务：提取 _CHORUS_MARKERS 常量并落实角色命名三规则。

先读：
- PRD-009 §4.3 §4.3.1
- /home/ubuntu/case-study/src/mvstudio/director/intake.py 行 180-210（_split_character_names）
- /home/ubuntu/case-study/src/mvstudio/director/drafting.py 行 370-430（_bind_director_cast, _characters）

执行改动（用 Edit 工具）：
1. intake.py：在模块顶部（import 区块后、第一个 def 前）新增：
   _CHORUS_MARKERS = frozenset({"合"})
2. intake.py _split_character_names 约行 192：将硬编码 'if value == "合"' 改为
   'if value in _CHORUS_MARKERS'；若有未知标记 raise ValueError 给出可读错误消息
3. 不改 _split_character_names 返回值结构
4. 不改 drafting.py（character_design executor 在 Phase 3b 处理）
5. 不改 service.py

§4.3.1 三命名规则（记录如下，供 Phase 3b 实现者参考，本阶段不新建文件）：
规则1: executor 生成的角色文件 stem 必须 == 合约角色名（不是id）
规则2: hash 后缀 == hexdigest()[:10]（恰好10位小写十六进制）
规则3: brief.characters 保持空列表，让 _characters 走 stem 推导

完成后返回纯文本，说明做了哪些改动。`,
    { label: 'Phase 2 实现者', phase: 'Phase 1+2 实施' }
  ),
])
if (!p1?.done) log(`⚠️ Phase 1 未完成: ${(p1?.blockers_hit ?? []).join('; ')}`)
if (!p2?.done) log(`⚠️ Phase 2 未完成: ${(p2?.blockers_hit ?? []).join('; ')}`)

// ── Phase 3a：门改造（blocker-1，最先落地，其他编排依赖它）────────────────
phase('Phase 3a 门改造')
const p3a = await agent(
  `你是「Phase 3a 实现者」。任务：service.py 两道门改读磁盘桶（blocker-1 地基，必须先于编排）。

先读：
- PRD-009 §2.1.1 §4.4.3
- /home/ubuntu/case-study/mv_platform/application/service.py 行 3480-3580（start_director_intake + _start_director_animatic_test）
- /home/ubuntu/case-study/mv_platform/domain/contracts.py（确认 JobSpec.input_refs 是 Tuple[str,...]，不可变）

执行改动（用 Edit 工具，改 service.py）：
1. start_director_intake（约行 3484）门卫段：
   - 删除原 input_refs 计数校验（约行 3499-3502）
   - 改为读磁盘桶：audio_count = len(list((project_dir/"inputs/audio").glob("*")))
     lyrics_count = len(list((project_dir/"inputs/lyrics").glob("*")))
     char_count   = len(list((project_dir/"inputs/characters").glob("*")))
   - 判断：audio_count != 1 → raise 或返回 gate_fail（按现有错误模式）
   - lyrics_count < 1 或 char_count < 1 → 不阻断（软门，由编排层补齐）
2. start_director_intake staging 循环（约行 3507-3517）：
   - 改为遍历磁盘桶文件：list((project_dir/"inputs/audio").glob("*")) 等，
     而非遍历 job.input_refs
3. _start_director_animatic_test（约行 3549-3553）：
   - 同样删除 input_refs 计数校验（约行 3553）
   - staging 循环改读磁盘桶（同上逻辑）
4. 不改 JobSpec，不改 job_id，不改 add_job

完成后返回纯文本，说明做了哪些改动。`,
  { label: 'Phase 3a 实现者', phase: 'Phase 3a 门改造' }
)
if (!p3a?.done) log(`⚠️ Phase 3a 未完成，后续编排可能无法运行: ${(p3a?.blockers_hit ?? []).join('; ')}`)
else log(`✅ Phase 3a 完成 — 两道门已改读磁盘桶`)

// ── Phase 3b：编排 + 计费去重（在 3a 完成后才能安全写 service.py）──────────
phase('Phase 3b 编排+计费')
const p3b = await agent(
  `你是「Phase 3b 实现者」。任务：实现 materialize 四步编排和计费幂等键。
Phase 3a 已完成磁盘桶门改造，你在此基础上继续写 service.py。

先读：
- PRD-009 §4.4 §4.4.1 §4.4.4 §5.2 §5.3
- /home/ubuntu/case-study/mv_platform/application/service.py 行 3080-3110（_record_cost）
- /home/ubuntu/case-study/mv_platform/application/service.py 行 4450-4470（submit_job 及其 job_id）
- /home/ubuntu/case-study/src/mvstudio/director/intake.py（_split_character_names、_CHORUS_MARKERS——Phase 2 已加）

执行改动（用 Edit 工具，改 service.py）：
1. 新增 async def _materialize_job(self, project_id, job_id, confirm_billing):
   步骤严格按 §4.4 四步顺序：
   a. 检查 inputs/audio/ 桶恰好1个文件；否则 raise MaterializeError("no_audio")
   b. 检查 inputs/lyrics/ 桶；为空则调用 self._run_lyrics_transcribe(project_id, job_id)
      - step_id = "materialize:lyrics:<audio_file_stem_hash10>"（§4.4.4 幂等键）
      - 调用 _record_cost(project_id, job_id, step_id, "whisper", {})
   c. 检查 inputs/characters/ 桶；为空则读歌词推导角色名列表，
      为每个非合唱角色调用 self._run_character_design(project_id, job_id, char_name)
      - step_id = "materialize:character:<char_name>"（§4.4.4）
      - 调用 _record_cost(project_id, job_id, step_id, "image_gen", {})
   d. 调用 start_director_intake（门此时读桶，桶已齐）
2. _materialize_job 只写磁盘桶，不调用 add_job 或 update_job
3. 新增 pending_materialization 计算方法（读桶状态，返回缺少哪些料）
4. 所有 _record_cost 调用的 metadata 参数不含时间戳或随机值（保持确定性）

完成后返回纯文本，说明做了哪些改动。`,
  { label: 'Phase 3b 实现者', phase: 'Phase 3b 编排+计费' }
)
if (!p3b?.done) log(`⚠️ Phase 3b 未完成: ${(p3b?.blockers_hit ?? []).join('; ')}`)
else log(`✅ Phase 3b 完成 — materialize 编排 + 计费幂等键落地`)

// ── Phase 3c-1：API 端点（单一职责）─────────────────────────────────────────
phase('Phase 3c API+前端')
const p3cApi = await agent(
  `你是「Phase 3c API 实现者」。单一任务：在 FastAPI 路由层新增 POST /api/v1/jobs/{job_id}/materialize 端点。

第一步：用 Bash 找到路由文件位置：
  find /home/ubuntu/case-study/apps/mv_api -name "*.py" | xargs grep -l "jobs" 2>/dev/null
  然后读找到的路由文件，了解现有路由结构和 service 调用方式。

第二步：阅读 PRD-009 §5 的端点规格。

第三步：用 Edit 工具在找到的路由文件中新增端点：
  - 路由: POST /api/v1/jobs/{job_id}/materialize
  - Request body: {"confirm_billing": bool}（Pydantic model 或 dict）
  - confirm_billing 缺失/false → 返回 HTTP 422，body {"error":"billing_confirmation_required"}
  - 调用 await service._materialize_job(project_id, job_id, confirm_billing)
    （project_id 从 job 记录查，参考现有路由从 job 取 project_id 的方式）
  - 成功返回 {"status":"ok","pending_materialization": await service.pending_materialization(...)}
  - 不改任何其他路由或 service 层

完成所有代码改动后，返回纯文本说明做了哪些改动（不需要结构化JSON）。`,
  { label: 'Phase 3c-1 API实现者', phase: 'Phase 3c API+前端' }
)
if (!p3cApi?.done) log(`⚠️ Phase 3c API 未完成: ${(p3cApi?.blockers_hit ?? []).join('; ')}`)
else log(`✅ Phase 3c API 完成`)

// ── Phase 3c-2：前端文件夹上传 UI（无 schema，验收由独立 agent 读文件确认）──
const p3cFe = await agent(
  `你是「Phase 3c 前端实现者」。目标文件已知：
  /home/ubuntu/case-study/apps/mv_api/static/index.html
  /home/ubuntu/case-study/apps/mv_api/static/app.js

先读这两个文件，再阅读 PRD-009 §6.1 §6.2 §6.3。

用 Edit 工具做以下四项改动：
1. index.html 中文件选择 <input type="file">：加 webkitdirectory directory 属性，令用户可选整个文件夹
2. app.js 上传后检测逻辑：若上传内容无歌词文件（.lrc/.txt/.xlsx）或无角色图（.png/.jpg/.webp），
   在界面显示软门提示「缺少歌词/角色，将自动补齐，确认后计费」，并显示确认按钮（confirm_billing）
3. intake 展示区域：若素材对象含 provenance=="auto_generated" 字段，
   在该素材旁显示「自动生成」小标签（可用简单 <span class="tag-auto">自动生成</span>）
4. 「删除」按钮：自动生成素材旁增加删除按钮，调用 DELETE /api/v1/projects/{project_id}/assets/{asset_id}

只改这两个文件，不改 Python 后端。完成后返回一段纯文本，说明做了哪4项改动（不需要JSON）。`,
  { label: 'Phase 3c-2 前端实现者', phase: 'Phase 3c API+前端' }
)
log(`Phase 3c 前端: ${String(p3cFe ?? '').slice(0, 200)}`)

const p3c = { done: !!p3cApi?.done, sub: { api: p3cApi, fe: p3cFe } }

// ── Phase 4：测试补全 ────────────────────────────────────────────────────────
phase('Phase 4 测试')
const p4 = await agent(
  `你是「Phase 4 测试工程师」。任务：按 PRD-009 §7.1 写测试用例并运行。

先读：
- PRD-009 §7 §7.1（测试用例 a / a2 / a3 / b）
- /home/ubuntu/case-study/（找到现有测试目录，如 tests/ 或 mv_platform/tests/）
- /home/ubuntu/case-study/src/mvstudio/director/intake.py（_CHORUS_MARKERS、_split_character_names）
- /home/ubuntu/case-study/src/mvstudio/director/drafting.py（_bind_director_cast 行 377-396）

按 §7.1 实现以下4个测试（用 Write/Edit 工具写入测试文件）：
(a) 角色命名 + 绑定：
    - 生成文件名 "林渊-abc123def4.png"（stem="林渊"，10位hex）
    - 调用 _bind_director_cast，断言 binding 成功
    - 逆向断言：文件名 "C01-abc123def4.png" 绑定失败，"林渊-abc123.png"（6位hex）绑定失败
(a2) gate 读磁盘桶：
    - 创建临时项目目录，inputs/audio/ 放1个 mp3
    - 调用 materialize（mock transcribe+image gen）
    - 断言 intake 被调用，input_refs 行数不变（不可变验证）
(a3) 混合合唱处理：
    - 歌词 cells 含 "林渊+合"
    - 调用 _split_character_names，断言返回 ["林渊", "合"]
    - 调用 character_design 路径，断言只为 "林渊" 生成图，不为 "合" 生成
(b) 计费去重：
    - 同一 (project_id, job_id, step_id) 调用 _record_cost 两次
    - 断言 cost_entries 行数 == 1（INSERT OR IGNORE 幂等）

在测试文件顶部写清楚依赖和 mock 策略。
完成后用 python -m pytest <test_file> -v 运行并贴出输出。
完成后返回纯文本：列出写了哪个测试文件，并贴出 pytest 运行输出。`,
  { label: 'Phase 4 测试工程师', phase: 'Phase 4 测试' }
)
if (!p4?.done) log(`⚠️ Phase 4 测试未完成: ${(p4?.blockers_hit ?? []).join('; ')}`)
else log(`✅ Phase 4 测试完成`)

// ── 独立验收（§四 要求 3：验收者 ≠ 实现者）────────────────────────────────
phase('独立验收')
const acceptResults = await parallel([
  // 验收维度 1：gate 改造（p3a 的产物）
  () => agent(
    `你是「gate 改造验收者」，独立验收 Phase 3a 的产物，不查看 p3a 实现者的报告。

读 /home/ubuntu/case-study/mv_platform/application/service.py 行 3480-3580。
逐条核实：
1. start_director_intake 门卫段是否已改读磁盘桶（inputs/audio/ inputs/lyrics/ inputs/characters/）
2. input_refs 计数校验（原约行 3499-3502）是否已删除
3. staging 循环是否遍历磁盘文件而非 job.input_refs
4. _start_director_animatic_test 门卫段是否同样改读磁盘桶（原约行 3553 计数校验已删）
5. JobSpec 和 add_job 未被修改（不可变约束保持）
输出 ACCEPT_SCHEMA（target_phase="Phase 3a"）。`,
    { label: 'gate 改造验收者', phase: '独立验收', schema: ACCEPT_SCHEMA }
  ),
  // 验收维度 2：intake.py + 命名规则（p2 的产物）
  () => agent(
    `你是「Phase 2 验收者」，独立验收 Phase 2 的产物。

读 /home/ubuntu/case-study/src/mvstudio/director/intake.py 行 1-30（模块顶部常量区）和行 180-210。
逐条核实：
1. 模块顶部是否存在 _CHORUS_MARKERS = frozenset({"合"})
2. _split_character_names 约行 192 是否改为 "if value in _CHORUS_MARKERS"
3. 未知标记是否 raise ValueError（可读错误消息）
4. 原有 align() 方法签名未被修改
读 /home/ubuntu/case-study/src/mvstudio/director/drafting.py 行 377-396。
5. _bind_director_cast 的 stem 推导逻辑（re.sub strip hash）未被修改
输出 ACCEPT_SCHEMA（target_phase="Phase 2"）。`,
    { label: 'Phase 2 验收者', phase: '独立验收', schema: ACCEPT_SCHEMA }
  ),
  // 验收维度 3：编排 + 计费（p3b 的产物）
  () => agent(
    `你是「编排计费验收者」，独立验收 Phase 3b 的产物。

读 /home/ubuntu/case-study/mv_platform/application/service.py（搜索 _materialize_job）。
逐条核实：
1. _materialize_job 存在且按四步顺序：audio检查→lyrics补→character补→intake
2. 不调用 add_job 或 update_job（只写磁盘桶）
3. lyrics step_id 格式为 "materialize:lyrics:<hash10>"（确定性，无时间戳）
4. character step_id 格式为 "materialize:character:<角色名>"（确定性）
5. _record_cost 的 metadata 参数不含时间戳或随机值
6. pending_materialization 方法读桶状态（不读 input_refs）
输出 ACCEPT_SCHEMA（target_phase="Phase 3b"）。`,
    { label: '编排计费验收者', phase: '独立验收', schema: ACCEPT_SCHEMA }
  ),
  // 验收维度 4：测试（p4 的产物）
  () => agent(
    `你是「测试验收者」，独立验收 Phase 4 的产物。

先找测试文件（搜 /home/ubuntu/case-study 中最近修改的 test_*.py 文件）。
逐条核实：
1. 用例 (a)：正向绑定 + 逆向断言（错误命名格式绑定失败）均存在
2. 用例 (a2)：gate 读磁盘桶测试存在，含 input_refs 不变断言
3. 用例 (a3)：混合合唱 "林渊+合" 测试存在，只为"林渊"生图
4. 用例 (b)：计费去重测试存在，cost_entries 行数==1 断言
5. 运行 python -m pytest <找到的测试文件> -v，报告通过/失败
输出 ACCEPT_SCHEMA（target_phase="Phase 4"，checks 中含 pytest 实际结果）。`,
    { label: '测试验收者', phase: '独立验收', schema: ACCEPT_SCHEMA }
  ),
])

const failedAccepts = (acceptResults ?? []).filter(Boolean).filter(r => r.verdict !== 'PASS')
if (failedAccepts.length > 0) {
  failedAccepts.forEach(r => log(`❌ 验收 FAIL [${r.target_phase}]: ${(r.fail_reasons ?? []).join('; ')}`))
} else {
  log(`✅ 全部4维验收 PASS`)
}

// ── 汇总复核 ─────────────────────────────────────────────────────────────────
phase('汇总复核')
const summary = await agent(
  `你是「汇总复核者」。任务：整体一致性检查 + 起草执行日志条目。

读以下文件（验证最终状态）：
- /home/ubuntu/case-study/mv_platform/application/service.py（搜 _materialize_job、_PROJECT_DIRECTORIES、start_director_intake）
- /home/ubuntu/case-study/src/mvstudio/director/intake.py（_CHORUS_MARKERS）
- /home/ubuntu/case-study/src/mvstudio/providers/alignment_faster_whisper.py（transcribe 方法）
- /home/ubuntu/case-study/docs/design/PRD-009-AUDIO-FIRST-AUTO-MATERIALIZATION.md §8（验收标准16条）

检查以下一致性项：
1. §8 16条验收标准，逐条读代码确认 DONE/MISSING
2. Phase 3a 门改读磁盘桶与 Phase 3b materialize 编排的衔接（桶满→gate通过）
3. _CHORUS_MARKERS 在 intake.py 中被 _split_character_names 实际引用
4. 角色文件命名三规则（stem==角色名, 10位hex, brief.characters空）在 character_design executor 中落实

起草执行日志 YAML 条目（格式与现有日志一致），包含：
- run_id: prd009-audio-first-materialization-<今日日期>
- stage: PRD-009 实施
- trigger: 音频优先自动补料 + 文件夹导入放宽
- role_reasoning_reviewed: 列出本次5类角色
- errors_found: 列出实施中出现的 blockers_hit（若有）
- what_was_built: 简要列出各 Phase 成果
- gates_passed: 验收结果
- carry_forward: 下一步建议

返回 JSON {"consistency_items": [...], "log_entry_yaml": "..."}。`,
  { label: '汇总复核者', phase: '汇总复核' }
)

log(`汇总复核完成`)

// §四 要求 4：主LLM 日志由 main loop 调用后写入执行日志（workflow 返回数据供 main 使用）
return {
  status: failedAccepts.length === 0 ? 'SUCCESS' : 'PARTIAL',
  archResult,
  implResults: { p0, p1, p2, p3a, p3b, p3c, p4 },
  acceptResults,
  summary,
  failedAccepts,
}
