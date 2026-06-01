---
name: component-craft
description: Building accessible, reusable, well-typed React components through component-driven development. Covers component API design, typed variants, composition vs configuration, interactive states, accessibility, and TypeScript prop typing (ComponentPropsWithoutRef, ref forwarding, discriminated unions).
when_to_use: When the task is to build a component, design a component API, add variants, or make a component reusable / accessible. Triggers — "build a component", "design a component API", "add variants", "make this reusable", "make this accessible".
---

# Component Craft

Build React + TypeScript components that are small, composable, accessible, and precisely typed. Default to the simplest component that solves the problem; add flexibility only when a second real use case demands it.

## Mindset

- Build from the smallest reusable unit up. One component, one responsibility.
- A component is an API. Design the call site first, then the implementation.
- Prefer composition (subcomponents, `children`) over configuration (a wall of boolean props).

## Prop API design

- Minimal required props; sensible defaults for the rest.
- Model mutually exclusive variants as a discriminated union, not loose optional props — the compiler then rejects invalid combinations.
- Forward refs on any component that wraps a real DOM node; spread remaining props onto the root element so consumers reach native attributes.
- Reach for `asChild` / polymorphism only when consumers genuinely need to swap the rendered element. It is not free — skip it by default.

```tsx
type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: "solid" | "outline" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
};
```

## Composition over configuration

When a component starts growing booleans like `showHeader`, `showFooter`, `withIcon`, that is the signal to expose compound subcomponents instead:

```tsx
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Body>…</Card.Body>
</Card>
```

Compound components let consumers compose what they need without you predicting every layout. Use a boolean prop only for a genuine binary toggle.

## Typed variants

Keep variant logic in one typed map keyed by the prop union. cva works; a small typed record is enough and dependency-free:

```tsx
const styles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  solid: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-blue-600 text-blue-600 hover:bg-blue-50",
  ghost: "text-blue-600 hover:bg-blue-50",
};
```

The `Record` over the union forces every variant to be handled — adding a variant to the union and forgetting its style becomes a compile error.

## Handle every interactive state

A component is not done until all states are styled and reachable:

`default` · `hover` · `focus-visible` · `active` · `disabled` · `loading` · `error`

- Use `:focus-visible` (not `:focus`) so keyboard users get a ring without mouse-click rings.
- `disabled` must block interaction and convey it (`disabled` attribute / `aria-disabled`), not just dim opacity.
- `loading` should set `aria-busy` and prevent duplicate submits.

## Accessibility baked in

- Semantic element first: a `<button>` before a `<div role="button">`. Native semantics give you keyboard, focus, and roles for free.
- Add `role` / `aria-*` only where semantics fall short (custom widgets: tabs, combobox, dialog).
- Keyboard: every interactive element reachable and operable by keyboard; respect expected key behavior (Enter/Space, Arrow keys, Esc).
- Manage focus deliberately for overlays — move focus in on open, restore it on close, trap it while open.
- Pair every icon-only control with an accessible name (`aria-label`).

## TypeScript

- Type props precisely; extend native props with `ComponentPropsWithoutRef<"button">` so consumers get the full native surface.
- Use `ComponentPropsWithoutRef` together with `forwardRef` for ref-forwarding components.
- Add generics only when they carry real type information (e.g. a `Select<T>` whose `value`/`onChange` track the option type). Do not add generics gratuitously.
- Do not reach for `useEffect` to derive state from props — compute during render. Use it only for genuine external synchronization (subscriptions, focus management, non-React DOM).

## Worked example: Button

```tsx
import { ComponentPropsWithoutRef, forwardRef } from "react";

type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: "solid" | "outline" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
};

const variantStyles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  solid: "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800",
  outline: "border border-blue-600 text-blue-600 hover:bg-blue-50",
  ghost: "text-blue-600 hover:bg-blue-50",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "solid", size = "md", loading = false, disabled, className, children, ...rest }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      aria-busy={loading}
      className={[
        "inline-flex items-center justify-center rounded font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
        "disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" ? "h-8 px-3 text-sm" : "h-10 px-4",
        variantStyles[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </button>
  ),
);

Button.displayName = "Button";
```

This shows the whole pattern: native props extended, discriminated variant union, exhaustive variant map, ref forwarding, rest-prop spreading, `focus-visible` ring, and merged `disabled` + `loading` state with `aria-busy`.

## Pitfalls

- **Prop drilling** — threading props through layers that do not use them. Lift to composition (`children`) or context.
- **Leaky abstractions** — a wrapper that hides native props consumers need (`id`, `aria-*`, `type`). Spread `...rest` to the root instead.
- **Premature flexibility** — config props, slots, and generics added for a use case that does not exist yet. Build for the second real case, not the imagined one.
