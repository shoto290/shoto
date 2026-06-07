---
name: plugin
description: 'Author, package, test, and distribute a whole Claude Code plugin and its manifest — scaffold the directory, write the plugin.json, bundle skills/subagents/hooks/MCP, and ship it.'
when_to_use: 'When packaging, scaffolding, or shipping a plugin as a whole: create a new plugin and its plugin.json manifest, lay out the directory, validate it, distribute it through a marketplace, or migrate an existing plugin. For a single skill, subagent, hook, or project MCP inside it, route to the matching author.'
argument-hint: '[action — e.g. "new", "validate", "migrate"]'
---

# Plugin

A **plugin** is a directory with a `.claude-plugin/plugin.json` manifest that bundles skills, sub-agents, hooks, MCP servers, LSP servers, background monitors, color themes, output styles, and default settings into a single distributable unit. Plugin components are namespaced (`/<plugin-name>:<component-name>`) so they don't clash with other plugins.

This skill covers the **plugin-level** concerns: manifest, layout, local testing, distribution. For authoring individual artifacts inside a plugin, route to:

- [skills/skill/SKILL.md](../skill/SKILL.md) — for `SKILL.md` files
- [skills/subagent/SKILL.md](../subagent/SKILL.md) — for sub-agent definitions
- [skills/hooks/SKILL.md](../hooks/SKILL.md) — for hook handlers
- [skills/mcp/SKILL.md](../mcp/SKILL.md) — for project-level MCP servers (`.mcp.json` at the repo root, `claude mcp add`). This skill owns MCP **bundled inside a plugin** (`.mcp.json` at the plugin root, `mcpServers` in `plugin.json`).
- [skills/evolve/SKILL.md](../evolve/SKILL.md) — when a change spans multiple artifact types

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

Edit files, then `/reload-plugins` to pick up changes without restarting. For a full minimal walkthrough see [reference/minimal-plugin.md](./reference/minimal-plugin.md). For the bare scaffold Claude produces, see [examples/plugin-scaffold-output.md](./examples/plugin-scaffold-output.md).

## Single-skill plugin

A plugin with `SKILL.md` at its root, no `skills/` subdirectory, and no `skills` field in the manifest is auto-loaded as a single-skill plugin (v2.1.142+). You do NOT need `"skills": ["./"]` for this layout. Invocation name comes from the frontmatter `name` field, or the plugin directory basename if `name` is missing. See [reference/structure.md](./reference/structure.md).

## Plugin Structure

> **Common mistake:** Do NOT put `commands/`, `agents/`, `skills/`, `hooks/`, `themes/`, or `output-styles/` inside `.claude-plugin/`. Only `plugin.json` goes inside `.claude-plugin/`. All other directories live at the plugin root.

| Directory / file | Location | Purpose |
| :-- | :-- | :-- |
| `.claude-plugin/plugin.json` | Plugin root | Manifest. |
| `skills/<name>/SKILL.md` | Plugin root | Skills as folders. |
| `commands/*.md` | Plugin root | Legacy flat-Markdown skills. Prefer `skills/`. |
| `agents/<name>.md` | Plugin root | Sub-agent definitions. |
| `output-styles/*.md` | Plugin root | Output-style presets. |
| `themes/*.json` | Plugin root | Experimental color themes. |
| `hooks/hooks.json` | Plugin root | Event handlers. |
| `.mcp.json` | Plugin root | MCP server configurations. |
| `.lsp.json` | Plugin root | LSP server configurations. |
| `monitors/monitors.json` | Plugin root | Experimental background monitors. |
| `bin/` | Plugin root | Executables added to `PATH` while the plugin is enabled. |
| `settings.json` | Plugin root | Default settings applied when the plugin is enabled. |

Full layout, path-behavior rules, and the single-skill / `bin/` / `CLAUDE.md` details: [reference/structure.md](./reference/structure.md).

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
- Hooks in `hooks/hooks.json` use the same schema as `settings.json` hooks.

## Manifest

Minimal `plugin.json`:

