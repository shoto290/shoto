# Template: db-reader with hook validation

Allows Bash access but uses a `PreToolUse` hook to permit only read-only SQL. Use this pattern when the `tools` field is too blunt — you want *some* operations of a tool but not others.

```markdown
---
name: db-reader
description: Execute read-only database queries. Use when analyzing data or generating reports.
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

You are a database analyst with read-only access. Execute SELECT queries to answer questions about the data.

When asked to analyze data:
1. Identify which tables contain the relevant data
2. Write efficient SELECT queries with appropriate filters
3. Present results clearly with context

You cannot modify data. If asked to INSERT, UPDATE, DELETE, or modify schema, explain that you only have read access.
```

The validation script at `./scripts/validate-readonly-query.sh`:

```bash
#!/bin/bash
# Blocks SQL write operations, allows SELECT queries

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Block write operations (case-insensitive)
if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|MERGE)\b' > /dev/null; then
  echo "Blocked: Write operations not allowed. Use SELECT queries only." >&2
  exit 2
fi

exit 0
```

`chmod +x ./scripts/validate-readonly-query.sh` after creating it.

Key design choices:
- `tools: Bash` — needed for `psql`, `mysql`, `bq`, etc.
- `hooks.PreToolUse` with `matcher: "Bash"` → runs before every Bash call.
- Hook exits with code 2 to **block** the call and feeds the stderr message to Claude as an error.
- Body explicitly tells the agent it's read-only so it doesn't try forbidden operations.

**Plugin restriction:** if you ship this in a plugin, the `hooks` field is silently dropped. Place it in `.claude/agents/` or `~/.claude/agents/` instead.

On Windows: rewrite the script in PowerShell and add `shell: powershell` to the hook entry.
