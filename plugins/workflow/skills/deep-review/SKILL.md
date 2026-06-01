---
name: deep-review
description: 'Multi-agent code-review workflow. Fans out diff-review agents by lens (correctness, security, performance, style/maintainability) over the current branch diff, dedupes their findings, validates each into a verdict (FIX / FIX-STYLE / INTENTIONAL / OUT-OF-SCOPE / DISCUSS) using review-comments criteria, then — gated by a param — either stops for your review (default) or autonomously applies the FIX/FIX-STYLE items via review-fix and runs verification.'
when_to_use: "Use on `/workflow:deep-review`, 'run a deep/parallel review of my changes', 'review my diff from multiple angles then fix'."
argument-hint: "[--auto-fix] [--base <branch>]"
allowed-tools: [AskUserQuestion, Workflow, Read, Bash]
---

# Deep Review

`deep-review` runs a multi-agent review of the current branch diff. It is a **thin wrapper** around one bundled workflow (`deep-review.workflow.js`): lens agents review the diff in parallel, their findings are deduped and triaged into verdicts, and — only when `--auto-fix` is passed — the FIX/FIX-STYLE items are applied with verification. The human gate lives here, in the main thread, **after** the read-only run; the workflow itself never asks the user anything.

```
/workflow:deep-review
 ├─ parse params (--auto-fix, --base)
 ├─ Workflow(deep-review.workflow.js)  → structured findings + verdicts   (read-only unless --auto-fix)
 ├─ render findings + verdict blocks + decision counts
 └─ gate (only when not --auto-fix): offer to apply FIX/FIX-STYLE now —
    launches apply-fixes.workflow.js, which fans out one review:review-fix subagent
    per file in parallel (sequential within a file), then verifies once
```

This skill only parses, runs, renders, and gates. It holds **no** orchestration logic — that lives entirely in the script.

## 1. Parse params

- `--auto-fix` → `autoFix = true` (default `false`).
- `--base <branch>` → `base` (default `origin/main`).
- Everything else is ignored.

## 2. Run the workflow

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-review/scripts/deep-review.workflow.js",
  args: JSON.stringify({ autoFix, base, applyFixesScriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-review/scripts/apply-fixes.workflow.js" })
})
```

`applyFixesScriptPath` is passed because the workflow runs in a sandbox with no `fs`/`__dirname` and cannot compute the sibling script path itself; on the `--auto-fix` path the workflow delegates the Fix fan-out to that script.

It returns `{ comments[], verdicts[], summary, fixReport? }`:

- `comments[]` — numbered findings `{ n, file, line, lens, severity, title, body }`.
- `verdicts[]` — one per finding `{ n, verdict, confidence, reason }`.
- `summary` — the decision-count breakdown and run note.
- `fixReport` — present only on the `--auto-fix` path `{ applied[], skipped[], verification, newTickets[] }`.

## 3. Render the result

Render to the user:

- **Findings** — the numbered list (n, title, lens, severity, file:line, body).
- **Verdicts** — one verdict block per finding, in `n` order, using the review-comments format:

  ```
  ---
  [#N] [File:line]
  Comment: "[finding title — body]"

  Verdict: [FIX | FIX-STYLE | INTENTIONAL | OUT-OF-SCOPE | DISCUSS]
  Reason: [one sentence]
  Action: [what review:review-fix or the human should do next]
  Confidence: [high | medium | low]
  ---
  ```

  Use `[File]` instead of `[File:line]` when `line` is null.
- **Decision summary** — the FIX / FIX-STYLE / INTENTIONAL / OUT-OF-SCOPE / DISCUSS counts from `summary`.
- **Applied fixes** (only if `fixReport` is present) — the `applied[]` list, the `verification` block (tests / linter / types), the `skipped[]` items, and any `newTickets`.

If `summary` reports no findings, render the single clean-diff line and stop.

## 4. Gate (only when not --auto-fix)

After rendering the verdicts, if `autoFix` was false and at least one verdict is `FIX` or `FIX-STYLE`, use `AskUserQuestion` to offer applying those items now in the main thread (options: **Apply now** / **Skip**).

- **Apply now** → launch the apply-fixes workflow, passing the comments + verdicts already computed by the read-only run (step 2) plus base:

  ```
  Workflow({
    scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-review/scripts/apply-fixes.workflow.js",
    args: JSON.stringify({ comments, verdicts, base })
  })
  ```

  It fans out one `review:review-fix` subagent per file in parallel (sequential within a file, edits in the real working tree, no worktree), runs verification ONCE over the whole tree, and returns the fixReport shape `{ applied[], skipped[], verification{tests,linter,types}, newTickets[] }`. Render the returned fixReport exactly as the step 3 "Applied fixes" rendering describes (`applied[]` list, verification block, `skipped[]` items, newTickets).
- **Skip** → stop. Nothing has been written (the run was read-only).

## Critical principles

- **Default run is READ-ONLY.** No file is written until the gate (or `--auto-fix`). The workflow never edits anything when `autoFix` is false.
- **The workflow never asks the user anything.** The wrapper owns the gate; all `AskUserQuestion` lives here, never in the script.
- **Thin wrapper.** Param parsing, rendering, and the gate only. The lens fan-out, dedupe, triage, and fix logic live entirely in `deep-review.workflow.js`.
- **Fixes fan out via the apply-fixes workflow.** The gate launches `apply-fixes.workflow.js`, which fans out one `review:review-fix` subagent per file in parallel (sequential within a file) with a single final verification over the whole tree — never main-thread `Skill` calls.
