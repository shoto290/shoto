---
name: agent-team
description: Understand and orchestrate a Claude Code agent team — multiple Claude Code instances coordinated by a lead, sharing a task list and messaging each other directly. Use when the user wants to enable agent teams, spawn or steer a team, draft a spawn prompt, talk to a specific teammate, assign or claim tasks, require plan approval, shut down or clean up the team, wire a teammate hook, or decide between a team and subagents. Triggers on, agent team, agent teams, team lead, teammate, spawn a team, spawn teammates, teammateMode, CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS, SendMessage, mailbox, shared task list, TeammateIdle, TaskCreated, TaskCompleted, plan approval, parallel review, competing hypotheses, scientific debate, cross-layer feature, split panes, in-process, tmux teammates, clean up team, shutdown teammate.
argument-hint: '[task]'
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Agent teams

An **agent team** is a group of independent Claude Code sessions that coordinate through a shared task list and a mailbox. One session is the **lead** (the current one — the session that creates the team). The others are **teammates**: each is a full Claude Code instance with its own context window. Teammates can message each other directly and claim work off the shared task list. This is distinct from [subagents](../subagent/SKILL.md), which only report back to the parent.

Agent teams are **experimental** and require Claude Code v2.1.32+ with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set. See [reference/enable.md](./reference/enable.md).

## Detect intent

If invoked as `/agent-team <task>`, treat `$ARGUMENTS` as the task to seed the spawn prompt with.

1. **Not enabled yet** (env var missing, version < v2.1.32) → route to **enable flow**
2. **No team running, user wants to start one** → **start flow** — draft a spawn prompt the user sends to the lead (this current session)
3. **Team already running, user wants to steer it** → **manage flow**
4. **Conceptual question** ("what is a team?", "team vs subagent?") → **explain flow** → route to [reference/](./reference/)
5. **Empty / ambiguous** → ask the user

## When to suggest each flow

**Enable** when:
- `claude --version` < `2.1.32`, or
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is unset/`0`, or
- The user wants to change `teammateMode` (`auto` / `tmux` / `in-process`) or the default teammate model

**Start** when the user wants to:
- Review a PR from multiple lenses (security, perf, tests) in parallel
- Investigate a bug with competing hypotheses
- Build a feature that spans frontend, backend, and tests (each owned by a teammate)
- Research a problem from multiple angles
- Spawn N parallel workers that need to talk to each other (not just report back)

**Manage** when the user wants to:
- Send a message to a specific teammate by name
- Assign a task to a teammate, or have a teammate claim work
- Require plan approval before a teammate implements
- Shut down one teammate, or clean up the whole team
- Wire a `TeammateIdle` / `TaskCreated` / `TaskCompleted` hook
- Diagnose teammates not appearing, perm-prompt floods, orphaned tmux sessions, or a lead that quits early

**Explain** — point at [reference/](./reference/); don't draft a spawn prompt or change config.

## Team vs subagent — pick the right tool first

| | Subagent | Agent team |
| :-- | :-- | :-- |
| **Communication** | Reports back to parent only | Teammates message each other directly |
| **Coordination** | Parent manages everything | Shared task list, self-claiming |
| **Context** | Own window; result returns | Own window; fully independent session |
| **Cost** | Lower (results summarised) | Higher (each teammate is a full session) |
| **Best for** | Focused tasks where only the result matters | Work needing discussion, debate, or collaborative ownership |

If the workers only need to report back, suggest [subagents](../subagent/SKILL.md) instead — cheaper and simpler. Full decision matrix in [reference/concepts.md](./reference/concepts.md).

---

## Enable flow

1. **Check version**: `claude --version` must report `2.1.32` or later. If older, ask the user to upgrade before continuing.
2. **Set the env var**. Either in shell env, or in `~/.claude/settings.json`:
   ```json
   { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
   ```
3. **Choose `teammateMode`** (default `auto`):
   - `in-process` — all teammates inside this terminal; Shift+Down to cycle. Works anywhere.
   - `tmux` — split panes, one per teammate. Requires tmux or iTerm2 + `it2` CLI.
   - `auto` — tmux if already in a tmux session, else in-process.
