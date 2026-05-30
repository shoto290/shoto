---
name: performance
description: Web performance patterns for React and Next.js apps distilled from Linear's architecture. Apply when building or auditing fast web apps and discussing bundle size, code splitting, lazy loading, IndexedDB, local-first data, optimistic UI, sync engine, MobX granular reactivity, animations, transitions, GPU rendering, command palette, keyboard shortcuts, service worker precaching, modulepreload, vendor chunks, variable fonts, app shell, hydration, or optimistic mutations.
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Performance

These are web app performance patterns distilled from Linear's architecture; apply them when building or auditing fast web apps.

## Data Layer

The data layer decides whether interactions feel instant. Treat the network as a sync channel, not a read path.

*See [reference/data-layer.md](./reference/data-layer.md) for the principle behind each pattern and when to apply it.*

- **Local-first IndexedDB** — UI reads from an in-memory store hydrated from IndexedDB; the network is for sync, not reads. Reads never block on a round trip.
- **Optimistic mutations** — apply changes to local state immediately, push to the server asynchronously, and roll back silently on failure. The user sees the result before the request leaves.
- **Async sync engine** — a background transaction queue flushes via WebSocket so mutations never block on network. The UI and the wire are decoupled.
- **Granular reactivity** — track per-property dependencies (MobX-style), not per-component. A 50-row update triggers 50 cell renders, not a full list render.
- **Data-level code splitting** — lazy-hydrate heavy collections (issues, comments) on demand instead of loading the full dataset at startup. Startup cost stays bounded as data grows.

## Initial Load

Initial load is a bandwidth and waterfall problem. Push critical bytes early, parallelize the rest, and never wait on identity before painting.

*See [reference/initial-load.md](./reference/initial-load.md) for the principle behind each pattern and when to apply it.*

- **Aggressive bundle splitting** — route-level chunks fetched on demand. Linear ships ~21MB total but only what's needed per route ever reaches a given user.
- **Parallel modulepreload** — list every chunk dependency via `<link rel=modulepreload>` in the HTML so the browser fetches them in parallel instead of discovering them through a serial import waterfall.
- **Service worker precaching** — download route chunks during login; by the first navigation, the full app already sits in the cache.
- **Inlined app-shell CSS** — critical CSS in `<head>` eliminates a stylesheet request, and a small inline script reads localStorage to restore theme and auth state before bundles parse.
- **Deferred authentication** — render UI immediately from `localStorage`; let invalid sessions fail on the first API call instead of blocking the paint on a `/me` request.

## Runtime

Runtime cost compounds: every stylesheet, animation frame, and cache miss adds latency. Bias toward GPU-cheap work and stable cache keys.

*See [reference/runtime.md](./reference/runtime.md) for the principle behind each pattern and when to apply it.*

- **Vendor chunk isolation** — one chunk per npm dependency so bumping a single package invalidates a single chunk, not the entire vendor graph.
- **Variable fonts** — a single `.woff2` file with `font-weight: 100-900` replaces per-weight requests; match `crossorigin` between the preload and the CSS reference so the browser reuses the same fetch.
- **GPU-only animations** — animate `transform` and `opacity` only; layout-triggering properties (`width`, `height`, `margin`, `padding`) are off-limits because they force re-layout on the main thread.
- **Asymmetric animation timing** — appear instant, fade out over ~150ms. Reduces perceived latency on user-initiated actions while keeping dismissal feedback legible.

## Input & Navigation

The fastest UI is the one you don't have to point at. Optimize the path from intent to action.

*See [reference/input-navigation.md](./reference/input-navigation.md) for the principle behind each pattern and when to apply it.*

- **Keyboard shortcut hierarchy** — single-letter shortcuts for frequent operations, two-letter combos for navigation. Shorter path than mouse, predictable to learn.
- **Global command palette** — `⌘K` searches the local store, not the server, so it is instant and works offline.
- **Contextual scoping** — the same palette adapts its actions to the current context (issue, project, settings), teaching shortcuts organically as the user navigates.

## Closing Principle

> Performance emerges from architectural coherence, not isolated optimizations. Remove any layer — local database, optimistic writes, or granular observables — and the system degrades.

*Patterns initially distilled from Linear's public engineering writeup; each reference file states the principle directly so the skill remains useful if the original article moves or disappears.*
