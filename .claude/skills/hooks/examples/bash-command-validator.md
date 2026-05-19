# Bash command validator

**Goal.** Block dangerous Bash commands (`rm -rf /`, `drop table`, `git push --force` to main) before they run, with a structured deny reason returned to Claude. Allow everything else.

**Event.** `PreToolUse`

**Scope.** Project — `.claude/settings.json` + `.claude/hooks/validate-bash.sh`.

**Matcher.** `Bash` to limit to Bash tool calls.

**Output mode.** Stdout JSON (`hookSpecificOutput.permissionDecision: "deny"`). More structured than `exit 2`, and Claude sees the reason as a tool error so it can adapt.

## Script

`.claude/hooks/validate-bash.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

deny() {
  jq -n --arg reason "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

# Patterns to block
if echo "$CMD" | grep -qE '\brm\b.*-r[fF]?\b'; then
  deny "rm -r/-rf is blocked. Use a script that lists files for review first."
fi

if echo "$CMD" | grep -qiE 'drop\s+(table|database|schema)'; then
  deny "Destructive SQL ('drop table/database/schema') is blocked. Migrate via the migration tool instead."
fi

if echo "$CMD" | grep -qE '\bgit\s+push\b' \
  && echo "$CMD" | grep -qE '(^|[[:space:]])(--force|-f|--force-with-lease)([[:space:]]|$)' \
  && echo "$CMD" | grep -qE '(^|[[:space:]])(main|master)([[:space:]]|$)'; then
  deny "Force-push to main/master is blocked. Open a PR or push to a feature branch."
fi

exit 0
```

`chmod +x .claude/hooks/validate-bash.sh`.

## Hook config

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-bash.sh"
          }
        ]
      }
    ]
  }
}
```

## Why JSON output here

Two reasons:

1. **Structured reason.** `permissionDecisionReason` is delivered to Claude as the tool error, formatted clearly. With `exit 2` you only get the first line of stderr in the transcript notice.
2. **Future flexibility.** Same script can also return `"ask"` (escalate to user) or `"allow"` (skip prompt), not just allow/deny.

## Composing with `if`

For per-subcommand routing, use `if` at the handler level so the script only runs when relevant:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "if": "Bash(rm *)",
      "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-rm.sh"
    },
    {
      "type": "command",
      "if": "Bash(git push *)",
      "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-push.sh"
    }
  ]
}
```

Compound Bash like `rm -rf /tmp && git push` triggers **both** handlers (each subcommand evaluated independently). The most restrictive answer wins per `deny > defer > ask > allow`.

## Unit-test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"}}' \
  | ./.claude/hooks/validate-bash.sh
# Expect a JSON object with permissionDecision: "deny" and a reason.
```
