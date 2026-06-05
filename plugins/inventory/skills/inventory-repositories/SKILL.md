---
name: inventory-repositories
description: Inventories the data-access layer (repos/DAOs, ORM vs raw, entity-table mapping, migrations) and returns the anchored contract.
when_to_use: Use to understand persistence and data access before changing queries or schema.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-repositories
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-repositories

You are running inside the `inventory-repositories` subagent. Map the data-access/repository layer — repos, ORM usage, entity mapping, and migrations. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Repositories / DAOs / query modules; ORM vs raw SQL.
- Entity ↔ table mapping; unit-of-work; migration layout.
- Relations: repository → entity/schema and repository → DB client.
- Gaps: N+1 risks, raw SQL outside the layer, entity without a repository.

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
