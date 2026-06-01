---
name: frontend-perf
description: Front-end performance for React/Next — rendering, bundle size, and Core Web Vitals. Covers React performance, needless re-renders, bundle size and code splitting, layout shift (CLS), LCP, INP, and RSC. Use to diagnose and fix slow UI, oversized bundles, and poor web-vitals scores.
when_to_use: Triggers — "make it faster", "reduce bundle size", "fix a slow render / too many re-renders", "improve Core Web Vitals / LCP / CLS / INP". Use for any React + Next.js performance diagnosis or optimization.
---

# Frontend Perf

Performance work in React + Next.js. The rule above all: measure first, change second. Optimize the proven bottleneck, not the suspected one.

## Measure First

Never optimize blind. Find the actual bottleneck before touching code.

- React DevTools **Profiler** — which components re-render, how often, and why.
- **Lighthouse** / PageSpeed — field and lab Core Web Vitals.
- **Bundle analyzer** (`@next/bundle-analyzer`) — what is actually shipped to the client.
- **web-vitals** library — real-user LCP, CLS, INP in production.

Confirm the cost is real and locate it. A change with no measured before/after is not an optimization.

## Rendering

- Avoid needless re-renders. Lift state to where it is used; co-locate it so a change does not re-render an unrelated subtree.
- Reach for `memo` / `useMemo` / `useCallback` **only when profiling shows they help**. Gratuitous memoization adds cost and noise.
- Use stable, identity-preserving keys in lists — never the array index for reorderable data.
- Do not allocate new objects, arrays, or inline functions in render hot paths; they break referential equality and defeat memoization downstream.

## Hooks Discipline

Do **not** reach for `useEffect` by default — it is for synchronizing with an external system only.

- Derive values during render instead of mirroring them into state via an effect.
- Run logic in event handlers, not effects, when it responds to a user action.
- Subscribe to external stores with `useSyncExternalStore`, not an effect-plus-state pattern.
- Effect-driven data fetching is an anti-pattern here: prefer server components, route loaders, or a query library.

## Server vs Client

- Prefer **React Server Components** and server-side work. Keep data and heavy logic off the client.
- Keep `"use client"` boundaries small and pushed to the leaves — every client component and its imports ship as JS.
- Use **Suspense** and streaming to show meaningful content sooner instead of blocking on the slowest data.

## Bundle

- Code-split with dynamic `import()` (`next/dynamic`) for routes and heavy, non-critical UI.
- Ensure tree-shaking works: import named exports, avoid barrel files that pull in whole libraries.
- Audit heavy dependencies — prefer a lighter alternative or a native API over a large transitive dependency.
- Defer non-critical JS; do not block first paint on analytics or third-party widgets.

## Assets

- Use `next/image` (or correct `width`/`height` + lazy loading) so images are sized, responsive, and non-blocking.
- Load fonts with `next/font`; set `font-display: swap` and preload the critical face to avoid invisible or shifting text.
- Eliminate render-blocking resources — inline critical CSS, defer the rest.

## Core Web Vitals

- **LCP** — prioritize the hero element: preload it, mark the hero image `priority`, and keep the critical path short.
- **CLS** — reserve space for anything that loads late. Always set explicit dimensions or aspect ratios on images, embeds, and ad/widget slots. Layout and intrinsic sizing belong to the `css-craft` skill — delegate there for the layout mechanics.
- **INP** — keep the main thread free: break up long tasks, debounce high-frequency handlers, and use `useDeferredValue` / `startTransition` to keep input responsive during expensive updates.

## Pitfalls

- Premature optimization — tuning code that was never the bottleneck.
- Over-memoization — `memo`/`useMemo`/`useCallback` everywhere, unmeasured.
- Giant client bundles — `"use client"` too high in the tree, heavy deps shipped to the browser.
- Effect-driven data fetching instead of server components or a query layer.
