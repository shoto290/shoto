# Invocation control

By default, both the user and Claude can invoke any skill. Two frontmatter fields restrict this.

## `disable-model-invocation: true`

Only the user can invoke the skill (via `/name`). Claude won't auto-load it.

Use for skills with side effects or where you want to control timing:
- `/commit` — you decide when to commit
- `/deploy` — you don't want Claude deploying because code "looks ready"
- `/send-slack-message` — outbound messages

Also blocks the skill from being preloaded into subagents.

## `user-invocable: false`

Only Claude can invoke (auto-load when relevant). Hidden from the `/` menu.

Use for background knowledge skills that aren't meaningful as commands:
- `legacy-system-context` — explains how an old system works; Claude should know this when relevant, but `/legacy-system-context` isn't a meaningful action.

## Matrix

| Frontmatter | User can invoke | Claude can invoke | Context loading |
| :-- | :-- | :-- | :-- |
| (default) | Yes | Yes | Description always in context; body loads on invocation |
| `disable-model-invocation: true` | Yes | No | Description **not** in context; body loads when user invokes |
| `user-invocable: false` | No | Yes | Description always in context; body loads on Claude invocation |

In a regular session, only descriptions live in context; full content loads when invoked. Subagents with preloaded skills inject full content at startup instead.

## `allowed-tools`

Pre-approve tools while the skill is active — Claude can call them without per-use approval. Tools not listed remain available; permission settings still govern them.

Project skills' `allowed-tools` takes effect after workspace trust is accepted (same as permission rules). **Review project skills before trusting a repository** — a skill can grant itself broad tool access.

```yaml
---
name: commit
description: Stage and commit current changes
disable-model-invocation: true
allowed-tools: Bash(git add *) Bash(git commit *) Bash(git status *)
---
```

To block a skill from using certain tools, add deny rules in permission settings.

## Restrict Claude's skill access globally

Three ways to control which skills Claude can invoke:

**Disable all skills**: deny the `Skill` tool in `/permissions`.

```text
# deny rule
Skill
```

**Allow / deny specific skills** via permission rules:

```text
Skill(commit)
Skill(review-pr *)
Skill(deploy *)        # used as a deny rule
```

Syntax: `Skill(name)` exact, `Skill(name *)` prefix with any args.

**Hide a single skill from Claude**: set `disable-model-invocation: true` in its frontmatter.

> `user-invocable` only controls menu visibility, not Skill tool access. Use `disable-model-invocation: true` to block programmatic invocation.

## Settings-side overrides

`skillOverrides` (typically in `.claude/settings.local.json`) sets visibility without editing the skill. Use it for skills you don't own (shared repo, MCP-provided). Values: `"on"`, `"name-only"`, `"user-invocable-only"`, `"off"`. The `/skills` menu writes this — Space cycles states, Enter saves.

```json
{
  "skillOverrides": {
    "legacy-context": "name-only",
    "deploy": "off"
  }
}
```

Plugin skills are not affected by `skillOverrides` — manage them through `/plugin`.
