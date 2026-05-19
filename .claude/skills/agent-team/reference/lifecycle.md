# Lifecycle

A team's life: **spawn → steer → shut down → clean up**. The lead drives every stage.

## Spawn prompt anatomy

Teammates don't inherit the lead's conversation history. Everything they need must be in the spawn prompt (CLAUDE.md, MCP servers, and skills load automatically from project/user settings). A complete prompt has:

1. **The task** — concrete deliverable
2. **Team structure** — role + scope per teammate
3. **Names** — explicit so you can reference them later
4. **Model** — if you don't want the default
5. **Plan approval** — if the work is risky/architectural
6. **Synthesis instruction** — how the lead should consolidate findings

Template:
```text
Create an agent team to <task>.
Spawn <N> teammates:
- <name1>: <role + scope>
- <name2>: <role + scope>
- ...
Use <model> for each teammate. [Require plan approval before any changes.]
<Synthesis instruction.>
```

### Naming teammates

Without explicit names the lead picks. Predictable names (`security`, `perf`, `tests`, `frontend`) make later messages clean: "ask `perf` to re-run the benchmark on the new commit".

### Specifying the model

Teammates default to whatever **Default teammate model** is set to in `/config` — not the lead's `/model`. Be explicit in the prompt when it matters:

```text
Use Sonnet for the reviewers and Opus for the architect.
```

### Reusing a subagent definition as a teammate role

Any [subagent](../../subagent/SKILL.md) (project / user / plugin) can be reused as a teammate role:

```text
Spawn a teammate using the security-reviewer agent type to audit src/auth/.
```

The teammate honors the subagent's `tools` allowlist and `model`. The definition body is **appended** to the teammate's system prompt rather than replacing it. Team coordination tools (`SendMessage`, task management) are always available even if `tools` restricts other tools.

> **Not applied when reused as a teammate**: `skills` and `mcpServers` from the subagent's frontmatter. Teammates load these from project/user settings, same as a regular session.

### Plan approval

```text
Spawn an architect teammate to refactor src/auth/.
Require plan approval before any changes.
```

The teammate works in read-only plan mode, sends a plan to the lead, and waits. The lead approves (teammate exits plan mode and implements) or rejects with feedback (teammate revises and resubmits). The lead's approval is autonomous — bias it via the spawn prompt: "only approve plans that include test coverage" or "reject plans that touch the schema".

## Steer

### Talking to a specific teammate

- **In-process**: Shift+Down cycles through teammates; type to message the highlighted one. Enter views the teammate's session; Esc interrupts; Ctrl+T toggles the task list. Shift+Down after the last teammate wraps back to the lead.
- **Split-pane**: click into the teammate's pane to interact directly.

You can also ask the lead to relay: "tell `<name>` to ...".

### Assigning vs self-claiming

- **Lead assigns**: "Give the dependency-audit task to `security`."
- **Self-claim**: an idle teammate picks the next unblocked task. File locking prevents two teammates claiming the same task.

If the lead's task list is too coarse — long tasks, no check-ins — ask it to split the work. Aim for 5–6 tasks per teammate.

### Replacing a teammate

A teammate that's stopped on an error can be redirected ("ignore the network failure and proceed") or replaced by spawning a fresh one with an updated prompt.

## Shut down

Graceful shutdown of one teammate:
```text
Ask the researcher teammate to shut down.
```

The lead sends a shutdown request. The teammate can approve (graceful exit) or reject with an explanation. Shutdown may be slow — teammates finish their current request or tool call first.

## Clean up

When the work is done:
```text
Clean up the team.
```

This removes shared team resources (`~/.claude/teams/{team-name}/`, `~/.claude/tasks/{team-name}/`). Cleanup fails if any teammate is still active — shut down stragglers first.

> **Always run cleanup from the lead.** A teammate's team context may not resolve correctly, which can leave resources in an inconsistent state.

## After cleanup

The lead can create a **new** team — but only one team at a time, and the lead is fixed for each team's lifetime. There's no nested teams, no leadership transfer.
