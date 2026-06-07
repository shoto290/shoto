---
name: scalable-architecture
description: Architecture for scale - deep interfaces and evolutionary design.
---

# Scalable Architecture

Design boundaries that stay simple as the system grows. Choose interface depth and the right amount of upfront structure deliberately — most scale problems are boundary problems, not throughput problems.

## Deep vs shallow interfaces

Prefer **deep modules** (Ousterhout): a simple interface that hides a substantial implementation. The cost of a module is its interface; the value is what it does. Maximize value over cost.

Reject **shallow modules** — a wide interface guarding almost no logic. They add surface without hiding anything. **Pass-through methods** (a method that only forwards to another) are a smell: they widen the interface while adding zero abstraction.

```ts
// Shallow: caller still owns the work, the interface just relays it
class Cache { get(k: string) { return this.store.lookup(k); } }

// Deep: one call hides eviction, TTL, and refetch
class Cache { async get(k: string): Promise<Value> { /* ...substantial... */ } }
```

## Hide complexity

Apply information hiding: expose the **minimum surface** a caller needs, and keep design decisions (storage format, retry policy, ordering) inside the module. A caller that must know internals to use you correctly means the boundary leaks. Fewer public methods, fewer required parameters, fewer assumptions escape.

## Evolutionary architecture

Design for **change**, not for an imagined final scale. You cannot predict the real load shape — so make the architecture cheap to evolve instead of betting on a blueprint.

- Make decisions **reversible**: prefer choices you can undo over ones that lock the system in.
- **Defer big commitments** (sharding, a message bus, a new datastore) until a concrete need forces them.
- Do not build for hypothetical scale — see `avoid-over-engineering` (YAGNI). The cost of a wrong abstraction outlives the cost of adding one later.

## System-design judgment

**State your assumptions before choosing**: expected scale, latency budget, and failure modes. A design is only "right" relative to those numbers.

- Pick the **simplest design that meets today's load** while leaving a path to grow.
- **Find the bottleneck before scaling it** — measure, don't guess. Scaling the wrong component adds cost without moving the limit.
- Keep modules orthogonal and decoupled so one can change without the others — see `pragmatic-principles`.

## Robustness

- **Fail loudly at boundaries.** Surface errors where they occur; never swallow them into a silent bad state.
- **Validate inputs at the edge** so the core operates on trusted data — see `secure-by-default`.
- **Isolate failures** so one module's fault does not cascade.
- **No shared mutable state across modules** — communicate through interfaces, not through reaching into each other's data.

## Pass/fail checklist

- [ ] Every module interface is narrower than its implementation (deep, not shallow).
- [ ] No pass-through methods that only forward a call.
- [ ] Public surface exposes the minimum; design decisions stay hidden.
- [ ] Scale, latency, and failure assumptions are stated before the design is chosen.
- [ ] The design meets today's load and has a named path to grow.
- [ ] Big, irreversible commitments are deferred until a concrete need forces them.
- [ ] Inputs are validated at the edge; errors fail loudly at boundaries.
- [ ] No shared mutable state crosses a module boundary.
