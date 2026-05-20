# shoto — Claude Code plugin

Meta-tooling for designing, creating, and evolving Claude Code **skills**, **sub-agents**, and **hooks**. Drop it into Claude Code and you get a set of expert skills that know the conventions cold, plus two architect sub-agents that own the actual file-writing.

## Install

Distribution is **private**: the repo is hosted privately on GitHub, so only people with read access can add the marketplace or install the plugin. Claude Code authenticates against the user's local `gh` / GitHub credentials when fetching.

### Via the private marketplace (recommended)

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install shoto@shoto
```

Updates flow through the same channel: when the marketplace refreshes, Claude Code re-fetches via Git. Revoking a user's repo access stops their future updates.

### Local clone (`--plugin-dir`)

```bash
git clone git@github.com:shoto290/shoto.git
claude --plugin-dir ./shoto
```

### Single session (`--plugin-url`)

Works with a GitHub-generated zip URL for the private repo (requires a token with `repo` scope in the URL or via `gh auth`):

```bash
claude --plugin-url https://github.com/shoto290/shoto/archive/refs/heads/main.zip
```

Once loaded, run `/help` to see the skills under the `shoto:` namespace and `/agents` to confirm the sub-agents are registered.

## What's inside

### Skills (`/shoto:<name>`)

| Skill | Purpose |
| :--- | :--- |
| `/shoto:skill` | Create or update a Claude Code skill (`SKILL.md` + supporting files). |
| `/shoto:subagent` | Design or update a sub-agent: frontmatter, tools allowlist, scope, model. |
| `/shoto:hooks` | Build or audit hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, ...). |
| `/shoto:agent-team` | Spawn and orchestrate experimental Claude Code agent teams. |
| `/shoto:explore-codebase` | Run an `Explore` fork that returns a compact, location-anchored map. |
| `/shoto:evolve` | High-level capability planner — inventories existing skills/agents/hooks and proposes coordinated changes. |

### Sub-agents

| Agent | When it fires |
| :--- | :--- |
| `agent-architect` | Auto-delegates whenever the user asks to create, scaffold, or modify a sub-agent. |
| `skill-architect` | Auto-delegates whenever the user asks to create, scaffold, or modify a skill. |

Both architects own the file-writing flow end-to-end (search-by-`name:`, scope selection, frontmatter, validation gate).

## Typical flow

1. Describe the capability you want — `/shoto:evolve add a CI-failure triage workflow`.
2. `evolve` inventories what already exists and proposes a plan touching one or more of skill / sub-agent / hook.
3. After approval, it delegates the actual writes to `skill-architect`, `agent-architect`, and/or the `hooks` skill.
4. Restart Claude Code (or use `/reload-plugins`) to load the new artifacts.

## Layout

```
.claude-plugin/plugin.json        # plugin manifest (name: shoto)
agents/                           # agent-architect, skill-architect
skills/                           # skill, subagent, hooks, agent-team, evolve, explore-codebase
```

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
