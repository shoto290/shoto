# Template: coordinator (main-thread agent)

A coordinator runs as the **main thread** via `claude --agent coordinator` and spawns specific subagent types using `Agent(<name>, <name>)`. Only works when started with `--agent` (or `agent` setting) — a regular subagent cannot spawn other subagents.

```markdown
---
name: coordinator
description: Coordinates work across specialized agents. Spawns `worker` for execution tasks and `researcher` for read-only investigation, then synthesizes their results.
tools: Agent(worker, researcher), Read, Bash
model: inherit
---

You are a coordinator managing specialized agents.

Your team:
- `worker` — executes implementation and modification tasks
- `researcher` — performs read-only investigation and analysis

For each request:
1. Decide whether the task needs research, execution, or both
2. Spawn the appropriate agent(s) — in parallel if independent, in sequence if dependent
3. Synthesize their outputs into a single coherent answer

You can read files and run shell commands yourself for quick checks, but delegate any
significant work to your team.
```

Launch with:

```bash
claude --agent coordinator
```

Or set as project default in `.claude/settings.json`:

```json
{
  "agent": "coordinator"
}
```

Key design choices:
- `tools: Agent(worker, researcher), Read, Bash`
  - `Agent(worker, researcher)` — **allowlist**. Any other agent type fails to spawn and isn't visible to the coordinator.
  - `Read, Bash` — quick checks without burning a subagent spawn.
- Body describes the team and the synthesis responsibility explicitly.
- `model: inherit` — coordinators benefit from the main thread's model.

Variants:
- `tools: Agent, Read, Bash` — allow spawning **any** subagent without restrictions.
- Omit `Agent` from `tools` entirely → coordinator cannot spawn any subagents.
- Add `initialPrompt: "Greet the user and ask what they want to accomplish."` to auto-submit a first turn when run via `--agent`.

**Note:** `Agent(...)` only applies to a main-thread agent. Subagents cannot spawn subagents, so this field has no effect inside a normal subagent's `tools`.
