# Hooks — input/output

Command and HTTP hooks exchange JSON. Prompt and agent hooks have their own minimal `{"ok": ..., "reason": ...}` format. Mcp_tool hooks return whatever the tool returns (interpreted as the same JSON shape as a command hook's stdout).

## Stdin: what the hook receives

Every event includes a baseline of common fields plus event-specific extras.

### Common fields

```json
{
  "session_id": "abc123",
  "cwd": "/Users/me/project",
  "hook_event_name": "PreToolUse",
  "stop_hook_active": false
}
```

- `session_id` — unique per Claude Code session
- `cwd` — Claude's working directory at the moment the event fired
- `hook_event_name` — the event that triggered this hook
- `stop_hook_active` — true if a previous `Stop`/`SubagentStop` hook already blocked once; check this and exit 0 to avoid the 8-blocks-in-a-row cap

### Event-specific examples

`PreToolUse` / `PostToolUse` add `tool_name` and `tool_input` (or `tool_response` for post):

```json
{
  "session_id": "abc123",
  "cwd": "/Users/me/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" }
}
```

`UserPromptSubmit` adds `prompt`:

```json
{ "hook_event_name": "UserPromptSubmit", "prompt": "fix the failing test" }
```

`SessionStart` adds `source` (one of `startup`, `resume`, `clear`, `compact`).

`FileChanged` / `CwdChanged` add `watchPaths`, file paths, and previous/current values.

`ConfigChange` adds `source` and `file_path`.

For the exhaustive per-event schema, see the [Hooks reference page](https://docs.anthropic.com/en/docs/claude-code/hooks).

## Stdout & exit codes: what the hook returns

Two output modes — pick one. **Don't mix.**

### Mode A: exit codes (+ stderr for blocked feedback)

Simplest. Read input, decide, exit.

```bash
#!/bin/bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command')

if echo "$CMD" | grep -qE '\brm\b.*-rf'; then
  echo "Blocked: rm -rf is not allowed" >&2
  exit 2
fi
exit 0
```

| Exit code | Effect |
| :-- | :-- |
| `0` | Action proceeds. For `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` — stdout becomes Claude's context. |
| `2` | **Block** the action. stderr is fed back to Claude as feedback. Some events can't be blocked — see [events.md exit-code-2 behavior](./events.md#exit-code-2-behavior-summary). |
| anything else | Action proceeds. Transcript shows `<hook name> hook error` + first line of stderr; full stderr goes to debug log. |

### Mode B: stdout JSON

For structured control: inject context, allow/deny with reason, modify permissions, rewrite tool input. **Exit 0** and print a JSON object.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Use rg instead of grep for better performance"
  }
}
```

> Claude Code **ignores** stdout JSON when the hook exits 2. Either exit 0 with JSON, or exit 2 with stderr — never both.

## Decision control

Each event uses a slightly different shape inside `hookSpecificOutput` or at the top level. The most common:

| Event | Field path | Values | Effect |
| :-- | :-- | :-- | :-- |
| `PreToolUse` | `hookSpecificOutput.permissionDecision` | `"allow"`, `"deny"`, `"ask"`, `"defer"` (headless) | Skip prompt / cancel call / show prompt as normal / defer to caller |
| `PreToolUse` | `hookSpecificOutput.permissionDecisionReason` | string | Sent to Claude on deny, shown in transcript on allow |
| `PreToolUse` | `hookSpecificOutput.updatedInput` | object | Replace the tool's arguments before execution |
| `PostToolUse`, `PostToolBatch`, `Stop`, `SubagentStop` | `decision` (top-level) | `"block"` | Feeds `reason` back to Claude (Stop keeps it working) |
| `PostToolUse`, `PostToolBatch`, `Stop`, `SubagentStop` | `reason` (top-level) | string | The text Claude sees |
| `PermissionRequest` | `hookSpecificOutput.decision.behavior` | `"allow"`, `"deny"` | Answer the permission dialog |
| `PermissionRequest` | `hookSpecificOutput.decision.updatedPermissions` | array | Apply a `setMode` (e.g. `acceptEdits`) to the session |
| `UserPromptSubmit`, `SessionStart` | `hookSpecificOutput.additionalContext` | string | Append text to Claude's context |
| `UserPromptSubmit`, `UserPromptExpansion` | `decision` | `"block"` | Block the prompt with `reason` |
| `PermissionDenied` | `hookSpecificOutput.retry` | bool | Tell the model it may retry the denied call |
| `ConfigChange` | `decision` | `"block"` | Reject the configuration change, except for `policy_settings` |

### `permissionDecision` values

- `"allow"` — skip the interactive prompt. Deny and ask rules from settings still apply.
- `"deny"` — cancel the tool call; `permissionDecisionReason` is returned to Claude as the tool error.
- `"ask"` — show the prompt as normal (default behavior).
- `"defer"` — non-interactive mode (`-p`) only. Exits the process with the call preserved so an Agent SDK wrapper can collect input and resume.

`"allow"` does **not** override permission `deny` rules. Hooks can only tighten policy, never loosen it.

### Permission mode override

A `PermissionRequest` hook can change the active permission mode for the rest of the session:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedPermissions": [
        { "type": "setMode", "mode": "acceptEdits", "destination": "session" }
      ]
    }
  }
}
```

`mode` can be `default`, `acceptEdits`, `bypassPermissions`, or `plan`. `destination: "session"` applies only to this session — never persisted as the default. `bypassPermissions` only works if the session was launched with bypass already available (`--dangerously-skip-permissions`, etc.).

## Combine results from multiple hooks

When several hooks match the same event:

1. All run in parallel to completion. One hook's deny does **not** stop another from running.
2. `PreToolUse` permission decisions: most restrictive wins. `deny` > `defer` > `ask` > `allow`.
3. `additionalContext` strings: concatenated, all delivered to Claude.
4. `updatedInput`: last finisher wins. Order is non-deterministic. Don't have two hooks mutate the same call's input.
5. Identical hook commands are auto-deduplicated.

## HTTP response equivalence

HTTP hooks use the same JSON shape in the response body that command hooks use on stdout. **HTTP status codes alone cannot block actions** — you must return a 2xx response with the appropriate `hookSpecificOutput` to deny.

## Prompt/agent response format

Both `prompt` and `agent` types return:

```json
{ "ok": true }
```

or

```json
{ "ok": false, "reason": "tests are failing" }
```

The hook event determines what `ok: false` does — see [types.md](./types.md#prompt) for the per-event behavior.
