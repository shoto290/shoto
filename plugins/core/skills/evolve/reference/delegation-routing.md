# Delegation routing

## Routing table

| Artifact | Executor | Invocation |
| :-- | :-- | :-- |
| Skill (create or update) | `skill-architect` subagent | `Agent({subagent_type: "skill-architect", prompt: "<full spec>"})` |
| Subagent (create or update) | `subagent-architect` subagent | `Agent({subagent_type: "subagent-architect", prompt: "<full spec>"})` |
| Workflow (create or update) | `workflow-architect` subagent | `Agent({subagent_type: "workflow-architect", prompt: "<full spec>"})` |
| Hook (create or update) | `hooks` skill via the Skill tool | `Skill({skill: "hooks", args: "<event-or-pattern>"})` |
| MCP server (recommend or configure) | `mcp` skill via the Skill tool | `Skill({skill: "mcp", args: "<recommend|add|debug> <signal-or-server>"})` |

## Spec template for each executor

### `skill-architect`

Include in the prompt:

- Scope: `project` (`.claude/skills/`), `personal` (`~/.claude/skills/`), or `plugin`.
- Skill name (lowercase, hyphens).
- Type: reference (knowledge) or task (action).
- Description (the trigger sentence Claude will match on).
- `argument-hint` if the skill takes arguments.
- Supporting files needed (`reference/`, `examples/`, `scripts/`, `assets/`, `template.md`).
- Body outline — section list with one-line intent per section.

### `subagent-architect`

Include in the prompt:

- Scope: project (`.claude/agents/`) or personal (`~/.claude/agents/`).
- Agent name (lowercase, hyphens).
- Focused purpose in one sentence.
- Tools allowlist (only what the agent needs).
- Model (`sonnet`, `opus`, etc.).
- System prompt outline — sections and constraints.

### `workflow-architect`

Include in the prompt:

- Scope: `project` (`.claude/workflows/`) or `personal` (`~/.claude/workflows/`).
- Workflow name (kebab-case, `.js`).
- One-sentence purpose (what it orchestrates).
- Orchestration shape: fan-out / pipeline / loop-until-dry / judge-panel, and what fans out vs. verifies vs. synthesizes.
- Per-stage agent prompts and any output `schema`.
- Token-budget posture and whether agents need `isolation: 'worktree'`.

### `hooks`

- Pass the event (or matcher pattern) as `args`.
- Let the `hooks` skill handle the rest of the flow (event selection, command shape, settings file edit).

### `mcp`

- Pass the intent (`recommend` / `add` / `debug`) plus the detected signal or target server as `args`.
- Let the `mcp` skill own scope selection (project / local / user) and secret-via-env handling.
- Never inline secrets.

## Notes

- Pass enough context for the executor to act without asking the user follow-ups.
- Always include **why** the artifact is needed so the executor can craft a good description.
- Spawn architects in parallel only if their work is independent. Chain them sequentially when one depends on the other (e.g., subagent depends on skill output shape).
