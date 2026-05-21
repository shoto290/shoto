# Frontmatter

Portable rules for the YAML frontmatter block at the top of every skill and subagent file.

## Required structure

- Frontmatter lives between two `---` markers at the very top of the file.
- The block must parse as valid YAML — no tabs, consistent indentation, quoted strings when they contain `:` or other YAML-significant characters.
- Anything outside the markers is rendered as Markdown body.

```yaml
---
name: example
description: One sentence covering what this does and when to use it.
---
```

## Mandatory fields

| Field | Applies to | Notes |
| :-- | :-- | :-- |
| `name` | skills, subagents | kebab-case, must match the directory or filename. See [naming.md](./naming.md). |
| `description` | skills, subagents | One concise sentence. For skills, this is the trigger Claude matches against user requests — put the key use case first. |

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
- [ ] `name` and `description` are both present.
- [ ] `name` is kebab-case and matches the directory or filename.
- [ ] Every internal Markdown link in the body resolves to a real file.
