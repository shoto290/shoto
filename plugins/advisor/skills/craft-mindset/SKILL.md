---
name: craft-mindset
description: Senior engineering judgment for correctness - edge cases, illegal states, fail-loud, verify before guessing.
when_to_use: Preloaded so code is written correct by construction, and composed by the correctness review lens to judge whether a change handles every path. Covers boundary conditions, null and empty handling, ordering, off-by-one, concurrency, partial failure, and error paths.
user-invocable: false
disable-model-invocation: true
---

# Craft Mindset

Correctness is designed in, not tested in afterwards. Assume nothing, enumerate the ways a change can be wrong, and make the wrong states impossible to reach. This is the discipline for writing correct code and the lens for judging whether code is correct.

## Enumerate the edge cases

Before implementing, list the inputs and states that are easy to forget. Every one is a defect waiting to ship if unhandled.

- Empty: zero items, empty string, empty collection, no rows returned.
- Boundary: first, last, min, max, exactly-at-the-limit, one past it.
- Absent: null, undefined, missing key, optional not provided, default not set.
- Extreme: very large input, deep nesting, zero, negative, overflow.
- Duplicate and out-of-order input where order or uniqueness is assumed.

## Make illegal states unrepresentable

- Model data so an invalid combination cannot be constructed in the first place.
- Prefer a type or shape that carries its guarantees over a validity flag checked everywhere.
- Parse and normalize at the boundary into a trusted shape; the core then operates on data that is correct by construction.
- Fewer reachable states means fewer paths to get wrong.

## Fail loud and early

- Surface errors at the point they occur; never continue into a silently corrupt state.
- Never swallow an exception into an empty catch, a bare log-and-continue, or a default that hides the failure.
- Validate preconditions up front and reject bad input immediately rather than deep inside the logic.
- A crash with a clear message beats a wrong answer that looks right.

## Never guess — verify against the code

- Do not assume a function's behavior, a field's nullability, or a call's ordering. Read it.
- An unverified assumption is a bug waiting to ship. Confirm it in the actual code before relying on it.
- When behavior is genuinely unclear, stop and ask a precise question rather than guessing and hoping.

## Check the paths that hide bugs

- Off-by-one: loop bounds, slice ranges, inclusive vs exclusive limits, pagination edges.
- Ordering: does the sequence of operations matter, and is it guaranteed?
- Error paths: is every failure branch handled, or only the happy path?
- Concurrency: shared mutable state, race conditions, non-atomic read-modify-write, partial writes.
- Partial failure: one call in a sequence fails midway — is the result left consistent or half-applied?

## Prefer explicit over clever

- Straightforward code that is obviously correct beats a terse trick that hides a case.
- If a line needs a comment to prove it is right, it probably needs to be simpler instead.
- Optimize for the reader who must verify correctness under pressure.

## Pass/fail checklist

- [ ] Empty, boundary, null, and extreme inputs are each handled deliberately.
- [ ] Invalid states are unrepresentable, not merely guarded against.
- [ ] Errors fail loud and early; no exception is swallowed or hidden behind a default.
- [ ] Every assumption about behavior, nullability, or ordering was verified in the code.
- [ ] Off-by-one, ordering, and every error path were checked, not just the happy path.
- [ ] Concurrency and partial-failure outcomes leave state consistent.
- [ ] The implementation is explicit and obviously correct, not clever.
