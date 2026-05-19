---
description: Analyze the project's existing skills, subagents, and hooks to propose what to create or update for a new capability. Use when the user describes a high-level need ("I want to add X", "how should I structure Y", "what's the cleanest way to evolve our setup for Z") or when a feature spans multiple artifact types (skill + agent + hook).
argument-hint: '[capability or feature description]'
---

# Evolve

`evolve` analyzes existing skills/agents/hooks, proposes a coordinated plan, gets approval, then delegates execution to the architects. It never writes artifact files directly.

## Detect intent

Treat `$ARGUMENTS` as the capability description.

- **Empty or ambiguous** → ask one targeted clarifying question with `AskUserQuestion` (what capability, which surface, who triggers it). Do not proceed until the intent is concrete enough to inventory against.
- **Concrete** → move to Phase 1 immediately.

## Phase 1 — Inventory (read-only)

Delegate the inventory to the `explore-codebase` skill so the raw frontmatter dumps stay out of the main thread. Invoke it via the `Skill` tool with a topic targeted at `.claude/`:

```
Skill({ skill: "explore-codebase", args: "inventory all skills under .claude/skills/*/SKILL.md (description, argument-hint, disable-model-invocation, user-invocable, context, agent, flow type), all subagents under .claude/agents/*.md (name, description, tools, model), and hooks + permissions in .claude/settings.json and .claude/settings.local.json" })
```

`explore-codebase` runs in `context: fork` and returns a compact location-anchored report. Use that report as the inventory for Phases 2-3.

Fallback: if `explore-codebase` is unavailable or the `.claude/` directory is tiny (<3 skills, <2 agents, no hooks), run the inline Glob/Read steps in [reference/inventory-checklist.md](./reference/inventory-checklist.md) instead. Do not modify any file during this phase.

## Phase 2 — Classify

Map the user's intent to one or more artifact types using [reference/decision-matrix.md](./reference/decision-matrix.md).

Output is a list of entries:

```
{ artifact-type, action: create | update | reuse, name, why }
```

## Phase 3 — Surface conflicts and overlaps

For each entry, compare against the inventory:

- If an existing artifact covers **≥70%** of the need → prefer `reuse` or `update` over `create`.
- If two existing artifacts together cover the need → propose `reuse` + a small extension to one.
- Call out every overlap explicitly in the plan, even when you still recommend `create`.
- Never duplicate functionality across artifacts.

## Phase 4 — Present the plan

Render a markdown plan matching [examples/evolve-plan-output.md](./examples/evolve-plan-output.md).

Order entries by dependency:

1. Reused assets first (no action needed).
2. Updates next.
3. Creates in dependency order — skill before the agent that wraps it; hook last unless it blocks something else.
4. Restart-required flag.
5. Test plan.

## Phase 5 — Get approval

Use `AskUserQuestion` to confirm or adjust the plan. Never auto-execute. The user can edit any entry before approval.

## Phase 6 — Delegate

Route each approved entry per [reference/delegation-routing.md](./reference/delegation-routing.md):

| Artifact | Executor |
| :-- | :-- |
| Skill (create or update) | `skill-architect` subagent |
| Subagent (create or update) | `agent-architect` subagent |
| Hook (create or update) | `hooks` skill via the Skill tool |

Pass a full spec so the executor never has to ask the user follow-ups. Spawn architects in parallel only when their work is independent.

## Phase 7 — Report

Summarize what was created/updated. Explicitly flag if a restart is needed:

- New top-level skill directory → restart required.
- New subagent file → restart required.
- Hook change in `settings.json` → restart required.
- In-place edits to existing `SKILL.md` files → no restart.

List the test commands the user should run.

## Critical principles

- **Never write artifact files directly** — always delegate to `skill-architect`, `agent-architect`, or the `hooks` skill.
- **Always inventory before proposing** — read what exists; do not guess.
- **Prefer reuse or update over create** when overlap is ≥70%.
- **Order the plan by dependency** so the executor chain runs cleanly.
- **Always get explicit approval** before delegating.

## Reference

- [reference/inventory-checklist.md](./reference/inventory-checklist.md) — Phase 1 step-by-step
- [reference/decision-matrix.md](./reference/decision-matrix.md) — pick artifact type, update vs create, when to reject
- [reference/delegation-routing.md](./reference/delegation-routing.md) — routing table and per-executor spec templates

## Examples

- [examples/evolve-plan-output.md](./examples/evolve-plan-output.md) — sample plan output
