---
name: design-systems
description: Token-driven React + TypeScript design system and theming.
---

# Design Systems

Build and evolve a token-driven design system. The whole discipline reduces to one rule: **components consume semantic tokens, never primitives or raw values.**

## Token Layers

Three layers, each referencing the one above. Components only ever touch the bottom layer.

1. **Primitive** — raw, context-free values. `--blue-500: #3b82f6`, `--gray-900`, `--size-16`. Never used directly by components.
2. **Semantic** — intent, not appearance. `--color-bg`, `--color-fg`, `--color-fg-muted`, `--color-border`, `--color-accent`, `--space-4`. Maps to primitives. This is the layer theming swaps.
3. **Component** — optional, scoped overrides for one component. `--button-bg: var(--color-accent)`. Add only when a component needs to diverge.

Semantic tokens decouple UI from raw values: change `--blue-500` once, or remap `--color-accent` per theme, and every consumer updates. No find-and-replace across components.

## Token Categories

| Category | Tokens |
| :-- | :-- |
| Color | `--color-bg`, `--color-fg`, `--color-fg-muted`, `--color-border`, `--color-accent`, `--color-danger` |
| Spacing | `--space-1`…`--space-12` (numeric scale, e.g. 4px step) |
| Typography | `--font-size-*`, `--line-height-*`, `--font-weight-*` |
| Radius | `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full` |
| Elevation | `--shadow-sm`, `--shadow-md`, `--shadow-lg` |
| Z-index | `--z-dropdown`, `--z-modal`, `--z-toast` (named, ordered) |
| Motion | `--duration-fast`, `--duration-base`, `--ease-out` |

## Naming & Scale Conventions

- **kebab-case**, prefixed by category: `--color-fg-muted`, `--space-4`.
- **Numeric scales** for continuous dimensions (spacing, type, radius): `--space-1`…`--space-12`. Predictable, extensible.
- **T-shirt sizes** for small discrete sets (radius, shadow): `sm` / `md` / `lg`.
- **Intent names** for color and z-index: `bg` / `fg` / `accent` / `danger`, `modal` / `toast` — describe role, not value (`--color-accent`, not `--color-blue`).

## Theming

Define light values on `:root`, override only the swapped semantic tokens under `[data-theme="dark"]`. Primitives stay fixed; semantics remap.

```css
:root {
  --blue-500: #3b82f6;
  --gray-50: #f9fafb;
  --gray-900: #111827;

  --color-bg: var(--gray-50);
  --color-fg: var(--gray-900);
  --color-accent: var(--blue-500);

  --space-1: 0.25rem;
  --space-4: 1rem;
  --radius-md: 0.5rem;
  --shadow-md: 0 4px 6px rgb(0 0 0 / 0.1);
}

[data-theme="dark"] {
  --color-bg: var(--gray-900);
  --color-fg: var(--gray-50);
}
```

Toggle by setting `document.documentElement.dataset.theme = "dark"`. Components read `--color-bg` and follow automatically — no per-component theme logic.

## Typed Accessor + Consumer

A typed accessor keeps token names honest in TS:

```ts
const tokens = {
  colorBg: "--color-bg",
  colorFg: "--color-fg",
  colorAccent: "--color-accent",
  space4: "--space-4",
  radiusMd: "--radius-md",
} as const;

type Token = keyof typeof tokens;

export const cssVar = (token: Token) => `var(${tokens[token]})`;
```

```tsx
export function Button({ children }: { children: React.ReactNode }) {
  return (
    <button
      style={{
        background: cssVar("colorAccent"),
        color: cssVar("colorBg"),
        padding: `${cssVar("space4")}`,
        borderRadius: cssVar("radiusMd"),
      }}
    >
      {children}
    </button>
  );
}
```

The component references only semantic tokens. Theme switches and primitive edits flow through untouched.

## Workflows

**Create from scratch**
1. Define primitives (color ramps, a base spacing unit, type scale).
2. Map semantics on `:root` (`--color-bg`, `--color-fg`, `--space-*`, …).
3. Add `[data-theme="dark"]` overrides for the semantics that change.
4. Build the typed accessor; wire the first components to semantics only.

**Extend without breaking**
1. Add the new token alongside existing ones (never repurpose a live token's meaning).
2. Provide it in every theme block so no theme is missing it.
3. Add it to the typed accessor. Existing consumers are unaffected because nothing was renamed or removed.

**Refactor hardcoded → tokens**
1. Grep for raw values (`#`, `px`, `rgb(`) in components.
2. Map each to the nearest existing semantic token; if none fits, add one (extend workflow).
3. Replace inline. Verify visually per theme.

## Consistency Checks & Pitfalls

- **One-off values** — a raw `#`, `px`, or `rgb()` in a component is drift. Route it through a token.
- **Primitive leakage** — a component using `--blue-500` breaks theming. Always go through a semantic token.
- **Token sprawl** — don't add a token per component; reuse semantics first, add component tokens only on real divergence.
- **Contrast** — verify `--color-fg` on `--color-bg` meets WCAG AA in both light and dark.
- **Scale gaps** — keep numeric scales contiguous and evenly stepped; arbitrary in-between values signal a missing scale step.
