# SKILL.md slot

## What it is

The required entry point of every skill. A skill is a directory; `SKILL.md` is the single file Claude Code must find inside it. The file has two parts: YAML frontmatter between `---` markers at the top, then a markdown body. The directory name becomes the slash command; `name:` only sets the display label (except a plugin-root `SKILL.md`).

Every other slot in the skill (`template.md`, `examples/`, `reference.md` / `reference/`, `scripts/`) is optional and only loaded when `SKILL.md` references it.

## Structure

The canonical shape of the file:

```
---
name: my-skill              # mandatory — kebab-case, matches the directory
description: ...            # mandatory — drives auto-loading, key use case first
when_to_use: ...           # mandatory — trigger phrases / example requests
---

<markdown body>
```

The full list of supported frontmatter fields is documented in [frontmatter.md](./frontmatter.md). In this marketplace `name`, `description`, and `when_to_use` are mandatory; `description` plus `when_to_use` is what Claude matches against the user's request when deciding whether to auto-load the skill.

## Body content guidance

The body is the recurring cost of the skill — every line stays in context for the rest of the session once loaded. The official docs are explicit:

> Keep the body itself concise. Once a skill loads, its content stays in context across turns, so every line is a recurring token cost. State what to do rather than narrating how or why.

The recommended ceiling for the body is **500 lines**:

> Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

When the body would exceed this, offload to `reference.md` or `reference/` — see [slot-reference.md](./slot-reference.md).

## Reference vs Task content

The docs distinguish two flavours of skill content:

- **Reference content** — passive knowledge applied inline (style guides, conventions, domain facts). It runs alongside the conversation context and never triggers tool calls on its own.
- **Task content** — step-by-step instructions for actions Claude should perform (deploy, commit, send-message). Task skills are often combined with `disable-model-invocation: true` so they only run when the user explicitly invokes them.

The split is a content decision, not a frontmatter field — pick the body shape that matches the intent.

## Lifecycle (token cost)

The rendered `SKILL.md` enters the conversation as a single message and stays for the rest of the session. Claude Code does not re-read the file on later turns.

When auto-compaction runs, the conversation keeps the most recent invocation of each skill (first 5,000 tokens of each), with a combined budget of 25,000 tokens across all re-attached skills, filled from most recent to oldest. Full details in [lifecycle.md](./lifecycle.md).

## Live edits propagation

Edits to existing skill directories propagate within the running session — re-invoking the skill picks up the latest body. Creating a **brand-new top-level skill directory** requires restarting Claude Code so the directory gets watched.

Scope, discovery rules, and precedence (enterprise > personal > project) are documented in [locations.md](./locations.md).

## Cross-links

- [frontmatter.md](./frontmatter.md) — every YAML field accepted in the `---` block
- [lifecycle.md](./lifecycle.md) — compaction behavior across turns
- [locations.md](./locations.md) — scopes, discovery, precedence
- [slot-template.md](./slot-template.md) — the `template.md` slot
- [slot-examples.md](./slot-examples.md) — the `examples/` slot
- [slot-reference.md](./slot-reference.md) — the `reference.md` / `reference/` slot
- [slot-scripts.md](./slot-scripts.md) — the `scripts/` slot

## Anti-patterns

- Body that narrates rationale ("we chose this approach because…") instead of giving instructions Claude can act on.
- Body that exceeds ~500 lines without offloading the long-form material to `reference/`.
- Using frontmatter for fields not documented in [frontmatter.md](./frontmatter.md) — they are silently ignored and create false expectations.
