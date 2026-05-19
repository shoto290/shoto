# Template: basic

Minimal skill — just description and instructions. Copy the YAML block into `<scope>/<skill-name>/SKILL.md` and customize.

```yaml
---
description: <one-sentence summary + when to use it, with trigger phrases the user would naturally say>
---

<instructions for Claude — concise, since this content stays in context once invoked>
```

Use when:
- No arguments needed
- No live data injection
- No subagent execution
- Reference-style content OR very simple task

For richer patterns see [task.md](./task.md), [reference.md](./reference.md), [advanced.md](./advanced.md).
