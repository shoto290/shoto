---
name: hooks
description: 'Understand, design, and create or update Claude Code hooks (shell commands, prompts, agents, or HTTP endpoints that run at specific lifecycle events). Use when the user wants to learn how hooks work, decide which event/type to use, write a new hook in `settings.json`, edit an existing one, add a matcher or `if` filter, build a hook script, switch between exit-code and JSON output, scope a hook to user/project/local, auto-approve a permission prompt, block a tool call, inject context on session start, audit config changes, or debug a hook that isn''t firing. Triggers on: hook, hooks, PreToolUse, PostToolUse, SessionStart, SessionEnd, Stop, Notification, UserPromptSubmit, PermissionRequest, ConfigChange, FileChanged, CwdChanged, PreCompact, SubagentStart, SubagentStop, hook matcher, hook type, hook script, hook output, exit code 2, hookSpecificOutput, additionalContext, permissionDecision, allowedEnvVars, CLAUDE_PROJECT_DIR, CLAUDE_ENV_FILE, /hooks menu, disableAllHooks.'
argument-hint: '[event-or-pattern]'
---

# Hooks

A **hook** is a deterministic action — a shell command, prompt-based LLM check, subagent verification, or HTTP call — that fires at a specific point in Claude Code's lifecycle. Hooks are configured in `settings.json` under a `hooks` block keyed by event name. Use them to enforce rules that should never depend on Claude choosing to follow them: format-on-save, block edits to protected files, validate Bash commands, audit changes, re-inject context after compaction, notify on idle, auto-approve specific permission prompts.

## Detect intent

If invoked as `/hooks <pattern>`, treat `$ARGUMENTS` as the target event name (`PreToolUse`, `SessionStart`, …) or a free-form goal (`format on save`, `block .env edits`).

1. **Pattern matches an event** → propose a hook for that event (route to [reference/events.md](./reference/events.md))
2. **Pattern describes a goal** → pick the smallest event that fires for that goal and propose a hook
3. **Empty / "explain"** → route to **Explain flow** below — do not write files
4. **User wants to edit an existing hook** → **Update flow**

> The built-in `/hooks` slash command opens a read-only browser of installed hooks. It cannot add, edit, or remove them — only the settings JSON does. Tell the user this if they expect `/hooks` to be interactive.

## When to suggest each flow

**Create** when the user:
- Wants something to happen *every time* (format, lint, log, notify) without relying on the model
- Needs to block a class of actions (edits to `.env`, `rm -rf`, schema drops) before they execute
- Wants to inject context at session start or after compaction
- Wants to auto-approve a recurring permission prompt
- Needs an external service (web hook, audit log) to receive lifecycle events

**Update** when the user wants to:
- Tighten or widen a `matcher` so the hook fires on the right tool calls
- Add an `if` rule to filter by tool arguments (`Bash(git *)`, `Edit(*.ts)`)
- Switch a hook from exit-code control (`exit 2`) to structured JSON (`hookSpecificOutput`)
- Move a hook from user → project → local scope (or to managed/plugin)
- Add `allowed-tools`-style env injection (`headers`, `allowedEnvVars`) for HTTP hooks
- Convert a `command` hook into a `prompt` or `agent` hook (model-based judgment instead of rules)
- Diagnose why a hook isn't firing, exits non-zero, or trips the Stop block cap

**Explain** when the user is *asking how something works* rather than wiring it up. Route to the right reference (see "Explain flow" below).

---

## Create flow

### 1. Clarify the hook

Propose defaults from the user's request; confirm before writing:

