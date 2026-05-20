# Plugin CLI Commands

Every command runs as `claude plugin <subcommand>`. Scopes are `user`, `project`, `local`, or `managed` (read-only). See [reference/scopes.md](./scopes.md).

## `claude plugin install <plugin>`

Install a plugin from a marketplace.

| Argument / option | Description |
| :-- | :-- |
| `<plugin>` | Plugin name, or `name@marketplace`. |
| `-s, --scope <user\|project\|local>` | Default `user`. |
| `-h, --help` | Show help. |

```bash
claude plugin install security-toolkit
claude plugin install security-toolkit@acme --scope project
claude plugin install security-toolkit --scope local
```

## `claude plugin uninstall <plugin>`

Aliases: `remove`, `rm`.

| Option | Description |
| :-- | :-- |
| `-s, --scope <user\|project\|local>` | Default `user`. |
| `--keep-data` | Preserve the persistent data directory. |
| `--prune` | Also remove auto-installed dependencies no other plugin needs. |
| `-y, --yes` | Skip confirmation. Required when stdin/stdout is not a TTY. |
| `-h, --help` | Show help. |

By default, uninstalling from the LAST remaining scope also deletes the persistent data directory (`${CLAUDE_PLUGIN_DATA}`). `--keep-data` preserves it.

## `claude plugin prune`

Alias: `autoremove`. Removes auto-installed dependencies no longer required by any installed plugin. Directly-installed plugins are never touched.

Requires v2.1.121+.

| Option | Description |
| :-- | :-- |
| `-s, --scope <user\|project\|local>` | Scope to prune. |
| `--dry-run` | Print what would be removed without removing it. |
| `-y, --yes` | Skip confirmation. |
| `-h, --help` | Show help. |

## `claude plugin enable <plugin>`

Enable a previously disabled plugin.

If the plugin has `dependencies`, Claude Code enables them transitively at the same scope. The command fails when a dependency is not installed — install it first.

| Option | Description |
| :-- | :-- |
| `-s, --scope <user\|project\|local>` | Scope to enable in. |
| `-h, --help` | Show help. |

## `claude plugin disable <plugin>`

Disable an enabled plugin.

Fails when another enabled plugin depends on the target. The error message includes a chained command to disable every dependent first.

| Option | Description |
| :-- | :-- |
| `-s, --scope <user\|project\|local>` | Scope to disable in. |
| `-h, --help` | Show help. |

## `claude plugin update <plugin>`

Update a plugin to the latest version available from its marketplace.

| Option | Description |
| :-- | :-- |
| `-s, --scope <user\|project\|local\|managed>` | Scope to update. |
| `-h, --help` | Show help. |

## `claude plugin list`

List installed plugins.

| Option | Description |
| :-- | :-- |
| `--json` | Machine-readable output. |
| `--available` | Also list plugins available in connected marketplaces. Requires `--json`. |
| `-h, --help` | Show help. |

## `claude plugin details <name>`

Show a plugin's COMPONENT INVENTORY and projected token cost. Components are grouped as Skills (includes both `skills/` and `commands/`), Agents, Hooks, MCP servers, and LSP servers.

Two cost figures per plugin:

- **Always-on** — tokens added to EVERY session (the listing text — skill descriptions, agent descriptions, command names).
- **On-invoke** — tokens a component costs when it fires, computed per component.

Example output:

```text
security-guidance@acme  1.2.0

  Always-on cost: 412 tokens (descriptions in every session)

  Skills (3)
    review-pr           on-invoke: 1,840 tokens
    audit-secrets       on-invoke:   980 tokens
    threat-model        on-invoke: 2,310 tokens

  Agents (1)
    security-reviewer   on-invoke: 1,120 tokens

  Hooks (2)
    PostToolUse:Write   command hook
    SessionStart        command hook
```

The always-on total is computed via the `count_tokens` API for the active model; per-component figures are scaled proportionally. Falls back to a character-based estimate when the API is unreachable.

## `claude plugin tag`

Create a release git tag. Run from inside the plugin folder.

| Option | Description |
| :-- | :-- |
| `--push` | Push the tag to the configured remote. |
| `--dry-run` | Print the tag that would be created without creating it. |
| `-f, --force` | Overwrite an existing tag with the same name. |
| `-h, --help` | Show help. |

## `claude plugin validate`

Validate the manifest, skill/agent frontmatter, and `hooks.json`. Recommended in CI before publishing.

| Option | Description |
| :-- | :-- |
| `--strict` | Treat warnings (e.g. unrecognized manifest fields, top-level `themes`/`monitors`) as errors. |
| `-h, --help` | Show help. |

```bash
claude plugin validate ./my-plugin --strict
```

## `claude --debug`

Not a `plugin` subcommand, but the primary debugging entry point. Shows plugin loading details: which plugins loaded, manifest errors, skill/agent/hook registration, and MCP server initialization.
