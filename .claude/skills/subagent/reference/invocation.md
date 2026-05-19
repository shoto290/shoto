# Invocation: how subagents run

## Automatic delegation

Claude decides to delegate based on:
1. The task description in your request
2. The `description` field in subagent configurations
3. Current conversation context

To encourage proactive delegation, include phrases like **"use proactively"** or **"use immediately"** in the `description`. The model uses these as signals.

## Explicit invocation — three patterns

Escalate from one-off suggestion to session-wide default:

### 1. Natural language

Name the subagent in your prompt. Claude typically delegates, but the choice is left to the model.

```
Use the test-runner subagent to fix failing tests
Have the code-reviewer subagent look at my recent changes
```

### 2. @-mention

Guarantees the named subagent runs for this task. Type `@` and pick from the typeahead.

```
@"code-reviewer (agent)" look at the auth changes
```

Your full message still goes to Claude — Claude writes the subagent's task prompt based on what you asked. The `@-mention` only controls **which** subagent is invoked, not what prompt it receives.

**Plugin subagents** appear under scoped names like `my-plugin:code-reviewer` or `my-plugin:review:security`. You can also type the mention manually: `@agent-<name>` or `@agent-<plugin>:<name>`.

**Background subagents** currently running in the session show in the typeahead with their status.

### 3. Whole-session subagent — `--agent`

```bash
claude --agent code-reviewer
```

The main thread itself takes on the subagent's system prompt, tool restrictions, and model. This replaces the default Claude Code system prompt entirely (like `--system-prompt`). `CLAUDE.md` and project memory still load normally. The agent name appears as `@<name>` in the startup header.

For plugin agents, name alone usually works:

```bash
claude --agent security-reviewer
```

If multiple plugins ship the same name, scope it: `claude --agent my-plugin:security-reviewer`. For plugin subfolders: `claude --agent my-plugin:review:security`.

Make it the project default in `.claude/settings.json`:

```json
{
  "agent": "code-reviewer"
}
```

The CLI flag overrides the setting if both are present.

## Foreground vs background

| | Foreground | Background |
| :-- | :-- | :-- |
| Main conversation | Blocked until done | Continues; runs concurrently |
| Permission prompts | Passed through to you | Auto-denied (uses already-granted permissions) |
| Clarifying questions | Surfaced as prompts | The tool call fails, but the subagent continues |

Claude picks foreground vs background based on the task. You can:
- Ask Claude to "run this in the background"
- Press **Ctrl+B** to background a running task
- Set `background: true` in frontmatter to always run a specific agent in background

Disable backgrounding entirely with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.

If a background subagent fails due to missing permissions, restart the same task in the foreground to retry with interactive prompts.

## Fork mode

A **fork** is a subagent that inherits the entire conversation so far instead of starting fresh. Same system prompt, tools, model, and history as the main session — but its tool calls stay out of your conversation, and only the final result returns.

Use a fork when:
- A named subagent would need too much background to be useful
- You want to try several approaches in parallel from the same starting point

**Experimental.** Requires Claude Code v2.1.117+ and `CLAUDE_CODE_FORK_SUBAGENT=1`. Works in interactive, headless (`claude -p`), and SDK modes.

What changes when fork mode is on:
- Claude spawns a **fork** whenever it would have used the `general-purpose` subagent. Named subagents (Explore, custom) still spawn normally.
- Every subagent spawn runs in the **background**, whether fork or named. Override with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.
- `/fork` spawns a fork (instead of being an alias for `/branch`).

Manual fork with a directive:

```
/fork draft unit tests for the parser changes so far
```

Claude Code names the fork from the first words of the directive. The fork appears in a panel below your prompt and its result arrives as a message in your main conversation when finished.

**Panel controls** while forks run:

| Key | Action |
| :-- | :-- |
| `↑` / `↓` | Move between rows |
| `Enter` | Open the fork's transcript, send follow-up messages |
| `x` | Dismiss a finished fork or stop a running one |
| `Esc` | Return focus to the prompt input |

### Fork vs named subagent

|  | Fork | Named subagent |
| :-- | :-- | :-- |
| Context | Full conversation history | Fresh context |
| System prompt + tools | Same as main session | From the agent's file |
| Model | Same as main session | From the agent's `model` field |
| Permissions | Prompts surface in your terminal | Auto-denied (when background) |
| Prompt cache | Shared with main session | Separate cache |

Because a fork's prompt and tools are identical to the parent's, the first request reuses the parent's prompt cache — **cheaper than spawning a fresh subagent** for tasks that need the same context.

When Claude spawns a fork via the Agent tool, it can pass `isolation: "worktree"` so file edits go to a separate git worktree instead of your checkout.

**Forks cannot spawn further forks.**

## Patterns

### Isolate high-volume operations

Anything that dumps lots of output — test runs, doc fetches, log scans — should go to a subagent so only the summary comes back.

```
Use a subagent to run the test suite and report only the failing tests with their error messages
```

### Parallel research

For independent investigations, spawn multiple subagents simultaneously:

```
Research the authentication, database, and API modules in parallel using separate subagents
```

Each works independently; Claude synthesizes findings. Best when paths don't depend on each other.

> Many subagents each returning detailed results can still consume significant context. For sustained parallelism beyond your window, use **agent teams**.

### Chain subagents

For multi-step workflows, ask Claude to use them in sequence:

```
Use the code-reviewer subagent to find performance issues, then use the optimizer subagent to fix them
```

Each completes and returns; Claude passes relevant context to the next.

## Choose: subagent vs main vs `/btw`

**Main conversation** when:
- The task needs frequent back-and-forth
- Multiple phases share heavy context (plan → implement → test)
- It's a quick, targeted change
- Latency matters (subagents start fresh)

**Subagent** when:
- Verbose output you don't want in main context
- Tool/permission lockdown is required
- Self-contained work that can return a summary

**`/btw`** for a quick question about something already in your conversation — sees full context, no tools, answer is discarded rather than added to history.

> **Subagents cannot spawn other subagents.** For nested delegation, use skills or chain subagents from the main conversation.
