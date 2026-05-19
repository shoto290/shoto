# Format on save

**Goal.** Run Prettier on every file Claude edits so formatting stays consistent without manual intervention.

**Event.** `PostToolUse`

**Scope.** Project — add to `.claude/settings.json` so the rule travels with the repo.

**Matcher.** `Edit|Write` so the hook only fires after file-editing tools, not after `Bash`, `Read`, etc.

## Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. After the `Edit` or `Write` succeeds, Claude Code feeds the event JSON to the hook's stdin.
2. `jq -r '.tool_input.file_path'` extracts just the path.
3. `xargs npx prettier --write` formats that file in place.
4. The hook exits 0; the formatted file replaces the edited one.

## Variations

- **Different formatter:** swap `npx prettier --write` for `ruff format -`, `cargo fmt --`, `gofmt -w`, etc.
- **Multiple matchers:** `"matcher": "Edit|Write|NotebookEdit"` to catch notebook edits too.
- **Per-extension:** wrap in a script and switch on file extension. Save as `.claude/hooks/format.sh`:
  ```bash
  #!/bin/bash
  FILE=$(jq -r '.tool_input.file_path')
  case "$FILE" in
    *.ts|*.tsx|*.js|*.jsx) npx prettier --write "$FILE" ;;
    *.py)                  ruff format "$FILE" ;;
    *.go)                  gofmt -w "$FILE" ;;
  esac
  ```
  `chmod +x` and call via `"$CLAUDE_PROJECT_DIR"/.claude/hooks/format.sh`.

## Caveats

- `PostToolUse` cannot undo a write that already happened — this hook reformats, but if the write was destructive the change is already on disk.
- The hook runs after every edit, including many tiny ones. If your formatter is slow, consider a `Stop` hook that formats once per turn instead.
- `Bash`-driven file changes (Claude using `sed`, `cat >`, etc.) don't trigger `Edit|Write`. To catch those too, add a `Stop` hook that runs `git status --porcelain | awk '{print $2}' | xargs npx prettier --write`.
