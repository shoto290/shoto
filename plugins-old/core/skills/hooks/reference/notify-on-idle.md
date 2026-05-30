# Notify on idle

**Goal.** Get a desktop notification whenever Claude Code is idle and waiting for your input, so you can context-switch without watching the terminal.

**Event.** `Notification`

**Matcher.** `idle_prompt` (other valid values: `permission_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response`).

**Scope.** Personal — add to `~/.claude/settings.json`.

## Why `terminalSequence`

As of Claude Code v2.1.139, hooks run without a controlling terminal. Writing escape sequences directly to `/dev/tty` fails on macOS and Linux, and `/dev/tty` never existed on Windows. Instead, return the escape sequence in the [`terminalSequence`](./io.md#emit-terminal-notifications) JSON output field and Claude Code emits it through its own terminal write path. This is race-free inside tmux and GNU screen, works on Windows, and the same JSON works on every platform — no `uname` branching required.

## Script

Save to `~/.claude/hooks/notify-on-idle.sh` and `chmod +x`:

```bash
#!/bin/bash
# .claude/hooks/notify-on-idle.sh
input=$(cat)
title="Claude Code"
body=$(jq -r '.message // "Needs your attention"' <<<"$input")
seq=$(printf '\033]777;notify;%s;%s\007' "$title" "$body")
jq -nc --arg seq "$seq" '{terminalSequence: $seq}'
```

`printf '\033]777;notify;%s;%s\007'` builds an OSC 777 notification terminated with BEL. `jq -n --arg` escapes the sequence safely into the JSON string so quotes, backslashes, and newlines in the message survive.

## Settings entry

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/notify-on-idle.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

For a user-scope install, swap the path to `$HOME/.claude/hooks/notify-on-idle.sh` (or any absolute path).

## Terminal allowlist

`terminalSequence` only accepts the following sequences. Anything else (CSI cursor sequences, OSC 8 hyperlinks, OSC 52 clipboard, OSC 1337, etc.) is rejected and the field is silently ignored:

| Sequence | Use |
| :-- | :-- |
| OSC `0` / `1` / `2` | Window and icon titles |
| OSC `9` | iTerm2, ConEmu, Windows Terminal, WezTerm notifications (including `9;4` taskbar progress) |
| OSC `99` | Kitty notifications |
| OSC `777` | urxvt, Ghostty, Warp notifications |
| Bare BEL | Audible bell |

Pick the OSC that matches your terminal. OSC 777 covers Ghostty and Warp; OSC 9 covers Windows Terminal and iTerm2.

## Verify

1. Open `/hooks`, expand `Notification`, confirm `notify-on-idle.sh` appears under matcher `idle_prompt`.
2. Ask Claude to do something, then leave it idle waiting on input. The notification should fire when Claude posts the idle prompt.
3. If nothing appears, verify the escape sequence is in the allowlist (rebuild the `printf` string with octal escapes), and check `claude --debug-file` output for `terminalSequence` being dropped.
