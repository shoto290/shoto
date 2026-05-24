---
name: explore
description: Single entry point for codebase exploration. Routes the request internally to the right specialist (architecture patterns, component reuse, control/data flow, code conventions) or falls back to a general map (survey / deep-dive / targeted profiles). Use whenever an agent or user wants to "explore the codebase", "map this feature", "find patterns", "see if a component already exists for X", "check whether Y is reusable", "trace the flow of Z", "understand how this repo handles errors / naming / structure", "audit an area before refactoring", or get a structured location-anchored report on a module. The 4 specialists are internal — never call them directly; always go through this skill.
argument-hint: [profile=architecture|component|flow|convention|general|survey|deep-dive|targeted] <topic>
context: fork
allowed-tools: [Read, Glob, Grep, Bash, Skill]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore

You are the exploration orchestrator. Parse the request, pick the best specialist (or run multiple in parallel for broad questions), or fall back to general mode when the intent is unclear. Return the specialist's report(s) unchanged — never narrate or summarize.

## Arguments
$ARGUMENTS

## Profile parsing

- If `$ARGUMENTS` starts with `profile=<value>`, strip it and use the remainder as the topic.
- Specialist profiles: `architecture`, `component`, `flow`, `convention`.
- General-mode profiles: `general`, `survey`, `deep-dive`, `targeted`.
- If no `profile=` is given, run **intent detection** (see [reference/routing.md](./reference/routing.md)):
  - Map keywords to specialists (e.g. "pattern", "layering", "architecture" → architecture; "reuse", "existing", "duplicate", "déjà" → component; "flow", "trace", "by where", "passe", "appelle" → flow; "convention", "naming", "idiom", "style" → convention).
  - If exactly one specialist matches → dispatch to it.
  - If multiple specialists match → dispatch them in PARALLEL (single tool-use block, multiple Skill calls), then concatenate the reports with a `## <specialty>` header per block.
  - If zero specialists match → fall back to general mode (default `profile=deep-dive`).

## Dispatch rules

- For specialist profiles, call the Skill tool with `skill: explore:explore-<specialty>` and `args: <topic>`. The skill runs in fork with its agent — you get back the report only.
- Multiple specialists in parallel: emit them in a SINGLE tool-use block with multiple Skill calls. Wait for all, then concatenate with `## architecture`, `## component`, etc. headers.
- For general mode, follow the rules in [reference/general-profiles.md](./reference/general-profiles.md). Do NOT dispatch — you handle it inline using `Read`, `Glob`, `Grep`, `Bash`.

## Output contract

- Specialist mode → return the specialist's report verbatim, nothing else.
- Multi-specialist mode → concatenate reports with `## <specialty>` headers in the order the specialists were called. No preamble, no closing.
- General mode → return the canonical report as defined in [reference/general-profiles.md](./reference/general-profiles.md).

## See also

- [reference/routing.md](./reference/routing.md) — keyword → specialist mapping table.
- [reference/general-profiles.md](./reference/general-profiles.md) — the general-mode profiles and canonical report format.
