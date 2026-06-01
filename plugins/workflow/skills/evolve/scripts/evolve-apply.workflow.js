// evolve-apply: fan out the executable entries of an approved PLAN to the
// core smiths (skill / subagent / hooks / plugin), then verify each authored
// artifact. MCP servers and secret-dependent hooks are NOT executed here — an
// autonomous agent cannot wire secrets/auth — they are returned in deferred[]
// for the wrapper to hand to core:mcp / core:hooks in the main thread.
// Finally, it always chains a deep-review over the freshly authored diff by
// DELEGATING to the bundled deep-review + apply-fixes workflows (their paths
// arrive as deepReviewScriptPath / applyFixesScriptPath in args, because the
// sandbox has no fs/__dirname to resolve cross-skill paths). Nesting is one
// level deep, so it runs deep-review READ-ONLY (never its --auto-fix path,
// which would call workflow(apply-fixes) = a 2nd level and throw) and then
// calls the apply-fixes leaf directly — both are single-level children here.
// Zero duplication: review+triage stay in deep-review, fix+verify in apply-fixes.
// JavaScript only. The script only coordinates agents; the spawned smiths are
// the only things that touch files. It asks the user nothing.

export const meta = {
  name: 'evolve-apply',
  description: 'Fan-out applier of an approved evolve plan — routes each executable entry to the matching core smith (skill/subagent/hooks/plugin), verifies the authored files, then chains a deep-review (and optional auto-fix) over the diff, and returns a report plus a deferred list of MCP/secret-hook items for the main thread.',
  whenToUse: 'Invoked by the evolve wrapper skill AFTER the user approves the plan. Authors and edits files via the core smiths; defers anything needing secrets or live MCP setup; always finishes by reviewing the authored diff.',
  phases: [
    { title: 'Apply', detail: 'One agent per executable entry, routed by agentType to the matching core smith with a full no-questions spec' },
    { title: 'Verify', detail: 'One agent per applied artifact confirms the file exists and its name frontmatter matches its path' },
    { title: 'Review', detail: 'Delegates to the bundled deep-review workflow (read-only) over the freshly authored diff, returning numbered findings and verdicts' },
    { title: 'Fix', detail: 'When the review yields FIX/FIX-STYLE verdicts, delegates to the bundled apply-fixes workflow to apply them per file and verify once' },
  ],
}

// ─── Schemas ───
const APPLY_SCHEMA = {
  type: 'object',
  required: ['name', 'artifactType', 'action', 'status'],
  properties: {
    name: { type: 'string' },
    artifactType: { type: 'string', enum: ['skill', 'subagent', 'hook', 'plugin'] },
    action: { type: 'string', enum: ['create', 'update'] },
    path: { type: 'string' },
    status: { type: 'string', enum: ['done', 'failed', 'skipped'] },
    summary: { type: 'string' },
  },
}

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['name', 'exists', 'nameMatchesPath'],
  properties: {
    name: { type: 'string' },
    path: { type: 'string' },
    exists: { type: 'boolean' },
    nameMatchesPath: { type: 'boolean' },
    notes: { type: 'string' },
  },
}

const SMITH_BY_TYPE = {
  skill: 'core:skill-smith',
  subagent: 'core:subagent-smith',
  hook: 'core:hooks-smith',
  plugin: 'core:plugin-smith',
}

// ─── Parse args once (the approved PLAN object) ───
const RAW = (typeof args === 'string' && args.trim()) || ''
if (!RAW) return { error: 'No plan provided. Pass the approved PLAN as a JSON args string.' }

let plan
try {
  plan = JSON.parse(RAW)
} catch (e) {
  return { error: 'args is not valid JSON: ' + (e && e.message ? e.message : String(e)) }
}

const allEntries = Array.isArray(plan && plan.entries) ? plan.entries : []
if (!allEntries.length) return { error: 'Approved plan has no entries to apply.' }

// Cross-skill workflow paths for the final review chain (the sandbox cannot
// resolve them itself). When absent, the review chain is skipped silently.
const deepReviewScriptPath = (plan && plan.deepReviewScriptPath) || ''
const applyFixesScriptPath = (plan && plan.applyFixesScriptPath) || ''
const reviewBase = (plan && plan.base) || 'origin/main'

// Drop reuse entries (no action needed). Split the rest into executable vs deferred:
// deferred = mcp servers and any hook needing secrets — an autonomous agent
// cannot wire those, so they are handed back for the main thread.
const actionable = allEntries.filter(e => e && e.action !== 'reuse')

const deferred = actionable
  .filter(e => e.artifactType === 'mcp' || (e.artifactType === 'hook' && e.needsSecret === true))
  .map(e => ({
    artifactType: e.artifactType,
    name: e.name,
    targetPath: e.targetPath || '',
    spec: e.spec || e.why || '',
    route: e.artifactType === 'mcp' ? 'core:mcp' : 'core:hooks',
  }))

const executable = actionable.filter(
  e => SMITH_BY_TYPE[e.artifactType] && !(e.artifactType === 'hook' && e.needsSecret === true)
)

if (!executable.length) {
  return {
    applied: [],
    deferred,
    restartRequired: plan.restartRequired === true,
    testCommands: Array.isArray(plan.testPlan) ? plan.testPlan : [],
    note: 'No executable entries — everything was reuse or deferred to the main thread.',
  }
}

