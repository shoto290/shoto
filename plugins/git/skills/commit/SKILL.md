---
name: commit
description: "Creates a single git commit with a Conventional Commit title (`type(scope): description`) from the current uncommitted changes. Auto-stages tracked changes, skips secrets (`.env`, `*.pem`, `*.key`, `*.cert`, `secrets/`), and requires user confirmation before committing. Never pushes — pushing is `/git:create`'s job. Exactly one commit per invocation."
when_to_use: Use when the user types `/git:commit`, says `create commit`, `commit changes`, `stage and commit`, or `make a commit`.
argument-hint: '(none — operates on current uncommitted changes)'
allowed-tools: Bash, Read, AskUserQuestion
---

# commit

Stage the current changes and create a single commit with a Conventional Commit title. Complements `/git:create` (commit → then open a PR).

## Prerequisites

- Must be run from a git repository.
- Working tree has at least one change (staged or unstaged). Otherwise the skill stops cleanly.

## Steps

### 1. Read repo conventions

Read `CLAUDE.md` and `AGENTS.md` at the repo root in parallel if they exist. Absorb naming, commit conventions, and language rules before drafting anything.

### 2. Inspect the workspace

Run these in parallel:

- `git status --porcelain`
- `git diff --stat`
- `git diff --cached --stat`
- `git branch --show-current`

### 3. Pre-flight checks

In order:

- If the working tree is clean (no staged AND no unstaged changes), stop with: `No changes to commit.` Do not create empty commits.
- If `git status --porcelain` lists any path matching `.env`, `.env.*`, `*.pem`, `*.key`, `*.cert`, or anything under `secrets/`, stop and list the offending paths. Tell the user to either remove them from the working tree or add them to `.gitignore` and retry. Never auto-stage secrets.
- Resolve the default branch:

  ```bash
  gh repo view --json defaultBranchRef -q .defaultBranchRef.name
  ```

  If `gh` is unavailable or the call fails, fall back to `main`. Store as `<base>`.

- If the current branch equals `main`, `master`, or `<base>`, warn and ask via `AskUserQuestion`:
  - (a) Abort (Recommended)
  - (b) Continue anyway

### 4. Auto-stage

Run `git add -A`. Then re-run `git diff --cached --stat` and present the staged file list to the user as a short summary.

### 5. Infer Conventional Commit type and scope

Apply the rules from [../create/reference/type-scope-mapping.md](../create/reference/type-scope-mapping.md). Quick recap:

- `feat` — new functionality
- `fix` — bug fix
- `refactor` — internal restructure without behavior change
- `chore` — tooling, CI, deps, version bumps
- `docs` — documentation only
- `test` — test-only changes
- `style` — formatting only

Scope is the single touched top-level directory, or omitted entirely when the change is cross-cutting.

### 6. Draft the title

Format: `type(scope): description` or `type: description`.

- ≤72 characters total
- lowercase after the colon
- no trailing period
- imperative mood (`add`, `fix`, `update` — not `added`, `fixes`)
- describes WHAT changed, not HOW
- single-line title only — no extended body (one commit per call; re-invoke for further work)

### 7. Confirm with the user

Show the drafted title via `AskUserQuestion`. Options:

- (a) Commit as drafted (Recommended)
- (b) Adjust — collect a new title from the user, validate against the constraints (length, format), re-confirm.

### 8. Create the commit

```bash
git commit -m "<title>"
```

Do not pass `--no-verify`, `--amend`, or `--no-gpg-sign` under any circumstance.

If a pre-commit hook fails: show the hook's output, surface the failing command, and stop. Do not retry, do not amend, do not bypass.

### 9. Print the result

Output the short hash (`git rev-parse --short HEAD`) and the committed title. If the branch has commits ahead of `<base>`, suggest `/git:create` as the next step.

## Hard rules

- NEVER add a "Generated with Claude Code" footer to the commit message.
- NEVER add `Co-authored-by` lines.
- NEVER commit `.env`, `.env.*`, `*.pem`, `*.key`, `*.cert`, or contents under `secrets/`.
- NEVER use `--no-verify`, `--amend`, or `--no-gpg-sign`.
- NEVER push after the commit — pushing is `/git:create`'s job.
- Exactly one commit per invocation. If the user wants several logical commits, they re-invoke the skill.
- NEVER commit on `main`, `master`, or the resolved default branch without explicit user confirmation (step 3).

## Reference

- [../create/reference/type-scope-mapping.md](../create/reference/type-scope-mapping.md) — Conventional Commit types and scope-selection rules (reused from `/git:create`).
