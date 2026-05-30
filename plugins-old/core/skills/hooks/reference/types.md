# Hooks — types

Each handler under `hooks` has a `type` that selects how it executes. The five types share the same input/output contract (stdin JSON in, stdout JSON or stderr+exit code out) — they differ in *how* the work is done.

## `command` (default)

A shell command. Runs in a non-interactive shell (`sh -c` on macOS/Linux, Git Bash on Windows; falls back to PowerShell on Windows when Git Bash isn't installed).

```json
{
  "type": "command",
  "command": "jq -r '.tool_input.command' >> ~/.claude/bash.log",
  "timeout": 30
}
```

- **Default timeout:** 600 seconds (10 minutes) for `command`, `http`, and `mcp_tool`. `UserPromptSubmit` lowers them to 30 s. `SessionEnd` is **1.5 s** (override with `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` or a per-hook `timeout` — see [SessionEnd](./events.md)).
- **Communicates via** stdin (JSON), stdout (JSON for structured output), stderr (feedback to Claude on `exit 2`), exit code.
- **Cannot trigger `/` commands or tool calls** — output is plain text injected as a system reminder.

### Common command-hook fields

| Field | Description |
| :-- | :-- |
| `command` | Shell command to execute (shell form) or the executable name/path (exec form, when `args` is set). |
| `args` | Argument list. When present, switches to exec form: `command` resolves on `PATH` and is spawned directly with `args` as the argument vector, no shell. |
| `async` | If `true`, runs in the background. See [Async hooks](#async-hooks). |
| `asyncRewake` | If `true`, runs in the background and wakes Claude on exit code 2 (implies `async`). |
| `shell` | `"bash"` (default) or `"powershell"`. Forces the shell to use in shell form on Windows. Ignored when `args` is set. |
| `if` | Permission rule (e.g. `"Bash(git *)"`). Tool events only. See [matchers.md](./matchers.md#the-if-field). |
| `timeout` | Override the default in seconds. |
| `statusMessage` | Custom spinner message shown while the hook runs. |
| `once` | If `true`, runs once per session then is removed. Honored only for hooks declared in skill frontmatter; ignored in settings files and agent frontmatter. |

### Exec form vs shell form

A command hook runs as **exec form** when `args` is set, and **shell form** when `args` is omitted. Use exec form whenever the hook references a [path placeholder](#reference-scripts-by-path) — each `args` element passes as one argument with no quoting and no shell tokenization. Use shell form when you need shell features like pipes, `&&`, redirects, or globs.

**Exec form** (with `args`). `command` is resolved as an executable on `PATH` and spawned directly. Each `args` element is one argument exactly as written. Path placeholders (`${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`) substitute into `command` and into each `args` element as plain strings. Special characters such as apostrophes, `$`, and backticks pass through verbatim — there is no shell to interpret them.

```json
{
  "type": "command",
  "command": "node",
  "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/format.js", "--fix"]
}
```

> **Windows caveat.** Exec form requires `command` to resolve to a real executable (`.exe`). The `.cmd` and `.bat` shims that npm, npx, eslint, and similar tools install in `node_modules/.bin` are **not** executables and cannot be spawned without a shell. To run them in exec form, invoke `node` directly with the underlying script path (e.g. `"command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/node_modules/eslint/bin/eslint.js"]`). To run a `.cmd`/`.bat` shim by name, use shell form.

**Shell form** (no `args`). The `command` string is passed to a shell: `sh -c` on macOS/Linux, Git Bash on Windows, or PowerShell when Git Bash isn't installed. Set `"shell": "bash"` or `"shell": "powershell"` to choose explicitly. The shell tokenizes the string, expands variables, and interprets pipes, `&&`, redirects, and globs. Path placeholders still substitute, but wrap them in double quotes to handle spaces.

```json
{
  "type": "command",
  "command": "node \"${CLAUDE_PLUGIN_ROOT}\"/scripts/format.js --fix"
}
```

Both forms export `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, and `CLAUDE_PLUGIN_DATA` as environment variables on the spawned process, so a script can read `process.env.CLAUDE_PLUGIN_ROOT` regardless of how it was launched.

### Async hooks

Add `"async": true` to a `command` handler to run it in the background without blocking Claude. Only `command` hooks support async — `prompt`, `agent`, `http`, and `mcp_tool` do not.

```json
{
  "type": "command",
  "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/run-tests.sh",
  "args": [],
  "async": true,
  "timeout": 300
}
```

- **No decision control.** `decision`, `permissionDecision`, and `continue` are ignored — the triggering action has already proceeded by the time the hook completes.
- **`additionalContext` lands on the next turn.** If the session is idle, the hook's output waits for the next user input. Async completion notifications are suppressed by default — enable verbose mode (`Ctrl+O` or `--verbose`) to see them.
- **`asyncRewake: true`** is the same as `async: true` but exit code 2 wakes Claude immediately and surfaces stderr (or stdout if stderr is empty) as a system reminder. Use it for long-running checks that should interrupt the session on failure.
- **No deduplication across firings.** Each execution creates a separate background process.

### Script files

For anything beyond one line, write a script (`.claude/hooks/<name>.sh`), `chmod +x`, and call it through `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.sh`. `$CLAUDE_PROJECT_DIR` is always set to the project root, regardless of Claude's current working directory.

### Reference scripts by path

Use these placeholders to reference hook scripts relative to the project or plugin root, regardless of the working directory when the hook runs:

| Placeholder | Resolves to | Notes |
| :-- | :-- | :-- |
| `${CLAUDE_PROJECT_DIR}` | Project root | Always set during a session. |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install directory | For scripts bundled with a plugin. Changes on each plugin update. |
| `${CLAUDE_PLUGIN_DATA}` | Plugin's persistent data directory | For dependencies and state that should survive plugin updates. |

Prefer exec form when using these placeholders — `args` passes each element as one argument with no shell tokenization, so paths with spaces or special characters need no quoting. In shell form, wrap each placeholder in double quotes.

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
  - `PostToolUse` — by default the turn ends and `reason` appears as a warning line. Set `continueOnBlock: true` to feed the reason back to Claude and continue the turn instead
  - `PostToolBatch`, `UserPromptSubmit`, `UserPromptExpansion` — turn ends, `reason` shown as warning line. **`continueOnBlock` does not change this**; these events end the turn on `decision: "block"` regardless
  - `PostToolUseFailure`, `TaskCreated`, `TaskCompleted` — `reason` returned to Claude as a tool error
  - `PermissionRequest` — `ok: false` has no effect; use a `command` hook with `hookSpecificOutput.decision.behavior: "deny"` to deny

`continueOnBlock` is a prompt-hook field: when the prompt returns `ok: false`, the resulting `decision: "block"` is paired with `continue: true` so the turn continues with the reason as feedback. Default `false`.

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

- **Default timeout:** 600 seconds (10 minutes); 30 s for `UserPromptSubmit`.
- **Headers** support `$VAR` / `${VAR}` interpolation, but **only** variables listed in `allowedEnvVars` resolve. Unlisted references stay empty — there is no implicit env passthrough.
- **HTTP status codes alone cannot block.** To deny a tool call, return a 2xx response whose body contains the appropriate `hookSpecificOutput`. Non-2xx responses, connection failures, and timeouts all produce non-blocking errors.
- **No `${path}` substitution.** Only `mcp_tool` `input` strings substitute hook input fields; HTTP `url`, `headers`, and body do not. Identical HTTP hooks are deduplicated by `url`.

## `mcp_tool`

Call a tool on an already-connected MCP server, passing the hook input as the tool input.

```json
{
  "type": "mcp_tool",
  "server": "policy-server",
  "tool": "check_tool_call",
  "input": { "file_path": "${tool_input.file_path}" }
}
```

- **Default timeout:** 600 seconds (10 minutes).
- The tool's return value is parsed as the hook's output (same JSON shape as a command hook's stdout). If the named server is not connected, or the tool returns `isError: true`, the hook produces a non-blocking error and execution continues.
- **`input` substitution.** String values inside the `input` object support `${path}` substitution from the hook's JSON input, for example `"${tool_input.file_path}"`. This is the only hook type that performs this substitution.
- **Server must already be connected.** The hook never starts an OAuth or connection flow. `SessionStart` and `Setup` typically fire before MCP connects, so expect the "not connected" error on first run.
- Useful when policy logic is already centralized in an MCP server.

## Timeouts

| Type | Default | Notes |
| :-- | :-- | :-- |
| `command`, `http`, `mcp_tool` | 600 s (10 min) | `UserPromptSubmit` lowers to 30 s; `SessionEnd` is 1.5 s (override via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` or per-hook `timeout`, up to 60 s total budget; plugin timeouts do not raise the budget) |
| `prompt` | 30 s | |
| `agent` | 60 s | Hard cap of 50 tool-use turns |

Override per handler with `"timeout": <seconds>`. A timed-out hook reports a non-zero result and the action proceeds (the transcript shows a `<event> hook error` notice).

## Event support

Not every event supports every hook type.

**All five types** (`command`, `http`, `mcp_tool`, `prompt`, `agent`):

- `PermissionRequest`
- `PostToolBatch`
- `PostToolUse`
- `PostToolUseFailure`
- `PreToolUse`
- `Stop`
- `SubagentStop`
- `TaskCompleted`
- `TaskCreated`
- `UserPromptExpansion`
- `UserPromptSubmit`

**`command`, `http`, `mcp_tool` only** (no `prompt` or `agent`):

- `ConfigChange`
- `CwdChanged`
- `Elicitation`
- `ElicitationResult`
- `FileChanged`
- `InstructionsLoaded`
- `Notification`
- `PermissionDenied`
- `PostCompact`
- `PreCompact`
- `SessionEnd`
- `StopFailure`
- `SubagentStart`
- `TeammateIdle`
- `WorktreeCreate`
- `WorktreeRemove`

**`command` and `mcp_tool` only** (no `http`, `prompt`, `agent`):

- `SessionStart`
- `Setup`
