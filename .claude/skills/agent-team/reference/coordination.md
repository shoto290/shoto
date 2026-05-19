# Coordination

How teammates synchronise: a shared task list and a mailbox, plus optional hook gates.

## Task list

The lead creates tasks; teammates work them. Stored at `~/.claude/tasks/{team-name}/`.

### States

- **pending** — created, not yet claimed
- **in progress** — claimed by a teammate, work underway
- **completed** — work done; if other tasks depend on it, they unblock automatically

### Dependencies

A pending task with unresolved dependencies cannot be claimed. The lead sets dependencies when it creates the task list. When a dependency completes, blocked tasks become claimable without manual intervention.

### Claiming

Two modes:

- **Lead assigns**: the lead picks a teammate for a task — "give task #4 to `perf`"
- **Self-claim**: an idle teammate picks the next unblocked task on its own

Claiming uses **file locking** to prevent races when multiple teammates try to claim the same task. Exactly one wins.

### Task sizing

- **Too small** — coordination overhead exceeds the benefit
- **Too large** — teammates work too long without check-ins; wasted effort risk grows
- **Just right** — self-contained, clear deliverable (a function, a test file, a focused review)

Aim for **5–6 tasks per teammate**. With 15 independent tasks, 3 teammates is a good starting point. If the lead creates too-coarse tasks, ask it to split.

### Task status can lag

Teammates sometimes finish work without marking the task complete, which blocks dependents. If a task looks stuck, check whether the work is actually done and either update the status manually or tell the lead to nudge the teammate.

## Mailbox

Direct messaging between any two agents (lead↔teammate, teammate↔teammate). Delivered automatically — recipients don't poll. Tool: `SendMessage` (available to teammates only when agent teams is enabled).

- **One message, one recipient** — there's no broadcast. To reach every teammate, send N messages.
- **By name** — teammates address each other by the name the lead assigned at spawn. Predictable names matter (see [lifecycle.md](./lifecycle.md#naming-teammates)).
- **Idle notification** — when a teammate finishes and stops, the lead is notified automatically.

To find other team members, a teammate can read `~/.claude/teams/{team-name}/config.json` — the `members` array lists each teammate's name, agent ID, and agent type. Read-only for this purpose; don't write to the file.

## Plan approval round-trip

When a teammate is spawned with plan approval required:

1. Teammate works in read-only plan mode (can read, search, analyse — no edits, no commands)
2. Teammate sends a plan to the lead
3. Lead reviews and decides:
   - **Approve** → teammate exits plan mode and implements
   - **Reject with feedback** → teammate stays in plan mode, revises, resubmits

The lead's decision is autonomous. To shape it, give criteria in the original spawn prompt: "only approve plans with test coverage", "reject any plan that modifies the schema".

## Hooks

Three team-specific lifecycle events. Exit code `2` blocks the action and feeds the message back to the responsible agent. Full hook mechanics live in the [hooks skill](../../hooks/SKILL.md); semantics here:

| Event | When it fires | Exit-2 effect |
| :-- | :-- | :-- |
| `TeammateIdle` | A teammate is about to go idle | Sends feedback back to the teammate and keeps it working |
| `TaskCreated` | A task is being created | Prevents creation; the agent that tried to create it sees the feedback |
| `TaskCompleted` | A task is being marked complete | Prevents the completion; agent sees the feedback |

Use cases:
- `TeammateIdle` to enforce "did you write tests for what you just changed?" before letting a teammate stop
- `TaskCreated` to reject tasks that lack acceptance criteria
- `TaskCompleted` to require a status note before a task closes

### Permissions during teammate work

Teammate permission prompts bubble up to the lead. If the lead is in `default` mode, every prompt is a context switch. Pre-approve common operations in `.claude/settings.json` **before** spawning.

`bypassPermissions` on the lead propagates to every teammate — audit before enabling.
