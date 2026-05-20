---
name: plugin
description: Author, package, test, and distribute a Claude Code plugin as a whole — the `plugin.json` manifest, plugin directory layout, local testing with `--plugin-dir` / `--plugin-url`, `/reload-plugins`, LSP servers (`.lsp.json`), background monitors (`monitors/monitors.json`), plugin-level `settings.json`, version management, marketplace distribution (`.claude-plugin/marketplace.json`), community-marketplace submission, and migration from a standalone `.claude/` directory. Use when the user wants to scaffold a new plugin, edit its manifest, validate or debug a plugin, ship it, submit it to `claude-plugins-official` or `claude-community`, or convert an existing `.claude/` setup. Not for authoring individual skills, sub-agents, or hooks — route those to the `skill`, `subagent`, and `hooks` skills.
argument-hint: '[action — e.g. "new", "validate", "migrate"]'
---

# Plugin

A **plugin** is a directory with a `.claude-plugin/plugin.json` manifest that bundles skills, sub-agents, hooks, MCP servers, LSP servers, background monitors, and default settings into a single distributable unit. Plugin skills are namespaced (`/plugin-name:skill-name`) so they don't clash with other plugins.

This skill covers the **plugin-level** concerns: manifest, layout, local testing, distribution. For authoring individual artifacts inside a plugin, route to:

- [skills/skill/SKILL.md](../skill/SKILL.md) — for `SKILL.md` files
- [skills/subagent/SKILL.md](../subagent/SKILL.md) — for sub-agent definitions
- [skills/hooks/SKILL.md](../hooks/SKILL.md) — for hook handlers
- [skills/evolve/SKILL.md](../evolve/SKILL.md) — when a change spans multiple artifact types inside an existing plugin

## Plugin vs Standalone `.claude/`

| Approach | Skill names | Best for |
| :-- | :-- | :-- |
| Standalone (`.claude/`) | `/hello` | Personal workflows, project-specific config, quick experiments |
| Plugin (`.claude-plugin/plugin.json`) | `/plugin-name:hello` | Sharing with a team, marketplace distribution, versioned releases, reuse across projects |

Start standalone for iteration; promote to a plugin once you want to share. See [reference/migration.md](./reference/migration.md) for the conversion path.

## Quickstart

Create a plugin called `my-first-plugin` with one skill, test it locally, hot-reload it.

```bash
mkdir -p my-first-plugin/.claude-plugin my-first-plugin/skills/hello
```

`my-first-plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "my-first-plugin",
  "description": "A greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

`my-first-plugin/skills/hello/SKILL.md`:

```markdown
---
description: Greet the user with a personalized message
---