// ─── Apply: one smith per executable entry ───
// parallel() is safe here without worktree isolation: every entry writes to a
// distinct targetPath, so the smiths never contend on the same file.
phase('Apply')

const applied = (await parallel(
  executable.map(entry => () =>
    agent(
      '## Authoring task — ' + entry.artifactType + ' "' + entry.name + '" (' + entry.action + ')\n\n' +
      'You have a COMPLETE spec below. Do NOT ask any questions and do NOT wait for confirmation. ' +
      'Author or edit the files directly and return a structured summary.\n' +
      'Prefer UPDATE over CREATE when an existing artifact already covers ≥70% of this need.\n\n' +
      'Target path: ' + (entry.targetPath || '(resolve from the spec)') + '\n' +
      'Action: ' + entry.action + '\n' +
      'Why: ' + (entry.why || '') + '\n\n' +
      'Full spec:\n' + (entry.spec || entry.why || '') + '\n\n' +
      'Return { name, artifactType, action, path, status: done|failed|skipped, summary }. Structured output only.',
      {
        label: 'apply:' + entry.artifactType + ':' + entry.name,
        phase: 'Apply',
        agentType: SMITH_BY_TYPE[entry.artifactType],
        schema: APPLY_SCHEMA,
      }
    )
  )
)).filter(Boolean)

if (!applied.length) {
  return {
    applied: [],
    deferred,
    restartRequired: plan.restartRequired === true,
    testCommands: Array.isArray(plan.testPlan) ? plan.testPlan : [],
    note: 'Apply phase returned nothing — no artifact was authored.',
  }
}
log('Applied ' + applied.length + '/' + executable.length + ' entry(ies)')

// ─── Verify: confirm each authored file exists and name matches path ───
phase('Verify')

const toVerify = applied.filter(r => r.status === 'done' && r.path)

const verified = toVerify.length
  ? (await parallel(
      toVerify.map(r => () =>
        agent(
          '## Verify — ' + r.name + '\n\n' +
          'Read-only. Confirm the artifact at "' + r.path + '" exists and that its `name:` frontmatter matches its path ' +
          '(skill at skills/<name>/SKILL.md must have name: <name>; subagent at agents/<name>.md must have name: <name>). ' +
          'For hooks, confirm the entry exists in the settings file.\n\n' +
          'Return { name, path, exists, nameMatchesPath, notes }. Structured output only.',
          {
            label: 'verify:' + r.name,
            phase: 'Verify',
            agentType: 'Explore',
            schema: VERIFY_SCHEMA,
          }
        )
      )
    )).filter(Boolean)
  : []

log('Verified ' + verified.length + ' artifact(s)')

// ─── Review: always chain a deep-review over the freshly authored diff ───
// Single-level children only: deep-review runs READ-ONLY (autoFix:false) so it
// never calls workflow(apply-fixes) itself, then we call the apply-fixes leaf
// directly from here. Both calls are wrapped so a review failure never discards
// the apply report — the artifacts are already written.
let review = null
let fixReport = null

if (deepReviewScriptPath) {
  phase('Review')
  try {
    const reviewResult = await workflow({
      scriptPath: deepReviewScriptPath,
      args: JSON.stringify({ autoFix: false, base: reviewBase }),
    })
    review =
      reviewResult && typeof reviewResult === 'object' && !reviewResult.error
        ? {
            comments: Array.isArray(reviewResult.comments) ? reviewResult.comments : [],
            verdicts: Array.isArray(reviewResult.verdicts) ? reviewResult.verdicts : [],
            summary: reviewResult.summary || '',
          }
        : { comments: [], verdicts: [], summary: 'deep-review returned no usable result.' }
  } catch (e) {
    review = { comments: [], verdicts: [], summary: 'deep-review failed: ' + (e && e.message ? e.message : String(e)) }
  }

  const hasFixable = review.verdicts.some(v => v && (v.verdict === 'FIX' || v.verdict === 'FIX-STYLE'))

  if (hasFixable && applyFixesScriptPath) {
    phase('Fix')
    try {
      const fr = await workflow({
        scriptPath: applyFixesScriptPath,
        args: JSON.stringify({ comments: review.comments, verdicts: review.verdicts, base: reviewBase }),
      })
      fixReport =
        fr && typeof fr === 'object' && !fr.error
          ? fr
          : { applied: [], skipped: [], verification: { tests: 'skipped', linter: 'skipped', types: 'skipped' }, newTickets: [] }
    } catch (e) {
      fixReport = {
        applied: [],
        skipped: [],
        verification: { tests: 'skipped', linter: 'skipped', types: 'skipped' },
        newTickets: [],
        error: 'apply-fixes failed: ' + (e && e.message ? e.message : String(e)),
      }
    }
    log('Auto-fix applied ' + (Array.isArray(fixReport.applied) ? fixReport.applied.length : 0) + ' fix(es)')
  }
}

return {
  applied: applied.map(r => {
    const v = verified.find(x => x.name === r.name)
    return {
      name: r.name,
      artifactType: r.artifactType,
      action: r.action,
      path: r.path || '',
      status: r.status,
      summary: r.summary || '',
      verified: v ? v.exists === true && v.nameMatchesPath === true : false,
      verifyNotes: v ? v.notes || '' : 'not verified',
    }
  }),
  deferred,
  restartRequired: plan.restartRequired === true,
  testCommands: Array.isArray(plan.testPlan) ? plan.testPlan : [],
  review,
  fixReport,
}
