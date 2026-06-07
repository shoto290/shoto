---
name: design-systems-craft
description: 'Build, structure, and scale a design system - design tokens, component variants, and atomic-design naming and governance.'
when_to_use: 'When creating or restructuring a design system, tokens, or a component library, or naming and documenting components. Not for the React+TS implementation of tokens/theming - use design-engineer:design-systems.'
---

# Design Systems Craft

How a designer builds and scales a design system. One rule underpins all of it: **favor the smallest token, variant, and component set that solves the problem.** Every layer below earns its place only when reuse demands it — never speculatively.

## Token Layers

Three layers, each referencing the one above. Components consume the bottom layer, never raw values.

1. **Primitive** — raw, context-free values. `blue/500 = #3b82f6`, `gray/900`, `size/16`. A palette and a scale. Never applied directly to a design.
2. **Semantic** — role-based, describing intent not appearance: `color.text.primary`, `color.bg.surface`, `color.border.default`, `space.md`, `radius.lg`. Maps to primitives. This is the layer themes swap.
3. **Component** — optional, scoped overrides for one component: `button.bg = color.accent`. Add only when a component genuinely diverges.

| Layer | Example | Who consumes it |
| :-- | :-- | :-- |
| Primitive | `blue/500`, `gray/50`, `size/16` | Semantic tokens only |
| Semantic | `color.text.primary`, `space.md` | Components, designs |
| Component | `button.bg`, `card.shadow` | One component |

**Why semantic naming beats raw values.** `color.text.primary` survives a rebrand; `#111827` does not. Change a primitive once or remap a semantic per theme, and every consumer updates — no find-and-replace across files.

**Light/dark via semantic aliasing.** Primitives stay fixed; only the semantic → primitive mapping flips.

| Semantic token | Light → primitive | Dark → primitive |
| :-- | :-- | :-- |
| `color.bg.surface` | `gray/50` | `gray/900` |
| `color.text.primary` | `gray/900` | `gray/50` |
| `color.accent` | `blue/600` | `blue/400` |

In Figma, this is a variable collection with `Light` and `Dark` modes; the semantic variable points at different primitives per mode. Components bound to semantics re-theme with zero per-component work.

## Variants & Properties

Prefer **one component with properties** over many near-identical components. Figma exposes four property types:

| Property type | Use for | Example |
| :-- | :-- | :-- |
| Variant | Mutually exclusive visual states | `Type = Primary / Secondary`, `Size = SM / MD / LG` |
| Boolean | Optional, independent elements | `Has Icon`, `Disabled` |
| Instance swap | Replaceable nested instance | `Icon = ChevronRight` |
| Text | Editable copy | `Label = "Save"` |

**Single component vs separate components.** Keep one component when items share structure and differ only by property (a button's type and size). Split into separate components when structure differs fundamentally (a Button vs a Checkbox) — forcing them together creates a tangled variant set nobody can navigate.

**Organize variants in a matrix.** Lay variant properties on two axes so every combination is visible and gaps are obvious.

| | Default | Hover | Disabled |
| :-- | :-- | :-- | :-- |
| **Primary** | ✓ | ✓ | ✓ |
| **Secondary** | ✓ | ✓ | ✓ |

**Default + states.** Mark one variant as the default (the first, cleanest combination). Model interaction states (hover, focus, active, disabled) as variant values so designs can show real states instead of redrawing them.

## Atomic Design

Brad Frost's five-stage mental model for composing an interface from the smallest parts up.

| Stage | What it is | Library example |
| :-- | :-- | :-- |
| Atoms | Smallest indivisible UI | Button, Input, Label, Icon |
| Molecules | A few atoms bonded into a unit | Search field (Input + Button) |
| Organisms | Molecules + atoms into a section | Header, Card, Form |
| Templates | Page-level structure, no real content | Dashboard layout, article skeleton |
| Pages | Templates with real content | Settings page, signed-in home |

**Mapping to a component library.** Atoms and molecules are your reusable components. Organisms are composed patterns. Templates and pages live closer to product work. The boundaries are a thinking aid, not a filing law — do not agonize over whether something is a molecule or an organism.

**Composition over duplication.** Build a molecule by nesting existing atom instances, not by redrawing them. When an atom changes, every molecule and organism that nests it inherits the change. Duplication is the thing atomic design exists to prevent.

## Naming Conventions

Names are the system's API. Consistency here makes the library searchable and the handoff clean.

- **Slash-separated component names** group related variants: `Button/Primary/Large`, `Icon/Chevron/Right`. The slashes build a folder tree in the assets panel automatically.
- **Consistent casing.** Pick one convention and hold it: `Title Case` for component names, `lowercase.dot` for tokens (`color.text.primary`). Do not mix.
- **Descriptive layer names.** Rename layers to their role (`label`, `icon-leading`, `container`) — never ship `Frame 427` or `Rectangle 12`. Clean layers make instances legible and code generation accurate.
- **Assets-panel organization.** Slash prefixes plus a published library give consumers a browsable, predictable catalog.
- **Match design names to code component names.** The Figma `Button/Primary` should map to the coded `<Button variant="primary">`. Aligned names are the cheapest defense against design–code drift.

## Documentation

Document next to the component, as a single source of truth — not in a separate deck that rots.

For each component, capture:

- **Usage do / don't** — a correct example beside a common misuse.
- **Props / properties** — every variant, boolean, and instance-swap option, with allowed values.
- **States** — default, hover, focus, active, disabled, loading, error.
- **Accessibility notes** — required label, focus order, contrast, keyboard behavior, ARIA role.

| Field | Captures |
| :-- | :-- |
| When to use / when not | Intent and boundaries |
| Anatomy | Named parts of the component |
| Props | Variants and options |
| States | Interactive and validation states |
| A11y | Contrast, focus, labels, keyboard |

Keep docs where the component lives (component page, or a tool like ZeroHeight bound to the library) so updating the component and its docs is one motion. Separate docs drift out of sync the moment the component changes.

## Scaling & Governance

A design system is a product with internal users. Govern it like one (the *Design That Scales* mindset).

| Lever | What good looks like |
| :-- | :-- |
| Contribution model | A clear path for product teams to propose and add components |
| Versioning | Semantic versions; communicate what changed and why |
| Deprecation | Mark deprecated, give a migration path, then remove — never yank silently |
| Core team | A small, dedicated group owns quality and direction |
| Adoption metrics | Track detach rate, % screens on library components, token coverage |

- **Small core team, broad contribution.** A lean team curates; product teams contribute under review. This scales without a bottleneck and without anarchy.
- **Measure adoption.** If teams detach instances or recreate components, the system is failing them — investigate before adding more.
- **Version deliberately.** Breaking changes get a major bump and a migration note. Stability is what earns trust.

## Pitfalls

- **Token sprawl** — a token per component instead of reusing semantics. Reuse first; add a component token only on real divergence.
- **Premature abstraction** — building an organism for something used once. Abstract on the *second* real use, not the first guess.
- **One-off components** — a bespoke component that should have been a variant of an existing one. Check the matrix before creating new.
- **Undocumented variants** — a variant nobody knows exists gets recreated from scratch. Every variant needs a name and a usage note.
- **Drift between design and code** — mismatched names, missing states, divergent tokens. Aligned naming and a single source of truth keep design and code in lockstep.
