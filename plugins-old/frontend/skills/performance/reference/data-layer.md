# Data Layer

The data layer decides whether interactions feel instant. Treat the network as a sync channel, not a read path; treat the local store as the source of truth for the UI.

## Local-first IndexedDB

**What** — UI reads from an in-memory store hydrated from IndexedDB. The network is for sync, not reads.

**Why** — Removes the network from the read path. Memory access is microseconds; a network round trip is 50-500ms. Hydrating from IndexedDB on boot turns "fetch and render" into "render then sync".

**When to apply** — Collaborative or read-heavy apps where the same records are read repeatedly (issues, contacts, conversations) and the workspace fits in browser storage.

**Anti-pattern** — Fetch-on-render with skeletons. Every navigation pays a round trip, every revisit shows a loading state, and offline use is impossible.

## Optimistic mutations

**What** — Apply changes to local state immediately, push to the server asynchronously, roll back silently on failure.

**Why** — Removes network latency from the feedback loop. The user sees the result before the request leaves; the server becomes a validator, not a gatekeeper.

**When to apply** — Mutations with low conflict probability (toggles, status changes, edits) — any change the user expects to feel instant.

**Anti-pattern** — Spinner on every save. Couples UI feedback to network latency and conflates "request sent" with "operation succeeded".

## Async sync engine

**What** — A background transaction queue flushes via WebSocket so mutations never block on network.

**Why** — Decouples UI from the wire. The same queue retries on flaky networks, batches bursts of edits, and survives disconnects without per-feature error handling.

**When to apply** — Apps with real-time collaboration, offline support, or any flow where progress must continue regardless of network state.

**Anti-pattern** — Awaiting each fetch inside the UI handler. Disconnect becomes an error toast; flap becomes lost edits.

## Granular reactivity

**What** — Track per-property dependencies (MobX-style), not per-component. A 50-row update triggers 50 cell renders, not a full list render.

**Why** — Re-render cost scales with the changed surface, not the rendered surface. Large collaborative views stay smooth when many fields update simultaneously.

**When to apply** — Tables, lists, dashboards, multi-user editors — any view where a small change should not cascade into a large render.

**Anti-pattern** — Top-down `useState` plus prop drilling that re-renders the whole list on any update. Performance degrades linearly with list size.

## Data-level code splitting

**What** — Lazy-hydrate heavy collections (issues, comments) on demand instead of loading the full dataset at startup.

**Why** — Startup cost stays bounded as data grows. A workspace with 100k items boots as fast as one with 100 because only the visible slice is hydrated first.

**When to apply** — Datasets that grow over time and cannot be fully pre-loaded — issue trackers, message archives, file lists, audit logs.

**Anti-pattern** — Single bulk hydrate at boot. App start time scales with workspace size; large customers pay seconds of latency on every cold start.