| Decision | Options |
| :-- | :-- |
| **Event** | One of `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `UserPromptExpansion`, `Notification`, `Stop`, `StopFailure`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`, `PermissionRequest`, `PermissionDenied`, `ConfigChange`, `CwdChanged`, `FileChanged`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `Setup`, `InstructionsLoaded`, `PostToolBatch`, `Elicitation`, `ElicitationResult`, `TeammateIdle` — see [reference/events.md](./reference/events.md) |
| **Type** | `command` (shell, default), `prompt` (single-turn LLM), `agent` (multi-turn LLM with tools, experimental), `http` (POST to URL), `mcp_tool` (call a connected MCP tool). Support varies by event; check [reference/types.md](./reference/types.md#event-support) before choosing. `command` hooks accept either exec form (`args` set, no shell tokenization) or shell form (`args` omitted) — see [reference/types.md](./reference/types.md#exec-form-vs-shell-form) |
| **Matcher** | Empty string fires on every occurrence. Otherwise depends on event: tool name regex (`Bash`, `Edit&#124;Write`, `mcp__.*`), session source (`startup`, `compact`), notification kind, etc. — see [reference/matchers.md](./reference/matchers.md) |
| **`if` filter** | For tool events only: permission-rule syntax to filter by tool name + arguments (`Bash(git *)`, `Edit(*.ts)`). Requires Claude Code v2.1.85+ |
| **Run mode** | `async: true` runs the hook in the background; output is delivered on the next conversation turn. `asyncRewake: true` is the same but exit code 2 wakes Claude immediately and surfaces stderr (or stdout if stderr is empty). Only `command` hooks support async; async hooks cannot return `decision`, `permissionDecision`, or `continue` |
| **Output mode** | Exit code (0 = allow, 2 = block + stderr fed back to Claude) **or** stdout JSON (`hookSpecificOutput`, `additionalContext`, `decision`). Don't mix |
| **Scope** | User `~/.claude/settings.json`, Project `.claude/settings.json` (shareable), Local `.claude/settings.local.json` (gitignored), Managed (org policy), Plugin `hooks/hooks.json`, or Skill/agent frontmatter |
| **Timeout** | Defaults: `command`/`http`/`mcp_tool` = 600 s (10 min); `UserPromptSubmit` lowers them to 30 s; `SessionEnd` is 1.5 s (override with `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` or per-hook `timeout`, up to 60 s; plugin timeouts do not raise the budget); `prompt` = 30 s; `agent` = 60 s. Override per-hook with `"timeout"` (seconds) |

### 2. Pick an example

Start from a complete recipe in [reference/](./reference/):

- [reference/notify-on-idle.md](./reference/notify-on-idle.md) — `Notification` hook, desktop alert (macOS / Linux / Windows)
- [reference/format-on-save.md](./reference/format-on-save.md) — `PostToolUse` + `Edit|Write` matcher, runs Prettier on the edited file
- [reference/block-protected-files.md](./reference/block-protected-files.md) — `PreToolUse` + external script + `exit 2`
- [reference/bash-command-validator.md](./reference/bash-command-validator.md) — `PreToolUse` + `Bash` matcher + JSON `permissionDecision: "deny"`
- [reference/inject-context-on-compact.md](./reference/inject-context-on-compact.md) — `SessionStart` with `matcher: "compact"`, stdout becomes Claude's context
- [reference/audit-config-changes.md](./reference/audit-config-changes.md) — `ConfigChange` writes JSON line to audit log
- [reference/auto-approve-permission.md](./reference/auto-approve-permission.md) — `PermissionRequest` + matcher + `hookSpecificOutput.decision.behavior: "allow"`
- [reference/prompt-stop-check.md](./reference/prompt-stop-check.md) — `Stop` hook of `type: "prompt"`, model returns `{ok: false, reason}` to keep Claude working

For a minimal output sample (the JSON Claude produces), see [examples/hook-config-output.md](./examples/hook-config-output.md).

### 3. Add it to the right settings file

Hooks live under a top-level `hooks` block. Each event is a key whose value is an array of *handler groups*. A group has a `matcher` (regex/literal) and a `hooks` array of one or more handler objects (`type`, `command` / `prompt` / `url`, `timeout`, etc.).

If the settings file already has a `hooks` key, **add the new event as a sibling** of existing event keys — do not replace the whole `hooks` object.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "FILE=$(jq -r '.tool_input.file_path'); npx prettier --write \"$FILE\"" }
        ]
      }
    ]
  }
}
```

For shell scripts longer than one line, write them to `.claude/hooks/<name>.sh`, `chmod +x`, and reference via `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.sh` so the path resolves regardless of Claude's working directory.

Use path placeholders when bundling hook scripts with a project, plugin, or persistent data directory:

- `${CLAUDE_PROJECT_DIR}` — project root.
- `${CLAUDE_PLUGIN_ROOT}` — the plugin's install directory (changes on each plugin update). Use for scripts bundled with a plugin.
- `${CLAUDE_PLUGIN_DATA}` — the plugin's persistent data directory (survives plugin updates). Use for installed dependencies and runtime state.

Prefer exec form (`args` set) with placeholders so paths with spaces or special characters need no quoting.

### 4. Test

- The watcher normally picks up edits to settings JSON within a few seconds. If `/hooks` doesn't show the new hook, restart the session.
- **Manual unit test** for command hooks — pipe sample JSON via stdin and check the exit code:
  ```bash
  echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh
  echo $?
  ```
- **Live test** — trigger the event Claude-side (run a Bash command, edit a file, submit a prompt) and check the transcript view (`Ctrl+O`) for the one-line hook summary.
- **Full trace** — start Claude with `claude --debug-file /tmp/claude.log` (or `/debug` mid-session) and `tail -f /tmp/claude.log` to see every hook's stdin, stdout, stderr, and exit code.

---

## Update flow

### 1. Locate the hook

Hooks are scoped by the settings file they live in. Walk in this order and ask the user if multiple matches exist:

- Managed policy settings (org-wide)
- `~/.claude/settings.json` (user)
- `.claude/settings.json` (project, checked in)
- `.claude/settings.local.json` (project, gitignored)
- Enabled plugins (`<plugin>/hooks/hooks.json`)
- Skill or agent frontmatter (active only while that skill/agent is)

The `/hooks` browser shows every installed hook grouped by event with the source file — use it to find the right scope.

### 2. Read current state

Read the settings file and any referenced hook scripts. Don't propose changes blind — a hook that "doesn't fire" might be matched on the wrong event entirely.

### 3. Route the change

| Change | Where to look |
| :-- | :-- |
| Switch event (`PreToolUse` ↔ `PostToolUse`, add `SessionEnd`, etc.) | [reference/events.md](./reference/events.md) |
| Adjust `matcher` (tool regex, session source, MCP tool pattern) | [reference/matchers.md](./reference/matchers.md) |
| Add `if` filter (`Bash(git *)`, `Edit(*.ts)`) | [reference/matchers.md](./reference/matchers.md#the-if-field) |
| Switch between `exit 2` and JSON output | [reference/io.md](./reference/io.md) |
| Add `additionalContext`, `decision`, `permissionDecision`, `updatedInput`, `updatedPermissions` | [reference/io.md](./reference/io.md#decision-control) |
| Change hook `type` (command → prompt / agent / http / mcp_tool) | [reference/types.md](./reference/types.md) |
| Override `timeout` | [reference/types.md](./reference/types.md#timeouts) |
| Move scope (user ↔ project ↔ local ↔ managed ↔ plugin) | [reference/locations.md](./reference/locations.md) |
| HTTP `headers` / `allowedEnvVars` | [reference/types.md](./reference/types.md#http) |
| Handle `stop_hook_active` to avoid Stop block-cap | [reference/troubleshooting.md](./reference/troubleshooting.md#stop-hook-hits-the-block-cap) |
| Hook isn't firing / matcher never matches | [reference/troubleshooting.md](./reference/troubleshooting.md) |
| JSON parse errors from leaked shell-profile output | [reference/troubleshooting.md](./reference/troubleshooting.md#json-validation-failed) |

### 4. Apply the change

- Edit the JSON via `Edit` — preserve sibling event keys, never replace the whole `hooks` object.
- **Warn before** moving a hook from `local` → `project` (it becomes shared / checked in) or from `project` → `user` (it now affects every project).
- If switching from `exit 2` to JSON output, remove `exit 2` from the script — Claude Code ignores stdout JSON when the script exits 2.
- For HTTP hooks: env vars in `headers` only resolve if listed in `allowedEnvVars`; unlisted `$VAR` references stay empty.

### 5. Test

- File watcher picks up most edits automatically; if not, restart the session.
- Confirm via `/hooks` that the change is registered under the correct event.
- Trigger the event and watch the transcript (`Ctrl+O`) or debug log.

---

## Explain flow

If the user is asking how hooks work rather than wiring one up, skip create/update and route to the right reference:

| Question | Where |
| :-- | :-- |
| What's a hook? Why use one over prompting the model? | [reference/concepts.md](./reference/concepts.md) |
| What does each event fire on? Which ones can be blocked? | [reference/events.md](./reference/events.md) |
| What input does the hook get on stdin? What output formats exist? | [reference/io.md](./reference/io.md) |
| How do matchers work? `if` field? MCP tool patterns? | [reference/matchers.md](./reference/matchers.md) |
| `command` vs `prompt` vs `agent` vs `http` vs `mcp_tool` — when to use which? | [reference/types.md](./reference/types.md) |
| Where do hooks live? Precedence? `disableAllHooks`? | [reference/locations.md](./reference/locations.md) |
| Hook not firing / parse errors / Stop block cap / debug log | [reference/troubleshooting.md](./reference/troubleshooting.md) |

---

## Critical principles

- **Hooks are policy, not suggestions.** A `PreToolUse` hook that returns `permissionDecision: "deny"` blocks the tool even in `bypassPermissions` or `--dangerously-skip-permissions` mode. Use this when you genuinely don't want users to bypass.
- **Hooks tighten, never loosen.** A hook returning `"allow"` does **not** override `deny` rules from settings. Permission deny rules always win.
- **Most restrictive wins.** When several `PreToolUse` hooks fire on the same call, precedence is `deny > defer > ask > allow`. All hooks still run to completion — don't rely on one hook's `deny` to suppress another hook's side effects.
- **`exit 2` and JSON output are mutually exclusive.** Use exit 2 with stderr for a simple block; use exit 0 + stdout JSON for structured control (`additionalContext`, `updatedPermissions`, `decision: "block"`). Mixing them = JSON ignored.
- **Hooks have no controlling terminal (v2.1.139+).** To trigger a desktop notification, set a window title, or ring the bell, return [`terminalSequence`](./reference/io.md#emit-terminal-notifications) in JSON output. Do not write to `/dev/tty`; it is unavailable to hooks on all platforms.
- **Hook stdout/stderr is capped at 10,000 characters.** Larger output is spilled to a file and replaced with a short preview plus the file path, the same way large tool results are handled.
- **Hooks run in non-interactive shells.** Any `echo` in your `~/.zshrc` or `~/.bashrc` that always prints will be prepended to your hook's stdout and break JSON parsing. Guard those with `if [[ $- == *i* ]]; then …`.
- **`PostToolUse` can't undo.** The tool already ran. For pre-execution policy, use `PreToolUse`.
- **`PermissionRequest` doesn't fire in `-p` mode.** For automated permission decisions in headless / CI, use `PreToolUse` instead.
- **Multiple `updatedInput` rewrites race.** If two `PreToolUse` hooks both rewrite the tool's arguments, the last to finish wins — and order is non-deterministic. Don't have more than one hook mutate the same call's input.

## Common gotchas

- `/hooks` is **read-only** — to add/edit/remove, edit the settings JSON directly.
- Hook commands must produce executable scripts (`chmod +x`), or use absolute paths / `$CLAUDE_PROJECT_DIR`. "command not found" is almost always a path issue.
- `jq` isn't installed everywhere — for portable hooks use Python or Node for JSON parsing instead.
- `matcher` is **case-sensitive** and regex-evaluated. `bash` won't match the `Bash` tool.
- The `if` field requires Claude Code **v2.1.85+**; older versions silently ignore it and fire on every matched call.
- `if` only applies to tool events (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`). Adding it to any other event **prevents the hook from running**.
- Stop hooks fire on every "I'm done responding" — including mid-task pauses. Always check `stop_hook_active` in JSON input and exit 0 if true, or you'll hit the 8-blocks-in-a-row cap.
- HTTP status codes alone cannot block a tool call — only the JSON response body's `hookSpecificOutput` does.
- `bypassPermissions` mode in a `PermissionRequest` hook's `updatedPermissions` only takes effect if the session was launched with bypass already available.
- Use [`terminalSequence`](./reference/io.md#emit-terminal-notifications) (OSC `0`/`1`/`2`/`9`/`99`/`777` or bare BEL only) to fire desktop notifications or set window titles. `/dev/tty` is unavailable to hooks since v2.1.139.
- `hookSpecificOutput` requires `hookEventName` set to the firing event name. Without it, the JSON is inert and Claude Code falls back to the default behavior.
- Identical command hooks are auto-deduplicated by `command` + `args`. Identical HTTP hooks are auto-deduplicated by `url`. A subtle whitespace or env-var difference defeats dedup.

## Reference

- [reference/concepts.md](./reference/concepts.md) — what hooks are, why use them, where they fit vs skills/subagents/permissions
- [reference/events.md](./reference/events.md) — catalog of every event, when it fires, whether `exit 2` blocks it
- [reference/types.md](./reference/types.md) — `command`, `prompt`, `agent`, `http`, `mcp_tool` — fields, timeouts, trade-offs
- [reference/matchers.md](./reference/matchers.md) — matcher semantics per event, `if` field, MCP tool patterns
- [reference/io.md](./reference/io.md) — stdin schema, exit codes, JSON output, decision control table
- [reference/locations.md](./reference/locations.md) — settings files, scopes, precedence, `disableAllHooks`
- [reference/troubleshooting.md](./reference/troubleshooting.md) — hook not firing, parse errors, Stop block cap, debug log

## Examples

- [examples/hook-config-output.md](./examples/hook-config-output.md) — minimal `hooks` block in `settings.json`
- [examples/async-hook-output.md](./examples/async-hook-output.md) — JSON stdout from an async `PostToolUse` hook delivered on the next turn
- [examples/terminal-sequence-output.md](./examples/terminal-sequence-output.md) — `terminalSequence` JSON for an OSC 777 desktop notification

## Recipes

[reference/](./reference/) — complete working hook recipes for each common pattern. Read the matching one before drafting a new hook.
