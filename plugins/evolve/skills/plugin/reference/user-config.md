# User Configuration (`userConfig`)

`userConfig` declares values Claude Code PROMPTS THE USER for when the plugin is enabled. Use it instead of requiring users to hand-edit `settings.json`.

## Example

```json
{
  "userConfig": {
    "api_endpoint": {
      "type": "string",
      "title": "API endpoint",
      "description": "Your team's API endpoint"
    },
    "api_token": {
      "type": "string",
      "title": "API token",
      "description": "API authentication token",
      "sensitive": true
    }
  }
}
```

Keys must be valid identifiers. Each option supports the following fields.

| Field | Required | Description |
| :-- | :-- | :-- |
| `type` | Yes | One of `string`, `number`, `boolean`, `directory`, `file`. |
| `title` | Yes | Label shown in the config dialog. |
| `description` | Yes | Help text shown below the field. |
| `sensitive` | No | If `true`, input is masked and stored in secure storage (system keychain, falls back to `~/.claude/.credentials.json`). |
| `required` | No | If `true`, validation fails when the field is empty. |
| `default` | No | Value used when the user provides nothing. |
| `multiple` | No | For `string` type, allows an array of strings. |
| `min` / `max` | No | Numeric bounds for `number`. |

## Where values are substituted

- `${user_config.KEY}` is substituted in MCP/LSP server configs, hook commands, and monitor commands.
- Non-sensitive values are also substituted in skill and agent content.
- All values are exported as `CLAUDE_PLUGIN_OPTION_<KEY>` environment variables to plugin subprocesses (hooks, MCP/LSP servers, monitors).

## Storage

- Non-sensitive values are stored in `settings.json` under `pluginConfigs[<plugin-id>].options`.
- Sensitive values go to the system keychain (or `~/.claude/.credentials.json` where keychain storage is unavailable).
- Keychain storage is shared with OAuth tokens. Total ~2 KB limit — keep sensitive values small.
