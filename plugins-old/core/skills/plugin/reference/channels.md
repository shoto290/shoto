# Channels

`channels` lets a plugin declare one or more message channels that INJECT CONTENT into the conversation (Telegram, Slack, Discord, etc.). Each channel binds to an MCP server the plugin provides.

## Example

```json
{
  "channels": [
    {
      "server": "telegram",
      "userConfig": {
        "bot_token": {
          "type": "string",
          "title": "Bot token",
          "description": "Telegram bot token",
          "sensitive": true
        },
        "owner_id": {
          "type": "string",
          "title": "Owner ID",
          "description": "Your Telegram user ID"
        }
      }
    }
  ]
}
```

## Rules

- `server` is required. It must match a key in the plugin's `mcpServers`.
- Optional per-channel `userConfig` uses the same schema as the top-level `userConfig`. See [reference/user-config.md](./user-config.md).
- The per-channel `userConfig` lets the plugin prompt for credentials (bot tokens, owner IDs) at enable time without polluting global user config.
