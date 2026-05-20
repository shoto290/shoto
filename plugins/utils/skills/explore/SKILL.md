---
name: explore
description: Explore a codebase area and return a compact, location-anchored report for downstream agents. Supports three profiles — `survey` (broad map), `deep-dive` (full four-section report, default), and `targeted` (narrow question scope). Use when a sub-agent or the user needs a structured map of a feature, module, or topic — entry points, control flow, dependencies, and gotchas — without polluting the main context with raw file contents.
argument-hint: [profile=survey|deep-dive|targeted] <topic or feature to explore>
context: fork
agent: Explore
allowed-tools: [Read, Glob, Grep, Bash]
---

# explore

You are exploring this repository to produce a **compact, machine-friendly report** for another agent. Your output is the only thing the calling agent will see — every token must earn its place.

## Arguments
$ARGUMENTS

## Profile selection

Parse `$ARGUMENTS` for a leading `profile=<value>` token.

- If present, strip it and use the remainder as the topic.
- If absent, default to `profile=deep-dive`.
- Accept exactly: `survey`, `deep-dive`, `targeted`. Any other value → fall back to `deep-dive`.

Each profile defines its own budget and output shape. Respect both — do not overspend, do not under-fill.

### `survey` — Broad Map

**When to use it.** Caller needs to know what exists in an area before committing to a deeper look.

**Budget.** Open at most 8 files. Skim only.

**Output sections.** Emit only `## Entry points` and `## Dependencies`. Omit `## Flow` and `## Notes & gotchas` entirely.

### `deep-dive` — Full Report (default)

**When to use it.** Caller needs to understand and reason about an area end-to-end.

**Budget.** Open at most 25 files.

**Output sections.** Emit the full four-section report: `## Entry points`, `## Flow`, `## Dependencies`, `## Notes & gotchas`.

### `targeted` — Narrow Question

**When to use it.** Caller has a specific symbol, file, or question and wants the smallest possible answer.

**Budget.** Open at most 6 files, all within two hops (direct caller / callee / import) of the named target.

**Output sections.** Prepend a single `## Scope` line restating the question in ≤20 words. Then emit only the canonical sections the question actually requires. Every fact still carries a `path:line` anchor.

## Exploration protocol

1. **Locate** — use `Glob` for file patterns and `Grep` for symbol names matching the topic. Cast a wide net first, then narrow.
2. **Read targeted** — only open files that clearly relate. Skim, don't memorize. Stop when the profile's file budget is reached.
3. **Trace** — follow control flow across files. Note who calls whom. (Skip for `survey`.)
4. **Note constraints** — invariants, hidden side effects, env vars, race conditions, framework quirks. (Skip for `survey`.)

Stop exploring as soon as the required sections can be filled with confidence. Over-exploring wastes the calling agent's budget.

## Canonical report format

Return **ONLY** the report. No preamble ("Here is..."), no closing ("Let me know..."), no meta-commentary. Every fact must carry a `path:line` anchor so the caller can verify or jump in.

```markdown
## Scope
<one line — only emitted by the `targeted` profile>

## Entry points
- <path>:<line> — `<symbol signature>` — <≤8-word role>
- ...

## Flow
<arrow chains showing who calls whom, one chain per line>
<caller>:<line> → <callee>:<line> → ...

## Dependencies
- <external lib / service / DB table / API> — used at <path>:<line>
- ...

## Notes & gotchas
- <invariant, constraint, or non-obvious behavior> (<path>:<line>)
- ...
```

Section gating by profile:

- `survey` → `## Entry points`, `## Dependencies` only.
- `deep-dive` → all four sections.
- `targeted` → `## Scope` + only the sections the question requires.

## Token-efficiency rules

- **No narration, no headings beyond those above, no "I found...".**
- **No code blocks** quoting source — give the location, the caller reads it if needed.
- **Signatures**: one line, types only if non-obvious from the name (`login(email, pwd) → Session`).
- **Notes**: lead with the constraint, not the discovery story.
- **Empty section** → write `- (none)` on a single line. Do not omit a section the profile requires.
- **Unknowns**: if a fact can't be confirmed, prefix with `?` (e.g. `- ? rate limit (config/auth.yml:14)`). Do not invent.

## Examples

### `survey` — `profile=survey authentication`

```markdown
## Entry points
- src/auth/routes.ts:14 — `POST /login` — credential entry
- src/auth/routes.ts:42 — `POST /logout` — session teardown
- src/auth/middleware.ts:8 — `requireAuth(req, res, next)` — route guard

## Dependencies
- bcrypt — src/auth/hash.ts:3
- jsonwebtoken — src/auth/token.ts:1
- users table — src/auth/repo.ts:22
```

### `deep-dive` — `authentication` (default profile)

```markdown
## Entry points
- src/auth/routes.ts:14 — `POST /login` — credential entry
- src/auth/middleware.ts:8 — `requireAuth(req, res, next)` — route guard

## Flow
src/auth/routes.ts:14 → src/auth/service.ts:31 → src/auth/repo.ts:22 → src/auth/token.ts:9
src/auth/middleware.ts:8 → src/auth/token.ts:44

## Dependencies
- bcrypt — src/auth/hash.ts:3
- jsonwebtoken — src/auth/token.ts:1
- REDIS_URL env — src/auth/session.ts:6

## Notes & gotchas
- Tokens expire in 15 min; refresh is silent on `requireAuth` hit (src/auth/token.ts:58)
- `login` rate-limited per IP, not per user (src/auth/routes.ts:19)
- ? CSRF check only on cookie-based flow (src/auth/middleware.ts:21)
```

### `targeted` — `profile=targeted why does requireAuth reject valid tokens after deploy?`

```markdown
## Scope
Investigate why `requireAuth` rejects otherwise-valid tokens immediately after a deploy.

## Entry points
- src/auth/middleware.ts:8 — `requireAuth(req, res, next)` — route guard
- src/auth/token.ts:44 — `verify(token) → Claims` — signature check

## Notes & gotchas
- `verify` reads `JWT_SECRET` once at module load (src/auth/token.ts:12) — rotated secret on deploy invalidates in-flight tokens
- No grace window for previous secret (src/auth/token.ts:44)
```
