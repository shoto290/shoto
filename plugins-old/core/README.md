# core

A Claude Code plugin for **building Claude Code itself** — skills, sub-agents, and hooks. Install it once and you get expert skills that know the conventions cold, plus two architect sub-agents that own the file-writing.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install core@shoto
```

The repo is private — Claude Code uses your local `gh` / GitHub credentials. Updates flow through the same channel when the marketplace refreshes.

After install, run `/help` to see the `core:` skills and `/agents` to confirm the sub-agents are registered.

## Depends on

- [`explore`](../explore) — provides `explore:explore`, used by `core:evolve` for read-only codebase inventory.

## What's inside

### Skills (`/core:<name>`)

| Skill | Purpose |
| :--- | :--- |
| `/core:skill` | Create or update a skill (`SKILL.md` + supporting files). |
| `/core:subagent` | Design or update a sub-agent (frontmatter, tools, scope, model). |
| `/core:hooks` | Build or audit hooks (`PreToolUse`, `PostToolUse`, …). |
| `/core:plugin` | Scaffold, validate, migrate, and ship a Claude Code plugin as a whole. |
| `/core:agent-team` | Spawn and orchestrate experimental agent teams. |
| `/core:evolve` | Plan coordinated changes across skills / sub-agents / hooks. |

### Sub-agents

| Agent | When it fires |
| :--- | :--- |
| `skill-architect` | Auto-delegates when the user asks to create or modify a skill. |
| `subagent-architect` | Auto-delegates when the user asks to create or modify a sub-agent. |

Both own the writing flow end-to-end: search-by-`name:`, scope selection, frontmatter, validation gate.

## Typical flow

1. Describe the capability — e.g. `/core:evolve add a CI-failure triage workflow`.
2. `evolve` inventories what already exists (via `explore:explore`) and proposes a plan touching skill / sub-agent / hook.
3. After approval, it delegates the writes to `skill-architect`, `subagent-architect`, and/or the `hooks` skill. Restart Claude Code to load the new artifacts.

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
