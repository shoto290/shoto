---
name: inventory-feature
description: Traces the control/data flow of a single feature — entry point, ordered steps, branches, side effects, and success/error exits — and returns the unified anchored contract. Use when you need to understand how a feature actually executes before modifying it.
when_to_use: Use on `/inventory:inventory-feature`, `trace this feature`, `how does X flow`, `what's the control flow`, `walk the code path`, `inventory a feature`.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-feature
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-feature

You are running inside the `inventory-feature` subagent. Trace the control/data flow of one feature from entry point to exits. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Single entry point (the most public surface of the feature).
- Ordered synchronous steps (max ~5 hops) and branch conditions.
- Async / IO / event side effects.
- Both the success AND error exits.
- Gaps: dead branches, unhandled errors, missing validation.

## Output contract

```markdown
## Subject
<subject + scope, ≤20 words>
## Items
- <path>:<line> — `<name/sig>` — <role ≤10 words>
## Patterns
- <recurring pattern/convention> — e.g. <path>:<line>
## Relations
- <item> → <item/dep> (<path>:<line>)
## Gaps & risks
- <gap / inconsistency / risk> (<path>:<line>)
## Summary
<1 line: state + recommendation>
```

## Rules

- Budget ≤15–20 files opened, report ≤55 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)` on a single line — NEVER omit a section.
- Unknowns → prefix with `?`.
- Never invent. No code blocks quoting source. No narration.
