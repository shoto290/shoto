---
name: reuse-first
description: Reuse-first - extend existing code before writing anything new.
---

# Reuse First

Before writing a new component, utility, hook, or helper, prove that nothing existing already does the job. New code is the last resort, not the first move.

## The rule

Always check for existing code before writing new — even when verifying takes longer than rewriting. This is the global "Reuse existing functions/components" rule: duplication is a defect, not a shortcut. The minutes spent searching are cheaper than the long-term cost of a parallel implementation that drifts from the original.

## Search before create

Look before you build:

- Grep and glob for similar names — the capability, the domain noun, and obvious synonyms.
- Scan the design system and shared utility modules for an existing primitive.
- Check sibling modules and adjacent features for a pattern already solving this.

When unsure what already exists, run `inventory:inventory-components` to score existing candidates for fit, and `inventory:inventory-conventions` to match house style before adding anything.

## Reuse / Extend / New decision

Pick the lightest option that fits:

- **REUSE as-is** — an existing unit already covers the need. Import and use it.
- **EXTEND existing** — close but not exact. Add a prop, a variant, or a small wrapper rather than forking.
- **NEW** — only when nothing fits after a real search. Require a one-line justification naming what you searched and why each candidate failed.

If you cannot write that justification, you have not earned the right to build new.

## Composition over inheritance

Compose small units — children, wrappers, hooks — instead of reaching for deep class hierarchies. Composition keeps each piece independently testable and reusable; inheritance couples them.

```ts
function ConfirmButton(props: ButtonProps) {
  return <Button variant="danger" {...props} />;
}
```

The wrapper reuses `Button` and adds intent, rather than subclassing a base button to override behavior.

## Design-system reuse

Reach for existing tokens and components before anything bespoke. Use the design system's spacing, color, and typography primitives instead of hardcoded values, and its components instead of one-off markup. For how to build, extend, and theme those primitives, defer to `design-engineer:design-systems` — do not restate its guidance here.

## Pass/fail checklist

- [ ] Searched (grep/glob, design system, shared utils, sibling modules) before writing new code.
- [ ] Ran `inventory:inventory-components` / `inventory:inventory-conventions` when existing coverage was unclear.
- [ ] Chose the lightest fit: REUSE over EXTEND over NEW.
- [ ] Any NEW unit carries a one-line justification for why nothing existing fit.
- [ ] Composed small units instead of adding inheritance depth.
- [ ] Used existing design-system tokens and components instead of bespoke values.
