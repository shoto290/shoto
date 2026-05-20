# Tools & permissions

## Default: inherit everything

Without `tools` or `disallowedTools`, a subagent inherits **all** tools from the main conversation — including MCP tools. This is permissive. Tighten it.

## Allowlist with `tools`

```yaml
---
name: safe-researcher
description: Research agent with restricted capabilities
tools: Read, Grep, Glob, Bash
---
```

This subagent can read, search, and run shell commands. It cannot edit, write, fetch the web, or use any MCP tool.

## Denylist with `disallowedTools`

```yaml
---
name: no-writes
description: Inherits every tool except file writes
disallowedTools: Write, Edit
---
```

Keeps everything from the parent except `Write` and `Edit`. Use when you want to inherit MCP tools but block specific actions.

If both are set, `disallowedTools` is applied first, then `tools` resolves against the remaining pool. Tools in both lists are removed.

## Restricting which subagents a coordinator can spawn

When an agent runs as the **main thread** (`claude --agent coordinator`), it can spawn subagents via the Agent tool. Restrict which ones with `Agent(<name>, <name>)` in the `tools` field:

> The Agent tool was renamed from `Task` in Claude Code 2.1.63. Existing `Task(<name>, <name>)` references in settings and agent definitions still work as aliases.

```yaml
---
name: coordinator
description: Coordinates work across specialized agents
tools: Agent(worker, researcher), Read, Bash
---
```

This is an **allowlist**: only `worker` and `researcher` can be spawned. Attempting any other type fails, and the coordinator only sees the allowed types in its prompt.

- `Agent` (no parens) → any subagent type can be spawned.
- `Agent` omitted entirely → coordinator cannot spawn any subagents.
- To deny specific agents while allowing all others, use `permissions.deny` in settings (see [scopes.md](./scopes.md) and the deny example below).

**Important:** `Agent(...)` only applies when the agent runs as the main thread. Inside a normal subagent it has no effect — subagents cannot spawn subagents at all.

Disable specific subagents globally via `settings.json`:

```json
{
  "permissions": {
    "deny": ["Agent(Explore)", "Agent(my-custom-agent)"]
  }
}
```

Or per session: `claude --disallowedTools "Agent(Explore)"`.

## Permission modes

| Mode | Behavior |
| :-- | :-- |
| `default` | Standard permission prompts |
| `acceptEdits` | Auto-accept file edits + common filesystem commands in CWD / `additionalDirectories` |
| `auto` | Background classifier reviews commands and protected-directory writes |
| `dontAsk` | Auto-deny prompts (explicitly allowed tools still work) |
| `bypassPermissions` | Skip all prompts. **Dangerous** — writes to `.git`, `.claude`, `.vscode`, `.idea`, `.husky` go through without approval. `rm -rf /` and home-directory removals still prompt as a circuit breaker. |
| `plan` | Plan mode (read-only exploration) |

### Parent precedence

If the parent uses `bypassPermissions` or `acceptEdits`, that **overrides** the subagent's `permissionMode`. If the parent uses `auto`, the subagent inherits `auto` and any `permissionMode` in its frontmatter is **ignored** — the classifier evaluates the subagent's calls under the parent's block/allow rules.

## Hook-based validation (finer control than `tools`)

When you need to allow *some* uses of a tool and block others, use a `PreToolUse` hook. Classic example: allow `Bash` but only for read-only SQL.

```yaml
---
name: db-reader
description: Execute read-only database queries
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---
```

The hook receives the tool call as JSON on stdin. Exit code 2 blocks the call and sends the stderr message back to Claude:

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b' > /dev/null; then
  echo "Blocked: Only SELECT queries are allowed" >&2
  exit 2
fi

exit 0
```

`chmod +x` the script. On Windows, write in PowerShell and add `shell: powershell` to the hook entry.

## Hook events on subagents

Two places to define hooks:

1. **In the subagent's frontmatter** — runs only while that subagent is active, cleaned up when it finishes.
2. **In `settings.json`** — runs in the main session when subagents start/stop.

Common subagent hook events:

| Event | When it fires |
| :-- | :-- |
| `PreToolUse` | Before the subagent uses a tool |
| `PostToolUse` | After the subagent uses a tool |
| `Stop` | When the subagent finishes (converted to `SubagentStop` at runtime) |

Settings-level events:

| Event | When it fires |
| :-- | :-- |
| `SubagentStart` | A subagent begins (matcher = agent name) |
| `SubagentStop` | A subagent completes (matcher = agent name) |

Example: lint after every edit, plus validate Bash commands:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh $TOOL_INPUT"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
```

## Plugin restriction

Plugin subagents **silently ignore** `hooks`, `mcpServers`, and `permissionMode`. If a plugin agent needs them, copy the file into `.claude/agents/` or `~/.claude/agents/` instead.
