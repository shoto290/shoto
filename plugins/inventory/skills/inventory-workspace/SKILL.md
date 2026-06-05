---
name: inventory-workspace
description: Inventories repo/workspace structure (monorepo vs single, workspace globs, each package's name/path/role) and returns the contract.
when_to_use: Use for a map of how the repository is laid out before touching it.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-workspace
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-workspace

You are running inside the `inventory-workspace` subagent. Map the repository/workspace structure so a caller can understand the layout before changing it. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- Monorepo vs single package — declared workspace globs: `package.json` `workspaces`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, Cargo workspace, `go.work`.
- Each package/app — name + path + role (≤10 words each).
- Build / entry points and shared config roots (tsconfig, eslint, build configs).
- Gaps: orphan packages (on disk but unregistered), missing workspace registration, duplicate or competing roots.

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
