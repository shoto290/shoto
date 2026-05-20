# Hooks — troubleshooting

## Hook not firing

The hook is configured but never executes.

1. Run `/hooks` and check whether your handler appears under the expected event. If not, the file watcher missed the edit — restart the session.
2. Verify the event itself is the right one (`PreToolUse` runs *before* the tool, `PostToolUse` *after*). For permission decisions in `-p` mode, use `PreToolUse` — `PermissionRequest` doesn't fire in headless mode.
3. Confirm the matcher matches. Matchers are **case-sensitive regex**. `bash` won't match `Bash`. `mcp__github__.*` works; `github.*` does not.
4. If you added `"if": "..."` and the hook never fires, remember: `if` only applies to tool events (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`). Adding it elsewhere silently disables the handler.
5. `if` also requires Claude Code **v2.1.85+**. Older versions silently ignore the field and fire on every matched call.

## `<event> hook error: ...` in the transcript

Your script exited with a non-zero, non-2 code.

1. Reproduce manually by piping sample JSON to your script and check the exit code:
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh
   echo $?
   ```
2. "command not found" — use an absolute path or `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.sh`, **not** a relative path. To bypass shell quoting entirely, add `"args": []` to the handler — that switches to **exec form**, which spawns the binary directly.
3. "jq: command not found" — install jq (`brew install jq` / `apt-get install jq`) or rewrite the parsing in Python or Node.
4. "permission denied" — `chmod +x ./your-hook.sh`. The script must be executable.

## JSON validation failed

Even when your hook prints valid JSON, shell profile output can make the full stdout invalid.

When a shell-form `command` hook runs, Claude Code spawns `sh -c` (or Git Bash on Windows). Some shells source your profile, and any unconditional `echo` in `~/.zshrc` / `~/.bashrc` gets prepended to your hook's stdout, breaking JSON parsing:

```text
Shell ready on arm64
{"decision": "block", "reason": "..."}
```

Two fixes:

1. **Wrap echoes** in your profile so they only run in interactive shells:
   ```bash
   if [[ $- == *i* ]]; then
     echo "Shell ready"
   fi
   ```
2. **Use exec form** by adding `"args": []` to your handler. Exec form skips the shell entirely:
   ```json
   { "type": "command", "command": "/usr/local/bin/my-hook", "args": [] }
   ```

## Stop hook hits the block cap

Claude keeps working instead of stopping, then warns that the Stop hook blocked too many times.

After **8 consecutive blocks without progress**, Claude Code overrides the hook so the session can stop. To fix, check `stop_hook_active` in the JSON input and exit 0 when it's already true:

```bash
#!/bin/bash
INPUT=$(cat)
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0  # already triggered a continuation — allow stop
fi
# ... rest of your logic
```

If your hook legitimately needs more than 8 iterations to converge, raise the cap with the `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` environment variable.

## `/hooks` shows no hooks configured

You edited the settings JSON but `/hooks` is empty.

- Confirm the JSON is valid — no trailing commas, no `//` comments.
- Confirm the file location matches the scope you intended (project at `.claude/settings.json`, user at `~/.claude/settings.json`).
- Restart the session to force a reload if the watcher missed the edit.

## Hook fires twice / hooks duplicate

Identical handler commands are **auto-deduplicated** by Claude Code. If you're seeing duplicates, the commands differ in some subtle way (whitespace, quoting, env-var expansion in the JSON value). Diff the entries; trim differences.

## `permissionDecision: "allow"` doesn't bypass a deny rule

By design. Hooks can **tighten** restrictions but never **loosen** them past what the permission rules allow. A managed deny rule always wins. To audit which rule denied: check the debug log.

## "block" reason isn't visible to me

For `PreToolUse` denies, the `permissionDecisionReason` is fed back to **Claude**, not the user, so the model can adapt. To also see it yourself, write the same text to stderr (it goes to the transcript and debug log).

## Multiple `updatedInput` hooks corrupt the tool call

Two `PreToolUse` hooks both rewriting `tool_input`? The last one to finish wins, and they run in parallel, so order is non-deterministic. Don't do this. Consolidate into a single hook script that handles all rewrites.

## Async hook output never appears

You added `"async": true` and the hook's `additionalContext` never reaches Claude.

- Async hook output is delivered on the **next conversation turn**. If the session is idle, the response waits until the next user input.
- Exception: an `asyncRewake` hook that exits with code 2 wakes Claude immediately, even when idle. Use `asyncRewake` instead of `async` when failures must interrupt the session.
- Async completion notifications are suppressed by default. Enable verbose mode with `Ctrl+O` or start Claude with `--verbose` to see them.
- Async hooks cannot return `decision`, `permissionDecision`, or `continue` — the triggering action has already completed by the time the hook finishes. If you need to block, use a synchronous hook.

## `terminalSequence` ignored

Your JSON contains `terminalSequence` but no notification fires and no error appears.

- The field is **silently dropped** if the sequence contains anything outside the allowlist: OSC `0`, `1`, `2`, `9`, `99`, `777`, plus bare BEL. CSI cursor sequences, OSC 8 hyperlinks, OSC 52 clipboard writes, and OSC 1337 are all rejected.
- Build the escape sequence with `printf` octal escapes (e.g. `printf '\033]777;notify;%s;%s\007' "$title" "$body"`) so control bytes never appear on the shell command line where they could be mangled.
- Verify the field made it into the JSON: pipe the hook through `jq` and confirm `terminalSequence` is a single string starting with the right OSC introducer.
- Requires Claude Code v2.1.141+.

## How to debug in depth

1. **Transcript view** — toggle with `Ctrl+O`. Success hooks are silent; blocking errors show stderr; non-blocking errors show a one-line `<hook name> hook error` notice with the first line of stderr.
2. **Debug log** — start Claude with `claude --debug-file /tmp/claude.log`, then `tail -f /tmp/claude.log` in another terminal. Every hook's stdin, stdout, stderr, and exit code is captured. If you forgot the flag at startup, run `/debug` mid-session — it prints the log path.
3. **Verbose debug logging** — set `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` to surface matcher counts and per-handler `if`-field evaluation in the debug log. Pair with `claude --debug-file <path>` to capture: `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose claude --debug-file /tmp/claude.log`.
4. **Manual unit test** — pipe representative JSON via stdin to your script and inspect output. Most hook bugs are reproducible this way without going through Claude Code at all.

## Per-event "exit 2 doesn't block" surprises

`exit 2` blocks **most** events, but for some it just surfaces stderr and continues:

- `SessionStart`, `Setup`, `SessionEnd`
- `Notification`
- `PostToolUse`, `PostToolUseFailure` (the call already happened)
- `StopFailure` (API error already happened)
- `WorktreeRemove`, `InstructionsLoaded`, `PostCompact`
- `CwdChanged`, `FileChanged`

If you intended to block and the event doesn't support it, switch to a structured JSON output (`decision: "block"` for `Stop`/`PostToolUse`, `permissionDecision: "deny"` for `PreToolUse`) or move the policy to an earlier event in the lifecycle.
