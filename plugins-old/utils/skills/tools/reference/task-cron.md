# Tasks, cron, plan, worktree, and platform tools

Covers: `TaskCreate`, `TaskGet`, `TaskList`, `TaskOutput`, `TaskStop`, `TaskUpdate`, `CronCreate`, `CronDelete`, `CronList`, `RemoteTrigger`, `PushNotification`, `TodoWrite`, `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`, `ExitWorktree`, `TeamCreate`, `TeamDelete`, `ToolSearch`, `WaitForMcpServers`, `ListMcpResourcesTool`, `ReadMcpResourceTool`, `LSP`.

## Task lifecycle

A **task** is a named, persistent unit of work. Tasks outlive the current session.

| Tool | Purpose |
| :-- | :-- |
| `TaskCreate` | Define a new task with a name, prompt, and optional schedule. |
| `TaskGet` | Fetch metadata + current status for one task. |
| `TaskList` | List tasks (filter by status, owner). |
| `TaskOutput` | Read the task's most recent output. |
| `TaskStop` | Halt a running task. |
| `TaskUpdate` | Edit the task definition (prompt, schedule, status). |

**Permission rule.** Bare tool name (`TaskCreate`, `TaskStop`, …).

**When to use.** Long-running investigations, batch work that should survive disconnects, recurring jobs paired with a `Cron*` trigger.

**Pitfalls.**

- Treating `TaskCreate` as fire-and-forget without `TaskGet`/`TaskOutput` — outputs accumulate; check on them.
- Updating a task's prompt while it runs — the in-flight execution finishes with the old prompt; the new prompt applies on next trigger.

## Cron lifecycle

| Tool | Purpose |
| :-- | :-- |
| `CronCreate` | Create a recurring schedule that fires a task or prompt. |
| `CronDelete` | Remove a cron schedule. |
| `CronList` | List existing schedules. |

**Permission rule.** Bare tool name.

**Behaviour.**

- Schedules use standard cron syntax.
- Pairs with `TaskCreate` to run a stored prompt on schedule.

**Pitfalls.**

- Wall-clock timezone vs UTC — confirm what the surface uses.
- Forgetting to `CronDelete` orphans — they keep firing.

## RemoteTrigger

**Summary.** Invokes a registered remote runtime (e.g. a CI agent, a remote sandbox).

**Permission rule.** `RemoteTrigger` (bare).

**Behaviour.**

- First-class API for remote execution — preferred over `Bash ssh` / `curl` for managed integrations.
- Often pairs with `PushNotification` so the remote runtime can notify back.

## PushNotification

**Summary.** Sends a push notification to the user (mobile / desktop).

**Permission rule.** `PushNotification` (bare).

**Behaviour.**

- Use for completion of long-running work, escalations, or cross-session signalling alongside `SendMessage`.

## TodoWrite

**Summary.** Writes a structured todo list into the session for cross-turn tracking.

**Permission rule.** `TodoWrite` (bare).

**Behaviour.**

- Each todo has `content`, `activeForm`, and `status` (`pending`, `in_progress`, `completed`).
- Exactly one item should be `in_progress` at a time.
- Use for multi-step user-visible work; skip for trivial single-step tasks.

**Pitfalls.**

- Maintaining stale items — mark `completed` immediately on success.

## Plan mode

| Tool | Purpose |
| :-- | :-- |
| `EnterPlanMode` | Mark the start of a planning segment — no destructive ops allowed. |
| `ExitPlanMode` | Leave plan mode and proceed to execution. |

**Permission rule.** Bare tool names.

**Behaviour.**

- Plan mode is read-only by convention. The harness may enforce extra restrictions.

## Worktree

| Tool | Purpose |
| :-- | :-- |
| `EnterWorktree` | Enter (or create) a managed git worktree for isolated work. |
| `ExitWorktree` | Leave the worktree; can clean up. |

**Permission rule.** Bare tool names.

**Behaviour.**

- Preferred over `Bash git worktree …` because the lifecycle is managed and the harness tracks state.

## Teams

| Tool | Purpose |
| :-- | :-- |
| `TeamCreate` | Create a Claude Code team. |
| `TeamDelete` | Delete a team. |

**Permission rule.** Bare tool names. Admin-only in most deployments.

## Platform helpers

| Tool | Purpose |
| :-- | :-- |
| `ToolSearch` | Search the available tool surface — useful when you don't know if a tool exists. |
| `WaitForMcpServers` | Block until MCP servers finish initialising. |
| `ListMcpResourcesTool` | List resources exposed by connected MCP servers. |
| `ReadMcpResourceTool` | Read a specific MCP resource. |
| `LSP` | Language Server Protocol queries (definitions, references, diagnostics) when an LSP server is attached. |

**Permission rule.** Bare tool names.

**Pitfalls.**

- Calling MCP tools before servers are ready — use `WaitForMcpServers` if you've just configured them.
- Using `LSP` without an attached LSP server — calls return empty.