Greet the user named "$ARGUMENTS" warmly and ask how you can help today.
```

Test:

```bash
claude --plugin-dir ./my-first-plugin
```

In the session:

```text
/my-first-plugin:hello Alex
```

Edit files, then `/reload-plugins` to pick up changes without restarting. For a full minimal example see [examples/minimal-plugin.md](./examples/minimal-plugin.md).

## Plugin Structure Overview

> **Common mistake:** Do NOT put `commands/`, `agents/`, `skills/`, or `hooks/` inside `.claude-plugin/`. Only `plugin.json` goes inside `.claude-plugin/`. All other directories live at the plugin root.

| Directory / file | Location | Purpose |
| :-- | :-- | :-- |
| `.claude-plugin/plugin.json` | Plugin root | Manifest. Required if you want metadata; optional when components use default locations. |
| `skills/` | Plugin root | Skills as `<name>/SKILL.md` directories. |
| `commands/` | Plugin root | Legacy flat-Markdown skills. Prefer `skills/` for new plugins. |
| `agents/` | Plugin root | Sub-agent definitions. |
| `hooks/hooks.json` | Plugin root | Event handlers. |
| `.mcp.json` | Plugin root | MCP server configurations. |
| `.lsp.json` | Plugin root | LSP server configurations. |
| `monitors/monitors.json` | Plugin root | Background monitor entries. |
| `bin/` | Plugin root | Executables added to the Bash `PATH` while the plugin is enabled. |
| `settings.json` | Plugin root | Default settings applied when the plugin is enabled. |

Full layout and examples: [reference/structure.md](./reference/structure.md).

## Adding Components

Plugins compose existing artifact types — they don't redefine them. To author each artifact, use the matching skill in this plugin:

| Component | Where it lives in the plugin | Authoring skill |
| :-- | :-- | :-- |
| Skill | `skills/<name>/SKILL.md` | [skills/skill/SKILL.md](../skill/SKILL.md) |
| Sub-agent | `agents/<name>.md` | [skills/subagent/SKILL.md](../subagent/SKILL.md) |
| Hook | `hooks/hooks.json` | [skills/hooks/SKILL.md](../hooks/SKILL.md) |
| Multi-artifact change | spans `skills/`, `agents/`, `hooks/` | [skills/evolve/SKILL.md](../evolve/SKILL.md) |

Plugin-level notes:

- The skill folder name (`skills/hello/`) becomes the slash command after namespacing: `/<plugin-name>:hello`.
- Sub-agents in `agents/` appear in `/agents` once the plugin is loaded.
- Hooks in `hooks/hooks.json` use the same schema as `settings.json` hooks — but live at `hooks/hooks.json`, not in `settings.json`.

## LSP Servers (`.lsp.json`)

Plugins can ship Language Server Protocol configurations for languages not covered by the official LSP plugins. Add a `.lsp.json` at the plugin root:

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

Users must install the language-server binary themselves. For common languages, prefer the official LSP plugins over rolling your own.

## Background Monitors (`monitors/monitors.json`)

Monitors are background commands whose stdout lines are delivered to Claude as notifications during the session. Claude Code starts each monitor automatically when the plugin is active.

```json
[
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log"
  }
]
```

See the official Monitors reference for `when` triggers and variable substitution.

## Default Settings (`settings.json`)

A plugin-level `settings.json` at the plugin root applies defaults when the plugin is enabled. Only the `agent` and `subagentStatusLine` keys are currently supported.

```json
{ "agent": "security-reviewer" }
```

This activates the plugin's `agents/security-reviewer.md` as the main-thread agent. Settings in `settings.json` take priority over `settings` declared in `plugin.json`. Unknown keys are silently ignored.

## Local Testing

```bash
claude --plugin-dir ./my-plugin
claude --plugin-dir ./my-plugin.zip                  # zip archive (v2.1.128+)
claude --plugin-url https://example.com/plugin.zip   # remote archive, session-only
```

Combine flags to load several plugins:

```bash
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
claude --plugin-url "https://example.com/a.zip https://example.com/b.zip"
```

When a `--plugin-dir` plugin shares a name with an installed marketplace plugin, the local copy wins for that session — except plugins force-enabled or force-disabled by managed settings.

During development, run `/reload-plugins` after edits. It reloads plugins, skills, agents, hooks, plugin MCP servers, and plugin LSP servers without restarting Claude Code.

## Debugging Checklist

1. **Structure** — directories at the plugin root, not inside `.claude-plugin/`.
2. **Manifest** — `plugin.json` parses as valid JSON, `name` is unique, kebab-case.
3. **Discovery** — `--plugin-dir <path>` points at the plugin root (the folder containing `.claude-plugin/`).
4. **Component-by-component** — test each skill via `/<plugin-name>:<skill-name>`; check agents in `/agents`; trigger hooks manually.
5. **Validate** — run `claude plugin validate` for the same check the community-marketplace pipeline uses.
6. **Reload** — `/reload-plugins` after every edit; restart Claude Code only when adding brand-new top-level directories.

## Sharing & Marketplace

When the plugin is ready to share:

1. Add a `README.md` with install / usage instructions.
2. Choose a versioning strategy — explicit `version` in `plugin.json` (recommended) or rely on the git commit SHA (every commit counts as a new version).
3. Publish through a marketplace (`.claude-plugin/marketplace.json`) — see [reference/distribution.md](./reference/distribution.md).
4. Pilot it with teammates before wider release.

Private marketplaces (private repos) keep the plugin internal; public marketplaces let anyone install with `/plugin install`.

## Community Marketplace Submission

Anthropic maintains two public marketplaces:

| Marketplace | Repo | How users add it | How plugins land in it |
| :-- | :-- | :-- | :-- |
| `claude-plugins-official` | curated by Anthropic | Auto-available in every Claude Code install | Anthropic curates at its discretion — no application form |
| `claude-community` | [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community) | `/plugin marketplace add anthropics/claude-plugins-community`, install as `@claude-community` | Submit via the in-app form below; review pipeline pins your plugin to a commit SHA |

Submission forms:

- Claude.ai — <https://claude.ai/settings/plugins/submit>
- Console — <https://platform.claude.com/plugins/submit>

Before submitting, run `claude plugin validate` locally — the review pipeline runs the same check plus automated safety screening. After approval, the community catalog syncs nightly and CI bumps the pinned SHA as you push new commits.

## Migration from Standalone `.claude/`

High-level steps (full version with the `hooks.json` `jq` example in [reference/migration.md](./reference/migration.md)):

1. Create the plugin scaffold (`mkdir -p my-plugin/.claude-plugin`) and write `plugin.json`.
2. Copy existing trees: `cp -r .claude/commands my-plugin/`, same for `agents/` and `skills/`.
3. Move hooks: create `my-plugin/hooks/hooks.json`, paste the `hooks` object from `.claude/settings.json`; the format is identical.
4. Test with `claude --plugin-dir ./my-plugin`.
5. Remove the originals from `.claude/` once the plugin version is confirmed working (plugin takes precedence either way).

| Standalone | Plugin |
| :-- | :-- |
| Available only in one project | Distributable via marketplace |
| Files in `.claude/commands/` | Files in `my-plugin/commands/` |
| Hooks in `settings.json` | Hooks in `hooks/hooks.json` |
| Manually copy to share | Install via `/plugin install` |

## Reference

- [reference/manifest-schema.md](./reference/manifest-schema.md) — every `plugin.json` field
- [reference/structure.md](./reference/structure.md) — full plugin directory layout
- [reference/distribution.md](./reference/distribution.md) — `marketplace.json` schema, version management, community submission
- [reference/migration.md](./reference/migration.md) — `.claude/` → plugin step-by-step with the `jq` hook example

## Examples

- [examples/minimal-plugin.md](./examples/minimal-plugin.md) — complete `my-first-plugin` source
