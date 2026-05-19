# Audit configuration changes

**Goal.** Track every change to Claude Code settings or skills files during a session, for compliance or to spot unintended modifications.

**Event.** `ConfigChange` (fires when an external process or editor modifies a configuration file Claude Code watches).

**Scope.** Personal — `~/.claude/settings.json` so the audit applies to every project you work on.

**Matcher.** Empty (audit everything) or one of `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`.

## Append-only audit log

```json
{
  "hooks": {
    "ConfigChange": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -c '{timestamp: now | todate, source: .source, file: .file_path}' >> ~/claude-config-audit.log"
          }
        ]
      }
    ]
  }
}
```

Each line in `~/claude-config-audit.log` looks like:

```json
{"timestamp":"2026-05-19T14:21:38Z","source":"project_settings","file":"/Users/me/proj/.claude/settings.json"}
```

## Block specific changes

`ConfigChange` is one of the few non-tool events that **can be blocked**: exit 2 (or return `{"decision": "block"}`) and the change is not applied to the running session. Managed `policy_settings` changes are the exception: hooks still fire for audit logging, but blocking decisions are ignored.

```bash
#!/bin/bash
# .claude/hooks/forbid-project-settings-edits.sh
INPUT=$(cat)
SOURCE=$(echo "$INPUT" | jq -r '.source')

if [ "$SOURCE" = "project_settings" ]; then
  echo "Project settings changes require approval." >&2
  exit 2
fi
exit 0
```

Wire it up:

```json
{
  "hooks": {
    "ConfigChange": [
      {
        "matcher": "project_settings",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/forbid-project-settings-edits.sh" }
        ]
      }
    ]
  }
}
```

## Audit + alert

Pipe the JSON line to a Slack webhook (or whatever):

```bash
#!/bin/bash
INPUT=$(cat)
LINE=$(echo "$INPUT" | jq -c '{ts: now|todate, source, file: .file_path}')
echo "$LINE" >> ~/claude-config-audit.log
curl -sS -H 'Content-type: application/json' \
     --data "{\"text\": \"Claude config changed: $LINE\"}" \
     "$SLACK_WEBHOOK_URL"
```

Set `SLACK_WEBHOOK_URL` in your shell profile or in `~/.claude/settings.json`'s `env` block.

## Watch a single source

To only audit project-level edits (and ignore your own user settings tweaks):

```json
{ "matcher": "project_settings", "hooks": [ { "type": "command", "command": "..." } ] }
```

## When NOT to use this

`ConfigChange` fires when a file changes *during* a session, not for the initial load at startup. If you want to validate config on every session boot, use a `SessionStart` hook that lints / hashes the relevant files.