4. **Restart** the Claude Code session so the env var takes effect.

Full options (default teammate model, `--teammate-mode` flag, tmux/iTerm2 install) → [reference/enable.md](./reference/enable.md).

> Editing `~/.claude/settings.json` mutates the user's global config — confirm with them before writing.

---

## Start flow

The current session **is** the lead. This skill drafts the spawn prompt; the user sends it to the lead (you).

### 1. Clarify the team

Propose defaults from the user's request; confirm before drafting:

| Decision | Options |
| :-- | :-- |
| **Number of teammates** | 3–5 for most workflows (doc's sweet spot). 1–2 = subagent territory. 6+ = diminishing returns. |
| **Teammate names** | Give explicit names you can reference later (`security`, `perf`, `tests`). Without names, the lead picks. |
| **Model per teammate** | `inherit` (lead's), `sonnet` (balanced), `opus` (hard reasoning), `haiku` (cheap). Teammates don't inherit the lead's `/model` by default — be explicit. |
| **Plan approval** | Require teammates to plan first for risky/architectural work. Lead reviews and approves/rejects. |
| **Reuse a subagent definition** | A teammate can be spawned from any `subagent` definition (project / user / plugin). Honors its `tools` + `model`. `skills` and `mcpServers` from the definition are NOT applied — teammates use project/user settings. |
| **File ownership** | Each teammate owns a disjoint set of files. Two teammates editing the same file = overwrites. |

### 2. Pick a prompt pattern

- [reference/parallel-review.md](./reference/parallel-review.md) — 3 reviewers (security / perf / tests) on a PR
- [reference/competing-hypotheses.md](./reference/competing-hypotheses.md) — 5 adversarial debuggers in a scientific-debate pattern
- [reference/cross-layer-feature.md](./reference/cross-layer-feature.md) — frontend / backend / tests teammates with disjoint file ownership
- [reference/research-exploration.md](./reference/research-exploration.md) — multi-angle research (UX / architecture / devil's advocate)

### 3. Draft the spawn prompt

A good prompt has: **the task**, **the team structure** (roles + count), **names** for each teammate, **model** if not default, **plan-approval rule** if needed, and **task-specific context** (CLAUDE.md and project context load automatically, but conversation history does NOT).

```text
Create an agent team to <task>. Spawn <N> teammates:
- <name1>: <focused role + scope>
- <name2>: <focused role + scope>
- <name3>: <focused role + scope>
Use <model> for each teammate. <Plan approval clause if needed.>
<Synthesis instruction: "Have them report findings", "Update findings.md with consensus", etc.>
```

Give the drafted prompt to the user verbatim. The lead spawns the team when the user sends it.

### 4. Steer

Once spawned, point the user at the **manage flow** below for messaging, task assignment, and shutdown.

---

## Manage flow

### Talk to a teammate

- **In-process mode**: Shift+Down cycles through teammates; type to message the highlighted one. Enter views their session; Esc interrupts. Ctrl+T toggles the task list.
- **Split-pane mode**: click into the teammate's pane.

To message a specific teammate, tell the lead: "Ask `<name>` to ...". The lead routes via the mailbox.

### Tasks

- **Lead assigns**: "Give the dependency-audit task to `security`."
- **Self-claim**: an idle teammate picks the next unblocked task on its own. File locking prevents double-claims.
- **Dependencies**: a pending task with unresolved deps cannot be claimed. The lead manages this automatically.

Mailbox = one teammate to one teammate. No broadcast — send N messages for N recipients. Details in [reference/coordination.md](./reference/coordination.md).

### Plan approval

If a teammate was spawned with plan-approval required, it works in read-only plan mode until the lead approves. Approval is autonomous — to bias the lead, give criteria up front ("only approve plans with test coverage").

### Shut down + clean up

- **Shut down one teammate**: "Ask `<name>` to shut down." The teammate can approve (graceful exit) or reject with a reason.
- **Clean up the team**: "Clean up the team." Must run from the lead — teammates' team context may not resolve correctly. Fails if any teammate is still active, so shut down stragglers first.

### Hooks

Quality gates: `TeammateIdle`, `TaskCreated`, `TaskCompleted`. Exit code `2` blocks the action and sends feedback. Semantics in [reference/coordination.md](./reference/coordination.md#hooks); file mechanics in the [hooks skill](../hooks/SKILL.md).

---

## Explain flow

| Question | Where |
| :-- | :-- |
| What is an agent team? Architecture? Storage on disk? | [reference/concepts.md](./reference/concepts.md) |
| Team vs subagent — full breakdown | [reference/concepts.md](./reference/concepts.md#team-vs-subagent) |
| How do I turn it on? `teammateMode`? tmux setup? | [reference/enable.md](./reference/enable.md) |
| Spawn prompt anatomy, talking to teammates, shutdown, cleanup | [reference/lifecycle.md](./reference/lifecycle.md) |
| Task list, mailbox, plan approval, hooks | [reference/coordination.md](./reference/coordination.md) |
| Teammates not appearing, perm floods, orphaned tmux, lead quits early | [reference/troubleshooting.md](./reference/troubleshooting.md) |

---

## Critical principles

- **One team per lead, for its lifetime.** No nested teams, no leadership transfer. Clean up before creating a new one.
- **The session that creates the team is the lead.** You can't promote a teammate to lead.
- **Teammates don't inherit conversation history.** They get CLAUDE.md, MCP servers, skills, and the spawn prompt. Anything else must be in the prompt.
- **File conflicts overwrite.** Partition files across teammates; never have two own the same file.
- **3–5 teammates is the sweet spot.** Three focused teammates beat five scattered ones. 5–6 tasks per teammate keeps everyone busy without thrashing.
- **Permissions are set at spawn.** All teammates inherit the lead's mode. `--dangerously-skip-permissions` on the lead propagates to every teammate.
- **Always clean up from the lead.** Never have a teammate run cleanup — team context may not resolve correctly.

## Common gotchas

- `/resume` and `/rewind` do **not** restore in-process teammates. After resuming, the lead may try to message ghosts — spawn fresh teammates.
- Task status can lag — a teammate may finish work without marking the task complete, blocking dependents. Check and nudge.
- Teammates ignore `skills:` and `mcpServers:` from a reused subagent definition. They load these from project/user settings instead.
- A file like `.claude/teams/teams.json` in the project is **not** recognised — agent teams have no project-level config. Don't pre-author the team config at `~/.claude/teams/{team-name}/config.json` either; it's regenerated.
- Split-pane mode is unsupported in VS Code's integrated terminal, Windows Terminal, and Ghostty. Use in-process mode there.
- The lead sometimes starts doing work instead of delegating, or shuts the team down early. Tell it to "wait for teammates to finish" or "keep going".
- `bypassPermissions` on the lead means every teammate runs without prompts. Audit before enabling.

## Reference

- [reference/concepts.md](./reference/concepts.md) — architecture, components, storage, team-vs-subagent decision matrix
- [reference/enable.md](./reference/enable.md) — env var, version check, `teammateMode`, tmux/iTerm2 install, default teammate model
- [reference/lifecycle.md](./reference/lifecycle.md) — spawn prompt anatomy, talking to teammates, shutdown, cleanup
- [reference/coordination.md](./reference/coordination.md) — task list, mailbox, plan approval, hooks
- [reference/troubleshooting.md](./reference/troubleshooting.md) — not appearing, perm prompts, orphaned tmux, lead quits early, limitations

## Prompt Patterns

- [reference/parallel-review.md](./reference/parallel-review.md) — multi-lens PR review
- [reference/competing-hypotheses.md](./reference/competing-hypotheses.md) — adversarial debugging
- [reference/cross-layer-feature.md](./reference/cross-layer-feature.md) — frontend / backend / tests
- [reference/research-exploration.md](./reference/research-exploration.md) — multi-angle research
