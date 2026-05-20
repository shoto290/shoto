# Installation Scopes

Scope determines where a plugin is available and who else can use it. The plugin scope system mirrors the rest of Claude Code's configuration.

## Scopes

| Scope | Settings file | Use case |
| :-- | :-- | :-- |
| `user` | `~/.claude/settings.json` | Personal, all projects (default). |
| `project` | `.claude/settings.json` | Team plugins, shared via version control. |
| `local` | `.claude/settings.local.json` | Project-specific, gitignored. |
| `managed` | Managed settings | Read-only. Force-enabled or force-disabled by enterprise policy. |

## Install at a specific scope

```bash
claude plugin install <plugin> --scope user
claude plugin install <plugin> --scope project
claude plugin install <plugin> --scope local
```

`--scope user` is the default and can be omitted.

## Force-enable / force-disable via managed settings

Local `--plugin-dir` plugins override marketplace plugins for the duration of the session — EXCEPT for plugins force-enabled or force-disabled by managed settings. Managed settings always win.
