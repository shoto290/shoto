---
description: Understand and create or update a Claude Code subagent (custom AI assistant with its own context, tools, and system prompt). Use when the user wants to learn how subagents work, decide if a task needs one, write a new subagent file, edit an existing one in `.claude/agents/` or `~/.claude/agents/`, restrict tools/permissions, preload skills, enable persistent memory, hook into the lifecycle, or invoke one via natural language, @-mention, or `--agent`. Triggers on: subagent, sub-agent, agent file, /subagent command, /agents UI, .claude/agents, --agent flag, agent frontmatter, agent description, agent tools, agent model, agent permissionMode, agent hooks, agent memory, fork mode, agent teams, Explore, Plan, general-purpose.
argument-hint: '[agent-name]'
---

# Agents

A **subagent** is a Markdown file with YAML frontmatter that defines a specialized AI assistant. It runs in its own isolated context window with a custom system prompt, restricted tools, and independent permissions. Claude delegates to it automatically when its `description` matches the task, or you invoke it explicitly with `@agent-<name>`, natural language, or `claude --agent <name>`.

## Subagent file structure (canonical)

A subagent is a **single Markdown file** — there is no directory layout, no supporting files, no scripts. The frontmatter declares the agent; the markdown body is its system prompt.

```
.claude/agents/
└── my-agent.md         # frontmatter + system prompt
```

Only `name` and `description` are required in the frontmatter. Everything else (`tools`, `model`, `permissionMode`, `memory`, `skills`, `mcpServers`, `hooks`, `isolation`, `background`, …) is optional. The full field reference lives at [reference/frontmatter.md](./reference/frontmatter.md).

Use the pattern recipes in [reference/](./reference/) as starting points when drafting a new agent, and the [examples/](./examples/) directory as a guide to the response shape the architect produces.

## Detect intent

If invoked as `/subagent <name>`, treat `$ARGUMENTS` as the target name.

1. **Search for the name** in project (`.claude/agents/<name>.md` from CWD up to repo root), user (`~/.claude/agents/<name>.md`), and enabled plugin (`<plugin>/agents/<name>.md`) scopes. The filename does **not** have to match the agent name — identity is `name:` in frontmatter. When searching, also grep frontmatter `name:` fields.
2. **Match found** → propose **update flow** (confirm before editing)
3. **No match** → propose **create flow** (validate the name: lowercase letters and hyphens)
4. **Empty / ambiguous** → ask the user, or offer to **explain how subagents work** (route to [reference/concepts.md](./reference/concepts.md))

