// deep-review: multi-agent code review of the current branch diff. Lens agents
// review in parallel (correctness / security / performance / style), their
// findings are deduped and numbered, and one agent triages each into a verdict.
// Only when autoFix is true, the Fix phase DELEGATES to the bundled
// apply-fixes.workflow.js (its path arrives as applyFixesScriptPath in args,
// because the sandbox has no fs/__dirname to resolve the sibling path), which
// owns the per-file fan-out and the single final verification.
// The lens / triage steps run as the review:review-diff / review:review-comments subagents via agentType.
// JavaScript only. The script only coordinates agents — it never touches the
// filesystem or shell directly, and it asks the user nothing (the wrapper owns
// every AskUserQuestion and the human gate). All git/file/edit work happens
// inside agent() subagents.

export const meta = {
  name: 'deep-review',
  description: 'Multi-agent code review of the current branch diff. Fans out diff-review agents by lens (correctness, security, performance, style/maintainability), dedupes their findings, validates each into a verdict (FIX/FIX-STYLE/INTENTIONAL/OUT-OF-SCOPE/DISCUSS), then — gated by autoFix — either stops for human review (default) or autonomously applies the FIX/FIX-STYLE items and runs verification.',
  whenToUse: 'Invoked by the deep-review wrapper skill to produce a structured review of the current branch diff. Default run is read-only; set autoFix to apply fixes.',
  phases: [
    { title: 'Review', detail: 'Parallel lens agents review the whole diff but each surfaces only findings under its lens (correctness, security, performance, style)' },
    { title: 'Validate', detail: 'One agent triages every deduped finding into a single verdict using the review-comments criteria' },
    { title: 'Fix', detail: 'When autoFix is set, the Fix phase delegates to the bundled apply-fixes.workflow.js (path supplied as applyFixesScriptPath), which groups FIX/FIX-STYLE findings by file, applies them per file in parallel, and runs verification once afterward.' },
  ],
}

// ─── Schemas ───
const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'line', 'severity', 'title', 'body'],
        properties: {
          file: { type: 'string' },
          line: { type: ['integer', 'null'] },
          severity: { type: 'string', enum: ['low', 'medium', 'high'] },
          title: { type: 'string' },
          body: { type: 'string' },
        },
      },
    },
  },
}

