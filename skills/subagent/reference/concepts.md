# Concepts

## What a subagent is

A subagent is a specialized AI assistant defined in a Markdown file with YAML frontmatter. It runs in its **own context window** with:

- A custom **system prompt** (the markdown body of the file)
- A configurable **tool set** (inherited from the parent or restricted)
- Its own **permissions**, **model**, and **lifecycle hooks**
- An optional **persistent memory directory** that survives across conversations

When Claude encounters a task that matches a subagent's `description`, it delegates: the subagent works independently in its own context, then returns a summary to the main conversation. Only the summary lands in your main context window — the search dumps, log output, and intermediate tool calls stay isolated.

## Why use subagents

| Benefit | What it means |
| :-- | :-- |
| **Preserve context** | Verbose exploration / logs / dumps stay in the subagent's window, not yours |
| **Enforce constraints** | Restrict tools so a "reviewer" can't accidentally edit files |
| **Reuse configurations** | User-scope subagents are available in every project |
| **Specialize behavior** | Focused system prompts perform better than a generalist Claude |
| **Control costs** | Route cheap lookups to Haiku, hard reasoning to Opus |

## Built-in subagents

Claude Code ships with subagents you don't have to create. They're invoked automatically when appropriate.

| Agent | Model | Tools | Purpose |
| :-- | :-- | :-- | :-- |
| **Explore** | Haiku | Read-only (no Write/Edit) | File discovery, code search, codebase exploration. Skips CLAUDE.md and git status to stay fast. Takes a thoroughness level: `quick`, `medium`, `very thorough`. |
| **Plan** | Inherits | Read-only (no Write/Edit) | Research during plan mode. Prevents nesting (subagents can't spawn subagents). Skips CLAUDE.md and git status. |
| **general-purpose** | Inherits | All tools | Complex multi-step work that needs exploration AND modification. Loads CLAUDE.md + git status. |
| **statusline-setup** | Sonnet | n/a | Runs when you invoke `/statusline` |
| **claude-code-guide** | Haiku | n/a | Runs when you ask questions about Claude Code features |

You can disable any built-in or custom subagent globally:

```json
{
  "permissions": {
    "deny": ["Agent(Explore)", "Agent(my-custom-agent)"]
  }
}
```

Or per session: `claude --disallowedTools "Agent(Explore)"`.

## Subagent vs skill vs main conversation

| Primitive | Context | When to use |
| :-- | :-- | :-- |
| **Main conversation** | Full history, all context the user has loaded | Iterative work, multi-phase tasks sharing context, quick targeted edits |
| **Subagent** | Fresh, isolated context with its own system prompt | Self-contained tasks that produce verbose output; specialist personas; tool/permission lockdown |
| **Skill (`SKILL.md`)** | Runs *in* the current conversation context | Reusable prompts, workflows, conventions injected into the main thread |
| **Fork** (experimental) | Inherits the full main conversation history | Side task that needs background but shouldn't pollute your context |

A skill is a `SKILL.md` file that Claude loads as guidance into the current context — it doesn't spin up a new context window. A subagent does. If the user wants reusable guidance that runs *here*, build a skill. If they want isolation, build a subagent.

## Description sells the subagent

Claude decides when to delegate by reading `description`. A weak description means the subagent never gets picked, or gets picked for the wrong tasks.

**Weak:**
```yaml
description: Code reviewer
```

**Strong:**
```yaml
description: Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code.
```

The strong version states *what it does*, *when it should fire*, and uses "Proactively" / "Use immediately" as delegation triggers. The model uses these phrases as signals.

## Where to go next

- Frontmatter field reference: [frontmatter.md](./frontmatter.md)
- File locations and precedence: [scopes.md](./scopes.md)
- Tool restrictions and permissions: [tools-and-permissions.md](./tools-and-permissions.md)
- Context, memory, MCP, preloaded skills: [context.md](./context.md)
- Invocation, foreground/background, fork mode: [invocation.md](./invocation.md)
