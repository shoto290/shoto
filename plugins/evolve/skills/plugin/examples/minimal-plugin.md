# Minimal Plugin — `my-first-plugin`

A complete, runnable plugin with one skill that takes an argument.

## Layout

```
my-first-plugin/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── hello/
        └── SKILL.md
```

## Files

### `my-first-plugin/.claude-plugin/plugin.json`

```json
{
  "name": "my-first-plugin",
  "description": "A greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

### `my-first-plugin/skills/hello/SKILL.md`

```markdown
---
description: Greet the user with a personalized message
---

# Hello Skill

Greet the user named "$ARGUMENTS" warmly and ask how you can help them today. Make the greeting personal and encouraging.
```

## Build it

```bash
mkdir -p my-first-plugin/.claude-plugin my-first-plugin/skills/hello
# write the two files above
```

## Test it

```bash
claude --plugin-dir ./my-first-plugin
```

In the session:

```text
/my-first-plugin:hello Alex
```

Claude greets "Alex" by name.

## Iterate

Edit `SKILL.md`, then run `/reload-plugins` in the session — no restart needed. New top-level directories (e.g. adding `agents/` for the first time) do require a restart.

## Next steps

- Add a sub-agent: create `my-first-plugin/agents/<name>.md`. Use the [subagent skill](../../subagent/SKILL.md).
- Add a hook: create `my-first-plugin/hooks/hooks.json`. Use the [hooks skill](../../hooks/SKILL.md).
- Distribute: add a `marketplace.json` per [reference/distribution.md](../reference/distribution.md).
