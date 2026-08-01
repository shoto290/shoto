---
name: craft-architecture
description: Scalable architecture - deep modules, evolutionary design, bounded work, statelessness, concurrency safety.
when_to_use: Preloaded so structure is designed to scale and evolve, and composed by the scalability and architecture review lens to judge whether a change grows cleanly under load. Covers module depth, dependency direction, N+1 and unbounded work, idempotency, backpressure, and designing for change.
user-invocable: false
disable-model-invocation: true
---

# Craft Architecture

Design boundaries that stay simple as the system grows and cheap to change as requirements shift. Most scale problems are boundary problems, not throughput problems. This is the discipline for structuring code and the lens for judging whether a change scales.

## Deep modules behind simple interfaces

- Prefer a simple interface that hides a substantial implementation. The cost of a module is its interface; the value is what it does.
- Reject shallow modules — a wide surface guarding almost no logic — and pass-through methods that only forward a call.
- Expose the minimum a caller needs; keep design decisions (storage format, retry policy, ordering) inside the module.
- A caller that must know internals to use you correctly means the boundary leaks.

## Clear layering and dependency direction

- Dependencies point one way: toward stable, abstract cores, never back toward volatile detail.
- No cycles between modules; a cycle means the boundary is in the wrong place.
- Keep modules orthogonal so one can change without forcing changes in the others.
- Communicate through interfaces, not by reaching into another module's internals or shared mutable state.

## Bound the work

- No N+1 access patterns: fetch in a set, not one call per item in a loop.
- Paginate, batch, or stream anything that grows with data volume; never load an unbounded result set into memory.
- Cap the size of every queue, buffer, retry, and fan-out — unbounded work is a latent outage.
- Put an upper bound on loops and recursion driven by external input.

## Statelessness and idempotency

- Keep request handling stateless where possible; hold no per-request state in the process across calls.
- Make operations idempotent so a retry or duplicate delivery cannot double-apply an effect.
- Externalize shared state to a store built for it rather than in-process memory that breaks under multiple instances.

## Concurrency safety and backpressure

- Guard shared mutable state; avoid non-atomic read-modify-write across concurrent callers.
- Apply backpressure when a downstream cannot keep up — reject or queue with a bound rather than pile work up without limit.
- Isolate failures so one slow or broken dependency does not cascade; use timeouts on every outbound call.

## Design for change, not speculative generality

- Design for the load and requirements you have, with a clear path to grow — not an imagined final scale.
- Make big, irreversible commitments (sharding, a message bus, a new datastore) only when a concrete need forces them.
- Prefer reversible choices; the cost of a wrong abstraction outlives the cost of adding one later.
- State scale, latency, and failure assumptions before choosing a design — a design is only right relative to those numbers.

## Pass/fail checklist

- [ ] Every module interface is narrower than its implementation; no pass-through methods.
- [ ] Dependencies point one direction with no cycles; modules stay orthogonal.
- [ ] No N+1 patterns; growing work is paginated, batched, or streamed.
- [ ] Every queue, buffer, retry, and fan-out has an explicit bound.
- [ ] Handling is stateless and effects are idempotent under retry or duplication.
- [ ] Shared mutable state is guarded; outbound calls have timeouts and backpressure.
- [ ] Failures are isolated so one dependency cannot cascade.
- [ ] Scale and failure assumptions are stated; irreversible commitments are deferred.