```json
{
  "name": "my-first-plugin",
  "description": "A greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

Only `name` is required. See [reference/manifest-schema.md](./reference/manifest-schema.md) for every field, including `displayName`, `$schema`, `keywords`, `userConfig`, `channels`, `dependencies`, and `experimental.*`. Unrecognized top-level fields are tolerated for compatibility with `package.json` and similar manifests — pass `--strict` to `claude plugin validate` to escalate those warnings to errors.

## User Configuration

Declare values Claude Code prompts the user for at enable time. The values are substituted as `${user_config.KEY}` in MCP/LSP configs, hook commands, and monitor commands, and exported as `CLAUDE_PLUGIN_OPTION_<KEY>` to subprocesses. See [reference/user-config.md](./reference/user-config.md).

## Dependencies

Declare other plugins this plugin requires with optional semver constraints. Enabling pulls dependencies in transitively at the same scope; disabling fails when other plugins still depend on the target. See [reference/dependencies.md](./reference/dependencies.md).

## Environment Variables

| Variable | Description |
| :-- | :-- |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install directory. CHANGES on every update — treat as ephemeral. |
| `${CLAUDE_PLUGIN_DATA}` | Persistent directory that survives updates. Use for installed deps and caches. |
| `${CLAUDE_PROJECT_DIR}` | Project root (same as the `CLAUDE_PROJECT_DIR` env var hooks receive). |

Full substitution rules, mid-session update behavior, and the dependency-install pattern: [reference/env-vars.md](./reference/env-vars.md) and [reference/persistent-data.md](./reference/persistent-data.md).

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

Monitors are experimental — declare via `experimental.monitors` in `plugin.json`. Adding a new monitor or editing a monitor command requires a session restart, not just `/reload-plugins`.

## Default Settings (`settings.json`)

A plugin-level `settings.json` at the plugin root applies defaults when the plugin is enabled. Only the `agent` and `subagentStatusLine` keys are currently supported.

```json
{ "agent": "security-reviewer" }
```

Settings in `settings.json` take priority over `settings` declared in `plugin.json`. Unknown keys are silently ignored.

## Themes

Experimental: plugins can ship color themes under `themes/` and declare them with `experimental.themes`. Themes appear in `/theme` alongside built-in presets. See [reference/themes.md](./reference/themes.md).

## Installation Scopes

| Scope | Settings file | Use case |
| :-- | :-- | :-- |
| `user` | `~/.claude/settings.json` | Personal, all projects (default). |
| `project` | `.claude/settings.json` | Team plugins, version-controlled. |
| `local` | `.claude/settings.local.json` | Project-specific, gitignored. |
| `managed` | Managed settings | Read-only, force-enabled / force-disabled by policy. |

Install at a scope with `claude plugin install <plugin> --scope <user|project|local>`. See [reference/scopes.md](./reference/scopes.md).

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

During development, run `/reload-plugins` after edits. It reloads plugins, skills, agents, hooks, plugin MCP servers, and plugin LSP servers without restarting Claude Code. Monitors require a full restart.

## CLI Overview

- `claude plugin install <plugin>` — install from a marketplace.
- `claude plugin uninstall <plugin>` — uninstall (aliases: `remove`, `rm`). `--keep-data` preserves persistent data.
- `claude plugin list` — list installed plugins.
- `claude plugin details <name>` — component inventory + projected token cost.
- `claude plugin enable <plugin>` / `disable <plugin>` — toggle without uninstalling.
- `claude plugin update <plugin>` — update to latest.
- `claude plugin prune` — remove orphaned auto-installed deps.
- `claude plugin tag` — create a release git tag for semver resolution.
- `claude plugin validate` — manifest + frontmatter + hooks validation. `--strict` escalates warnings.

Full reference with every option: [reference/cli-commands.md](./reference/cli-commands.md).

## Plugin Caching

Marketplace plugins are COPIED into `~/.claude/plugins/cache` rather than used in place. Each installed version is a separate directory; on update or uninstall, the previous version is orphaned and removed automatically after 7 days. Installed plugins cannot reference files outside their directory (`../shared-utils` does NOT work). Symlinks within the same marketplace are dereferenced into the cache. See [reference/caching.md](./reference/caching.md).

## Debugging Checklist

1. **Structure** — directories at the plugin root, not inside `.claude-plugin/`.
2. **Manifest** — `plugin.json` parses as valid JSON, `name` is unique, kebab-case.
3. **Discovery** — `--plugin-dir <path>` points at the plugin root (the folder containing `.claude-plugin/`).
4. **Component-by-component** — test each skill via `/<plugin-name>:<skill-name>`; check agents in `/agents`; trigger hooks manually.
5. **Validate** — run `claude plugin validate` for the same check the community-marketplace pipeline uses.
6. **Reload** — `/reload-plugins` after every edit; restart Claude Code only when adding brand-new top-level directories or changing monitors.

Full troubleshooting reference (manifest errors, hook script issues, MCP startup failures, restart matrix): [reference/debugging.md](./reference/debugging.md).

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

- [reference/manifest-schema.md](./reference/manifest-schema.md) — every `plugin.json` field including `userConfig`, `channels`, `dependencies`, `experimental.*`, and the unrecognized-fields rule.
- [reference/structure.md](./reference/structure.md) — full plugin directory layout, path-behavior rules, single-skill plugin, `bin/`, `CLAUDE.md`.
- [reference/distribution.md](./reference/distribution.md) — `marketplace.json` schema, version management, community submission.
- [reference/migration.md](./reference/migration.md) — `.claude/` → plugin step-by-step with the `jq` hook example.
- [reference/minimal-plugin.md](./reference/minimal-plugin.md) — complete `my-first-plugin` walkthrough.
- [reference/env-vars.md](./reference/env-vars.md) — `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` / `${CLAUDE_PROJECT_DIR}` substitution rules and mid-session update behavior.
- [reference/persistent-data.md](./reference/persistent-data.md) — dependency-install pattern with `SessionStart` + `diff -q`, cleanup behavior.
- [reference/scopes.md](./reference/scopes.md) — user / project / local / managed scopes.
- [reference/caching.md](./reference/caching.md) — `~/.claude/plugins/cache`, version directories, 7-day orphan grace, symlink handling.
- [reference/cli-commands.md](./reference/cli-commands.md) — every `claude plugin <subcommand>` with args and options.
- [reference/user-config.md](./reference/user-config.md) — `userConfig` schema, substitution sites, sensitive-value storage.
- [reference/channels.md](./reference/channels.md) — channel declarations bound to an MCP server.
- [reference/dependencies.md](./reference/dependencies.md) — `dependencies` field, enable/disable behavior, auto-installed deps, prune.
- [reference/themes.md](./reference/themes.md) — experimental color themes shipped via `experimental.themes`.
- [reference/debugging.md](./reference/debugging.md) — `claude --debug`, common errors, hook/MCP troubleshooting, restart matrix.

## Examples

- [examples/plugin-scaffold-output.md](./examples/plugin-scaffold-output.md) — bare scaffold output (directory tree + `plugin.json` + stub `SKILL.md`).
