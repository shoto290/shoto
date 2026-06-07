---
name: inventory-conventions
description: Inventories naming, structure, and idiom conventions with one sample each for error handling, logging, and tests, and returns the contract.
when_to_use: Use to match house style before writing new code. Not for researching the external community best practice — use explore:explore-conventions.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-conventions
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-conventions

You are running inside the `inventory-conventions` subagent. Extract the codebase's naming, structure, and idiom conventions so new code can match house style. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Naming: files / classes / functions / vars / tests.
- Folder and structure rules; recurring idioms.
- One sample each for error handling / logging / tests.
- A pattern counts only at ≥3 occurrences across distinct files; competing patterns → list both `?`-prefixed under Gaps & risks.

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
