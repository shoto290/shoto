---
name: craft-principles
description: Clean-code craft - small named functions, readable flow, SOLID/DRY/KISS/YAGNI, reuse-first, surgical changes.
when_to_use: Preloaded so code reads clearly and stays minimal, and composed by the clean-code and craft review lens to judge whether a change is readable, reused, and free of over-engineering. Covers naming, control flow, the core design principles, premature abstraction, dead code, and change scope.
user-invocable: false
disable-model-invocation: true
---

# Craft Principles

Write code that explains itself and adds no more than the task requires. Clarity, reuse, and restraint over cleverness and speculative structure. This is the discipline for writing clean code and the lens for judging whether a change is well-crafted.

## Small, well-named functions

- Names reveal intent: verbs for functions, nouns for values, predicates (`is`, `has`, `should`) for booleans.
- No abbreviations or single letters except a loop index; name length tracks scope width.
- A function has one reason to change — extract until each does one thing.
- If you reach for a comment to separate sections, split into functions instead.

## Readable control flow

- Guard clauses first; return early to flatten nesting rather than piling up conditionals.
- Keep nesting shallow — deep indentation is a sign to extract.
- No flag arguments; they hide two functions in one.
- No clever one-liners that trade clarity for brevity.

## SOLID, DRY, KISS, YAGNI

- Single responsibility: each unit owns one concern; open to extension, closed to modification.
- Depend on abstractions, not concretions, so callers are not coupled to detail.
- DRY: one authoritative source for each piece of knowledge — but do not merge things that are merely similar by accident.
- KISS: the simplest solution that solves the problem, with the fewest moving parts.
- YAGNI: build only what the task needs now; no speculative flags, hooks, or configurability.

## Reuse first

- Search for an existing function, component, or utility before writing a new one.
- Extend or compose what already exists rather than duplicating it in a new shape.
- Match the established patterns and conventions of the surrounding code.
- A near-duplicate is a maintenance liability; converge on the shared implementation.

## Avoid premature abstraction and over-engineering

- Do not abstract on the first occurrence; wait until the real, repeated shape is clear.
- A wrong abstraction is more expensive than a little duplication — prefer duplication until the pattern proves itself.
- No layers, interfaces, or indirection that no current caller needs.
- Remove complexity that does not earn its place.

## Delete dead code and keep changes surgical

- Delete unused functions, variables, imports, and branches — version control remembers them.
- Never comment out code for later; delete it.
- Touch only what the task requires; do not refactor sections that are not broken or reformat adjacent code.
- Every changed line should trace directly to the request.

## Pass/fail checklist

- [ ] Every name reveals intent; booleans read as predicates.
- [ ] Each function does one thing with shallow nesting and early returns.
- [ ] No flag arguments and no clever one-liners.
- [ ] Knowledge is not duplicated; existing code was reused or extended before new code was written.
- [ ] The solution is the simplest that works; nothing speculative was added.
- [ ] No premature abstraction or indirection without a present need.
- [ ] No dead or commented-out code remains.
- [ ] Changes are surgical and every line traces to the task.
