# Concepts

## What an agent team is

A coordinated group of independent Claude Code sessions. One session is the **lead** — the session that creates the team. The others are **teammates**, each a full Claude Code instance with its own context window. Teammates share a task list and a mailbox.

Unlike [subagents](../../subagent/SKILL.md), teammates:
- Talk to each other directly, not only to the parent
- Self-claim work off a shared list
- Persist independently — you can interact with any teammate without going through the lead

Agent teams are **experimental** (gated by `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) and require Claude Code v2.1.32+.

## Architecture

| Component | Role |
| :-- | :-- |
| **Team lead** | The Claude Code session that creates the team, spawns teammates, coordinates work. Fixed for the team's lifetime. |
| **Teammates** | Separate Claude Code instances; each does assigned work in its own context. |
| **Task list** | Shared work items. Tasks have states (pending / in progress / completed) and may depend on other tasks. File-locked claiming prevents races. |
| **Mailbox** | Direct messaging between any two agents. No broadcast — one message per recipient. |

## How teammates share information

- **Automatic message delivery** — messages arrive at the recipient without polling
- **Idle notifications** — when a teammate finishes and stops, the lead is notified
- **Shared task list** — anyone can see status; anyone can claim available work
- **Spawn prompt** — the only conversation-time context teammates get from the lead. CLAUDE.md, MCP servers, and skills load automatically from project/user settings; the lead's conversation history does NOT carry over

## Storage on disk

- **Team config**: `~/.claude/teams/{team-name}/config.json` — runtime state (session IDs, tmux pane IDs, members array). Regenerated automatically; **do not hand-edit or pre-author**.
- **Task list**: `~/.claude/tasks/{team-name}/`

There is no project-level equivalent. A file like `.claude/teams/teams.json` in the project is not recognised as team config — Claude treats it as an ordinary file. To define reusable teammate roles, use a [subagent definition](../../subagent/SKILL.md) and reference it by name when spawning.

## How Claude starts teams

Two paths, both with user confirmation:

- **User requests** — "create an agent team to ..."
- **Claude proposes** — for a task that benefits from parallel work, Claude may suggest a team. The user confirms before spawning.

The user is always in the loop on team creation.

## Team vs subagent

| | Subagent | Agent team |
| :-- | :-- | :-- |
| **Context** | Own window; result returns to caller | Own window; fully independent session |
| **Communication** | Reports to the main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages everything | Shared task list with self-coordination |
| **Best for** | Focused tasks where only the result matters | Work requiring discussion, debate, collaborative ownership |
| **Token cost** | Lower — results summarised back | Higher — each teammate is a full session |
| **Spawning** | Any session can spawn a subagent | Only the lead can spawn / manage teammates; no nested teams |
| **Resume** | Subagents are spawned fresh per turn | `/resume` and `/rewind` do not restore in-process teammates |

**Decision rule**: do the workers need to talk to each other? If yes → team. If they only need to report back → subagents.

## Permissions

Teammates start with the lead's permission settings. `--dangerously-skip-permissions` on the lead propagates to every teammate. After spawn, you can change individual teammate modes, but not at spawn time.

## Token usage

Each teammate has its own context window — token usage scales with the number of active teammates. For research, review, and parallel feature work, the extra cost is usually worthwhile. For routine tasks, a single session or [subagents](../../subagent/SKILL.md) are cheaper.
