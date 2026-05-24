---
name: rebase
description: Rebases the current branch onto the repo's default branch with interactive per-file conflict resolution and an automatic local backup branch. Use when the user types `/git:rebase`, says `rebase my branch`, `rebase onto main`, `sync my branch with main`, or `update my branch via rebase`. Never pushes without explicit confirmation. Complements `/git:create` (rebase locally → then open a squash-merge PR with a clean linear history).
argument-hint: [base-branch]
allowed-tools: Bash, Read, AskUserQuestion, Edit
---

# rebase

Rebase the current feature branch onto the default branch (typically `main`), with interactive per-conflict prompts and an automatic backup branch so nothing is lost if the rebase goes sideways. Complements `/git:create` (rebase locally → then open a squash-merge PR with a clean linear history). The design follows the "golden rule of rebasing" from Pro Git ([git-scm.com](https://git-scm.com/book/fr/v2/Les-branches-avec-Git-Rebaser-Rebasing)): rebase locally before pushing; never rebase commits that are already shared.

## Prerequisites

- Must be run from a git repository.
- Working tree must be clean (no staged or unstaged changes). The skill stops and asks the user to commit or stash — it never auto-stashes.
- Current branch must be ahead of the base branch by at least one commit.
- Current branch must not be the base branch itself.

## Steps

### 1. Read repo conventions

Read `CLAUDE.md` and `AGENTS.md` at the repo root in parallel if they exist. Absorb naming, commit conventions, and language rules before drafting anything.

### 2. Inspect the workspace

Run these in parallel:

- `git status --porcelain`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git rev-parse --abbrev-ref @{u} 2>/dev/null` (detects whether the branch has an upstream — empty output means it doesn't)

Save the original commit count for later verification (run `git log --oneline <base>..HEAD | wc -l` once `<base>` is known).

### 3. Pre-flight checks

In order:

- If the working tree is not clean (any output from `git status --porcelain`), stop with: `Working tree is dirty. Commit or stash changes, then retry.` List the dirty paths. Never auto-stash.
- Resolve the base branch:

  ```bash
  gh repo view --json defaultBranchRef -q .defaultBranchRef.name
  ```

  If `gh` is unavailable or fails, fall back to `main`. If the user passed an argument (`[base-branch]`), use that instead. Store as `<base>`.

- If the current branch equals `<base>`, stop with: `Already on <base>. Switch to a feature branch first.`
- If the branch has zero commits ahead of `<base>` (`git log --oneline <base>..HEAD` is empty), stop with: `Branch is already at parity with <base>. Nothing to rebase.`
- **Golden rule check** — if step 2 found an upstream, warn explicitly:

  > This branch is already pushed. Rebasing rewrites history — anyone who has pulled these commits will need to re-sync. Continue only if you're the sole user of this branch (typical for solo feature branches in a squash-merge workflow).

  Then ask via `AskUserQuestion`:
  - (a) Continue — I own this branch (Recommended for solo feature branches)
  - (b) Abort

### 4. Create the safety backup

Build a UTC-timestamped backup branch name: `backup/<current-branch>-<YYYYMMDDTHHMMSSZ>`. Example: `backup/feat-rebase-skill-20260524T130000Z`.

```bash
git branch <backup-name>
```

Backup is local only — never auto-pushed. Tell the user explicitly:

> Backup created at `<backup-name>`. To restore at any point: `git reset --hard <backup-name>`.

### 5. Fetch the latest base

```bash
git fetch origin <base>
```

Then show the ahead/behind counts:

```bash
git rev-list --left-right --count HEAD...origin/<base>
```

Format as: `Your branch: N ahead, M behind origin/<base>.`

### 6. Confirm the replay plan

Show the user the list of commits that will be replayed:

```bash
git log --oneline origin/<base>..HEAD
```

Then ask via `AskUserQuestion`:

- (a) Proceed with rebase (Recommended)
- (b) Abort — also runs `git branch -D <backup-name>` to clean up the now-unused backup

### 7. Start the rebase

```bash
git rebase origin/<base>
```

If this completes without conflicts, skip to step 9.

### 8. Conflict loop (per file)

While `git status` reports `rebase in progress` (detect via `git status --porcelain | grep -E '^(UU|AA|DD|AU|UA|UD|DU)'`):

a. List conflicted files:

   ```bash
   git diff --name-only --diff-filter=U
   ```

b. For EACH conflicted file (one at a time, do not batch):
   - Read the file via the `Read` tool to see the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
   - Present to the user, for that file:
     - The "ours" hunk (your branch's version — what was between `<<<<<<<` and `=======`).
     - The "theirs" hunk (the version from `<base>` — between `=======` and `>>>>>>>`).
     - Surrounding context so the user can judge.
   - Ask via `AskUserQuestion`:
     - (a) Keep ours — the change from your branch (Recommended when unsure — your branch's intent is preserved)
     - (b) Keep theirs — the version from `<base>`
     - (c) I'll describe the merge — collect plain-text instructions from the user, then apply via `Edit` and show the result for confirmation before moving on
     - (d) Abort and restore — run `git rebase --abort`, then tell the user the backup branch is intact and how to use `git reset --hard <backup-name>` if they want to walk back further
   - For (a): resolve with `git checkout --ours <file> && git add <file>` (Bash). For (b): `git checkout --theirs <file> && git add <file>`. For (c): use `Edit` to write the resolved content, then `git add <file>`. For (d): stop the whole skill.

c. Once every conflicted file in the current step is resolved (no more `U` entries in `git status`):

   ```bash
   git rebase --continue
   ```

d. If `--continue` triggers a new conflict (Git replays the next commit and it conflicts too), loop back to (a). If `--continue` finishes cleanly, exit the loop.

### 9. Verify the rebased branch

Run:

```bash
git log --oneline <base>..HEAD
```

Compare the commit count to what was saved in step 2.

- If the count is identical → say so: `Replay complete: N commits replayed cleanly.`
- If the count dropped → warn loudly: `WARNING: was N commits, now M commits. Some commits may have been dropped or squashed. Inspect the diff vs. the backup branch before pushing.`

Always show the cumulative diff summary vs. the backup:

```bash
git diff <backup-name>..HEAD --stat
```

### 10. Offer to push

Ask via `AskUserQuestion`:

- (a) Push now with `--force-with-lease` (Recommended) — runs:

  ```bash
  git push --force-with-lease origin <current-branch>
  ```

  Never plain `--force`. If the push fails because the lease was broken (someone else pushed), surface the error, do NOT retry, and tell the user to investigate.
- (b) Stop here — print the new HEAD short hash, the backup branch name, and the exact push command above for the user to run later.

### 11. Print the result

Always print, even when (b) was chosen at step 10:

- Branch name
- New HEAD short hash (`git rev-parse --short HEAD`)
- Backup branch name (so the user always knows where their pre-rebase state lives)
- Suggested next step:
  - If commits were dropped → "Review `git diff <backup-name>..HEAD` carefully before deleting the backup."
  - Otherwise → "Once you've verified the branch is good, you can delete the backup with: `git branch -D <backup-name>`."

## Hard rules

- **Golden rule of rebasing**: NEVER silently rebase a branch that has been pushed to a shared remote. Always surface the warning in step 3 and require explicit confirmation. (Source: [Pro Git, chapitre Rebaser](https://git-scm.com/book/fr/v2/Les-branches-avec-Git-Rebaser-Rebasing) — rebasing pushed commits forces collaborators to re-sync and pollutes history with duplicate patches.)
- NEVER use `git push --force` — always `--force-with-lease`. The "lease" refuses the push when the remote moved since the last fetch, so a teammate's push isn't silently overwritten.
- NEVER push without going through step 10's `AskUserQuestion`.
- NEVER delete the backup branch automatically. The user removes it when they're confident.
- NEVER use `--no-verify`, `--strategy=ours`, `--strategy=theirs`, or any other lossy auto-resolution flag on `git rebase`.
- NEVER auto-stash dirty changes — stop and ask the user instead.
- NEVER rebase when the working tree is dirty.
- ALWAYS create the backup branch BEFORE running `git rebase`.
- ALWAYS resolve conflicts one file at a time with an explicit `AskUserQuestion` per file. Never batch.
