# Test format

Tests are markdown files colocated with the artifact they exercise. The `bench:run` skill discovers them by globbing `plugins/**/tests/*.md` from the repo root.

## Path → artifact mapping

| Path | Artifact | Kind |
|------|----------|------|
| `plugins/<plugin>/skills/<name>/tests/<test>.md` | `<plugin>:<name>` | skill |
| `plugins/<plugin>/agents/<name>/tests/<test>.md` | `<plugin>:<name>` | subagent |

Any other `tests/*.md` location is ignored.

## File shape

```yaml
---
name: <test-name>
description: <one-line — what this test exercises>
---

<prompt body — free-form markdown>
```

### Frontmatter fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Stable identifier shown in selection menus and the report. Kebab-case. |
| `description` | yes | One-line summary surfaced in the `AskUserQuestion` option description. |
| `prompt` | optional | Inline prompt string. When present, it is the prompt sent to `bench-runner`; the body is appended as extra context. When absent, the entire body is the prompt. |

### Body

Free-form markdown. May include:

- The prompt itself (when no `prompt:` field)
- Setup context, fixtures, or notes
- Expected-behavior hints for the human reader (the runner ignores them)

The runner forwards the prompt verbatim — no templating, no substitution.

## Authoring checklist

- File lives at the canonical path so discovery picks it up.
- `name:` matches the filename (without `.md`) by convention.
- `description:` reads well as a one-liner in a menu.
- Prompt is self-contained — the `bench-runner` sub-agent starts with no prior context.
