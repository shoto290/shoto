---
name: review-comments
description: 'Triages PR comments into a verdict list (FIX, FIX-STYLE, INTENTIONAL, OUT-OF-SCOPE, DISCUSS). Read-only; output feeds review:review-fix.'
when_to_use: Use to triage PR review comments into per-comment fix decisions.
argument-hint: "[paste PR comments or @PR-url]"
allowed-tools: Read, Glob, Grep, AskUserQuestion
---

Triage PR review comments into a structured decision list. Each comment gets one verdict block; the list is the handoff payload for `/review:review-fix`.

## Hard rules

- **READ-ONLY.** Never modify files. `allowed-tools` intentionally excludes `Edit`, `Write`, and `Bash`.
- **Never auto-apply a fix.** Output is a decision list only. `/review:review-fix` is the WRITE counterpart.
- **One verdict block per comment.** Preserve input order; never merge multiple comments into one block.
- **No PR fetching.** `Bash` is not in `allowed-tools`, so the skill cannot call `gh`. Require the user to paste comments inline; if the input is only a `@PR-url`, ask them to paste the comments.

## Input contract

User pastes review comments. Parse one tuple per comment:

```
(N, file, line, text)
```

- `N` is 1-based, in the order comments appear in the input.
- `text` is kept verbatim.
- File-level comments have no `line` — record `null` and render `[File]` in the block.

## Steps

1. **Read context.** Read `CLAUDE.md` and `AGENTS.md` at the repo root. If a plan file exists under `.plan/*.md`, read it. These distinguish intentional patterns from real issues.

2. **Parse comments** into the tuple list above. If the input is only a `@PR-url` (no inline comments), stop and ask the user to paste the comments — the skill cannot fetch them.

3. **Triage each comment inline.** For each comment, in input order:

   - `Read` the cited file with ±20 lines around the cited line. If the file or line cannot be located, emit a `DISCUSS` verdict naming what was missing.
   - Use `Grep` / `Glob` to check whether the flagged pattern appears elsewhere. Repeated, consistent use is strong evidence of an intentional convention; a one-off is more likely a local mistake.
   - Cross-check against the plan / `CLAUDE.md` / `AGENTS.md`.
   - Choose exactly one verdict using the criteria below and emit the verdict block.

4. **Render the decision list.** For each comment, emit exactly the block defined in [reference/verdict-block-format.md](./reference/verdict-block-format.md). Preserve input order.

5. **Summary and handoff.** End with:

   ```
   ## Decision summary
   Fix:           [N]
   Fix (style):   [N]
   Intentional:   [N]
   Out of scope:  [N]
   Discuss:       [N]

   Paste this output into /review:review-fix to apply the FIX and FIX-STYLE items.
   ```

## Verdict criteria

Choose exactly one verdict per comment:

- `FIX` — The comment identifies a real correctness, security, data-integrity, or behavioral defect. The code as written is wrong or unsafe. Confidence is high by default; downgrade only if reproduction or context is uncertain.
- `FIX-STYLE` — A valid stylistic or readability suggestion that does not change behavior (naming, dead code, clearer control flow, redundant branches). Worth applying but non-blocking.
- `INTENTIONAL` — The flagged pattern is deliberate per `CLAUDE.md`, `AGENTS.md`, the plan file, or a clear convention observed elsewhere. The reason MUST cite the specific source (file path and rule, or representative call sites).
- `OUT-OF-SCOPE` — The concern is legitimate but unrelated to the PR's stated intent and belongs in a separate ticket. Use the plan file (when present) as the authority on PR scope.
- `DISCUSS` — Ambiguous: competing valid approaches, missing context, the file or line cannot be located, or the comment depends on information not available locally. Human judgment required.

## What this skill does NOT do

- Does not modify files. Use `/review:review-fix`.
- Does not fetch PR comments from GitHub. Paste them inline.
- Does not file tickets in Linear / Jira.

## Reference

- [reference/verdict-block-format.md](./reference/verdict-block-format.md) — canonical verdict block and glossary
