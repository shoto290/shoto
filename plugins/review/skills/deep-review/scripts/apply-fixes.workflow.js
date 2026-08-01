// apply-fixes: the shared fix fan-out extracted verbatim from deep-review.workflow.js.
// Takes precomputed { comments, verdicts, base }, runs one review:review-fix subagent
// per file in parallel (sequential within a file, no worktree — edits the real working
// tree), then runs one global verification, and returns the fixReport shape directly.
// It asks the user nothing. JavaScript only; it only coordinates agents and never
// touches the filesystem or shell directly. It MUST NEVER call workflow() — nesting is
// one level deep, so this script is a leaf.

export const meta = {
  name: 'apply-fixes',
  description: 'Shared fix fan-out for deep-review: applies the approved FIX/FIX-STYLE findings by fanning out one review:review-fix subagent per file in parallel (sequential within a file), then runs one global verification. Returns the fixReport shape directly.',
  whenToUse: 'Invoked by deep-review SKILL.md gate (Workflow tool) and by deep-review.workflow.js --auto-fix (workflow() hook) with precomputed { comments, verdicts, base }.',
  phases: [
    { title: 'Fix', detail: 'One review-fix subagent per file applies FIX/FIX-STYLE in parallel (sequential within a file); verification runs once afterward.' },
  ],
}

// ─── Schemas ───
const FIXREPORT_SCHEMA = {
  type: 'object',
  required: ['applied', 'skipped', 'verification'],
  properties: {
    applied: {
      type: 'array',
      items: {
        type: 'object',
        required: ['n', 'file', 'description'],
        properties: {
          n: { type: 'integer' },
          file: { type: 'string' },
          description: { type: 'string' },
        },
      },
    },
    skipped: {
      type: 'array',
      items: {
        type: 'object',
        required: ['n', 'verdict'],
        properties: {
          n: { type: 'integer' },
          verdict: { type: 'string' },
        },
      },
    },
    verification: {
      type: 'object',
      required: ['tests', 'linter', 'types'],
      properties: {
        tests: { type: 'string' },
        linter: { type: 'string' },
        types: { type: 'string' },
      },
    },
    newTickets: { type: 'array', items: { type: 'string' } },
  },
}

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['verification'],
  properties: {
    verification: {
      type: 'object',
      required: ['tests', 'linter', 'types'],
      properties: {
        tests: { type: 'string' },
        linter: { type: 'string' },
        types: { type: 'string' },
      },
    },
  },
}

// ─── Parse args once ───
const RAW = (typeof args === 'string' && args.trim()) || ''

let input
try {
  input = JSON.parse(RAW || '{}')
} catch (e) {
  return { error: 'args is not valid JSON: ' + (e && e.message ? e.message : String(e)) }
}

const comments = Array.isArray(input && input.comments) ? input.comments : []
const verdicts = Array.isArray(input && input.verdicts) ? input.verdicts : []
const base = (input && input.base) || 'origin/main'

// ─── Phase Fix ───
phase('Fix')

// ─── Build the fixable set: FIX / FIX-STYLE findings only ───
const fixable = comments.filter(c => {
  const v = verdicts.find(x => x && x.n === c.n)
  return v && (v.verdict === 'FIX' || v.verdict === 'FIX-STYLE')
})

if (!fixable.length) {
  return {
    applied: [],
    skipped: [],
    verification: { tests: 'skipped', linter: 'skipped', types: 'skipped' },
    newTickets: [],
  }
}

// ─── Group fixable findings by file (ascending n within each group) ───
const groups = {}
for (const c of fixable) {
  ;(groups[c.file] || (groups[c.file] = [])).push(c)
}
for (const file of Object.keys(groups)) {
  groups[file].sort((a, b) => a.n - b.n)
}
const fileKeys = Object.keys(groups).sort()

