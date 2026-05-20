# Plugin Directory Structure

## Rule of thumb

> Only `plugin.json` lives inside `.claude-plugin/`. Everything else — `skills/`, `agents/`, `commands/`, `hooks/`, `output-styles/`, `themes/`, `monitors/`, `bin/`, `.mcp.json`, `.lsp.json`, `settings.json` — lives at the **plugin root**.

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
├── output-styles/
│   └── concise.md
├── themes/                        # experimental
│   └── dracula.json
├── hooks/
│   └── hooks.json                 # same schema as settings.json `hooks` block
├── monitors/                      # experimental
│   └── monitors.json
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
| `.claude-plugin/plugin.json` | Required for metadata | Manifest. Optional when every component uses default locations and you don't need `name`/`version`. |
| `skills/<name>/SKILL.md` | Optional | One skill per folder. The folder name becomes `/<plugin-name>:<folder-name>`. |
| `commands/*.md` | Optional | Legacy flat-Markdown skill format. Don't use for new plugins. |
| `agents/<name>.md` | Optional | Sub-agent definitions with YAML frontmatter. Visible in `/agents`. |
| `output-styles/*.md` | Optional | Output-style presets surfaced via `/output-style`. |
| `themes/*.json` | Optional (experimental) | Color themes surfaced via `/theme`. See [reference/themes.md](./themes.md). |
| `hooks/hooks.json` | Optional | Event-handler config. Same schema as the `hooks` object in `settings.json`. |
| `.mcp.json` | Optional | MCP server configurations. |
| `.lsp.json` | Optional | LSP server configurations. |
| `monitors/monitors.json` | Optional (experimental) | Background-monitor entries. Each stdout line is sent to Claude as a notification. |
| `bin/` | Optional | Executables added to Bash `PATH` while the plugin is enabled. |
| `settings.json` | Optional | Plugin-level defaults. Currently supports `agent` and `subagentStatusLine`. Overrides `settings` declared in `plugin.json`. |
| `README.md` | Recommended | Install / usage docs. Required for community-marketplace submission. |

## Path behavior rules

When a manifest specifies a custom path for a component, behavior depends on which component it is.

**REPLACES the default**: `commands`, `agents`, `outputStyles`, `experimental.themes`, `experimental.monitors`.

To keep the default location AND additional dirs, list them explicitly:

```json
{
  "commands": ["./commands/", "./extras/"]
}
```

**ADDS to the default**: `skills`. The default `skills/` directory is always scanned; custom paths load alongside it.

**Own merge rules**: `hooks`, `mcpServers`, `lspServers`. Multiple sources combine.

Path requirements:

- All paths must be RELATIVE to the plugin root and start with `./`.
- When a `skills` entry points at a directory containing `SKILL.md` directly (e.g., `"skills": ["./"]` at the plugin root), the frontmatter `name` field determines the invocation name. Falls back to the directory basename if `name` is missing.
- v2.1.140+ surfaces ignored default folders in `/doctor`, `claude plugin list`, and the `/plugin` detail view when both the default location and a manifest key coexist.

## Single-skill plugin (v2.1.142+)

A plugin with `SKILL.md` at its root, no `skills/` subdirectory, and no `skills` manifest field is auto-loaded as a single-skill plugin. You do NOT need `"skills": ["./"]` for this layout.

```
my-skill-plugin/
├── .claude-plugin/
│   └── plugin.json
└── SKILL.md
```

Invocation name follows the same rule as any other skill: the frontmatter `name` field if present, otherwise the plugin directory basename.

## Executables (`bin/`)

Files in `bin/` are added to the Bash tool's PATH while the plugin is enabled. They become invokable as BARE COMMANDS in any Bash tool call:

```
my-plugin/
└── bin/
    └── my-cli
```

Useful for shipping a CLI alongside skills. Skills can then call `my-cli` directly without an absolute path.

## `CLAUDE.md` at plugin root

A `CLAUDE.md` at the plugin root is NOT loaded as project context. Plugins contribute context via skills, agents, and hooks — not via `CLAUDE.md`. Ship loading instructions inside a skill instead.

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
