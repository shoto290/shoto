# Plugin Directory Structure

## Rule of thumb

> Only `plugin.json` lives inside `.claude-plugin/`. Everything else — `skills/`, `agents/`, `hooks/`, `.mcp.json`, `.lsp.json`, `monitors/`, `bin/`, `settings.json` — lives at the **plugin root**.

## Full layout

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                # manifest (name, description, version, ...)
├── skills/
│   ├── code-review/
│   │   └── SKILL.md
│   └── deploy/
│       ├── SKILL.md
│       └── scripts/
│           └── run.sh
├── commands/                      # legacy flat-Markdown skills — prefer skills/ for new plugins
│   └── legacy.md
├── agents/
│   ├── security-reviewer.md
│   └── doc-writer.md
├── hooks/
│   └── hooks.json                 # same schema as settings.json `hooks` block
├── monitors/
│   └── monitors.json              # background watchers
├── bin/                           # added to PATH while plugin is enabled
│   └── my-cli
├── .mcp.json                      # MCP servers
├── .lsp.json                      # LSP servers
├── settings.json                  # plugin-level defaults (agent, subagentStatusLine)
└── README.md                      # install + usage docs
```

## Directory reference

| Path | Required | Purpose |
| :-- | :-- | :-- |
| `.claude-plugin/plugin.json` | Required for metadata | Manifest. Optional when every component uses default locations and you don't need a `name`/`version`. |
| `skills/<name>/SKILL.md` | Optional | One skill per folder. The folder name becomes `/<plugin-name>:<folder-name>`. |
| `commands/*.md` | Optional | Legacy flat-Markdown skill format. Don't use for new plugins. |
| `agents/<name>.md` | Optional | Sub-agent definitions with YAML frontmatter. Visible in `/agents`. |
| `hooks/hooks.json` | Optional | Event-handler config. Same schema as the `hooks` object in `settings.json`. |
| `.mcp.json` | Optional | MCP server configurations. |
| `.lsp.json` | Optional | LSP server configurations. |
| `monitors/monitors.json` | Optional | Background-monitor entries. Each stdout line is sent to Claude as a notification. |
| `bin/` | Optional | Executables added to Bash `PATH` while the plugin is enabled. |
| `settings.json` | Optional | Plugin-level defaults. Currently supports `agent` and `subagentStatusLine`. Overrides `settings` declared in `plugin.json`. |
| `README.md` | Recommended | Install / usage docs. Especially required for community-marketplace submission. |

## Skill folder example

```
skills/code-review/
├── SKILL.md
├── reference/
│   └── checklist.md
└── examples/
    └── sample-review.md
```

For SKILL.md authoring, route to [skills/skill/SKILL.md](../../skill/SKILL.md).

## Hook config example

`hooks/hooks.json` uses the exact `hooks` object you would put in `settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npm run lint:fix" }
        ]
      }
    ]
  }
}
```

For hook authoring, route to [skills/hooks/SKILL.md](../../hooks/SKILL.md).

## Organizing large plugins

Group by feature when the plugin grows beyond a handful of artifacts. Skill folders can hold their own `reference/`, `examples/`, `scripts/`, and `assets/` subdirectories — Claude only loads `SKILL.md` plus whatever it explicitly links.
