---
name: inventory-test
description: Inventories test locations, runner, and which modules have tests versus which do not, and returns the unified anchored contract. Use when you need to know test coverage shape and find untested modules before changing code.
when_to_use: Use on `/inventory:inventory-test`, `where are the tests`, `what test runner is used`, `which modules lack tests`, `find untested code`, `inventory test coverage`.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-test
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# inventory-test

You are running inside the `inventory-test` subagent. Map test locations, the runner, and the coverage gap (which modules have tests versus which do not). Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Test file locations + naming: `*.test.ts`, `*_test.go`, `__tests__/`, and similar.
- Runner in use: jest / vitest / pytest / `go test` / other (from config + manifest scripts).
- Which modules HAVE tests vs which DON'T — gap detection is the goal.
- Fixture / mock patterns; unit / integration / e2e split.
- Gaps: untested modules, skipped or flaky tests.

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
