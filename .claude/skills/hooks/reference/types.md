# Hooks — types

Each handler under `hooks` has a `type` that selects how it executes. The five types share the same input/output contract (stdin JSON in, stdout JSON or stderr+exit code out) — they differ in *how* the work is done.

## `command` (default)

A shell command. Runs in a non-interactive shell (`sh -c` on macOS/Linux, Git Bash on Windows).

```json
{
  "type": "command",
  "command": "jq -r '.tool_input.command' >> ~/.claude/bash.log",
  "timeout": 30
}
```

- **Default timeout:** 10 minutes (30 s for `UserPromptSubmit` hooks).
- **Communicates via** stdin (JSON), stdout (JSON for structured output), stderr (feedback to Claude on `exit 2`), exit code.
- **Cannot trigger `/` commands or tool calls** — output is plain text injected as a system reminder.

### Exec form vs shell form

By default, Claude Code spawns a shell to run `command`. That shell sources your profile in some configurations, which can leak `echo` output into stdout and break JSON parsing. To bypass the shell entirely, switch to **exec form** with `args`:

```json
{
  "type": "command",
  "command": "/usr/local/bin/my-hook",
  "args": ["--mode", "strict"]
}
```

With `args` present, the binary is spawned directly — no shell interpretation, no profile sourcing.

### Script files

For anything beyond one line, write a script (`.claude/hooks/<name>.sh`), `chmod +x`, and call it through `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.sh`. `$CLAUDE_PROJECT_DIR` is always set to the project root, regardless of Claude's current working directory.

## `prompt`

A single-turn LLM call. The model receives your `prompt` plus the hook input JSON and must return `{"ok": true|false, "reason": "..."}`.

```json
{
  "type": "prompt",
  "model": "haiku",
  "prompt": "Did Claude complete every requested task? If not, respond with {\"ok\": false, \"reason\": \"what's missing\"}."
}
```

- **Default timeout:** 30 seconds.
- **Default model:** Haiku. Override with `model` (`haiku`, `sonnet`, `opus`, or a full model id).
- **Use when** the decision needs judgment but the hook input alone is enough — no codebase inspection.
- **`ok: false` behavior** depends on the event:
  - `Stop`, `SubagentStop` — `reason` is fed to Claude so it keeps working
  - `PreToolUse` — tool call is denied, `reason` returned as tool error
  - `PostToolUse`, `PostToolBatch`, `UserPromptSubmit`, `UserPromptExpansion` — turn ends, `reason` shown as warning line
  - `PermissionRequest` — `ok: false` has no effect; use a `command` hook with `hookSpecificOutput.decision.behavior: "deny"` to deny

## `agent` (experimental)

A subagent with tool access. Same response format as `prompt` (`{"ok": ..., "reason": ...}`) but can read files, run commands, and chain up to 50 tool-use turns.

```json
{
  "type": "agent",
  "prompt": "Verify that all unit tests pass. Run the test suite and check the results. $ARGUMENTS",
  "timeout": 120
}
```

- **Default timeout:** 60 seconds.
- **Use when** the decision needs to verify state in the codebase (tests pass, file conforms to schema, etc.).
- **Experimental** — behavior and configuration may change. For production, prefer `command` hooks that shell out to your own tooling.

## `http`

POST event data to a URL. The endpoint receives the same JSON a command hook would receive on stdin, and returns its result in the response body (same JSON format).

```json
{
  "type": "http",
  "url": "http://localhost:8080/hooks/tool-use",
  "headers": {
    "Authorization": "Bearer $MY_TOKEN"
  },
  "allowedEnvVars": ["MY_TOKEN"],
  "timeout": 60
}
```

- **Default timeout:** 10 minutes (30 s for `UserPromptSubmit`).
- **Headers** support `$VAR` / `${VAR}` interpolation, but **only** variables listed in `allowedEnvVars` resolve. Unlisted references stay empty — there is no implicit env passthrough.
- **HTTP status codes alone cannot block.** To deny a tool call, return a 2xx response whose body contains the appropriate `hookSpecificOutput`.

## `mcp_tool`

Call a tool on an already-connected MCP server, passing the hook input as the tool input.

```json
{
  "type": "mcp_tool",
  "server": "policy-server",
  "tool": "check_tool_call"
}
```

- **Default timeout:** 10 minutes.
- The tool's return value is parsed as the hook's output (same JSON shape as a command hook's stdout).
- Useful when policy logic is already centralized in an MCP server.

## Timeouts

| Type | Default | Notes |
| :-- | :-- | :-- |
| `command`, `http`, `mcp_tool` | 10 min | `UserPromptSubmit` lowers to 30 s |
| `prompt` | 30 s | |
| `agent` | 60 s | Hard cap of 50 tool-use turns |

Override per handler with `"timeout": <seconds>`. A timed-out hook reports a non-zero result and the action proceeds (the transcript shows a `<event> hook error` notice).

## Event support

Not every event supports every hook type:

| Events | Supported types |
| :-- | :-- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `SubagentStop`, `PermissionRequest`, `TaskCreated`, `TaskCompleted`, `UserPromptSubmit`, `UserPromptExpansion` | `command`, `http`, `mcp_tool`, `prompt`, `agent` |
| `ConfigChange`, `CwdChanged`, `Elicitation`, `ElicitationResult`, `FileChanged`, `InstructionsLoaded`, `Notification`, `PermissionDenied`, `PostCompact`, `PreCompact`, `SessionEnd`, `StopFailure`, `SubagentStart`, `TeammateIdle`, `WorktreeCreate`, `WorktreeRemove` | `command`, `http`, `mcp_tool` |
| `SessionStart`, `Setup` | `command`, `mcp_tool` |
