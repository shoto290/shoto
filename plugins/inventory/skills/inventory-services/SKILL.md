---
name: inventory-services
description: Inventories the service layer (classes, public operations, wiring, relations to repos and clients) and returns the anchored contract.
when_to_use: Use to understand business-logic services before extending them.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-services
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-services

You are running inside the `inventory-services` subagent. Map the service layer — service modules, their public operations, and how they wire to data and external systems. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Service classes/modules and their public operations.
- Wiring style: DI / singleton / service-locator; transaction boundaries.
- Relations: service → repository and service → external client.
- Gaps: god-services, business logic leaking into controllers/handlers.

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
