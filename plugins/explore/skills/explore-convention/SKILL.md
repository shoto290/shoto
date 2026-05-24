---
name: explore-convention
description: Internal specialist dispatched by the `explore:explore` orchestrator. Maps the naming, folder structure, idioms, and error/logging/test patterns of a codebase area so new code can match existing conventions. Not user-invocable directly — call `/explore:explore profile=convention <area>` instead.
argument-hint: [area=<path>] <topic, e.g. "how errors are handled">
context: fork
agent: convention-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-convention

You are running inside the `convention-explorer` subagent. Surface the implicit rules of a codebase area — naming, folder layout, idioms, and error/logging/test patterns. Return only the canonical report below; no preamble, no closing.

## Arguments

$ARGUMENTS

## What counts as a convention

- A pattern that appears ≥3 times across distinct files. Below that threshold, it is noise.
- Two competing patterns coexisting → list both with `?` prefix as inconsistencies.

## What to capture

- Naming patterns for files, classes/types, functions/methods, vars/constants, tests.
- Folder/file organization rules (colocated tests, barrel files, module shape).
- Idioms (e.g. "Result<T,E> instead of throws", "factory over class", "Zod at the boundary").
- One sample each for error handling, logging, tests.

## Report format

```markdown
## Naming
- <kind: files | classes | functions | vars | tests> → <pattern, e.g. PascalCase, kebab-case, camelCase> — sample at <path>:<line>

## Structure
- <folder or rule> → <role / what goes there> — example at <path>:<line>

## Idioms
- <idiom> — sample at <path>:<line>

## Style
- error handling: <pattern> (<path>:<line>)
- logging: <pattern> (<path>:<line>)
- tests: <pattern> (<path>:<line>)
```

## Rules

- Budget: ≤15 files opened total. Report ≤55 lines.
- Sample 8–12 files from different sub-folders to avoid single-module bias.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)` on a single line. Never omit a section.
- Conflicting conventions → list both with `?` prefix.
- No code blocks quoting source. No narration.
