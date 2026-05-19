# Example: pr-summary

**Pattern**: Subagent execution + multiple dynamic-context injections + pre-approved tools

Runs in an isolated `Explore` subagent. The skill body becomes the subagent's prompt. The `gh` commands run before Claude sees anything — their output is inlined into the prompt.

## SKILL.md

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request: what changed, why (if comments explain), and any risks you notice in the diff.
```

## Why `context: fork`

The main conversation context doesn't need the full PR diff — keep it in the subagent. The summary returns to the main conversation; the raw diff stays in the fork.

`agent: Explore` gives the subagent read-only tools optimized for codebase exploration and skips CLAUDE.md + git status to keep its context lean.

## Gotcha

`context: fork` **requires an explicit task** in the body. If the body were only guidelines like "follow these conventions", the subagent would receive the guidelines but no actionable prompt and return nothing. Always include a task ("Summarize", "Research", "Generate ...").
