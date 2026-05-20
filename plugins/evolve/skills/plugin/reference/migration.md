# Migrate `.claude/` to a Plugin

Convert a standalone `.claude/` directory into a distributable plugin.

## Steps

### 1. Create the plugin scaffold

```bash
mkdir -p my-plugin/.claude-plugin
```

`my-plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "my-plugin",
  "description": "Migrated from standalone configuration",
  "version": "1.0.0"
}
```

### 2. Copy existing artifacts

```bash
cp -r .claude/commands my-plugin/   # legacy flat skills
cp -r .claude/agents   my-plugin/   # sub-agents
cp -r .claude/skills   my-plugin/   # SKILL.md skills
```

Skip directories that don't exist in your `.claude/`.

### 3. Migrate hooks

Hooks move from `.claude/settings.json` (or `settings.local.json`) into a dedicated `hooks/hooks.json` at the plugin root. The schema is **identical** — copy the `hooks` object verbatim.

```bash
mkdir my-plugin/hooks
```

`my-plugin/hooks/hooks.json`:

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

Hook commands receive the hook input as JSON on stdin. Use `jq` to extract whatever field you need — e.g. `.tool_input.file_path` for the file Claude just wrote.

### 4. Test the migrated plugin

```bash
claude --plugin-dir ./my-plugin
```

- Run each command via `/<plugin-name>:<command>` to confirm the namespace works.
- Check `/agents` to see migrated sub-agents.
- Trigger an action that should fire a hook and confirm it runs.

### 5. Remove the originals

Once the plugin version is verified, delete the corresponding entries from `.claude/`. The plugin version takes precedence anyway, but keeping both invites drift.

## What changes

| Standalone (`.claude/`) | Plugin |
| :-- | :-- |
| Available only in the project where `.claude/` lives | Distributable via a marketplace |
| Files in `.claude/commands/`, `.claude/agents/`, `.claude/skills/` | Same files under `my-plugin/commands/`, `my-plugin/agents/`, `my-plugin/skills/` |
| Hooks defined inside `settings.json` `hooks` block | Hooks defined in `hooks/hooks.json` (same schema) |
| Skill names are unprefixed (`/deploy`) | Skill names are namespaced (`/<plugin-name>:deploy`) |
| Sharing means copying files | Sharing means `/plugin install` |

## Common pitfalls

- **Don't drop directories into `.claude-plugin/`.** Only `plugin.json` lives there. Skills, agents, hooks all sit at the plugin root.
- **Skill names change.** `/deploy` becomes `/my-plugin:deploy`. Update any docs or scripts that referenced the old name.
- **Hook stdin handling.** Standalone hooks may have read environment variables; plugin hooks receive JSON on stdin. Wrap with `jq` to extract fields like `.tool_input.file_path`, `.session_id`, etc.
