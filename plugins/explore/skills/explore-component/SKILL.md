---
name: explore-component
description: Find existing components, utilities, or services that match a desired capability; evaluate reusability and recommend REUSE / EXTEND / NEW. Use when an agent or user types `/explore-component <need>`, asks "does X already exist", "is there a component I can reuse", "can I extend Y instead of building Z", or needs to avoid duplicating logic.
argument-hint: <need or capability you want to add>
context: fork
agent: component-explorer
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-component

You are running inside the `component-explorer` subagent. The caller wants to know whether a capability they intend to build already exists somewhere in the codebase. Score candidates by fit, list gaps, and end with one recommendation. Return only the canonical report below.

## Arguments

$ARGUMENTS

## How to score fit

- **high**: ≥80% of the requested sub-capabilities are already covered.
- **medium**: 40–79% covered.
- **low**: <40% covered.

## Recommendation rules

- `REUSE <component>` when at least one high-fit candidate exists with no missing sub-capabilities.
- `EXTEND <component> (add <gap>)` when the best candidate is high or medium fit and the 1–2 missing pieces fit its surface.
- `NEW (no good match)` when no candidate is above low fit, or the best candidate's surface is wrong for the missing pieces.

## Report format

```markdown
## Matches
- <path>:<line> — `<signature>` — <≤10-word role> — fit: high|medium|low

## Reuse fit
- <component> covers: <comma-separated capabilities>
- <component> missing for this need: <comma-separated gaps>

## Gaps
- <capability> — closest workaround at <path>:<line>

## Recommendation
<exactly one of: REUSE <component> | EXTEND <component> (add <gap>) | NEW (no good match)>
```

## Rules

- Budget: ≤15 files opened total. Report ≤50 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)` on a single line. Never omit a section.
- Unknowns → prefix with `?`. Never invent.
- No code blocks quoting source. No narration.
