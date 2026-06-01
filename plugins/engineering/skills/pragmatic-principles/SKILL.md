---
name: pragmatic-principles
description: 'Pragmatic Programmer working principles: orthogonality and decoupling, tracer bullets, good-enough software, and dont-repeat-yourself applied to knowledge.'
when_to_use: 'Reach for it when designing module boundaries, deciding how to start a risky feature end-to-end, or judging when software is good enough to ship.'
---

# Pragmatic Principles

Working habits from The Pragmatic Programmer, scoped to decisions about module boundaries, how to start risky work, and when to stop polishing. For the SOLID/DRY/KISS/YAGNI rule set and broader system shape, defer to `solid-dry-kiss-yagni` and `scalable-architecture` rather than restating them here.

## Orthogonality

Decouple unrelated things so a change in one module does not ripple into others. Two components are orthogonal when neither knows the other exists.

- Do: isolate each concern behind a seam so editing one leaves the rest untouched.
- Don't: let one module reach into another's representation.

```ts
// Leaky: report logic knows how the store persists data
function buildReport(store: { rows: Row[] }) { return summarize(store.rows); }

// Orthogonal: report depends only on the data it needs
function buildReport(rows: Row[]) { return summarize(rows); }
```

## Decoupling

Talk to your immediate collaborators, not their internals, and depend on interfaces rather than concrete types.

- Do: accept an abstraction and let the caller supply the implementation.
- Don't: chain through objects you were merely handed (`a.getB().getC().run()`).

For the dependency-inversion rationale behind "depend on interfaces", see `solid-dry-kiss-yagni` (DIP); this skill only covers the day-to-day reflex.

## DRY as Knowledge

Every piece of knowledge has a single, authoritative representation. DRY is about duplicated knowledge, not duplicated text — two lines that look alike but encode different decisions are not a violation.

- Do: give each business rule, constant, or schema exactly one home.
- Don't: collapse code that merely looks similar today; for the duplication threshold, apply the Rule of Three from `avoid-over-engineering` as the counterweight.

## Tracer Bullets

Build a thin slice that runs end-to-end — real wiring, real boundaries — then flesh it out. A tracer bullet stays in the codebase and grows; you adjust aim with live feedback.

- Do: connect every layer with minimal logic first, then deepen each layer.
- Don't: confuse it with a throwaway prototype — prototypes are built to be discarded after they answer one question, tracer code is built to keep.

## Good-Enough Software

Ship at the quality bar the context demands. "Good enough" is a deliberate, negotiated target, not an excuse for sloppiness — and perfect is the enemy of done (SIMPLE: Pragmatic).

- Do: agree on the acceptable bar with stakeholders, hit it, and release.
- Don't: gold-plate past the point where added polish stops earning its cost.

## Pass/Fail Checklist

- [ ] Changing one module leaves unrelated modules untouched.
- [ ] Code depends on interfaces, not concrete collaborators' internals.
- [ ] Each piece of knowledge has exactly one authoritative source.
- [ ] Risky features start as a thin end-to-end slice, not a deep partial one.
- [ ] The quality bar was set against the context, not maxed by reflex.
- [ ] Tracer code is kept and grown; throwaway prototypes are discarded.