> Built-in subagents (`Explore`, `Plan`, `general-purpose`, `statusline-setup`, `claude-code-guide`) are not files on disk — they cannot be updated, only disabled via `permissions.deny`. See [reference/concepts.md](./reference/concepts.md#built-in-subagents).

## When to suggest each flow

**Create** when the user:
- Keeps spawning the same kind of worker with the same instructions
- Wants tool/permission lockdown around a recurring task (review, debug, db read, …)
- Needs a verbose-output task (test runs, log scans, doc fetches) isolated from main context
- Wants a session-default persona via `claude --agent <name>` or the `agent` setting

**Update** when the user wants to:
- Tighten or broaden `description` so delegation fires correctly
- Change `tools` / `disallowedTools` / `permissionMode`
- Add or change `model`, `effort`, `maxTurns`, `isolation`
- Preload `skills`, scope `mcpServers`, enable `memory`
- Add lifecycle `hooks` (frontmatter or `settings.json`)
- Convert to a coordinator with `Agent(<name>, <name>)`
- Move scope (project ↔ user ↔ plugin) or rename
- Diagnose why a subagent doesn't get delegated to

If the user just wants to learn how subagents work, skip both flows and route to the right reference (see "Explain" table below).

---

## Create flow

### 1. Clarify the subagent

Propose defaults from the user's request; confirm before writing:

| Decision | Options |
| :-- | :-- |
| **Name** | lowercase letters and hyphens (e.g. `code-reviewer`, `db-reader`) |
| **Scope** | Project `.claude/agents/` (default, checked into git), User `~/.claude/agents/`, Plugin `<plugin>/agents/` |
| **Purpose** | One specific task. Focused subagents win over generalists |
| **Tools** | Allowlist via `tools:` (safer) or denylist via `disallowedTools:` (preserves inherited MCP tools). Omit → inherit everything |
| **Model** | `inherit` (default), `haiku` (cheap), `sonnet` (balanced), `opus` (hard reasoning), or a full id like `claude-opus-4-7` |
| **Permissions** | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` |
| **Persistent memory** | `user`, `project`, or `local` (none by default) |
| **Hooks** | `PreToolUse`, `PostToolUse`, `Stop` in frontmatter; `SubagentStart`/`SubagentStop` in `settings.json` |
| **MCP scoping** | Inline server defs or string references in `mcpServers:` |
| **Preloaded skills** | `skills:` injects full skill content at startup |
| **Run mode** | `background: true` to always background; `isolation: worktree` for an isolated git worktree |

See [reference/decision-questions.md](./reference/decision-questions.md) for the canonical list of decisions to surface to the user, with options, implications, and recommended defaults. `subagent-architect` uses it to drive `AskUserQuestion` calls.

### 2. Pick a pattern recipe

Start from a complete pattern reference in [reference/](./reference/):

- [reference/basic.md](./reference/basic.md) — minimum viable subagent (description + body)
- [reference/code-reviewer.md](./reference/code-reviewer.md) — read-only review (`tools: Read, Grep, Glob, Bash`)
- [reference/debugger.md](./reference/debugger.md) — analyze + fix (`Edit` allowed)
- [reference/data-scientist.md](./reference/data-scientist.md) — domain specialist with `model: sonnet` pinned
- [reference/db-reader-hooks.md](./reference/db-reader-hooks.md) — `PreToolUse` hook whitelists SELECT-only SQL
- [reference/coordinator.md](./reference/coordinator.md) — main-thread agent that spawns specific workers via `Agent(worker, researcher)`

### 3. Create the file

```bash
mkdir -p <scope>/agents
# write the file at <scope>/agents/<name>.md
```

Frontmatter only requires `name` and `description`. The markdown body is the system prompt. The subagent does **not** see the full Claude Code system prompt — only this body plus environment details. Full field reference: [reference/frontmatter.md](./reference/frontmatter.md).

```markdown
---
name: <name>
description: <what it does + when to delegate; use "proactively" / "use immediately" for auto-delegation triggers>
tools: <comma-separated allowlist>          # optional
model: <inherit | haiku | sonnet | opus>    # optional
---

You are a <role>...

When invoked:
1. <step 1>
2. <step 2>
3. <step 3>

<output format expectations>
```

### 4. Restart the session

Subagents are loaded **at session start**. New or edited files on disk only become available after restart. Files created through the `/agents` UI take effect immediately.

### 5. Test

- **Auto-delegation**: phrase a request matching the `description`. Watch whether Claude picks it.
- **Forced**: `@agent-<name>` or `Use the <name> subagent to ...`.
- **Whole session**: `claude --agent <name>`, or set `"agent": "<name>"` in `.claude/settings.json` for a project default.
- If it doesn't trigger, see [reference/concepts.md](./reference/concepts.md#description-sells-the-subagent) — the description is almost always the cause.

---

## Update flow

### 1. Locate the target

Search for the agent by `name:` frontmatter (filename can differ):

- Project: `.claude/agents/` (walks up from CWD)
- User: `~/.claude/agents/`
- Plugin: `<plugin>/agents/` (note: plugin agents silently drop `hooks`, `mcpServers`, `permissionMode`)

If matches exist in multiple scopes, ask which one. Precedence (highest → lowest): managed > `--agents` CLI > project > user > plugin. See [reference/scopes.md](./reference/scopes.md).

### 2. Read the whole file

Frontmatter AND body matter equally — the body is the system prompt. Read both before proposing changes. If the agent preloads skills (`skills:` field), also read those.

See [reference/decision-questions.md](./reference/decision-questions.md) for the update-flow decisions (target scope when multiple matches, fields to change, rename / scope-move confirmation, destructive-delete confirmation).

### 3. Route the change

| Change | Where to look |
| :-- | :-- |
| `description`, `name`, `model`, `effort`, `maxTurns`, `isolation`, `color`, `initialPrompt`, `background` | [reference/frontmatter.md](./reference/frontmatter.md) |
| `tools`, `disallowedTools`, `Agent(<name>, <name>)` allowlist, `permissionMode` | [reference/tools-and-permissions.md](./reference/tools-and-permissions.md) |
| `mcpServers`, `skills` preload, `memory` (user/project/local) | [reference/context.md](./reference/context.md) |
| `hooks` (frontmatter + `settings.json`), validation script patterns | [reference/tools-and-permissions.md](./reference/tools-and-permissions.md) — hooks section |
| Rename: change `name:` (and/or the filename — filename ≠ identity) | [reference/scopes.md](./reference/scopes.md) — naming gotchas |
| Move scope (project ↔ user ↔ plugin) | [reference/scopes.md](./reference/scopes.md) — mind precedence + plugin restrictions |
| Convert to a coordinator | [reference/tools-and-permissions.md](./reference/tools-and-permissions.md) — `Agent(...)` |
| Invocation, foreground/background, fork mode, resume | [reference/invocation.md](./reference/invocation.md) |
| Doesn't trigger / triggers too often | [reference/concepts.md](./reference/concepts.md#description-sells-the-subagent) |

### 4. Apply the change

- Edit via `Edit`; preserve what already works.
- **Warn before** renaming or moving scope — both change how the agent is discovered and invoked.
- Plugin source? Either accept that `hooks` / `mcpServers` / `permissionMode` will be ignored, or copy the file out into `.claude/agents/` / `~/.claude/agents/`.

### 5. Restart and re-test

- Restart the session after editing on disk (or use the `/agents` UI to edit without restart).
- Re-test via `@agent-<name>` and via a request matching the new `description`.

---

## Explain flow

If the user just wants to understand a concept, don't trigger create/update. Route to the right reference:

| Question | Where |
| :-- | :-- |
| What is a subagent? Built-in vs custom? Subagent vs skill vs main? | [reference/concepts.md](./reference/concepts.md) |
| What does each frontmatter field do? | [reference/frontmatter.md](./reference/frontmatter.md) |
| Where do files live? Precedence? CLI flag? Plugins? | [reference/scopes.md](./reference/scopes.md) |
| Tools, `disallowedTools`, `permissionMode`, hook validation | [reference/tools-and-permissions.md](./reference/tools-and-permissions.md) |
| MCP scoping, preloading skills, persistent memory, what loads at startup, resume, compaction | [reference/context.md](./reference/context.md) |
| Automatic delegation, `@-mention`, `--agent`, foreground/background, fork mode, chaining | [reference/invocation.md](./reference/invocation.md) |

---

## Critical principles

- **One subagent, one job.** Description-based delegation only works when each agent's purpose is unambiguous. Generalist agents get picked for the wrong tasks.
- **Description is the trigger.** State *what it does* AND *when to use it*. Add "use proactively" / "use immediately" for things that should fire automatically.
- **Tools are blast radius.** Default-inherit gives the subagent everything the parent has, including MCP tools. Allowlist (`tools:`) is safer than denylist (`disallowedTools:`).
- **`bypassPermissions` is dangerous.** It skips prompts including writes to `.git`, `.claude`, `.vscode`, `.idea`, `.husky`. Use only when you understand what the subagent does.
- **CLAUDE.md and git status load** for every subagent except built-in `Explore` and `Plan`. You can't opt a custom subagent out.
- **Subagents can't spawn subagents.** Only a main-thread agent (`--agent`) can spawn workers via `Agent(<name>)`. For nested delegation, chain subagents from the main conversation or use skills.
- **Loaded at session start.** Edit on disk → restart. `/agents` UI edits propagate immediately.
- **Interactive by default** — when invoked via `subagent-architect`, every key decision is surfaced to the user via `AskUserQuestion` with options + recommendation + implications. See [reference/decision-questions.md](./reference/decision-questions.md).

## Common gotchas

- Two files with the same `name:` in one scope → one silently wins. Names must be unique across the whole tree per scope.
- Plugin subagents **silently ignore** `hooks`, `mcpServers`, and `permissionMode`. Copy the file out if you need them.
- Parent `bypassPermissions` / `acceptEdits` / `auto` **override** the subagent's `permissionMode`.
- Forks (experimental) require `CLAUDE_CODE_FORK_SUBAGENT=1` and replace the `general-purpose` agent. They cannot spawn further forks.
- `--add-dir` paths are **not scanned** for subagents — only CWD-rooted `.claude/agents/` and `~/.claude/agents/`.
- The filename does not determine the agent's id — `name:` in frontmatter does. Renaming the file alone has no effect.

## Reference

- [reference/concepts.md](./reference/concepts.md) — what a subagent is, built-in agents, subagent vs skill vs main
- [reference/frontmatter.md](./reference/frontmatter.md) — every YAML field, defaults, model resolution order
- [reference/scopes.md](./reference/scopes.md) — file locations, precedence, plugins, `--agents` CLI flag
- [reference/tools-and-permissions.md](./reference/tools-and-permissions.md) — `tools`, `disallowedTools`, `Agent(...)`, `permissionMode`, hook-based validation
- [reference/context.md](./reference/context.md) — what loads at startup, `skills` preload, `mcpServers`, `memory`, resume, compaction
- [reference/invocation.md](./reference/invocation.md) — automatic delegation, `@-mention`, `--agent`, foreground/background, fork mode, chaining

## Pattern References

- [reference/basic.md](./reference/basic.md) — minimum viable subagent
- [reference/code-reviewer.md](./reference/code-reviewer.md) — read-only review with restricted tools
- [reference/debugger.md](./reference/debugger.md) — analyze + fix with `Edit` allowed
- [reference/data-scientist.md](./reference/data-scientist.md) — domain specialist with `model: sonnet` pinned
- [reference/db-reader-hooks.md](./reference/db-reader-hooks.md) — `PreToolUse` hook gates SELECT-only SQL
- [reference/coordinator.md](./reference/coordinator.md) — main-thread agent that restricts spawnable workers via `Agent(...)`

## Output Examples

- [examples/create-basic-subagent-output.md](./examples/create-basic-subagent-output.md) — expected output for a minimal subagent
- [examples/create-restricted-subagent-output.md](./examples/create-restricted-subagent-output.md) — expected output for a subagent with restricted tools and a pinned model
- [examples/update-subagent-output.md](./examples/update-subagent-output.md) — expected final response after updating a subagent
