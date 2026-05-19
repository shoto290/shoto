# Frontmatter reference

A subagent file is YAML frontmatter between `---` markers, followed by the markdown system prompt:

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

Only `name` and `description` are required.

## All fields

| Field | Required | What it does |
| :-- | :-- | :-- |
| `name` | YES | Unique lowercase-hyphenated id. Hooks receive this as `agent_type`. Filename does **not** have to match. |
| `description` | YES | Tells Claude when to delegate. State *what* and *when*. Add "use proactively" / "use immediately" to encourage automatic delegation. |
| `tools` | no | Comma-separated allowlist. Omit → inherit everything from parent (including MCP tools). |
| `disallowedTools` | no | Denylist applied to the inherited or specified pool. |
| `model` | no | `sonnet`, `opus`, `haiku`, a full model id (e.g. `claude-opus-4-7`), or `inherit`. Default: `inherit`. |
| `permissionMode` | no | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`. Ignored for plugin subagents. |
| `maxTurns` | no | Hard cap on agentic turns before the subagent stops. |
| `skills` | no | Skill names to preload at startup. Full skill content is injected — not just the description. |
| `mcpServers` | no | MCP servers scoped to this subagent. Inline def or name-reference. Ignored for plugin subagents. |
| `hooks` | no | Lifecycle hooks scoped to this subagent. Ignored for plugin subagents. |
| `memory` | no | `user`, `project`, or `local`. Enables persistent memory directory. |
| `background` | no | `true` to always run as a background task. Default: `false`. |
| `effort` | no | `low`, `medium`, `high`, `xhigh`, `max`. Overrides session effort. Levels depend on model. |
| `isolation` | no | `worktree` → run inside a temporary git worktree. Auto-cleaned if no changes. |
| `color` | no | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. UI display color. |
| `initialPrompt` | no | First-turn prompt auto-submitted when this agent runs as the **main** session agent (`--agent`). |

If both `tools` and `disallowedTools` are set, `disallowedTools` is applied first, then `tools` is resolved against the remaining pool. A tool in both is removed.

## Body = system prompt

The markdown body is the subagent's full system prompt. Subagents do **not** see the full Claude Code system prompt — only this body plus environment details (working directory, etc.).

Write the body in second person ("You are a..."), make the role specific, and lay out a workflow. Example:

```markdown
You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- ...

Provide feedback organized by priority:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)
```

A focused workflow + checklist + output format gives much better results than a vague "review this code" prompt.

## Model selection

Resolution order when Claude invokes a subagent:

1. `CLAUDE_CODE_SUBAGENT_MODEL` env var
2. Per-invocation `model` parameter passed by the Agent tool
3. Frontmatter `model:`
4. Main conversation's model

Rules of thumb:
- `haiku` — cheap, fast, low-stakes lookups (Explore-style work)
- `sonnet` — balanced; default for review, analysis, data work
- `opus` — hardest reasoning; expensive
- `inherit` — match the main thread; safest default

## Restart requirement

Subagents are loaded **at session start**. If you create or edit a file directly on disk, restart the session. Files created through the `/agents` UI take effect immediately.
