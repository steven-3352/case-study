#!/usr/bin/env node
/**
 * validate.js · skill 自足性一致性校验
 *
 * 守三件事（防"内嵌镜像 ↔ 单一事实源"漂移）：
 *  1. 两个 workflow 内嵌的 ROLE_REGISTRY 常量，逐角色 == roles/registry.json
 *     （行为关键字段：name/group/wave/activation/dual_review/translation_layer/owns_dims/gates/output_template）
 *  2. registry 里所有 gates 引用的 QG-* 都存在于 quality/quality_registry.md
 *  3. registry 里所有 owns_dims 的 Dxx 都存在于 quality/video_19dim_scorecard.md
 *
 * 用法：node skill/workflows/validate.js   （从仓库根跑；失败 exit 1）
 */
const fs = require('fs')
const path = require('path')

const SKILL = path.resolve(__dirname, '..')
const p = (...a) => path.join(SKILL, ...a)

let failures = 0
const fail = (msg) => { console.error('  ✗ ' + msg); failures++ }
const okline = (msg) => console.log('  ✓ ' + msg)

// ── 载入单一事实源 ──
const registry = JSON.parse(fs.readFileSync(p('roles', 'registry.json'), 'utf8'))
const jsonRoles = registry.roles
const registryText = fs.readFileSync(p('quality', 'quality_registry.md'), 'utf8')
const scorecardText = fs.readFileSync(p('quality', 'video_19dim_scorecard.md'), 'utf8')

// 从 workflow JS 文本里抽出 ROLE_REGISTRY 数组字面量并求值（纯数据，无函数调用）
function extractMirror(file) {
  const src = fs.readFileSync(file, 'utf8')
  const m = src.match(/const ROLE_REGISTRY = (\[[\s\S]*?\n\])\n/)
  if (!m) throw new Error(`在 ${path.basename(file)} 找不到 ROLE_REGISTRY 字面量`)
  // eslint-disable-next-line no-new-func
  return Function('return ' + m[1])()
}

const CMP_FIELDS = ['group', 'wave', 'activation', 'dual_review', 'translation_layer', 'output_template']
const eqSet = (a, b) => {
  const A = [...(a || [])].sort(), B = [...(b || [])].sort()
  return A.length === B.length && A.every((x, i) => x === B[i])
}

function compareMirror(name, mirror) {
  console.log(`\n[1] 内嵌镜像一致性 · ${name}`)
  if (mirror.length !== jsonRoles.length) {
    fail(`${name} 角色数 ${mirror.length} ≠ registry.json ${jsonRoles.length}`)
  }
  const jsonByName = {}
  for (const r of jsonRoles) jsonByName[r.name] = r
  for (const mr of mirror) {
    const jr = jsonByName[mr.name]
    if (!jr) { fail(`${name}: 角色「${mr.name}」不在 registry.json`); continue }
    for (const f of CMP_FIELDS) {
      if (mr[f] !== jr[f]) fail(`${name}: ${mr.name}.${f} = ${JSON.stringify(mr[f])} ≠ json ${JSON.stringify(jr[f])}`)
    }
    if (!eqSet(mr.owns_dims, jr.owns_dims)) fail(`${name}: ${mr.name}.owns_dims 不一致（${JSON.stringify(mr.owns_dims)} vs ${JSON.stringify(jr.owns_dims)}）`)
    if (!eqSet(mr.gates, jr.gates)) fail(`${name}: ${mr.name}.gates 不一致（${JSON.stringify(mr.gates)} vs ${JSON.stringify(jr.gates)}）`)
  }
  // 反向：json 里有但镜像缺
  const mirrorNames = new Set(mirror.map(r => r.name))
  for (const jr of jsonRoles) if (!mirrorNames.has(jr.name)) fail(`${name}: registry.json 的「${jr.name}」在镜像中缺失`)
  if (failures === 0) okline(`${name}: ${mirror.length} 角色逐字段一致`)
}

const prdMirror = extractMirror(p('workflows', 'prd_pipeline.js'))
const bpMirror = extractMirror(p('workflows', 'blueprint.js'))
const before1 = failures
compareMirror('prd_pipeline.js', prdMirror)
compareMirror('blueprint.js', bpMirror)
if (failures === before1) okline('两 workflow 镜像均与 registry.json 一致')

// ── [2] gates 引用存在性 ──
console.log('\n[2] gates 引用 → quality_registry.md 存在性')
const knownGates = new Set((registryText.match(/QG-[A-Z0-9-]+/g) || []))
const referencedGates = new Set()
for (const r of jsonRoles) for (const g of (r.gates || [])) referencedGates.add(g)
let gateMiss = 0
for (const g of referencedGates) {
  if (!knownGates.has(g)) { fail(`gate「${g}」被 registry 引用但 quality_registry.md 无定义`); gateMiss++ }
}
if (gateMiss === 0) okline(`${referencedGates.size} 个被引用 gate 全部在 quality_registry.md 有定义`)

// ── [3] owns_dims 存在性 ──
console.log('\n[3] owns_dims → video_19dim_scorecard.md 存在性')
const knownDims = new Set((scorecardText.match(/D\d{2}/g) || []))
const referencedDims = new Set()
for (const r of jsonRoles) for (const d of (r.owns_dims || [])) referencedDims.add(d)
let dimMiss = 0
for (const d of referencedDims) {
  if (!knownDims.has(d)) { fail(`维度「${d}」被 registry owns_dims 引用但 scorecard 无此维`); dimMiss++ }
}
if (dimMiss === 0) okline(`${referencedDims.size} 个被引用维度全部在 scorecard 有定义`)

// ── 汇总 ──
console.log('')
if (failures === 0) {
  console.log('✓ 全部一致：镜像 == registry.json，gates/dims 引用无悬空。')
  process.exit(0)
} else {
  console.error(`✗ ${failures} 处不一致，见上。`)
  process.exit(1)
}
