# Auto-approve a specific permission prompt

**Goal.** Stop being prompted to approve a tool call you always allow. The canonical example: auto-approving `ExitPlanMode` so Claude proceeds out of plan mode without you confirming each time.

**Event.** `PermissionRequest`

**Scope.** Personal — `~/.claude/settings.json`.

**Matcher.** **As narrow as possible.** `ExitPlanMode` here; never `.*` or empty unless you really want to auto-approve every prompt.

**Output mode.** Stdout JSON. `PermissionRequest` requires `hookSpecificOutput.decision.behavior` to take effect — exit codes alone can't answer the prompt.

## Minimal: auto-approve `ExitPlanMode`

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PermissionRequest\", \"decision\": {\"behavior\": \"allow\"}}}'"
          }
        ]
      }
    ]
  }
}
```

When the dialog would have appeared, the transcript instead shows "Allowed by PermissionRequest hook".

> The hook path stays in the current conversation. It can't clear context and start a fresh implementation session the way the manual `ExitPlanMode` dialog can.

## Switch permission mode at the same time

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PermissionRequest\", \"decision\": {\"behavior\": \"allow\", \"updatedPermissions\": [{\"type\": \"setMode\", \"mode\": \"acceptEdits\", \"destination\": \"session\"}]}}}'"
          }
        ]
      }
    ]
  }
}
```

This allows the call **and** switches the session into `acceptEdits` so edit prompts no longer fire. `destination: "session"` means this session only — it's never persisted as the default mode.

> `bypassPermissions` is only honored if the session was launched with bypass already available (`--dangerously-skip-permissions`, `permissionMode: bypassPermissions`, etc.). It is never persisted as `defaultMode`.

## Narrow further with a script

To approve `ExitPlanMode` only when the plan is short, use a script:

```bash
#!/bin/bash
INPUT=$(cat)
PLAN=$(echo "$INPUT" | jq -r '.tool_input.plan // empty')
LINES=$(echo "$PLAN" | wc -l)

if [ "$LINES" -le 20 ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"allow"}}}'
else
  # Long plan — fall through to user
  echo '{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"ask"}}}'
fi
```

## When this doesn't fire

- **`-p` / headless mode.** `PermissionRequest` is interactive-only. For automation, use `PreToolUse` with `permissionDecision: "allow"`.
- **Deny rules.** A `permissions.deny` entry matching the call still blocks, even if your hook says allow. Hooks tighten, never loosen.

## Safety

Hold the matcher as narrow as possible. Matching `.*` or leaving it empty auto-approves **every** permission prompt — file writes, shell commands, MCP tool calls. That's almost never what you want.
