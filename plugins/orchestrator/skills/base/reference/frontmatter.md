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

Before returning, verify:

- [ ] The file exists at the expected path.
- [ ] Frontmatter parses as valid YAML.
- [ ] `name`, `description`, and `when_to_use` are all present (skills); `name` and `description` for subagents.
- [ ] `name` is kebab-case and matches the directory or filename.
- [ ] Combined `description` + `when_to_use` stays within the 1,536-character cap.
- [ ] Every internal Markdown link in the body resolves to a real file.
