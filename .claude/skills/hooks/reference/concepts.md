# Hooks — concepts

## What a hook is

A hook is a user-defined action that fires at a specific point in Claude Code's lifecycle. Unlike instructions in `CLAUDE.md` or a system prompt, a hook is **deterministic**: it runs whether or not Claude chooses to follow guidance. Five action types are available:

| `type` | What runs | When to pick it |
| :-- | :-- | :-- |
| `command` | A shell command (default) | Anything that fits a script: format, lint, log, validate, transform |
| `prompt` | A single-turn LLM call (Haiku by default) | The decision needs judgment but doesn't need to read the codebase |
| `agent` | A subagent with tool access (up to 50 turns, experimental) | The decision needs to verify something against actual files / commands |
| `http` | POST to an HTTP endpoint | A central service (audit, policy server) handles the decision |
| `mcp_tool` | Call a tool on an already-connected MCP server | Reuse logic exposed via MCP |

All five exchange JSON: command/HTTP via stdin/stdout/exit code (or response body), prompt/agent via a yes/no response object, mcp_tool via the MCP tool call result.

## Why use a hook vs alternatives

| Need | Better tool |
| :-- | :-- |
| "Claude should usually do X" | `CLAUDE.md` instruction |
| "Claude must always do X before tool Y" | `PreToolUse` hook |
| "Don't even prompt me to approve tool Y when arg Z matches" | `PermissionRequest` hook with `decision.behavior: "allow"` |
| "Block tool Y absolutely, even in bypass mode" | `PreToolUse` hook with `permissionDecision: "deny"` |
| "Run X every time a session starts" | `SessionStart` hook (or for context only: `CLAUDE.md`) |
| "Run X after every file edit" | `PostToolUse` hook with `Edit&#124;Write` matcher |
| "Block Bash commands matching a pattern" | `PreToolUse` hook on `Bash` with `if: "Bash(<pattern>)"` |
| "Block specific filenames from being written" | Permission `deny` rule (preferred) **or** `PreToolUse` hook |
| "Hand off the whole task to a different model" | Subagent, not a hook |

Hooks complement permissions, skills, and subagents:

- **Permissions** decide whether a tool call needs an approval prompt. Hooks can run *before* permissions to override the answer.
- **Skills** give Claude knowledge or workflows it pulls in when relevant. Hooks fire whether Claude wants them to or not.
- **Subagents** isolate work in a separate context. Hooks observe or guard lifecycle events of the main session and subagents.

## Lifecycle overview

A typical session triggers events in roughly this order:

```
SessionStart → InstructionsLoaded → UserPromptSubmit
              ↓
              [model turn]
              ↓
PreToolUse → PermissionRequest → tool runs → PostToolUse (or PostToolUseFailure)
              ↓
              [more tool calls, possibly batched → PostToolBatch]
              ↓
              [PreCompact → PostCompact if compaction fires]
              ↓
Stop (or StopFailure on API error)
              ↓
SessionEnd
```

`ConfigChange`, `FileChanged`, `CwdChanged`, `Notification`, `SubagentStart`/`Stop`, `TaskCreated`/`Completed`, `WorktreeCreate`/`Remove`, and `Elicitation*` fire whenever their underlying event occurs.

See [events.md](./events.md) for the full catalog with firing conditions, matchers, and blocking behavior.

## Parallel execution and merge

When several hooks match the same event, they all run in parallel to completion. Their outputs are then merged:

- `PreToolUse` permission decisions: most restrictive wins (`deny` > `ask` > `allow`).
- `additionalContext` strings: concatenated and passed to Claude.
- `updatedInput` for tool args: last finisher wins — non-deterministic. Avoid more than one hook mutating the same call's input.
- Identical hook commands are auto-deduplicated.

Critically: **one hook's `deny` does not stop another hook from running.** Don't rely on a guard hook to suppress a logging hook's side effects.
