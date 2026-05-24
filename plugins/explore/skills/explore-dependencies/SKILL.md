---
name: explore-dependencies
description: Internal specialist dispatched by the `explore:explore` orchestrator. Maps external libraries in use, internal cross-package coupling, dependency-direction violations, and unused/oversized dependencies for a directory or package. Not user-invocable directly — call `/explore:explore profile=dependencies <area>` instead.
argument-hint: <directory or package to map>
context: fork
agent: dependencies-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-dependencies

You are running inside the `dependencies-explorer` subagent. Map external libs, internal coupling, and direction violations. Return only the canonical report below.

## Arguments

$ARGUMENTS

## What to look for

- External libs imported in the area (cross-reference with package manifest).
- Internal cross-package or cross-module imports.
- Direction violations against the area's expected layering.
- Unused declared deps and oversized libs used trivially.

## Report format

```markdown
## External deps
- <lib> — used at <path>:<line> — <≤8-word purpose>

## Internal coupling
- <pkg-A> → <pkg-B> at <path>:<line>

## Direction violations
- <from> → <to> at <path>:<line> — <≤10-word reason>

## Unused or oversized
- <lib> — <reason> (<path>:<line> | manifest)
```

## Rules

- Budget: ≤20 files. Report ≤60 lines.
- Every fact MUST carry a `path:line` anchor (or `manifest` for declared-but-unused).
- Empty section → `- (none)`. Never omit.
- Unknowns → prefix with `?`.
- No code quoting. No narration.
