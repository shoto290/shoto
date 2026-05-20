# Persistent Data Directory

`${CLAUDE_PLUGIN_DATA}` exists so plugins have a stable location that outlives any single version. The common use case: install language dependencies once and reuse them across sessions and updates, since `${CLAUDE_PLUGIN_ROOT}` is replaced on every update.

## Dependency-install pattern

Directory existence alone cannot detect when an update changes the dependencies. The recommended pattern: compare the bundled manifest to the copy in the data directory and reinstall when they differ.

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\""
          }
        ]
      }
    ]
  }
}
```

How it works:

- `diff -q` exits non-zero on first run (no manifest copy yet) OR when the bundled manifest changed. Both cases trigger a fresh install.
- If `npm install` fails, the trailing `rm` removes the copied manifest so the next session retries.

## Using the persisted dependencies

The matching MCP server config consumes the installed `node_modules` via `NODE_PATH`:

```json
{
  "mcpServers": {
    "routines": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
      "env": { "NODE_PATH": "${CLAUDE_PLUGIN_DATA}/node_modules" }
    }
  }
}
```

Same pattern works for Python (`pip install -r requirements.txt` + `PYTHONPATH`), Ruby, etc.

## Cleanup

The data directory is deleted automatically when the plugin is uninstalled from the LAST scope.

- The `/plugin` UI shows the data directory size and prompts before deletion.
- The CLI deletes by default. Pass `--keep-data` to preserve it.

See [reference/cli-commands.md](./cli-commands.md) for `claude plugin uninstall` flags.
