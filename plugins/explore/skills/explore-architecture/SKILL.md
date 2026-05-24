---
name: explore-architecture
description: Analyze architectural patterns, layering, and structural conventions of a codebase area. Returns a Patterns / Layers / Conventions / Anti-patterns report. Use when an agent or user types `/explore-architecture <area>`, asks about "patterns in this repo", "how is X layered", "what design patterns are used here", or wants a structural overview before refactoring.
argument-hint: <area or feature to analyze>
context: fork
agent: architecture-explorer
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-architecture

You are running inside the `architecture-explorer` subagent. The caller wants a structural map of a codebase area — patterns, layers, conventions, and anti-patterns. Return only the canonical report below; no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Recurring structural patterns (layered, hexagonal, MVC, repository, factory, observer, etc.) — only call something a pattern if >=3 occurrences.
- Layer boundaries (presentation / application / domain / infrastructure or equivalent), with responsibilities in <=10 words each.
- Conventions that hold across the area (e.g. "one aggregate per folder", "controllers thin, services thick").
- Concrete anti-patterns with >=2 occurrences (god object, layer leaks, circular deps).

## Report format

```markdown
## Patterns
- <pattern name> — applied at <path>:<line> — <=10-word rationale>

## Layers
- <layer> — <=10-word responsibility> — entry at <path>:<line>

## Conventions
- <convention> — exemplified at <path>:<line>

## Anti-patterns / smells
- <issue> (<path>:<line>)
```

## Rules

- Budget: <=20 files opened total. Report <=60 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section -> `- (none)` on a single line. Never omit a section.
- Unknowns -> prefix with `?`. Never invent.
- No code blocks quoting source. No narration.
