# Environment Variables and Path Substitution

Claude Code provides three variables for referencing paths inside a plugin. All three are substituted INLINE in:

- Skill and agent content
- Hook commands
- Monitor commands
- MCP and LSP server configs

They are also exported as environment variables to hook subprocesses and MCP/LSP server subprocesses.

## Variables

| Variable | Description |
| :-- | :-- |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin install directory. Use for scripts, binaries, configs bundled with the plugin. In hook EXEC form: pass as a single argument with no quoting. In SHELL-form hooks and monitor commands: wrap in double quotes (`"${CLAUDE_PLUGIN_ROOT}"`). The path CHANGES when the plugin updates — the previous version's directory remains on disk for ~7 days. Treat as ephemeral. Do NOT write state there. |
| `${CLAUDE_PLUGIN_DATA}` | Persistent directory that SURVIVES updates. Use for installed dependencies (`node_modules`, virtual envs), generated code, caches. Auto-created on first reference. Resolves to `~/.claude/plugins/data/{id}/` where `{id}` is the plugin identifier with any character not in `[a-zA-Z0-9_-]` replaced by `-`. Example: `formatter@my-marketplace` → `~/.claude/plugins/data/formatter-my-marketplace/`. See [reference/persistent-data.md](./persistent-data.md). |
| `${CLAUDE_PROJECT_DIR}` | Project root. Same value as the `CLAUDE_PROJECT_DIR` env var hooks receive. Wrap in quotes for paths with spaces. MCP servers can also call `roots/list` for the same info. |

## Mid-session updates

When a plugin updates mid-session, hook commands, monitor commands, MCP servers, and LSP servers keep using the previous version's path. To switch to the new version:

- `/reload-plugins` — refreshes hooks, MCP servers, and LSP servers to the new path.
- MONITORS require a full session restart — `/reload-plugins` is not enough.

## User config substitution

`${user_config.KEY}` is also substituted in MCP/LSP configs, hook commands, and monitor commands. Non-sensitive values are substituted in skill and agent content too. See [reference/user-config.md](./user-config.md).

## Example

PostToolUse hook command using a script bundled with the plugin:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/process.sh" }
        ]
      }
    ]
  }
}
```
