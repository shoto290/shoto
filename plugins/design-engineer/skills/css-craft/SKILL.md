---
name: css-craft
description: Modern CSS mastery for layout, responsive design, and maintainable styling architecture.
when_to_use: Use when laying out a component (flexbox vs grid, subgrid), implementing responsive behavior (container queries, breakpoints, fluid type), or making a styling-architecture decision (cascade layers, scoping, naming) - "lay out this component", "make it responsive", "structure these styles".
---

# CSS Craft

Modern CSS for expert front-end work. Default to intrinsic, declarative layout. Reach for hacks only when a platform gap forces it.

## Layout Decision Guide

- **Flexbox** — one-dimensional. Content flows along a single axis and sizes itself: toolbars, button rows, nav bars, a label beside a value. Use when item count is dynamic and you want content-driven wrapping (`flex-wrap` + `gap`).
- **Grid** — two-dimensional. You control rows *and* columns, or you want explicit track sizing independent of content: page shells, card grids, form layouts, dashboards.
- **Heuristic** — if you find yourself nesting flex containers to fake rows and columns, switch to grid. If a grid has a single track and you only care about distribution, switch to flex.
- **Subgrid** — `grid-template-columns: subgrid` lets a nested grid inherit the parent's tracks so card internals (title, body, footer) align across siblings. Use it instead of hardcoding matching heights.

## Container Queries Over Viewport Breakpoints

Components should respond to *their own* available width, not the viewport. A card in a sidebar and the same card full-width should adapt independently. This is the default for component-level responsiveness.

```css
.card-list {
  container-type: inline-size;
}

.card {
  display: grid;
  gap: 1rem;
}

@container (min-width: 24rem) {
  .card {
    grid-template-columns: auto 1fr;
  }
}
```

Reserve viewport media queries for true page-level shifts (e.g. collapsing the whole app shell).

## Logical Properties

Use flow-relative properties so layout survives RTL and vertical writing modes without rework.

- `margin-inline` / `margin-block` over `margin-left/right` / `top/bottom`
- `padding-inline` / `padding-block`
- `inset-inline-start` / `inset` over `left` / `top`
- `border-inline-start`, `text-align: start`

Physical properties leak direction assumptions; logical properties are direction-safe by construction.

## Fluid Type, Space, and Intrinsic Sizing

- `clamp(min, preferred, max)` for type and spacing that scales with the viewport without breakpoints. Preferred value uses a viewport unit so it interpolates smoothly.
- `min()` / `max()` to cap or floor a value against context.
- `fit-content`, `min-content`, `max-content` for content-driven track and box sizing.

```css
:root {
  --step-0: clamp(1rem, 0.92rem + 0.4vw, 1.25rem);
  --step-1: clamp(1.25rem, 1.1rem + 0.75vw, 1.75rem);
  --step-2: clamp(1.56rem, 1.3rem + 1.3vw, 2.44rem);
}

h2 { font-size: var(--step-2); }
p  { font-size: var(--step-0); }
```

## Cascade, Specificity, and Scoping

- `:where(...)` wraps selectors at **zero specificity** — ideal for resets, defaults, and library styles that consumers must override effortlessly. `:is(...)` is the same grouping but takes the specificity of its strongest argument.
- `@layer` (cascade layers) orders override priority explicitly, independent of source order or specificity. Define the order once, then later layers always win:

```css
@layer reset, base, components, utilities;

@layer components {
  .btn { background: var(--accent); }
}
```

Layers end specificity wars: a `utilities` rule beats a `components` rule even with lower specificity, because the layer order decides.

## Modern Niceties

- `gap` on flex, grid, *and* `display: flex` — never margin hacks for spacing between siblings.
- `aspect-ratio` for media boxes and avatars instead of padding-percent tricks.
- `:has()` — the relational selector. Style a parent from its children: `.field:has(input:invalid)`, `.card:has(img)`, `form:has(:focus-visible)`.

## Responsive Without Hacks

- **Mobile-first**: base styles for the smallest case, enhance upward with `min-width` container/media queries.
- **No magic numbers**: derive spacing and sizing from tokens (`clamp`, custom properties), not hand-tuned pixel constants.
- **Intrinsic layouts**: let content and available space drive wrapping. The auto-fit grid below reflows with zero breakpoints.

## Worked Examples

**Responsive card grid (intrinsic, no media queries):**

```css
.grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(min(16rem, 100%), 1fr));
}
```

Cards fill the row, wrap when they hit `16rem`, and `min(16rem, 100%)` prevents overflow on narrow screens.

**Container-query card adapting to its slot** — see the example under [Container Queries](#container-queries-over-viewport-breakpoints): the card switches from stacked to side-by-side based on its container, so it works identically in a sidebar or a full-width region.

## Pitfalls

- **Specificity wars** — escalating selectors and `!important`. Fix with `@layer` and `:where()`, not more specificity.
- **Fixed heights** — `height: 400px` clips content. Prefer `min-height`, intrinsic sizing, and `aspect-ratio`.
- **px-everything** — blocks user font scaling and fluid behavior. Use `rem` for type/space, `clamp()` for fluidity.
- **Deeply nested selectors** — `.a .b .c .d` is fragile and slow to override. Keep selectors flat and component-scoped.
- **Viewport queries for components** — couples a component to the page. Use container queries.
