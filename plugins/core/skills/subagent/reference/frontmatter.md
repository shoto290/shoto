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

Upstream, only `name` and `description` are required. **This marketplace additionally requires** `permissionMode`, `skills`, `color`, and a recorded `isolation` / `initialPrompt` decision on every create and update — see [Mandatory in this marketplace](#mandatory-in-this-marketplace).

## All fields

The **Required** column below reflects the upstream Claude Code spec. Fields this marketplace adds on top are listed in [Mandatory in this marketplace](#mandatory-in-this-marketplace).

| Field | Required | What it does |
| :-- | :-- | :-- |
| `name` | YES | Unique lowercase-hyphenated id. Hooks receive this as `agent_type`. Filename does **not** have to match. |
| `description` | YES | Tells Claude when to delegate. State *what* and *when*. Add "use proactively" / "use immediately" to encourage automatic delegation. |
| `tools` | no | Comma-separated allowlist. Omit → inherit everything from parent (including MCP tools). |
| `disallowedTools` | no | Denylist applied to the inherited or specified pool. |
| `model` | no | `sonnet`, `opus`, `haiku`, a full model id (e.g. `claude-opus-4-8`), or `inherit`. Default: `inherit`. |
| `permissionMode` | no | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`. Ignored for plugin subagents. |
| `maxTurns` | no | Hard cap on agentic turns before the subagent stops. |
| `skills` | no | Skill names to preload at startup. Full skill content is injected — not just the description. Marketplace rule: always lists `core:base` first. |
| `mcpServers` | no | MCP servers scoped to this subagent. Inline def or name-reference. Ignored for plugin subagents. |
| `hooks` | no | Lifecycle hooks scoped to this subagent. Ignored for plugin subagents. |
| `memory` | no | `user`, `project`, or `local`. Enables persistent memory directory. |
| `background` | no | `true` to always run as a background task. Default: `false`. |
| `effort` | no | `low`, `medium`, `high`, `xhigh`, `max`. Overrides session effort. Levels depend on model. |
| `isolation` | no | `worktree` → run inside a temporary git worktree. Auto-cleaned if no changes. |
| `color` | no | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. UI display color. |
| `initialPrompt` | no | First-turn prompt auto-submitted when this agent runs as the **main** session agent (`--agent`). |

If both `tools` and `disallowedTools` are set, `disallowedTools` is applied first, then `tools` is resolved against the remaining pool. A tool in both is removed.

## Mandatory in this marketplace

Beyond the upstream `name` + `description`, every subagent authored here decides seven fields on create **and** update:

| Field | Emission rule |
| :-- | :-- |
| `name` | Always emitted. |
| `description` | Always emitted. |
| `permissionMode` | Always emitted (default `default`). **Loaded but ignored for plugin-scope agents** — kept for consistency across scopes. |
| `skills` | Always emitted, **`core:base` first**. Always use the fully-qualified `core:base` — it is the canonical plugin-skill id and resolves from any scope, including inside the `core` plugin itself, so there is one form to remember. Resolution requires the `core` plugin enabled — declare it under the consuming plugin's `dependencies` in `plugin.json`; if `core` is absent the entry is skipped with a debug-log warning (non-fatal). `base` is preloadable because it does not set `disable-model-invocation`. |
| `color` | Always emitted. One of the eight UI colors above. |
| `isolation` | Mandatory decision. The only value is `worktree`, so emit `isolation: worktree` only when an isolated worktree is wanted; otherwise omit and record the decision as "none". |
| `initialPrompt` | Mandatory decision. Emit only when the agent runs as a main session (`--agent` / `agent` setting); otherwise omit and record as "none". |

On update, if an existing target lacks any of these, add them — `skills` always gains `core:base` if missing. Do not strip fields the user did not ask to remove.

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
