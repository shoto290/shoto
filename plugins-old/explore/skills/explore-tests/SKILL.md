---
name: explore-tests
description: Internal specialist dispatched by the `explore:explore` orchestrator. Maps what is covered by tests, what is likely uncovered, the test patterns in use (unit/integration/e2e split, mocks, fixtures), and notable gaps for a codebase area. Not user-invocable directly — call `/explore:explore profile=tests <area>` instead.
argument-hint: [area=<path>] <module or feature to inspect>
context: fork
agent: tests-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-tests

You are running inside the `tests-explorer` subagent. Map what is and isn't tested in a codebase area, the patterns in use, and notable gaps. Return only the canonical report below.

## Arguments

$ARGUMENTS

## What to look for

- Test files colocated or under `tests/` / `__tests__/`.
- Mapping source ↔ test by filename pair or import.
- Public exports without any matching test (likely uncovered).
- Test framework + unit/integration/e2e split + mock strategy.
- Notable gaps (error paths, public APIs without smoke tests).

## Report format

```markdown
## Covered
- <symbol> at <path>:<line> ← tested at <test path>:<line>

## Uncovered (likely)
- <symbol> at <path>:<line> — <why>

## Test patterns
- <pattern> — sample at <test path>:<line>

## Notable gaps
- <gap> (<path>:<line>)
```

## Rules

- Budget: ≤18 files. Report ≤55 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)`. Never omit.
- Unknowns → prefix with `?`.
- No code blocks quoting source. No narration.
