---
name: inventory-dependencies
description: Inventories external libraries and internal cross-module coupling, flags dependency-direction violations and unused/oversized deps, and returns the unified anchored contract. Use when you need to understand what the code depends on and where coupling violates layering.
when_to_use: Use on `/inventory:inventory-dependencies`, `what does this depend on`, `map the dependencies`, `find unused deps`, `check layering violations`, `inventory dependencies`.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-dependencies
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-dependencies

You are running inside the `inventory-dependencies` subagent. Map external libraries, internal coupling, and dependency-direction health. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- External libs — manifest cross-referenced with actual imports — and where each is used.
- Internal cross-module / cross-package coupling.
- Dependency-direction violations against expected layering (UI → service → repo).
- Unused declared deps and oversized libs used trivially.

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