// ─── Per-file fix prompt: WRITE step for ONE file, NO verification ───
const perFilePrompt = (file, findings) =>
  '## Apply fixes for a single file (review-fix step)\n\n' +
  'You are the review-fix WRITE step for ONE file only: ' + file + '. Edit ONLY this file.\n' +
  'Read CLAUDE.md and AGENTS.md at the repo root if they exist and respect any project rules.\n\n' +
  "This file's numbered findings, each as (n, file, line, verdict, title — body):\n\n" +
  findings
    .map(c => {
      const v = verdicts.find(x => x && x.n === c.n)
      return '(' + c.n + ', ' + c.file + ', ' + (c.line == null ? 'File' : c.line) +
        ', verdict=' + (v ? v.verdict : 'DISCUSS') + ', ' + c.title + ' — ' + c.body + ')'
    })
    .join('\n') + '\n\n' +
  'Hard rules:\n' +
  '- Apply ONLY the findings whose verdict is FIX or FIX-STYLE. Ignore everything else — do NOT re-evaluate decisions already made.\n' +
  '- SEQUENTIAL within this file: one fix at a time. Edit, confirm, then move to the next. Never batch changes.\n' +
  '- Minimal surgical changes only. The fix must address EXACTLY what the finding says. No refactoring, renaming, or improving adjacent code.\n' +
  '- Never re-open a rejected finding.\n' +
  '- Stop on regression: if a fix creates a new problem, STOP, record which fix caused which failure, and do not continue.\n' +
  '- Never commit and never push.\n' +
  '- Do NOT run verification (no tests, no lint, no typecheck) — verification runs once globally afterward. Set every verification field to "skipped".\n\n' +
  'Return { applied[]:{n,file,description}, skipped[]:{n,verdict}, verification:{tests,linter,types}, newTickets[] } scoped to THIS file. Each verification field is "skipped". Structured output only.'

// ─── Fan out: one review-fix agent per file, in parallel ───
const fileResults = await parallel(
  fileKeys.map(file => () =>
    agent(perFilePrompt(file, groups[file]), {
      label: 'fix:' + file,
      phase: 'Fix',
      schema: FIXREPORT_SCHEMA,
      agentType: 'review:review-fix',
    }).then(r => ({ file, r }))
  )
)

// ─── Aggregation barrier (plain JS): merge per-file reports, stable by n ───
const byN = (a, b) => (a.n || 0) - (b.n || 0)
const applied = []
const skipped = []
const newTickets = []
for (const { r } of fileResults) {
  if (!r) continue
  if (Array.isArray(r.applied)) applied.push(...r.applied)
  if (Array.isArray(r.skipped)) skipped.push(...r.skipped)
  if (Array.isArray(r.newTickets)) newTickets.push(...r.newTickets)
}
applied.sort(byN)
skipped.sort(byN)

// ─── Verify ONCE over the whole tree after the fan-out ───
const verifyResult = await agent(
  '## Verify the working tree (review-fix step)\n\n' +
  'All FIX/FIX-STYLE fixes have already been applied per file. You run verification ONCE over the whole working tree. Do NOT edit any source file, commit, or push.\n\n' +
  'Auto-detect verification commands by checking which manifest files exist at the repo root, then run the matching commands:\n' +
  '- package.json — detect the package manager from the lockfile (bun.lockb→bun, pnpm-lock.yaml→pnpm, yarn.lock→yarn, package-lock.json→npm), then run only the test/lint/typecheck scripts actually defined in package.json "scripts".\n' +
  '- Cargo.toml — cargo test, cargo clippy --no-deps, cargo check.\n' +
  '- pyproject.toml — pytest / ruff check . / mypy . only for tools present in pyproject.toml.\n' +
  '- go.mod — go test ./..., go vet ./....\n' +
  '- None present — mark each verification field "skipped".\n\n' +
  'Return { verification:{tests,linter,types} }. Each verification field is "pass", "fail", or "skipped". Structured output only.',
  { label: 'verify', phase: 'Fix', schema: VERIFY_SCHEMA, agentType: 'review:review-fix' }
)

const verification =
  (verifyResult && verifyResult.verification) ||
  { tests: 'skipped', linter: 'skipped', types: 'skipped' }

return { applied, skipped, verification, newTickets }
