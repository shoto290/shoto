---
name: inventory-context
description: Broad adaptive lens that inventories any subject when no precise lens fits, including Claude Code artifact roots, and returns the contract.
when_to_use: Use when the subject matches no specific inventory lens or when mapping a plugin/artifact root.
argument-hint: '[target path or scope — optional; defaults to the whole repo]'
context: fork
agent: inventory-context
user-invocable: true
allowed-tools: [Read, Glob, Grep, Bash]
---

# inventory-context

You are running inside the `inventory-context` subagent. This is the broad/adaptive lens: inventory whatever subject is given when no precise lens fits. Return only the canonical contract below — no preamble, no closing.

## Arguments

$ARGUMENTS

## What to look for

- When pointed at a Claude Code artifact root (a plugin dir or repo root), inventory existing artifacts:
  - Skills (`skills/*/SKILL.md`) — capture name / description / argument-hint / user-invocable from frontmatter.
  - Subagents (`agents/*.md`) — name / description / tools / model.
  - Hooks (`settings.json` / `settings.local.json`) — event / matcher / type / command + permissions.
  - Plugin manifests (`.claude-plugin/plugin.json`) and MCP config.
- Otherwise, fall back to a general location-anchored map of whatever subject is given.
- Gaps: stale entries, name/path mismatches, description overlaps that risk auto-trigger conflicts.

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
