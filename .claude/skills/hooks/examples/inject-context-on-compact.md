# Re-inject context after compaction

**Goal.** When Claude's context window fills up, it gets compacted into a summary — and that summary often loses important project conventions. A `SessionStart` hook with `matcher: "compact"` re-injects critical context every time compaction fires.

**Event.** `SessionStart`

**Scope.** Project — `.claude/settings.json` so the reminders are repo-specific.

**Matcher.** `compact` so the hook only fires after compaction, not at every session start (use `CLAUDE.md` for always-on context).

**Output mode.** `exit 0` + stdout text. Whatever you write to stdout is appended to Claude's context.

## Minimal config

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Reminder: use Bun, not npm. Run bun test before committing. Current sprint: auth refactor.'"
          }
        ]
      }
    ]
  }
}
```

## Dynamic context

Stdout can be any command, so you can re-inject *current* state:

```json
{
  "type": "command",
  "command": "git log --oneline -10 && echo '---' && git status --porcelain"
}
```

…or a script that assembles whatever the project needs:

```bash
#!/bin/bash
# .claude/hooks/post-compact-context.sh
echo "=== Project conventions ==="
cat "$CLAUDE_PROJECT_DIR/.claude/CONVENTIONS.md" 2>/dev/null
echo ""
echo "=== Recent commits ==="
git -C "$CLAUDE_PROJECT_DIR" log --oneline -10
echo ""
echo "=== Open TODOs in working tree ==="
grep -rnE 'TODO|FIXME' "$CLAUDE_PROJECT_DIR/src" 2>/dev/null | head -20
```

## Cover both startup and compact

If you want the same context delivered at startup *and* after compaction, register two groups:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|compact",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/load-context.sh" }
        ]
      }
    ]
  }
}
```

But for *always-on* context, prefer `CLAUDE.md` — it's the documented mechanism and doesn't run a shell command on every session boot.

## Other useful `SessionStart` patterns

- **direnv reload**: `direnv export bash > "$CLAUDE_ENV_FILE"` (also wire `CwdChanged` for per-directory env)
- **Print branch info**: `echo "Working on branch: $(git branch --show-current)"`
- **Inject pinned doc**: `cat "$CLAUDE_PROJECT_DIR/docs/HOOKS-CHEATSHEET.md"`

## Why not `UserPromptSubmit`?

`UserPromptSubmit` fires on every prompt — using it for context injection makes Claude re-read the same text dozens of times per session and tanks context efficiency. Reserve it for *prompt-specific* context (e.g. "if the user mentions X, also include Y").

## Plain stdout is the documented path

For `SessionStart`, the official docs describe stdout becoming Claude's context. Stick to `echo` / scripts that print to stdout. `additionalContext` is documented for `UserPromptSubmit`; if you want similar behavior for `SessionStart`, check the live `/en/hooks` reference first.
