# Context: what loads, what persists

## What loads at startup

Each subagent (except a fork) starts with a **fresh, isolated context window**. It does not see your conversation history, the skills you've already invoked, or files Claude has already read.

A non-fork subagent's initial context contains:

| Item | Notes |
| :-- | :-- |
| **System prompt** | The agent's own prompt (markdown body or `prompt` field) + Claude Code environment details. **Not** the full Claude Code system prompt. |
| **Task message** | The delegation prompt Claude writes when handing off the work. |
| **CLAUDE.md and memory** | Every level of the memory hierarchy: `~/.claude/CLAUDE.md`, project rules, `CLAUDE.local.md`, managed policy. **Built-in Explore and Plan skip this.** |
| **Git status** | A snapshot from the start of the parent session. Absent if CWD isn't a git repo or `includeGitInstructions` is `false`. Explore and Plan skip it regardless. |
| **Preloaded skills** | Full content of skills named in the `skills` field. Built-in agents don't preload skills. |

You cannot opt a custom subagent out of CLAUDE.md and git status — only Explore and Plan skip them.

The main conversation reads Explore and Plan results **with** full CLAUDE.md context, so most rules don't need to reach the subagent itself. If a rule must (e.g. "ignore `vendor/`"), repeat it in the delegation prompt.

## Preload skills into a subagent

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions and patterns from the preloaded skills.
```

The full content of each listed skill is injected at startup. This controls **what's preloaded** — without the field, the subagent can still discover and invoke project/user/plugin skills through the `Skill` tool during execution.

To prevent skill invocation entirely, omit `Skill` from `tools` or add it to `disallowedTools`.

You **cannot** preload a skill that sets `disable-model-invocation: true`. Missing/disabled skills are skipped with a debug log warning.

## Scope MCP servers to a subagent

```yaml
---
name: browser-tester
description: Tests features in a real browser using Playwright
mcpServers:
  # Inline definition: scoped to this subagent only
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  # Reference by name: reuses an already-configured server
  - github
---
```

- Inline servers are connected when the subagent starts, disconnected when it finishes.
- String references share the parent session's connection.
- Inline definitions use the same schema as `.mcp.json` entries (`stdio`, `http`, `sse`, `ws`).

**Use this to keep MCP servers out of the main conversation** — define them inline in the subagent so their tool descriptions don't consume parent context.

Plugin subagents ignore `mcpServers`.

## Persistent memory

The `memory` field gives the subagent a directory that survives across conversations. The subagent reads/writes there to accumulate institutional knowledge.

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
memory: user
---

You are a code reviewer. As you review code, update your agent memory with
patterns, conventions, and recurring issues you discover.
```

| Scope | Location | When to use |
| :-- | :-- | :-- |
| `user` | `~/.claude/agent-memory/<name>/` | Knowledge applies across all projects |
| `project` | `.claude/agent-memory/<name>/` | Project-specific, shareable via git |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific, not in version control |

**Behavior when `memory` is enabled:**
- System prompt includes instructions for reading/writing the memory directory.
- The first 200 lines or 25KB of `MEMORY.md` is injected (whichever is smaller), with instructions to curate if it exceeds the limit.
- `Read`, `Write`, `Edit` are auto-enabled so the agent can manage its files.

**Tips:**
- Default to `project` so team members benefit.
- Ask the agent to **consult** memory before starting: "check your memory for patterns you've seen before".
- Ask the agent to **update** memory after finishing: "save what you learned to your memory".
- Include memory instructions in the body so the agent maintains it without prompting:

  > Update your agent memory as you discover codepaths, patterns, library locations, and key architectural decisions. Write concise notes about what you found and where.

## Resume a subagent

Each spawn creates a new instance with fresh context. To continue prior work instead of starting over, ask Claude to resume:

```
Use the code-reviewer subagent to review the authentication module
[Agent completes]

Continue that code review and now analyze the authorization logic
[Claude resumes the subagent with full history]
```

Claude uses the `SendMessage` tool with the agent's id to resume. `SendMessage` is only available when **agent teams** is enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

Resumed subagents keep all prior tool calls, results, and reasoning. Agent ids are visible in transcript files at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.

## Transcript persistence + compaction

- Subagent transcripts persist **independently** of the main conversation. Main-conversation compaction doesn't touch them.
- Transcripts persist within their session; you can resume after restarting Claude Code by resuming the same session.
- Auto-cleanup is governed by `cleanupPeriodDays` (default 30 days).
- Subagents auto-compact at ~95% capacity using the same logic as the main conversation. Lower it with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`.
- Compaction events appear in the transcript as `{"type": "system", "subtype": "compact_boundary", ...}`.
