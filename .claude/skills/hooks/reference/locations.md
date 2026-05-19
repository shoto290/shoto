# Hooks — locations and scope

Where you put a hook decides who runs it and whether it's shareable. Hooks always live inside a top-level `hooks` block in a settings JSON file (or a skill/agent frontmatter).

## Scopes

| Location | Scope | Shareable | Notes |
| :-- | :-- | :-- | :-- |
| `~/.claude/settings.json` | All your projects (this user, this machine) | No | Your personal hooks |
| `.claude/settings.json` | One project | **Yes** — checked into git | Team-shared hooks |
| `.claude/settings.local.json` | One project | No — gitignored | Personal overrides per project |
| Managed policy settings | Organization-wide | Admin-controlled | Highest precedence; users can't disable |
| Plugin `hooks/hooks.json` | While plugin is enabled | Yes — bundled with plugin | Plugin author's hooks |
| Skill or agent frontmatter | While that skill/agent is active | Yes — embedded in the file | Per-skill/agent lifecycle hooks |

## Precedence

When hooks from multiple scopes match the same event, **they all run** — there is no override semantics for hook execution. (Contrast with permissions, where managed deny > project deny > user deny.) Outputs combine per [io.md](./io.md#combine-results-from-multiple-hooks).

What managed settings *can* enforce is `disableAllHooks: false` — managed-level hooks still run even when the user sets `"disableAllHooks": true`.

## Anatomy of a settings file with hooks

```json
{
  "permissions": { /* ... */ },
  "env": { /* ... */ },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "..." }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "..." }
        ]
      }
    ]
  }
}
```

- The `hooks` key is **one object** with one entry per event name.
- Each event maps to **an array of handler groups**.
- Each group has a `matcher` and a `hooks` array of one or more `{type, command, ...}` handlers.

When adding a new event to a file that already has `hooks`, add it as a **sibling** to existing event keys — don't replace the whole object.

## `$CLAUDE_PROJECT_DIR`

Always set to the absolute path of the project root. Use it whenever your hook references project-relative scripts:

```json
{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }
```

Without it, a hook script will fail if Claude has `cd`'d elsewhere during the session.

## `$CLAUDE_ENV_FILE`

Some events (`SessionStart`, `CwdChanged`, `FileChanged`) can write environment variables that Claude Code prepends as a shell preamble before each Bash command. Write your `KEY=value` lines (or `export` statements) to `$CLAUDE_ENV_FILE`:

```json
{ "type": "command", "command": "direnv export bash > \"$CLAUDE_ENV_FILE\"" }
```

This is how you wire direnv / devbox / nix into Claude's Bash tool: the hook writes the env, Claude sources it for every subsequent Bash call until the next `CwdChanged` re-runs the hook.

## Live reload

Edits to settings files are picked up automatically by the file watcher within a few seconds. If `/hooks` doesn't show your new hook after editing:

- Confirm the JSON is valid (no trailing commas, no comments)
- Confirm the location is correct (project vs user vs local)
- Restart the session to force a reload

Plugin-bundled and skill/agent-frontmatter hooks load when the plugin/skill/agent activates — usually at session start.

## Disabling hooks

Set `"disableAllHooks": true` in any settings file to disable hooks **from that scope**. Hooks defined in managed settings still run unless the managed config also sets `disableAllHooks: true`.

There is no per-event disable switch — to silence one event, remove or comment out (by deleting) its entries.

## Plugin and frontmatter notes

- **Plugin hooks** in `<plugin>/hooks/hooks.json` use the same shape as `settings.json`'s `hooks` value.
- **Skill frontmatter** can declare lifecycle hooks that run only while the skill is active. See the [skill](../../skill/SKILL.md) skill for layout.
- **Agent frontmatter** can declare lifecycle hooks inline. For exact behavior (which events are supported, plugin-sourced agent caveats), check the [subagent](../../subagent/SKILL.md) skill and the `/en/sub-agents` reference.