const VERDICTS_SCHEMA = {
  type: 'object',
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['n', 'verdict', 'confidence', 'reason'],
        properties: {
          n: { type: 'integer' },
          verdict: { type: 'string', enum: ['FIX', 'FIX-STYLE', 'INTENTIONAL', 'OUT-OF-SCOPE', 'DISCUSS'] },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          reason: { type: 'string' },
        },
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

const autoFix = input && input.autoFix === true
const base = (input && input.base) || 'origin/main'
const applyFixesScriptPath = (input && input.applyFixesScriptPath) || ''
const lenses = Array.isArray(input && input.lenses) && input.lenses.length
  ? input.lenses
  : ['correctness', 'security', 'performance', 'style']

// ─── Shared rubric injected into every lens prompt (self-contained) ───
const BUG_CRITERIA =
  'A finding qualifies only if ALL of these hold:\n' +
  '1. It meaningfully impacts the accuracy, performance, security, or maintainability of the code.\n' +
  '2. The bug is discrete and actionable (not a general issue with the codebase or a combination of multiple issues).\n' +
  '3. Fixing the bug does not demand a level of rigor not present in the rest of the codebase (e.g. one does not need very detailed comments and input validation in a repo of one-off scripts in personal projects).\n' +
  '4. The bug was introduced in this branch diff (pre-existing bugs must not be flagged).\n' +
  "5. The author of the original PR would likely fix the issue if they were made aware of it.\n" +
  "6. The bug does not rely on unstated assumptions about the codebase or author's intent.\n" +
  '7. It is not enough to speculate that a change may disrupt another part of the codebase; to count as a bug you must identify the other parts of the code that are provably affected.\n' +
  '8. The bug is clearly not just an intentional change by the original author.'

const LENS_DEFS = {
  correctness: 'CORRECTNESS — logic errors, wrong/edge-case behavior, off-by-one, null/undefined handling, incorrect control flow, broken data integrity, regressions, race conditions.',
  security: 'SECURITY — injection, missing authz/authn checks, unsafe deserialization, secret leakage, path traversal, unvalidated input crossing a trust boundary, unsafe defaults.',
  performance: 'PERFORMANCE — needless O(n^2) loops, N+1 queries, repeated work in hot paths, unbounded memory growth, blocking I/O on a hot path, missing pagination/limits.',
  style: 'STYLE / MAINTAINABILITY — dead code, misleading naming, duplicated logic that should be reused, unclear control flow, violations of documented project standards in CLAUDE.md / AGENTS.md.',
}

const DIFF_INSTRUCTIONS =
  'Obtain the diff via git CLI:\n' +
  '  MERGE_BASE=$(git merge-base ' + base + ' HEAD)\n' +
  '  git diff $MERGE_BASE HEAD     # committed diff vs target\n' +
  '  git diff HEAD                 # uncommitted changes\n' +
  'Review the combination of both outputs. Skip generated files, lockfiles, and binary blobs.\n' +
  'Read CLAUDE.md and AGENTS.md at the repo root first, and any .plan/*.md if present — these distinguish intentional patterns from real bugs.'

// ─── Phase Review: one lens agent per lens, in parallel ───
phase('Review')

const lensResults = (await parallel(
  lenses.map(lens => () =>
    agent(
      '## Lens reviewer: ' + lens + '\n\n' +
      'You are a read-only code reviewer for ONE lens of the current branch diff. Do NOT modify any file.\n\n' +
      'Your lens:\n' + (LENS_DEFS[lens] || lens.toUpperCase()) + '\n\n' +
      DIFF_INSTRUCTIONS + '\n\n' +
      'Review the WHOLE diff, but ONLY surface findings that fall under your lens above. Apply these bug criteria to every candidate:\n\n' +
      BUG_CRITERIA + '\n\n' +
      'Be conservative: if uncertain, do NOT flag. For each finding return { file, line, severity, title, body }:\n' +
      '- line: the 1-based line in the new file, or null for a file-level finding.\n' +
      '- severity: low | medium | high.\n' +
      '- title: a short noun phrase naming the issue.\n' +
      '- body: one paragraph, matter-of-fact, that states why it is a bug, the severity, and the inputs/scenarios under which it arises. No code chunks longer than 3 lines.\n\n' +
      'Return findings[] (empty array if nothing qualifies). Structured output only.',
      { label: 'review:' + lens, phase: 'Review', schema: FINDINGS_SCHEMA, agentType: 'review:review-diff' }
    ).then(result => ({ lens, result }))
  )
)).filter(Boolean)

// ─── Barrier: flatten, dedupe, number ───
const normalize = s => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim()

const seen = new Set()
const collected = []
for (let i = 0; i < lensResults.length; i++) {
  const lens = lensResults[i].lens
  const findings = (lensResults[i].result && lensResults[i].result.findings) || []
  for (const f of findings) {
    if (!f || !f.file || !f.title) continue
    const key = normalize(f.file) + '|' + (f.line == null ? 'file' : f.line) + '|' + normalize(f.title)
    if (seen.has(key)) continue
    seen.add(key)
    collected.push({
      file: f.file,
      line: f.line == null ? null : f.line,
      lens,
      severity: f.severity || 'medium',
      title: f.title,
      body: f.body || '',
    })
  }
}

collected.sort((a, b) => {
  if (a.file !== b.file) return a.file < b.file ? -1 : 1
  const la = a.line == null ? -1 : a.line
  const lb = b.line == null ? -1 : b.line
  return la - lb
})

const comments = collected.map((c, i) => ({ n: i + 1, ...c }))
log('Collected ' + comments.length + ' finding(s) across ' + lensResults.length + ' lens(es)')

if (!comments.length) {
  return {
    comments: [],
    verdicts: [],
    summary: 'No findings — diff is clean against the 8 bug criteria.',
  }
}

// ─── Phase Validate: triage every finding into one verdict ───
phase('Validate')

const VERDICT_CRITERIA =
  'Choose exactly one verdict per comment:\n' +
  '- FIX — a real correctness, security, data-integrity, or behavioral defect. The code as written is wrong or unsafe. Confidence high by default; downgrade only if reproduction or context is uncertain.\n' +
  '- FIX-STYLE — a valid stylistic or readability suggestion that does not change behavior (naming, dead code, clearer control flow, redundant branches). Worth applying but non-blocking.\n' +
  '- INTENTIONAL — the flagged pattern is deliberate per CLAUDE.md, AGENTS.md, the plan file, or a clear convention observed elsewhere. The reason MUST cite the specific source (file path and rule, or representative call sites).\n' +
  "- OUT-OF-SCOPE — the concern is legitimate but unrelated to the PR's stated intent and belongs in a separate ticket. Use the plan file (when present) as the authority on PR scope.\n" +
  '- DISCUSS — ambiguous: competing valid approaches, missing context, the file or line cannot be located, or the comment depends on information not available locally. Human judgment required.'

const commentTuples = comments
  .map(c => '(' + c.n + ', ' + c.file + ', ' + (c.line == null ? 'File' : c.line) + ', ' + c.title + ' — ' + c.body + ')')
  .join('\n')

const triaged = await agent(
  '## Verdict triage (review-comments step)\n\n' +
  'You are the review-comments triage step. You are READ-ONLY — do NOT modify any file.\n\n' +
  'First read CLAUDE.md and AGENTS.md at the repo root, and any .plan/*.md if present — these distinguish intentional patterns from real issues.\n\n' +
  'Below are numbered review findings as (N, file, line, text) tuples:\n\n' +
  commentTuples + '\n\n' +
  'For each finding, in order:\n' +
  '- Read the cited file with ±20 lines around the cited line. If the file or line cannot be located, emit a DISCUSS verdict.\n' +
  '- Use Grep/Glob to check whether the flagged pattern appears elsewhere. Repeated, consistent use is strong evidence of an intentional convention; a one-off is more likely a local mistake.\n' +
  '- Cross-check against the plan / CLAUDE.md / AGENTS.md.\n' +
  '- Choose exactly one verdict using the criteria below.\n\n' +
  VERDICT_CRITERIA + '\n\n' +
  'Return verdicts[] of { n, verdict, confidence, reason }, preserving the n of each finding (one verdict per finding). Set confidence low whenever the cited file/line could not be read or the plan was ambiguous. Structured output only.',
  { label: 'validate', phase: 'Validate', schema: VERDICTS_SCHEMA, agentType: 'review:review-comments' }
)

const verdicts = (triaged && Array.isArray(triaged.verdicts) && triaged.verdicts) || []

// ─── Decision-count summary (plain JS) ───
const counts = { FIX: 0, 'FIX-STYLE': 0, INTENTIONAL: 0, 'OUT-OF-SCOPE': 0, DISCUSS: 0 }
for (const v of verdicts) {
  if (v && Object.prototype.hasOwnProperty.call(counts, v.verdict)) counts[v.verdict]++
}
const countLine =
  'FIX: ' + counts.FIX +
  ' | FIX-STYLE: ' + counts['FIX-STYLE'] +
  ' | INTENTIONAL: ' + counts.INTENTIONAL +
  ' | OUT-OF-SCOPE: ' + counts['OUT-OF-SCOPE'] +
  ' | DISCUSS: ' + counts.DISCUSS

// ─── Phase Fix ───
phase('Fix')

if (!autoFix) {
  return {
    comments,
    verdicts,
    summary:
      comments.length + ' finding(s) triaged. ' + countLine +
      '. Stopped at the gate — no files changed (read-only run).',
  }
}

// ─── Delegate the Fix fan-out to the bundled apply-fixes workflow ───
if (!applyFixesScriptPath) {
  return {
    comments,
    verdicts,
    summary:
      comments.length + ' finding(s) triaged. ' + countLine +
      '. autoFix requested but applyFixesScriptPath was not provided; no fixes applied.',
  }
}

const fixReport = await workflow({
  scriptPath: applyFixesScriptPath,
  args: JSON.stringify({ comments, verdicts, base }),
})

const safeFixReport =
  fixReport && typeof fixReport === 'object' && !fixReport.error
    ? fixReport
    : { applied: [], skipped: [], verification: { tests: 'skipped', linter: 'skipped', types: 'skipped' }, newTickets: [] }

return {
  comments,
  verdicts,
  summary:
    comments.length + ' finding(s) triaged. ' + countLine +
    '. Auto-fix applied the FIX/FIX-STYLE items per file in parallel.',
  fixReport: safeFixReport,
}
