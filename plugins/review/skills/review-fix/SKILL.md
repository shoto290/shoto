---
name: review-fix
description: Applies the fix decisions produced by `review:review-comments`. WRITE operation — modifies files. Paste the `/review:review-comments` output into the prompt; this skill executes ONLY comments marked FIX or FIX-STYLE, one at a time, surgically. Skips INTENTIONAL / OUT-OF-SCOPE / DISCUSS. After all fixes, runs auto-detected verification commands (tests / lint / typecheck) based on the project's package manager.
when_to_use: Triggers on `/review:review-fix`, `apply review fixes`, `fix the review comments`.
argument-hint: "[paste /review:review-comments output]"
allowed-tools: Read, Edit, Bash, Glob, Grep
---

# review-fix

WRITE counterpart to `review:review-comments`. Consumes a verdict list (FIX / FIX-STYLE / INTENTIONAL / OUT-OF-SCOPE / DISCUSS) and applies ONLY the FIX and FIX-STYLE items, one at a time, with minimal surgical edits.

## Hard rules

- **One fix at a time.** Do NOT batch changes across multiple files or comments in one operation. Edit, confirm, then move to the next.
- **Minimal changes only.** The fix must address EXACTLY what the comment says. No refactoring, renaming, or "improvement" of adjacent code.
- **Never re-open a rejected comment.** If `review:review-comments` marked it INTENTIONAL, OUT-OF-SCOPE, or DISCUSS — do not touch it. Those decisions were already made.
- **Stop on regression.** If a fix creates a new problem (test breaks, type error, lint failure surfaced by the change), STOP, report which fix caused which failure, and do NOT continue with remaining fixes.
- **Never commit and never push.** This skill writes file changes only; the user reviews the diff and commits.

## Steps

### 1. Read context

Read `CLAUDE.md` and `AGENTS.md` at the repo root if they exist. Respect any project rules they declare.

### 2. Parse the decision list

Extract from the prompt ONLY the comments whose verdict is `FIX` or `FIX-STYLE`. Ignore `INTENTIONAL`, `OUT-OF-SCOPE`, and `DISCUSS` — do NOT re-evaluate decisions already made.

If no `FIX` / `FIX-STYLE` comments are present in the input, stop and report:

```
Nothing to apply.
```

### 3. Apply fixes one at a time

Process each FIX / FIX-STYLE comment in the order it appears in the decision list. For each comment:

1. Use `Read` to load the current state of the file at the referenced line.
2. Use `Edit` to apply the minimal change that resolves the comment.
3. Do NOT refactor, rename, or "improve" adjacent code.
4. Print confirmation immediately:

   ```
   [#N] Fixed — [File:line] — [one sentence describing the change]
   ```

If a fix uncovers a separate problem (something else broken nearby that this fix doesn't address), note it for the "New tickets to create" list. Do NOT fix it.

### 4. Verification

After all fixes are applied, auto-detect verification commands by checking which manifest files exist at the repo root, then run the matching commands via `Bash`.

- **`package.json` present** — detect the package manager from the lockfile (`bun.lockb` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `package-lock.json` → npm). Then run the matching script names that are actually defined in `package.json` `"scripts"`:
  - test → `<pm> run test` (or `<pm> test`)
  - lint → `<pm> run lint`
  - types / typecheck → `<pm> run typecheck` or `<pm> run types`

  Run ONLY the scripts that exist in `package.json`; skip the rest silently.
- **`Cargo.toml` present** — `cargo test`, `cargo clippy --no-deps`, `cargo check`.
- **`pyproject.toml` present** — `pytest` (if `pytest` configured), `ruff check .` (if `ruff` in deps), `mypy .` (if `mypy` configured). Detect by checking for the tool name in `pyproject.toml` content; if absent, skip.
- **`go.mod` present** — `go test ./...`, `go vet ./...`.
- **None of the above present** — print "No verification commands detected; please run your project's tests manually." and skip the verification step.

Report results in a structured block:

```
Post-fix verification:
- Tests:    pass / fail / skipped
- Linter:   pass / fail / skipped
- Types:    pass / fail / skipped
```

If any command fails, include a short excerpt (≤10 lines) of the failure output so the user can act.

### 5. Final summary

Print:

```
## Fixes applied: [N]
[list of #N with file:line and one-line description]

## Skipped (intentional / out-of-scope / discuss): [N]
[list of #N with verdict]

## New tickets to create: [N]
[list of out-of-scope items the user should track separately]
```
