# Runtime

Runtime cost compounds: every stylesheet, animation frame, and cache miss adds latency. Bias toward GPU-cheap work and stable cache keys.

## Vendor chunk isolation

**What** — One chunk per npm dependency so bumping a single package invalidates a single chunk, not the entire vendor graph.

**Why** — A traditional `vendor.js` bundle invalidates on any dependency update, forcing repeat visitors to re-download every library. Per-package chunks keep most of the cached vendor footprint warm across releases.

**When to apply** — Apps with many small dependencies and frequent releases — especially valuable for repeat users on metered or slow connections.

**Anti-pattern** — Monolithic `vendor.js`. One patch bump triggers a full vendor re-download for every returning user.

## Variable fonts

**What** — A single `.woff2` file with `font-weight: 100-900` replaces per-weight requests.

**Why** — A static font family fetches 4-9 weights as separate files; a variable font interpolates from one source. Match `crossorigin` between preload and CSS reference so the browser reuses a single fetch instead of double-fetching.

**When to apply** — Any UI using multiple weights of the same family — dashboards, editors, marketing pages.

**Anti-pattern** — Loading `font-400.woff2`, `font-500.woff2`, `font-600.woff2`, etc. Multiplies payload, cache entries, and preload tags for the same family.

## GPU-only animations

**What** — Animate `transform` and `opacity` only. Layout-triggering properties (`width`, `height`, `margin`, `padding`) are off-limits.

**Why** — Layout-triggering animations re-run the layout algorithm and repaint every frame on the main thread, stealing time from JS. `transform` and `opacity` are composited on the GPU and never invalidate layout.

**When to apply** — Every UI animation — menus, drawers, modals, list reorderings, hover states.

**Anti-pattern** — `transition: height 200ms`. Janks on cheap hardware and drops below 60 fps on busy main threads.

## Asymmetric animation timing

**What** — Appear instant, fade out over ~150ms.

**Why** — User-initiated actions feel laggy if entry takes longer than ~100ms because the brain stops associating cause with effect. Dismissal is non-critical, so a slower fade communicates "saved" or "closed" without delaying intent.

**When to apply** — Menus, popovers, toasts, autocomplete suggestions, modal dialogs.

**Anti-pattern** — Symmetric 300ms in/out. Entry feels sluggish, exit feels normal — the worst of both.
