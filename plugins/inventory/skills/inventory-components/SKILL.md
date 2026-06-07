---
name: inventory-components
description: Inventories existing components/utilities for a desired capability and returns the anchored contract with a REUSE / EXTEND / NEW verdict.
when_to_use: Use before adding a component to decide whether to reuse, extend, or build new. Not for the reuse-vs-build decision discipline itself — use engineering:reuse-first.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-components
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-components

You are running inside the `inventory-components` subagent. Find existing components/utilities matching a desired capability and judge reuse versus build-new. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Existing components/utilities matching the desired capability described in the arguments.
- Fit score per candidate: high (≥80% covered) / medium (40–79%) / low (<40%).
- Recurring component shape: factory / hook / HOC / other.
- The verdict — REUSE / EXTEND `<component>` (add `<gap>`) / NEW (no good match) — goes in `## Summary`.

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
