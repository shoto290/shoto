# Frontmatter

Portable rules for the YAML frontmatter block at the top of every skill and subagent file.

## Required structure

- Frontmatter lives between two `---` markers at the very top of the file.
- The block must parse as valid YAML — no tabs, consistent indentation, quoted strings when they contain `:` or other YAML-significant characters.
- Anything outside the markers is rendered as Markdown body.

```yaml
---
name: example
description: One sentence covering what this skill does — key use case first.
when_to_use: Trigger phrases or example requests that should load this skill.
---
```

## Mandatory fields

Every skill MUST declare all three of these. Subagents require `name` and `description`.

| Field | Applies to | Notes |
| :-- | :-- | :-- |
| `name` | skills, subagents | kebab-case, must match the directory or filename. See [naming.md](./naming.md). |
| `description` | skills, subagents | What the artifact does. For skills, this is the trigger Claude matches against user requests — put the key use case first. |
| `when_to_use` | skills | Additional context for when Claude should invoke the skill, such as trigger phrases or example requests. Appended to `description` in the skill listing and counts toward the 1,536-character cap. |

## Common optional fields (skills)

| Field | Effect |
| :-- | :-- |
| `argument-hint` | Inline hint shown next to the slash command. |
| `disable-model-invocation` | `true` prevents Claude from auto-loading the skill — user must invoke it (or another artifact must link to it). |
| `user-invocable` | `false` hides the slash command — only Claude can load it. |
| `allowed-tools` | Pre-approved tools the skill may use without prompting. Keep minimal. |

## Validation gate

Before returning, run [../scripts/validate-frontmatter.py](../scripts/validate-frontmatter.py) on the file — it is the authority on the mechanical checks. Two things it cannot decide:

- The file landed at the path you intended. The script only validates the path it is handed.
- A new or changed `description` does not collide with a sibling — see [discovery-check.md](./discovery-check.md).
