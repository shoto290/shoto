<!-- Schema is stable; any planning skill can parse this format. -->

---
name: migrate-auth-middleware-to-oauth2
mode: deep
patterns:
  - anchor: src/middleware/auth.ts:18-74
    description: existing custom JWT middleware with request decoration and 401 handling
  - anchor: src/lib/oauth/client.ts:9-46
    description: OAuth2 client wrapper used by the third-party integrations module
  - anchor: src/middleware/rateLimit.ts:12-58
    description: middleware composition pattern (Next.js `middleware.ts` chain)
  - anchor: tests/middleware/auth.test.ts:1-92
    description: middleware integration test harness with mocked request/response
  - anchor: docs/runbooks/auth-rollout.md:1-48
    description: previous auth rollout playbook (feature flag + staged ramp)
created: 2026-05-27
---

# Plan: Migrate the request auth middleware from custom JWT to OAuth2 with zero-downtime rollout

## Context

The custom JWT middleware in `src/middleware/auth.ts` predates the platform's adoption of OAuth2 for third-party integrations and now duplicates token handling logic. Security wants a single token model across the system, and product wants SSO unlocked for enterprise customers. The migration must be staged behind a feature flag with no user-visible downtime, and must preserve the existing `req.user` contract consumed by every downstream handler. Mode is `deep` because the change touches a shared middleware on the request path, carries rollback risk, and depends on coordinating client, middleware, and tests.

## Reuse-first

- Existing OAuth2 client — `src/lib/oauth/client.ts:9-46` — token introspection and refresh primitives are already battle-tested in the integrations module.
- Middleware composition chain — `src/middleware/rateLimit.ts:12-58` — canonical pattern for adding a middleware to the Next.js `middleware.ts` pipeline.
- Auth integration test harness — `tests/middleware/auth.test.ts:1-92` — fixtures and mocked request/response objects ready to extend.
- Auth rollout runbook — `docs/runbooks/auth-rollout.md:1-48` — feature flag + staged ramp playbook from the previous rollout.

## Steps

### Step 1 — Introduce an `auth-strategy` feature flag

- **action**: add a server-side feature flag `auth-strategy` with values `jwt` (default) and `oauth2`, wired into the existing flag provider.
- **verify**: flag resolves correctly per request in both states; `pnpm test src/lib/flags` covers both branches.
- **mirrors**: `src/lib/flags/strategies.ts:22-58`
- **risk**: `low` — flag plumbing only, no traffic shifted yet.
- **rollback**: delete the flag entry; no runtime consumer yet at this point.

### Step 2 — Implement an `oauth2Auth` middleware alongside the existing JWT path

- **action**: write a new `oauth2Auth` middleware that uses `src/lib/oauth/client.ts` to introspect the bearer token and decorate `req.user` with the same shape as the JWT path.
- **verify**: unit tests cover valid token, expired token, malformed token, and missing token cases; the `req.user` shape diff against the JWT path is empty.
- **mirrors**: `src/middleware/auth.ts:18-74`
- **risk**: `medium` — the `req.user` contract is consumed everywhere; a shape drift breaks downstream handlers silently.
- **rollback**: remove the new file; no other code references it yet.

### Step 3 — Branch the middleware chain on the feature flag

- **action**: in `src/middleware.ts`, read the `auth-strategy` flag and dispatch to either `jwtAuth` or `oauth2Auth`. Keep both wired.
- **verify**: requests with the flag forced to `jwt` produce identical responses to today's baseline; requests forced to `oauth2` succeed for tokens minted by the OAuth2 provider.
- **mirrors**: `src/middleware/rateLimit.ts:12-58`
- **risk**: `medium` — any branching bug routes traffic to the wrong handler; mitigated by leaving the JWT path intact.
- **rollback**: revert the dispatch block to call `jwtAuth` unconditionally.

### Step 4 — Extend the integration test suite to cover both strategies

- **action**: parameterize `tests/middleware/auth.test.ts` so every existing test runs against both `jwt` and `oauth2`; add new cases for OAuth2-specific behaviors (introspection failure, refresh).
- **verify**: `pnpm test tests/middleware/auth.test.ts` shows the doubled test count; both strategies green.
- **mirrors**: `tests/middleware/auth.test.ts:1-92`
- **risk**: `low` — tests only, no runtime impact.
- **rollback**: revert the test file to the JWT-only version.

### Step 5 — Stage the flag ramp in non-production

- **action**: enable `auth-strategy=oauth2` in staging for 100% of traffic; monitor error rate, p95 latency, and 401 ratio for 48h against the JWT baseline.
- **verify**: dashboards show no regression on the three metrics; no novel error classes in the auth log.
- **mirrors**: `docs/runbooks/auth-rollout.md:1-48`
- **risk**: `medium` — staging traffic exposes real client behavior; an unknown OAuth2 edge case can surface here rather than in tests.
- **rollback**: flip the flag back to `jwt` in staging; investigate before re-attempting.

### Step 6 — Ramp the flag in production behind a percentage rollout

- **action**: enable `auth-strategy=oauth2` for 1% → 10% → 50% → 100% of production traffic over a week, gating each step on the same three metrics.
- **verify**: each stage holds error rate, p95 latency, and 401 ratio within the agreed deltas of the JWT baseline.
- **mirrors**: `docs/runbooks/auth-rollout.md:1-48`
- **risk**: `high` — production traffic on the request path; a regression affects every authenticated request.
- **rollback**: flip the flag back to the previous stage's percentage; full rollback is `auth-strategy=jwt` globally.

### Step 7 — Remove the JWT middleware path

- **action**: delete `src/middleware/auth.ts` (JWT implementation), remove the dispatch branch from `src/middleware.ts`, and drop the `jwt` value from the feature flag (keep the flag name for one release to ease emergency rollback later).
- **verify**: `pnpm test` and `pnpm typecheck` pass with the JWT path removed; production stays green for 24h after deploy.
- **mirrors**: `src/middleware/rateLimit.ts:12-58`
- **risk**: `medium` — point of no return; rollback now requires re-introducing code, not flipping a flag.
- **rollback**: revert the deletion commit; redeploy the previous container image.

## Verification

- [ ] All authenticated routes respond identically under `oauth2` and the previous `jwt` baseline (shape, status codes, latency within agreed deltas).
- [ ] The `req.user` shape consumed by downstream handlers is byte-identical across both strategies before Step 7.
- [ ] Production error rate, p95 latency, and 401 ratio for the auth path stay within agreed deltas at every ramp stage.
- [ ] After Step 7, no reference to the old JWT middleware remains in the codebase (`rg "jwtAuth" src/` returns nothing).
