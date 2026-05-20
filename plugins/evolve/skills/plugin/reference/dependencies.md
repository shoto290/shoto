# Plugin Dependencies

The `dependencies` field declares OTHER PLUGINS this plugin requires, optionally with semver constraints.

## Example

```json
{
  "dependencies": [
    "helper-lib",
    { "name": "secrets-vault", "version": "~2.1.0" }
  ]
}
```

Two forms:

- **String** — just the plugin name. Any version is acceptable.
- **Object** — `{ "name": "...", "version": "..." }` with a semver constraint (`^`, `~`, `>=`, exact version).

## Enable / disable behavior

- `claude plugin enable <plugin>` — Claude Code enables dependencies transitively at the same scope. The command fails when a dependency is not installed; install it first.
- `claude plugin disable <plugin>` — fails when another enabled plugin DEPENDS on the target. The error message includes a chained command to disable every dependent first.

## Auto-installed dependencies

- Claude Code can auto-install dependencies to satisfy another plugin's `dependencies` list.
- `claude plugin prune` (alias `autoremove`) removes auto-installed dependencies no longer required by any installed plugin.
- Directly-installed plugins are NEVER touched by `prune`.
- `claude plugin uninstall <plugin> --prune` removes the plugin AND prunes orphaned dependencies in one step.

See [reference/cli-commands.md](./cli-commands.md) for the full flag list.

## Tag plugin releases for version resolution

Semver constraints resolve against git tags. Use `claude plugin tag` to create release tags from inside the plugin folder. See [reference/cli-commands.md](./cli-commands.md) for `claude plugin tag` options.
