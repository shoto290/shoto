---
name: review-diff
description: "Reviews the current workspace diff and posts inline findings via mcp__conductor__DiffComment. READ-ONLY — never modifies files. Applies 8 bug criteria from the review guidelines (impact, discreteness, rigor parity, introduced-in-commit, author would fix, no unstated assumptions, provable cross-file impact, not intentional). Posts one comment per distinct issue and returns a numbered markdown summary."
when_to_use: Use on `/review:review-diff`, `review my changes`, `review the workspace diff`, `code review of current changes`.
argument-hint: (none — reviews the current workspace diff)
allowed-tools: Read, Glob, Grep, Bash, mcp__conductor__GetWorkspaceDiff, mcp__conductor__DiffComment, AskUserQuestion
---

# review-diff

Review the current workspace diff against the 8 bug criteria and post one inline `DiffComment` per qualifying finding. READ-ONLY.

## Hard rules

- **READ-ONLY.** Never modify files. `allowed-tools` excludes `Edit` and `Write` by design.
- **One `DiffComment` per distinct issue.** Never batch multiple issues into one comment.
- **Prefer `mcp__conductor__GetWorkspaceDiff`.** Start with `stat: true`, then request specific files. Fall back to git CLI only if the MCP tool is unavailable.
- **Do not flag pre-existing bugs** (criterion 4). The bug must have been introduced in this branch's diff.
- **Do not flag intentional changes** (criterion 8) — if the diff itself looks like a deliberate refactor or behavior change, do not treat it as a bug.
- **Do not flag trivial style** unless it obscures meaning or violates documented standards (`CLAUDE.md`, `AGENTS.md`).

## Bug criteria

A finding qualifies only if ALL of these hold:

1. It meaningfully impacts the accuracy, performance, security, or maintainability of the code.
2. The bug is discrete and actionable (i.e. not a general issue with the codebase or a combination of multiple issues).
3. Fixing the bug does not demand a level of rigor that is not present in the rest of the codebase (e.g. one doesn't need very detailed comments and input validation in a repository of one-off scripts in personal projects)
4. The bug was introduced in the commit (pre-existing bugs should not be flagged).
5. The author of the original PR would likely fix the issue if they were made aware of it.
6. The bug does not rely on unstated assumptions about the codebase or author's intent.
7. It is not enough to speculate that a change may disrupt another part of the codebase, to be considered a bug, one must identify the other parts of the code that are provably affected.
8. The bug is clearly not just an intentional change by the original author.

## Comment style rules

Each `DiffComment` body must satisfy ALL of these:

1. The comment should be clear about why the issue is a bug.
2. The comment should appropriately communicate the severity of the issue. It should not claim that an issue is more severe than it actually is.
3. The comment should be brief. The body should be at most 1 paragraph. It should not introduce line breaks within the natural language flow unless it is necessary for the code fragment.
4. The comment should not include any chunks of code longer than 3 lines. Any code chunks should be wrapped in markdown inline code tags or a code block.
5. The comment should clearly and explicitly communicate the scenarios, environments, or inputs that are necessary for the bug to arise. The comment should immediately indicate that the issue's severity depends on these factors.
6. The comment's tone should be matter-of-fact and not accusatory or overly positive. It should read as a helpful AI assistant suggestion without sounding too much like a human reviewer.
7. The comment should be written such that the original author can immediately grasp the idea without close reading.
8. The comment should avoid excessive flattery and comments that are not helpful to the original author. The comment should avoid phrasing like "Great job ...", "Thanks for ...".

Additional formatting constraints:

- Use ` ```suggestion ` blocks ONLY for concrete replacement code (minimal lines; no commentary inside).
- In every ` ```suggestion ` block, preserve the exact leading whitespace of the replaced lines (spaces vs tabs, number of spaces).
- Do NOT introduce or remove outer indentation levels unless that is the actual fix.
- Avoid line ranges longer than 5–10 lines; pinpoint the issue.

## Steps

1. **Read repo conventions.** Read `CLAUDE.md` and `AGENTS.md` at the repo root. If `.plan/*.md` exists, read those too. These distinguish intentional patterns from real bugs.
2. **Get the diff stat** by calling `mcp__conductor__GetWorkspaceDiff` with `stat: true`.
3. **Per-file diff.** For each changed file, request its diff via `mcp__conductor__GetWorkspaceDiff`. Skip generated files, lockfiles, and binary blobs.
4. **Analyze hunks.** For each file, analyze every hunk against the 8 bug criteria. Be conservative: if uncertain, do not flag.
5. **Post one comment per finding.** For each qualifying finding, call `mcp__conductor__DiffComment` once with the file path, line (or line range — keep it ≤5–10 lines), and a comment body following the 8 style rules.
6. **Render the summary** back to the user using the output contract below.

## Output contract

In addition to posting `DiffComment`s, render to the user:

```
### #1 <short title>
<one-paragraph explanation — same wording as the inline comment>
File: <path>

### #2 <short title>
...
```

If there are no qualifying findings, output a single line:

```
No findings — the diff looks clean against the 8 bug criteria.
```

## Fallback (no MCP tool)

If `mcp__conductor__GetWorkspaceDiff` is unavailable, use git directly:

```bash
MERGE_BASE=$(git merge-base origin/main HEAD)
git diff $MERGE_BASE HEAD     # committed diff vs target
git diff HEAD                  # uncommitted changes
```

Review the combination of both outputs. No need to mention which path was used in the final report.
