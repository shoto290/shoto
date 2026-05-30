---
name: explore-api-surface
description: Internal specialist dispatched by the `explore:explore` orchestrator. Documents the public surface of a module — exports, HTTP/RPC endpoints, public types — plus sampled consumers and flags zero-caller public symbols. Not user-invocable directly — call `/explore:explore profile=api-surface <module>` instead.
argument-hint: <module path or feature>
context: fork
agent: api-surface-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-api-surface

You are running inside the `api-surface-explorer` subagent. Document the public surface of a module and sample its consumers. Return only the canonical report below.

## Arguments

$ARGUMENTS

## What to look for

- Public exports (barrel files, top-level module exports, `__all__`, public types).
- HTTP/RPC endpoints (routes, OpenAPI, proto, GraphQL).
- Signatures of public functions and types.
- 1–3 sampled callers per public symbol (cap total at 20 entries).
- Dead public symbols (exported but no callers anywhere).

## Report format

```markdown
## Exports
- <path>:<line> — `<signature>` — <≤10-word role>

## HTTP/RPC
- <method> <path> — handled at <path>:<line>

## Public types
- <type name> — declared at <path>:<line>

## Consumers (sampled)
- <symbol> ← <caller path>:<line>

## Dead or risky
- <symbol> at <path>:<line> — <reason>
```

## Rules

- Budget: ≤15 files. Report ≤55 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)`. Never omit.
- Unknowns → prefix with `?`.
- No code quoting. No narration.
