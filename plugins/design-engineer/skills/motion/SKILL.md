---
name: motion
description: Animation and micro-interactions for React + TypeScript.
---

# Motion

Animation that communicates, not decorates. Every motion earns its place by clarifying one of three things: a **state change**, a **spatial relationship**, or **continuity** between views. Subtle and fast by default — if a user notices the animation instead of the result, it is too much.

## Timing & Easing

| Scope | Duration | Easing |
| :-- | :-- | :-- |
| Micro (hover, press, toggle) | 100–200ms | `ease-out` |
| Larger (enter, expand, page) | 200–400ms | `ease-out` in, `ease-in` out |

- **Entrances** ease-out — fast start, gentle settle. **Exits** ease-in — gentle start, quick finish.
- **Standard** for in-view transitions; **emphasized** (slower, more pronounced curve) only for hero moments.
- Avoid `linear` except for continuous loops (spinners, progress).

## Performant Properties Only

Animate only what the compositor handles off the main thread:

- **Yes** — `transform` (translate, scale, rotate) and `opacity`.
- **No** — `width`, `height`, `top`, `left`, `margin`, `box-shadow`, `color`: these trigger layout or paint and jank.
- `will-change` sparingly — add right before an animation, remove after. Permanent `will-change` wastes memory and can hurt more than it helps.

To move or resize, translate/scale a `transform` rather than animating geometry.

## CSS vs Keyframes vs Spring

- **CSS `transition`** — default for state-driven changes (hover, active, open/close). Cheapest, declarative.
- **`@keyframes`** — multi-step or looping sequences with no JS state (spinners, attention pulses).
- **JS / spring library** (`motion` / Framer Motion) — only when you need spring physics, gesture-driven values, orchestrated sequences, layout/shared-element transitions, or animating mount/unmount cleanly. Keep it framework-light; reach for a library when CSS genuinely cannot express the interaction.

```css
.card {
  transition: transform 150ms ease-out, opacity 150ms ease-out;
}
.card:hover {
  transform: translateY(-2px);
}
```

## Accessibility — Always Honor Reduced Motion

Wrap non-essential motion so it collapses when the user opts out. This is mandatory, not optional.

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

For JS-driven motion, gate on the matching hook and fall back to an instant or fade-only change:

```ts
import { useSyncExternalStore } from "react";

const query = "(prefers-reduced-motion: reduce)";

export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", cb);
      return () => mql.removeEventListener("change", cb);
    },
    () => window.matchMedia(query).matches,
    () => false,
  );
}
```

Use it to skip or shorten animation: `const duration = usePrefersReducedMotion() ? 0 : 200;`.

## Common Micro-interactions

- **Hover / press** — small `transform` (scale 0.98 on press, slight lift on hover) plus opacity. Fast, ease-out.
- **Enter / exit** — fade + short translate for lists, toasts, menus. Stagger children subtly when many appear at once.
- **Layout / shared-element** — animate position changes between states. Use a spring library's layout animation, or the native `view-transition` API (`document.startViewTransition`) for cross-view continuity.

## Vocabulary

Shared names for motion patterns — entrances, sequencing, transforms, state transitions, scroll, feedback, springs, ambient loops, polish, and principles — so a request maps to a known pattern and you describe precisely what to build. See [reference/vocabulary.md](reference/vocabulary.md) for the full glossary (adapted from animations.dev).

## Pitfalls

- **Over-animation** — everything moving competes for attention and slows the user. Motion is a budget; spend it where it clarifies.
- **Janky properties** — animating `width`/`top`/`box-shadow` drops frames. Use `transform` and `opacity`.
- **Blocking interaction** — never make the user wait on a flourish; keep durations short and let content be usable immediately.
- **Ignoring reduced-motion** — unguarded animation is an accessibility defect, not a polish gap.
