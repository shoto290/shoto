---
name: create
description: "Creates a pull request with a conventional commit title (`type(scope): description`), a concise human-readable changelog as the PR body, and pushes the current branch. Generic (no ticket-tracker integration); requires `gh` CLI and a GitHub remote."
when_to_use: When you want to open a PR and push the branch — turn the current branch's commits into a pull request with a conventional title and changelog body.
argument-hint: '(none — operates on the current branch)'
allowed-tools: Bash, Read, AskUserQuestion
---

# create

Open a pull request for the current branch with a Conventional Commit title and a short, non-developer-friendly changelog body.

## Prerequisites

- `gh` CLI installed and authenticated. If `gh auth status` fails, stop and tell the user to run `gh auth login`.
- Current branch has at least one commit ahead of the repository's default branch.

## Steps

### 1. Read repo conventions

Read `CLAUDE.md` and `AGENTS.md` at the repo root if they exist. Absorb naming, tone, and commit conventions before drafting anything.

### 2. Resolve the base branch

```bash
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

If the call fails, fall back to `main`. Store the result as `<base>`.

### 3. Gather branch info in parallel

Run these together:

- `git branch --show-current`
- `git log <base>..HEAD --oneline`
- `git diff <base>...HEAD --stat`
- `git status --porcelain`

### 4. Pre-flight checks

- If `git status --porcelain` is non-empty, warn about uncommitted changes and ask via `AskUserQuestion`:
  - (a) Continue without committing
  - (b) Abort so the user can commit first
- If `git log <base>..HEAD` is empty, stop with: `No commits ahead of <base>; nothing to create a PR for.`

### 5. Determine the Conventional Commit type

Infer from commit messages and the diff. See [reference/type-scope-mapping.md](./reference/type-scope-mapping.md) for the full list. Quick map:

- `feat` — new functionality
- `fix` — bug fix
- `refactor` — internal restructure without behavior change
- `chore` — tooling, CI, deps, version bumps
- `docs` — documentation only
- `test` — test-only changes
- `style` — formatting only

### 6. Determine the scope

Derive from the directory prefix of the changed files:

- Single top-level directory touched → use that directory name as scope.
- Two directories, one clearly primary by line count → use the primary scope.
- Three or more, or cross-cutting → omit the scope parentheses entirely.

See [reference/type-scope-mapping.md](./reference/type-scope-mapping.md) for worked examples.

### 7. Draft the title

Format: `type(scope): description` or `type: description`.

- ≤72 characters total
- lowercase after the colon
- no trailing period
- imperative mood (`add`, `fix`, `update` — not `added`, `fixes`)
- describes WHAT changed, not HOW

### 8. Draft the body

Fill in the skeleton in [template.md](./template.md); apply the wording rules in [reference/pr-body-rules.md](./reference/pr-body-rules.md). The Summary is written for a non-developer audience:

- 1 to 4 bullets max
- one short sentence each, starting with an imperative verb
- no file paths, no function names, no technical jargon
- WHAT and WHY, not HOW

### 9. Confirm with the user

Show the drafted title and body via `AskUserQuestion`. Options:

- (a) Create as-is
- (b) Adjust — collect changes, redraft, confirm again

### 10. Push and create the PR

Push the current branch (never `main`, `master`, or `<base>`):

```bash
git push -u origin HEAD
```

Create the PR:

```bash
gh pr create --base <base> --title "<title>" --body "$(cat <<'EOF'
## Summary

- bullet 1
- bullet 2
EOF
)"
```

### 11. Print the result

Output the resulting PR URL and title.

## Hard rules

- NEVER add a "Generated with Claude Code" footer to the PR body.
- NEVER add `Co-authored-by` lines.
- The Summary section is for non-developers — no code refs, no file paths, no function names, no internal jargon.
- NEVER push to a branch named `main`, `master`, or the resolved default branch — push only the current feature branch.
- NEVER force-push.

## Reference

- [template.md](./template.md) — canonical PR body skeleton Claude fills in.
- [reference/type-scope-mapping.md](./reference/type-scope-mapping.md) — Conventional Commit types and scope-selection rules.
- [reference/pr-body-rules.md](./reference/pr-body-rules.md) — wording rules, sample outputs, and opt-in test plan section.
