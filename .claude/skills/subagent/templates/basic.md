# Template: basic

Minimum-viable subagent. Copy into `.claude/agents/<name>.md` (project) or `~/.claude/agents/<name>.md` (user) and customize.

```markdown
---
name: my-agent
description: <what this agent does + when Claude should delegate to it>
---

You are a <role>. When invoked:

1. <step 1>
2. <step 2>
3. <step 3>

<output format expectations>
```

Use when:
- The agent needs a simple, focused job
- No tool restrictions required (inherits everything)
- No memory, hooks, or MCP scoping

For more capable patterns:
- Read-only review → [code-reviewer.md](./code-reviewer.md)
- Edit allowed (debug & fix) → [debugger.md](./debugger.md)
- Domain specialist → [data-scientist.md](./data-scientist.md)
- Hook-validated tool use → [db-reader-hooks.md](./db-reader-hooks.md)
- Coordinator that spawns specific subagents → [coordinator.md](./coordinator.md)
