# Example: summarize-changes

**Pattern**: Dynamic context injection + auto-invocable

Pulls live diff data into the prompt with `` !`command` `` so Claude responds to the actual working tree, not what it can guess from open files. Auto-invocable when the user asks what changed.

## SKILL.md

```yaml
---
description: Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed, wants a commit message, or asks to review their diff.
---

## Current changes

!`git diff HEAD`

## Instructions

Summarize the changes above in two or three bullet points, then list any risks you notice such as missing error handling, hardcoded values, or tests that need updating. If the diff is empty, say there are no uncommitted changes.
```

## Key choices

- **No `name:`** — the directory name `summarize-changes` becomes the slash command
- **`description` with trigger phrases** ("what changed", "commit message", "review their diff") so Claude knows when to auto-load it
- **`` !`git diff HEAD` `` is preprocessing** — runs before Claude sees the content, output is inlined
- **Body is short** — content stays in context for the session, so brevity matters
