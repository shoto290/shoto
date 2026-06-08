---
name: solid-dry-kiss-yagni
description: The four core design principles - SOLID, DRY, KISS, YAGNI.
---

# SOLID, DRY, KISS, YAGNI

The four principles that keep a design honest. Apply them to decide where boundaries go, when to abstract, and when to stop. For the broader discipline of cutting speculative work, defer to the `avoid-over-engineering` skill rather than re-deriving it here.

## SOLID

- **SRP — Single Responsibility.** A unit changes for one reason. If a class both formats a report and emails it, two unrelated requirements can break it.

```ts
class Invoice { calculateTotal() {} }
class InvoiceMailer { send(invoice: Invoice) {} }
```

- **OCP — Open/Closed.** Extend behavior without editing the dispatcher. Replace a growing `switch` with a strategy map.

```ts
const handlers: Record<Kind, (o: Order) => number> = { standard: std, express: exp };
const fee = handlers[order.kind](order);
```

- **LSP — Liskov Substitution.** A subtype must honor the base contract. A `ReadOnlyList` that throws on `add()` is not substitutable for `List` — model it as a separate type, not a subclass.

- **ISP — Interface Segregation.** Depend on the narrow interface you use. A consumer that only reads should take `{ get(id): T }`, not the full repository with writes and migrations.

- **DIP — Dependency Inversion.** Depend on abstractions, not concretions. Take the interface as a constructor argument so the concrete client is injected, not imported.

```ts
class Notifier { constructor(private channel: Channel) {} }
```

## DRY

DRY is about a single source of truth for **knowledge**, not about deleting code that merely looks alike. Two functions with the same shape but different reasons to change are coincidental duplication — collapsing them couples unrelated concepts. Extract only when the same decision lives in two places and must always move together. Before extracting from a third occurrence, apply the Rule of Three (see the `avoid-over-engineering` skill).

## KISS

Pick the simplest thing that works and reject cleverness that buys nothing. A reader should understand the code on first pass; a dense one-liner that needs a comment to decode has already failed.

```ts
const isAdult = (age: number) => age >= 18;
```

This embodies the **S** in SIMPLE: less code, fewer abstractions, no machinery the problem did not ask for.

## YAGNI

Build for today's requirement, not an imagined one. Every speculative parameter, feature flag, or config knob is code you maintain, test, and explain for a caller that may never arrive. Delete the `options` bag with one real field; add the second field when a second caller exists.

```ts
function exportCsv(rows: Row[]) {}
```

Not `exportCsv(rows, { delimiter = ",", encoding = "utf8", async = false } = {})` until something actually passes those.

## When they conflict

DRY and KISS pull against each other. Premature DRY is the more expensive mistake: a shared abstraction extracted too early hardens the wrong seam, and every later divergence fights the abstraction with flags and special cases. Prefer a little duplication over the wrong coupling — inline the repetition until the real shared knowledge is obvious, then extract once.

## Pass/fail checklist

- **SRP** — Does this unit have exactly one reason to change?
- **OCP** — Can I add a new variant without editing existing branching?
- **LSP** — Can every subtype stand in for its base without surprising the caller?
- **ISP** — Does each consumer depend only on the methods it calls?
- **DIP** — Do high-level modules depend on interfaces, not concrete classes?
- **DRY** — Is each piece of knowledge expressed in exactly one place?
- **KISS** — Would a senior engineer call this the obvious solution, not the clever one?
- **YAGNI** — Does every parameter, flag, and branch serve a requirement that exists today?
- **Abstraction** — Did I add an abstraction without a second real caller?
