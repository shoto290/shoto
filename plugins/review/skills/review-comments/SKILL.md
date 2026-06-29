---
name: review-comments
description: 'Triages PR comments into a verdict list (FIX, FIX-STYLE, INTENTIONAL, OUT-OF-SCOPE, DISCUSS). Read-only; output feeds review:review-fix.'
when_to_use: When you need to triage PR comments — turn a batch of review feedback into a per-comment verdict list (FIX, FIX-STYLE, INTENTIONAL, OUT-OF-SCOPE, DISCUSS) before deciding what to change.
argument-hint: "[optional: paste PR comments or @PR-url — omit to auto-fetch the current PR's unresolved threads]"
allowed-tools: Read, Glob, Grep, AskUserQuestion, Bash
---

Triage PR review comments into a structured decision list. Each comment gets one verdict block; the list is the handoff payload for `/review:review-fix`.

## Hard rules

- **READ-ONLY on the codebase.** Never modify files: `allowed-tools` excludes `Edit` and `Write`. `Bash` is allowed ONLY to run read-only `gh` commands that fetch PR comments — never to mutate files, git state, or the PR.
- **Fetch only on the no-argument path.** If the user provides inline comments or a `@PR-url`, use them (paste mode) and do NOT call `gh`. Only when NO argument is given may the skill auto-fetch via `gh`.
- **Never auto-apply a fix.** Output is a decision list only. `/review:review-fix` is the WRITE counterpart.
- **One verdict block per comment.** Preserve input order; never merge multiple comments into one block.

## Input contract

User pastes review comments. Parse one tuple per comment:

```
(N, file, line, text)
```

- `N` is 1-based, in the order comments appear in the input.
- `text` is kept verbatim.
- File-level comments have no `line` — record `null` and render `[File]` in the block.

## Steps

1. **Acquire comments.**

   - If the user supplied inline comments or a `@PR-url` argument → PASTE MODE: skip fetching and go straight to parsing the pasted input (existing behavior). If the input is only a `@PR-url` with no inline comments, ask the user to paste them.
   - If NO argument was given → AUTO-FETCH MODE:
     1. Detect the current branch's PR:
        ```bash
        gh pr view --json number -q .number
        ```
        If this fails / returns nothing (no PR for the branch), STOP fetching and ask the user to paste the comments inline — there is nothing to auto-fetch.
     2. Resolve the repo and fetch UNRESOLVED review threads only:
        ```bash
        gh api graphql \
          -F owner="$(gh repo view --json owner -q .owner.login)" \
          -F repo="$(gh repo view --json name -q .name)" \
          -F pr="$(gh pr view --json number -q .number)" \
          -f query='
            query($owner:String!, $repo:String!, $pr:Int!) {
              repository(owner:$owner, name:$repo) {
                pullRequest(number:$pr) {
                  reviewThreads(first:100) {
                    nodes {
                      isResolved
                      comments(first:1) {
                        nodes { path line originalLine body author { login } }
                      }
                    }
                  }
                }
              }
            }' \
          --jq '.data.repository.pullRequest.reviewThreads.nodes[]
                | select(.isResolved == false)
                | .comments.nodes[0]
                | {file: .path, line: (.line // .originalLine), text: .body, author: .author.login}'
        ```
        Only `isResolved == false` threads are kept; resolved threads are excluded. Take the root (first) comment of each unresolved thread.
     3. Build the `(N, file, line, text)` tuple list from these results, numbering 1-based in the order returned. A null `line` (file-level or outdated) → record `null` and render `[File]`, exactly as the paste path already does.
     4. If the PR exists but has zero unresolved threads, report that there are no unresolved comments to triage and stop.

2. **Read context.** Read `CLAUDE.md` and `AGENTS.md` at the repo root. If a plan file exists under `.plan/*.md`, read it. These distinguish intentional patterns from real issues.

3. **Parse comments** into the tuple list above. If the input is only a `@PR-url` (no inline comments), stop and ask the user to paste the comments — the skill cannot fetch them.

4. **Triage each comment inline.** For each comment, in input order:

   - `Read` the cited file with ±20 lines around the cited line. If the file or line cannot be located, emit a `DISCUSS` verdict naming what was missing.
   - Use `Grep` / `Glob` to check whether the flagged pattern appears elsewhere. Repeated, consistent use is strong evidence of an intentional convention; a one-off is more likely a local mistake.
   - Cross-check against the plan / `CLAUDE.md` / `AGENTS.md`.
   - Choose exactly one verdict using the criteria below and emit the verdict block.

5. **Render the decision list.** For each comment, emit exactly the block defined in [reference/verdict-block-format.md](./reference/verdict-block-format.md). Preserve input order.

6. **Summary and handoff.** End with:

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
- Fetches PR comments only on the no-argument path, and only unresolved review threads. When you supply input inline, it does not fetch — it triages what you paste.
- Does not file tickets in Linear / Jira.

## Reference

- [reference/verdict-block-format.md](./reference/verdict-block-format.md) — canonical verdict block and glossary
