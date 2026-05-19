# Notify on idle

**Goal.** Get a desktop notification whenever Claude Code stops working and is waiting for your input or permission, so you can context-switch without watching the terminal.

**Event.** `Notification`

**Scope.** Personal — add to `~/.claude/settings.json`.

**Matcher.** Empty (fires for every notification). To narrow, set to `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, or `elicitation_response`.

## macOS

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

If no notification appears: `osascript` routes through the built-in Script Editor app, which needs notification permission. Run `osascript -e 'display notification "test"'` once in Terminal, then open **System Settings → Notifications**, find **Script Editor**, and turn on **Allow Notifications**.

## Linux

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude Code needs your attention'"
          }
        ]
      }
    ]
  }
}
```

Requires `libnotify` / `notify-send`.

## Windows (PowerShell)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude Code needs your attention', 'Claude Code')\""
          }
        ]
      }
    ]
  }
}
```

## Verify

Open `/hooks`, select `Notification`, confirm your entry. Then ask Claude to do something that needs permission and switch tabs — the notification should fire.
