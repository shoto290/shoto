---
name: review-fix
description: Applies the fix decisions produced by `review:review-comments`. WRITE operation — modifies files. Paste the `/review:review-comments` output into the prompt; this skill delegates each comment marked FIX or FIX-STYLE to its own subagent, one fix at a time, with minimal surgical edits. Skips INTENTIONAL / OUT-OF-SCOPE / DISCUSS. After all fixes, runs auto-detected verification commands (tests / lint / typecheck) based on the project's package manager.
when_to_use: Triggers on `/review:review-fix`, `apply review fixes`, `fix the review comments`.
argument-hint: "[paste /review:review-comments output]"
allowed-tools: Agent, Read, Bash, Glob, Grep
---

# review-fix

WRITE counterpart to `review:review-comments`. Consumes a verdict list (FIX / FIX-STYLE / INTENTIONAL / OUT-OF-SCOPE / DISCUSS) and delegates each FIX and FIX-STYLE item to its own subagent, one fix at a time, each making minimal surgical edits.

## Hard rules

- **One subagent per fix.** Delegate each FIX / FIX-STYLE to its own subagent and process them one at a time — spawn, confirm, then the next. Never batch multiple fixes into one subagent or one edit.
- **Let the orchestrator choose the specialist.** Spawn a subagent suited to the fix's domain, but do NOT prescribe which agent here — routing each fix to the best-fit specialist is the orchestrator's job.
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

### 3. Delegate each fix to its own subagent

Process each FIX / FIX-STYLE comment in the order it appears in the decision list. For each comment:

1. Spawn ONE subagent via the `Agent` tool, scoped to EXACTLY that one fix. Pass it the finding tuple (N, file, line, verdict, text), the repo rules from `CLAUDE.md` / `AGENTS.md`, and the constraints: the minimal change that resolves exactly the comment; no refactor, rename, or "improvement" of adjacent code; never re-open a rejected comment. Let the orchestrator route the spawn to the best-fit specialist for the fix's domain — do NOT name or map specific agents here.
2. Wait for the subagent's confirmation, then print:

   ```
   [#N] Fixed — [File:line] — [one sentence describing the change]
   ```

3. If a subagent reports it could not apply the fix cleanly or introduced a regression, STOP — record which fix failed and do NOT spawn the remaining ones.

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
