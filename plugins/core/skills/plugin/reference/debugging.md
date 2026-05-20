# Debugging and Troubleshooting

## Debug command

```bash
claude --debug
```

Shows plugin loading details: which plugins loaded, manifest errors, skill/agent/hook registration, MCP server initialization.

## Common issues

| Issue | Cause | Solution |
| :-- | :-- | :-- |
| Plugin not loading | Invalid `plugin.json` | Run `claude plugin validate` or `/plugin validate`. |
| Skills not appearing | Wrong directory structure | Ensure `skills/` or `commands/` is at the plugin ROOT, not inside `.claude-plugin/`. |
| Hooks not firing | Script not executable | `chmod +x script.sh`. |
| MCP server fails | Missing `${CLAUDE_PLUGIN_ROOT}` | Use the variable for all plugin paths. |
| Path errors | Absolute paths in manifest | All paths must be relative and start with `./`. |
| LSP `Executable not found in $PATH` | Language server binary not installed | Install the binary separately. |

## Manifest validation errors

- `Invalid JSON syntax: Unexpected token } in JSON at position 142` — missing or extra commas, unquoted strings.
- `Plugin has an invalid manifest file ... Validation errors: name: Required` — a required field is missing.
- `Plugin has a corrupt manifest file ... JSON parse error` — JSON syntax error.

## Plugin loading errors

- `Warning: No commands found in plugin my-plugin custom directory: ./cmds. Expected .md files or SKILL.md in subdirectories.` — the command path exists but contains no valid files.
- `Plugin directory not found at path: ./plugins/my-plugin. Check that the marketplace entry has the correct path.` — the `source` path in `marketplace.json` points to a non-existent directory.
- `Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.` — remove duplicate component definitions or set `strict: false` on the marketplace entry.

## Hook troubleshooting

Script not executing:

- `chmod +x` the script.
- Verify the shebang (`#!/bin/bash` or `#!/usr/bin/env bash`).
- Use `${CLAUDE_PLUGIN_ROOT}` in the path.
- Test the script manually.

Hook not triggering:

- Verify the event name is CASE-SENSITIVE (`PostToolUse`, not `postToolUse`).
- Check that the matcher matches the tools you expect.
- Confirm the hook type is one of `command`, `http`, `mcp_tool`, `prompt`, `agent`.

## MCP server troubleshooting

Server not starting:

- Check the command exists and is executable.
- Verify all paths use `${CLAUDE_PLUGIN_ROOT}`.
- Run with `claude --debug` for startup logs.
- Test the server command manually.

Tools not appearing:

- Confirm the server is configured in `.mcp.json` or `plugin.json`.
- Verify the server implements the MCP protocol correctly.
- Check the debug output for connection timeouts.

## Directory structure mistakes

Components must live at the plugin ROOT, not inside `.claude-plugin/`. Only `plugin.json` belongs in `.claude-plugin/`.

Correct layout:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
└── hooks/
    └── hooks.json
```

## Restart matrix

When does a change require restarting Claude Code vs just `/reload-plugins`?

| Change | Restart? |
| :-- | :-- |
| Edit existing `SKILL.md`, agent `.md`, hook config | No — `/reload-plugins`. |
| Edit MCP / LSP server config | No — `/reload-plugins`. |
| Add a brand-new top-level directory (`skills/`, `agents/`, `hooks/`) for the first time | Yes. |
| Add a new monitor or edit a monitor command | Yes — monitors require a restart. |
| Plugin update mid-session (path change) | `/reload-plugins` for hooks/MCP/LSP; restart for monitors. |
