# Template: advanced

Combines dynamic context injection, positional arguments, subagent execution, and pre-approved tools — strip what you don't need.

````yaml
---
name: <override-directory-name-if-needed>
description: <what + when, with trigger phrases>
when_to_use: |
  - <additional context for auto-invocation>
  - <example trigger phrases>
argument-hint: '[arg1] [arg2]'
arguments: [arg1, arg2]
allowed-tools:
  - Bash(gh *)
  - Read
  - Grep
context: fork
agent: Explore
model: inherit
effort: medium
---

## Context
- Current branch: !`git rev-parse --abbrev-ref HEAD`
- Recent commits:
```!
git log --oneline -5
```

## Task

<Use $arg1 and $arg2 (named arguments) — or $0 and $1, or $ARGUMENTS for raw input>

1. <Step using injected context>
2. <Step with file references>
3. <Final action or output>
````

Use when:
- The skill needs live shell output, args, isolated execution, AND tool pre-approval
- You want the cleanest single-file demonstration of "everything"

Every field is optional — see [reference/frontmatter.md](../reference/frontmatter.md) for each field's semantics.
