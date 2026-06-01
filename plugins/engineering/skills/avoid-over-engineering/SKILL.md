---
name: avoid-over-engineering
description: 'Write less code: the senior paradox, delete over add, the Rule of Three, and avoiding premature abstraction, premature optimization, and golden-hammer overreach.'
when_to_use: 'Reach for it when tempted to add an abstraction, a config flag, a generic layer, or an optimization — to check whether the simpler or smaller solution is right.'
---

# Avoid Over-Engineering

The simplest solution that solves the problem wins. SIMPLE — **S**imple, **I**ntentional, **P**ragmatic — and AGENTS.md Simplicity First both say the same thing: minimum content that solves the problem, nothing speculative. This skill is the concrete checklist for resisting the urge to add.

## Write less code

The senior paradox: seniority is measured by the code you remove and the problems you avoid, not the lines you ship. The code you don't write can't break, can't drift, and costs nothing to maintain. **Delete over add** — when a change can be made by removing code, prefer that.

- Before adding, ask: can an existing function do this? (reuse over duplication)
- Before keeping, ask: does anything still call this? If not, delete it.
- Self-check from Simplicity First: "Would a senior engineer say this is overcomplicated?"

## Rule of Three

Do not abstract until the **third** real occurrence. Two similar blocks are a coincidence; three is a pattern. Premature DRY guesses the shape of the abstraction before you know it, and the wrong abstraction is more expensive than duplication. See `solid-dry-kiss-yagni` for the full DRY/YAGNI treatment — this is the trigger rule.

```ts
// Two callers: leave them. Inlining is honest.
const a = price * 1.2;
const b = total * 1.2;
```

Extract `withTax()` only when a third caller proves the rule.

## Premature abstraction

No speculative interfaces, base classes, or plugin systems for a single caller. An interface with one implementation is indirection with no payoff.

```ts
// Before: one implementation hiding behind an interface
interface Notifier { send(m: string): void }
class EmailNotifier implements Notifier { send(m: string) { /* ... */ } }

// After: just the function the one caller needs
function sendEmail(m: string) { /* ... */ }
```

## Premature optimization

Measure before optimizing. Readable, correct code first; only optimize a path proven hot by a profiler or a real metric (Measurable). Clever code traded for unmeasured speed is a net loss.

```ts
// Before: hand-rolled cache for a list of 12 items
const memo = new Map<string, User>();
function find(id: string) { /* cache plumbing */ }

// After: trivially correct, fast enough
const find = (id: string) => users.find(u => u.id === id);
```

## Golden hammer

Don't force a favorite tool or pattern onto every problem. State machines, event buses, dependency-injection containers, and generics are tools, not defaults. Pick the pattern the problem asks for, not the one you reached for last time.

## Speculative flexibility

Delete unused params, options, and "just-in-case" machinery (Intentional: every line exists for a reason). Flexibility that wasn't requested is dead weight that still has to be read and maintained.

```ts
// Before: options nobody passes
function format(d: Date, opts?: { tz?: string; locale?: string; pad?: boolean }) { /* ... */ }

// After: the signature the callers actually use
function format(d: Date) { /* ... */ }
```

Add a parameter when a real caller needs it — not before.

## Pass/fail checklist

- [ ] Could this change be made by **deleting** code instead of adding it?
- [ ] Is each new abstraction backed by a **third** real occurrence (Rule of Three)?
- [ ] Does every interface/base class have **more than one** real implementation?
- [ ] Is every optimization backed by a **measurement** of a proven hot path?
- [ ] Is the chosen pattern the one the **problem** asks for, not a habit?
- [ ] Does every param, option, and flag have a **real caller** today?
- [ ] Would a senior engineer call this **overcomplicated**? If yes, simplify.
