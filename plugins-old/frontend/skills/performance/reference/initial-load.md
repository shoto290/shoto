# Initial Load

Initial load is a bandwidth and waterfall problem. Push critical bytes early, parallelize the rest, and never wait on identity before painting.

## Aggressive bundle splitting

**What** — Route-level chunks fetched on demand. Ship only what's needed per route.

**Why** — Each route depends on a subset of the full app. Splitting along route boundaries means cold visits only pay for the entry route's code, not the entire workspace's worth.

**When to apply** — SPAs with distinct route surfaces (dashboard, settings, detail views) and apps shipping more than ~500KB compressed JS.

**Anti-pattern** — Single `app.js` containing every screen. Time-to-interactive scales with total app size, not the screen the user actually opens.

## Parallel modulepreload

**What** — List every chunk dependency via `<link rel=modulepreload>` in the HTML so the browser fetches them in parallel.

**Why** — Without preload hints, ES module imports form a serial waterfall — each chunk is discovered only after its parent finishes parsing. Modulepreload collapses N round trips into a single batch.

**When to apply** — Any app with a non-trivial dependency graph of ES modules (framework + state library + UI kit + utility chunks).

**Anti-pattern** — Relying on the browser to discover dependencies via runtime `import()`. Cold load takes N × RTT instead of 1 × RTT.

## Service worker precaching

**What** — Download route chunks during login so by the first navigation the full app already sits in cache.

**Why** — Authenticated sessions are predictable; the user will visit the same routes. Pre-warming the cache shifts download cost off the critical interactive path.

**When to apply** — Apps with a login boundary and a known route set. Particularly valuable for repeat visitors and offline tolerance.

**Anti-pattern** — Cold-fetch every route on first navigation. Each new section pays full network latency the first time it is opened.

## Inlined app-shell CSS

**What** — Critical CSS in `<head>` eliminates a stylesheet request. A small inline script reads `localStorage` to restore theme and auth state before bundles parse.

**Why** — External stylesheets block first paint; inlining the shell skips a render-blocking round trip. Restoring theme before bundle parse prevents flash-of-wrong-theme.

**When to apply** — Any app where first paint matters — especially apps with theme switching or auth-gated layouts.

**Anti-pattern** — Linking an external `app.css` and letting the framework paint the chrome. White flash, then theme flash, then content.

## Deferred authentication

**What** — Render UI immediately from `localStorage`. Let invalid sessions fail on the first API call instead of blocking paint on a `/me` request.

**Why** — Identity verification is a slow round trip that gates nothing painted. Treat localStorage as the optimistic identity and reconcile asynchronously.

**When to apply** — Authenticated apps where the worst case (expired session) is a recoverable redirect, not a security hole.

**Anti-pattern** — `await fetch('/me')` before mounting the app. Cold visits pay a blocking RTT for an answer that almost always confirms a valid session.
