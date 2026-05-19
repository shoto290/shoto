# Block edits to protected files

**Goal.** Prevent Claude from modifying sensitive files like `.env`, `package-lock.json`, or anything under `.git/`. Block the call before it runs and give Claude a reason so it can adjust.

**Event.** `PreToolUse`

**Scope.** Project — `.claude/settings.json` plus a script at `.claude/hooks/protect-files.sh`.

**Matcher.** `Edit|Write` so we only check file-editing tools.

## Script

Save to `.claude/hooks/protect-files.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

PROTECTED_PATTERNS=(".env" "package-lock.json" ".git/")

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: $FILE_PATH matches protected pattern '$pattern'" >&2
    exit 2
  fi
done

exit 0
```

Make it executable:

```bash
chmod +x .claude/hooks/protect-files.sh
```

## Hook config

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Before the `Edit` or `Write` runs, Claude Code pipes the event JSON to the script.
2. The script extracts `tool_input.file_path` with `jq`.
3. If the path matches any protected pattern, the script writes the reason to stderr and `exit 2`s — Claude Code blocks the call and shows Claude the stderr.
4. Otherwise `exit 0` and the edit proceeds.

## Why a script, not inline

Could you do this with a one-liner? Sure — but multi-line shell inside JSON is painful, profile leaks can corrupt stdout, and you can't unit-test it. A script file is cleaner:

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":".env"}}' \
  | ./.claude/hooks/protect-files.sh
echo $?   # 2
```

## Stronger alternative: permission rules

For pure path-based blocks, **permission `deny` rules** are simpler and unbypassable:

```json
{ "permissions": { "deny": ["Edit(.env)", "Write(.env)", "Edit(.git/**)"] } }
```

Hooks are the better fit when the decision involves logic the rule engine can't express — e.g. "block edits to any file matching `*.lock` *unless* the user is in the `infra` group".

## Catching Bash-driven file writes

This hook only guards `Edit` and `Write`. If you want to also block `Bash`-driven writes (`sed -i`, `cat >`, …), add a second handler:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "if": "Bash(* .env*)",
      "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-bash-write.sh"
    }
  ]
}
```

The `if` filter limits the hook process spawn to commands that look like they touch `.env*`. Requires Claude Code v2.1.85+.
