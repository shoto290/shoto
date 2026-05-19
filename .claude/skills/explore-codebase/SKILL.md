---
name: explore-codebase
description: Explore a codebase area and return a compact, location-anchored report for downstream agents. Use when a sub-agent or the user needs a structured map of a feature, module, or topic — entry points, control flow, dependencies, and gotchas — without polluting the main context with raw file contents.
argument-hint: <topic or feature to explore>
context: fork
agent: Explore
---

# explore-codebase

You are exploring this repository to produce a **compact, machine-friendly report** for another agent. Your output is the only thing the calling agent will see — every token must earn its place.

## Topic
$ARGUMENTS

## Exploration protocol

1. **Locate** — use `Glob` for file patterns and `Grep` for symbol names matching the topic. Cast a wide net first, then narrow.
2. **Read targeted** — only open the files that clearly relate. Skim, don't memorize.
3. **Trace** — follow the control flow across files. Note who calls whom.
4. **Note constraints** — invariants, hidden side effects, env vars, race conditions, framework quirks.

Stop exploring as soon as the four sections below can be filled with confidence. Over-exploring wastes the calling agent's budget.

## Output format

Return **ONLY** the report below. No preamble ("Here is..."), no closing ("Let me know..."), no meta-commentary. Every fact must carry a `path:line` anchor so the caller can verify or jump in.

```markdown
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

## Token-efficiency rules

- **No narration, no headings beyond the four above, no "I found...".**
- **No code blocks** quoting source — give the location, the caller reads it if needed.
- **Signatures**: one line, types only if non-obvious from the name (`login(email, pwd) → Session`).
- **Notes**: lead with the constraint, not the discovery story. "JWT expires at 24h" ✓ — "While reading lib/jwt.ts I noticed JWT expires at 24h" ✗.
- **Empty section** → write `- (none)` on a single line. Do not omit it.
- **Unknowns**: if a fact can't be confirmed, prefix with `?` (e.g. `- ? rate limit (config/auth.yml:14)`). Do not invent.

## Example (illustrative — for an "authentication flow" exploration)

```markdown
## Entry points
- src/auth/login.ts:42 — `login(email, pwd) → Session` — REST handler
- src/auth/logout.ts:18 — `logout(sess) → void` — revokes JWT
- src/middleware/requireAuth.ts:9 — `requireAuth(req, res, next)` — guard

## Flow
login.ts:42 → db/users.ts:120 (findByEmail) → lib/bcrypt.ts:8 (verify) → lib/jwt.ts:24 (sign)
requireAuth.ts:9 → lib/jwt.ts:55 (verify) → db/sessions.ts:33 (lookup)

## Dependencies
- bcryptjs — lib/bcrypt.ts:1
- jsonwebtoken — lib/jwt.ts:1
- PostgreSQL `users`, `sessions` tables — db/users.ts:5, db/sessions.ts:5
- POST /auth/login, /auth/logout — routes/auth.ts:12,18

## Notes & gotchas
- JWT TTL is 24h hardcoded, not env-driven (lib/jwt.ts:12)
- Sessions table not pruned on logout — only revoked flag flipped (db/sessions.ts:78)
- requireAuth silently allows expired JWTs in dev mode (requireAuth.ts:21)
- ? Refresh token rotation (no code path found)
```
