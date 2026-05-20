# Hooks — input/output

Command and HTTP hooks exchange JSON. Prompt and agent hooks have their own minimal `{"ok": ..., "reason": ...}` format. Mcp_tool hooks return whatever the tool returns (interpreted as the same JSON shape as a command hook's stdout).

## Stdin: what the hook receives

Every event includes a baseline of common fields plus event-specific extras.

### Common fields

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/me/.claude/projects/.../transcript.jsonl",
  "cwd": "/Users/me/project",
  "permission_mode": "default",
  "effort": { "level": "medium" },
  "hook_event_name": "PreToolUse",
  "stop_hook_active": false
}
```

- `session_id` — unique per Claude Code session
- `transcript_path` — absolute path to the conversation JSONL transcript on disk
- `cwd` — Claude's working directory at the moment the event fired
- `permission_mode` — current permission mode: `"default"`, `"plan"`, `"acceptEdits"`, `"auto"`, `"dontAsk"`, or `"bypassPermissions"`. Not all events receive this field
- `effort` — object with a `level` field (`"low"`/`"medium"`/`"high"`/`"xhigh"`/`"max"`) for the active effort. Present on events that fire within a tool-use context (`PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`) when the model supports the effort parameter. Also available to hook commands as `$CLAUDE_EFFORT`
- `hook_event_name` — the event that triggered this hook
- `stop_hook_active` — true if a previous `Stop`/`SubagentStop` hook already blocked once; check this and exit 0 to avoid the 8-blocks-in-a-row cap

When running with `--agent` or inside a subagent, two additional fields are included:

- `agent_id` — unique identifier for the subagent. Present only when the hook fires inside a subagent call
- `agent_type` — agent name (e.g. `"Explore"`, `"security-reviewer"`). For custom subagents, this is the `name` field from frontmatter, not the filename

Only `SessionStart` hooks receive a `model` field. There is **no** `$CLAUDE_MODEL` environment variable; the parent shell's `$ANTHROPIC_MODEL` is inherited but does not change when you switch models with `/model`.

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

> Hook output strings (including `additionalContext`, `systemMessage`, and plain stdout) are capped at 10,000 characters. Output exceeding the limit is saved to a file and replaced with a short preview and the file path — the same way large tool results are handled.

#### Universal JSON output fields

These fields apply to every event. Beyond these, each event adds its own decision fields under `hookSpecificOutput` (see [Decision control](#decision-control)).

| Field | Default | Description |
| :-- | :-- | :-- |
| `continue` | `true` | If `false`, Claude stops processing entirely after the hook runs. Takes precedence over any event-specific decision fields |
| `stopReason` | none | Message shown to the user when `continue` is `false`. Not shown to Claude |
| `suppressOutput` | `false` | If `true`, omits stdout from the debug log |
| `systemMessage` | none | Warning message shown to the user (not to Claude) |
| `terminalSequence` | none | A terminal escape sequence for Claude Code to emit on your behalf. Restricted to OSC `0`/`1`/`2`/`9`/`99`/`777` and bare BEL. Anything outside the allowlist is ignored. See [Emit terminal notifications](#emit-terminal-notifications) |

To stop Claude entirely regardless of event type:

```json
{ "continue": false, "stopReason": "Build failed, fix errors before continuing" }
```

#### Emit terminal notifications

Requires Claude Code v2.1.141+. Hooks run without a controlling terminal (v2.1.139+), so writing escape sequences directly to `/dev/tty` fails (and `/dev/tty` does not exist on Windows). Instead, return the escape sequence in `terminalSequence` and Claude Code emits it through its own terminal write path. This is race-free, works inside tmux and GNU screen, and works on Windows.

The field accepts a string of one or more allowlisted escape sequences:

- OSC `0`, `1`, `2`: window and icon titles
- OSC `9`: iTerm2, ConEmu, Windows Terminal, WezTerm notifications (including `9;4` taskbar progress)
- OSC `99`: Kitty notifications
- OSC `777`: urxvt, Ghostty, Warp notifications
- Bare BEL

Sequences may be terminated with BEL or ST. Anything outside the allowlist — CSI cursor/color sequences, OSC palette, OSC 8 hyperlinks, OSC 52 clipboard, OSC 1337, etc. — is rejected and the field is ignored.

Example: fire a desktop notification from a `Notification` hook. The escape sequence is built with `printf` octal escapes so control bytes never appear on the shell command line:

```bash
#!/bin/bash
input=$(cat)
title="Claude Code"
body=$(jq -r '.message // "Needs your attention"' <<<"$input")
seq=$(printf '\033]777;notify;%s;%s\007' "$title" "$body")
jq -nc --arg seq "$seq" '{terminalSequence: $seq}'
```

The `{ "terminalSequence": "..." }` shape is the same from any shell or language. See [reference/notify-on-idle.md](./notify-on-idle.md) for the full recipe.

## Decision control

Each event uses a slightly different shape inside `hookSpecificOutput` or at the top level. The most common:

| Event | Field path | Values | Effect |
| :-- | :-- | :-- | :-- |
| `PreToolUse` | `hookSpecificOutput.permissionDecision` | `"allow"`, `"deny"`, `"ask"`, `"defer"` (headless) | Skip prompt / cancel call / show prompt as normal / defer to caller |
| `PreToolUse` | `hookSpecificOutput.permissionDecisionReason` | string | Sent to Claude on deny, shown in transcript on allow |
| `PreToolUse` | `hookSpecificOutput.updatedInput` | object | Replace the tool's arguments before execution |
| `PostToolUse`, `PostToolBatch`, `Stop`, `SubagentStop` | `decision` (top-level) | `"block"` | Feeds `reason` back to Claude (Stop keeps it working) |
| `PostToolUse`, `PostToolBatch`, `Stop`, `SubagentStop` | `reason` (top-level) | string | The text Claude sees |
| `PostToolUse` | `hookSpecificOutput.updatedToolOutput` | object | Replaces Claude's view of the tool result. The tool already ran; this only changes what Claude sees. Value must match the tool's output shape |
| `PostToolUse` | `hookSpecificOutput.updatedMCPToolOutput` | object | MCP-only legacy form of `updatedToolOutput`. Prefer `updatedToolOutput`, which works for all tools |
| `PermissionRequest` | `hookSpecificOutput.decision.behavior` | `"allow"`, `"deny"` | Answer the permission dialog |
| `PermissionRequest` | `hookSpecificOutput.decision.updatedPermissions` | array | Apply [permission updates](#permission-update-entries) (rules, mode, directories) — session or persisted |
| `UserPromptSubmit` | `hookSpecificOutput.additionalContext` | string | Append text to Claude's context. For `SessionStart`, write to stdout instead — anything printed is added to Claude's context |
| `UserPromptSubmit` | `hookSpecificOutput.sessionTitle` | string | Sets the session title (useful for naming sessions from the prompt content) |
| `UserPromptSubmit`, `UserPromptExpansion` | `decision` | `"block"` | Block the prompt with `reason` |
| `SubagentStart` | `hookSpecificOutput.additionalContext` | string | Injects context at the start of the subagent's conversation |
| `CwdChanged`, `FileChanged` | `watchPaths` (top-level) | array of absolute paths | Replaces the dynamic watch list for `FileChanged`. Paths from `matcher` config are always watched. Empty array clears the dynamic list |
| `Elicitation`, `ElicitationResult` | `hookSpecificOutput.action` | `"accept"`, `"decline"`, `"cancel"` | Responds programmatically (Elicitation) or overrides the user's action (ElicitationResult) |
| `Elicitation`, `ElicitationResult` | `hookSpecificOutput.content` | object | Form field values to submit (`Elicitation`) or override (`ElicitationResult`). Only meaningful when `action` is `"accept"` |
| `WorktreeCreate` | stdout / `hookSpecificOutput.worktreePath` | absolute path | Command hooks print the path on stdout; HTTP hooks return `hookSpecificOutput.worktreePath`. Missing path fails worktree creation |
| `PermissionDenied` | `hookSpecificOutput.retry` | bool | Tell the model it may retry the denied call |
| `ConfigChange` | `decision` | `"block"` | Reject the configuration change, except for `policy_settings` |

### `permissionDecision` values

- `"allow"` — skip the interactive prompt. Deny and ask rules from settings still apply.
- `"deny"` — cancel the tool call; `permissionDecisionReason` is returned to Claude as the tool error.
- `"ask"` — show the prompt as normal (default behavior).
- `"defer"` — non-interactive mode (`-p`) only. Exits the process with the call preserved so an Agent SDK wrapper can collect input and resume. See [Defer a tool call](#defer-a-tool-call).

`"allow"` does **not** override permission `deny` rules. Hooks can only tighten policy, never loosen it.

### Defer a tool call

`"defer"` is for integrations that run `claude -p` as a subprocess and read its JSON output, such as an Agent SDK app or a custom UI built on top of Claude Code. It lets the calling process pause Claude at a tool call, collect input through its own interface, and resume where it left off.

- Requires Claude Code v2.1.89+. Earlier versions do not recognize it and fall back to the normal permission flow.
- Honored **only** in non-interactive mode (`-p`). In interactive sessions Claude logs a warning and ignores the result.
- Only works when the turn has a **single** tool call. If Claude makes several tool calls at once, `"defer"` is ignored with a warning and the tool proceeds through the normal flow. Resume can only re-run one tool.
- `AskUserQuestion` and `ExitPlanMode` are the canonical use cases — both require user interaction that headless mode normally blocks.

Round trip:

1. Claude calls `AskUserQuestion`. The `PreToolUse` hook fires.
2. The hook returns `permissionDecision: "defer"`. The process exits with `stop_reason: "tool_deferred"` and the pending tool call preserved in the transcript. The SDK result contains a `deferred_tool_use` field with the tool's `id`, `name`, and `input`.
3. The calling process surfaces the question in its own UI and waits for an answer.
4. The calling process runs `claude -p --resume <session-id>`. The same tool call fires `PreToolUse` again.
5. The hook returns `permissionDecision: "allow"` with the answer in `updatedInput`. The tool executes and Claude continues.

There is no timeout or retry limit. The session remains on disk until you resume it, subject to `cleanupPeriodDays` (default 30). If the answer is not ready when you resume, the hook can return `"defer"` again.

**For `AskUserQuestion` specifically**, returning `"allow"` alone is not sufficient in headless mode. The `updatedInput` must echo back the original `questions` array **and** add an `answers` object mapping each question's text to the chosen option label (multi-select answers join labels with commas). Without `answers`, the tool still attempts to prompt and blocks the headless run.

If the deferred tool is no longer available on resume (e.g. its MCP server is not connected), the process exits with `stop_reason: "tool_deferred_unavailable"` and `is_error: true` before the hook fires; the `deferred_tool_use` payload is still included.

### Permission update entries

`updatedPermissions` is an array of entry objects. Each entry has a `type` that determines its other fields and a `destination` that controls where the change is written.

| `type` | Fields | Effect |
| :-- | :-- | :-- |
| `addRules` | `rules`, `behavior`, `destination` | Adds permission rules. `rules` is an array of `{toolName, ruleContent?}` objects. Omit `ruleContent` to match the whole tool. `behavior` is `"allow"`, `"deny"`, or `"ask"` |
| `replaceRules` | `rules`, `behavior`, `destination` | Replaces all rules of the given `behavior` at the `destination` with the provided `rules` |
| `removeRules` | `rules`, `behavior`, `destination` | Removes matching rules of the given `behavior` |
| `setMode` | `mode`, `destination` | Changes the permission mode. Valid modes: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `addDirectories` | `directories`, `destination` | Adds working directories. `directories` is an array of path strings |
| `removeDirectories` | `directories`, `destination` | Removes working directories |

`destination` values:

| `destination` | Writes to |
| :-- | :-- |
| `session` | In-memory only, discarded when the session ends |
| `localSettings` | `.claude/settings.local.json` |
| `projectSettings` | `.claude/settings.json` |
| `userSettings` | `~/.claude/settings.json` |

`PermissionRequest` input includes a `permission_suggestions` array (the "always allow" options from the dialog). A hook can echo one of them back as its own `updatedPermissions` output, equivalent to the user selecting that option in the dialog.

Example: change the active permission mode for the rest of the session.

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

`setMode` with `bypassPermissions` only takes effect if the session was launched with bypass already available (`--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, `--allow-dangerously-skip-permissions`, or `permissions.defaultMode: "bypassPermissions"`). `bypassPermissions` is never persisted as `defaultMode` regardless of `destination`.

## Combine results from multiple hooks

When several hooks match the same event:

1. All run in parallel to completion. One hook's deny does **not** stop another from running.
2. `PreToolUse` permission decisions: most restrictive wins. Precedence is `deny > defer > ask > allow`.
3. `additionalContext` strings: concatenated, all delivered to Claude.
4. `updatedInput`: last finisher wins. Order is non-deterministic. Don't have two hooks mutate the same call's input.
5. Identical command hooks are auto-deduplicated by `command` + `args`. Identical HTTP hooks are auto-deduplicated by `url`. Subtle whitespace or env-var differences defeat dedup.

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
