# Enable

Agent teams are experimental and **disabled by default**. Two requirements before any team can be spawned:

1. Claude Code **v2.1.32 or later** — check with `claude --version`
2. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set in env or `settings.json`

## Set the env var

Pick one method. Both work; `settings.json` persists across shells.

**Shell environment** (one shell only):
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**`~/.claude/settings.json`** (persistent, user-scope):
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Restart the Claude Code session after setting either. Editing `~/.claude/settings.json` mutates the user's global config — confirm before writing for them.

## Display: `teammateMode`

How teammates' terminals are presented. Set in `~/.claude/settings.json`:

```json
{ "teammateMode": "in-process" }
```

| Mode | Behaviour | Requires |
| :-- | :-- | :-- |
| `auto` (default) | Split panes if already inside tmux, else in-process | — |
| `in-process` | All teammates share the main terminal. Shift+Down cycles; Enter views; Esc interrupts; Ctrl+T toggles the task list | Any terminal |
| `tmux` | Each teammate gets its own pane (auto-detects tmux or iTerm2) | tmux **or** iTerm2 + `it2` CLI |

Per-session override:
```bash
claude --teammate-mode in-process
```

### Split-pane prerequisites

- **tmux** — install via your package manager. `tmux -CC` from inside iTerm2 is the recommended entrypoint on macOS.
- **iTerm2** — install the [`it2` CLI](https://github.com/mkusaka/it2), then **iTerm2 → Settings → General → Magic → Enable Python API**.

Split-pane mode is **not supported** in VS Code's integrated terminal, Windows Terminal, or Ghostty — use `in-process` there.

## Default teammate model

Teammates don't inherit the lead's `/model` selection by default. Two ways to control which model new teammates use:

- **`/config` → Default teammate model** — pick a specific model, or **Default (leader's model)** to track the lead
- **In the spawn prompt** — "Use Sonnet for each teammate"

The spawn-prompt setting overrides the `/config` default for that team.

## Verification

After restart, ask the lead:

```text
Create a 2-teammate agent team to summarise the README from two perspectives.
```

If teams are enabled correctly, the lead spawns teammates and shows them in the task list / new panes. If nothing happens, see [troubleshooting.md](./troubleshooting.md#teammates-not-appearing).
