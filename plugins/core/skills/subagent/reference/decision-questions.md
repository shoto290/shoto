# Decision Questions Catalog

This catalog is consumed by [`subagent-architect`](../../../agents/subagent-architect.md). The agent must walk every applicable entry in order, present the options + implications + recommended option via `AskUserQuestion`, and treat any value already supplied in the user prompt as a pre-selection (not a reason to skip the question — surface the pre-selection for confirmation when it materially affects scope, tool access, or destructive actions).

---

## Create flow

### 1. Name (validation step — not an `AskUserQuestion`)

**Question**: not asked via `AskUserQuestion`.
**Multi-select**: n/a
**Skip when**: always skipped as a question — applied as a validation step on the proposed name.
**Validation rule**: lowercase letters and hyphens only (regex `^[a-z][a-z-]*$`); must start with a letter. The chosen `name` value becomes the identifier hooks receive as `agent_type` and the id used by `@agent-<name>`. Filename does **not** have to match `name:`, but by convention we keep them aligned (`<name>.md`).

### 2. Scope

**Question**: Where should this subagent live?
**Multi-select**: no
**Skip when**: never — always ask.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Project | Installed at `.claude/agents/<name>.md` — committed to the repo, scoped to this project, shared with every collaborator. | ✅ (default) |
| User | Installed at `~/.claude/agents/<name>.md` — available in every project on this machine, not shared. | |
| Plugin | Installed at `<plugin>/agents/<name>.md` — shipped via a plugin marketplace. **Silently drops** `hooks`, `mcpServers`, and `permissionMode`. | |

### 3. Purpose (validation step — not an `AskUserQuestion`)

**Question**: not asked via `AskUserQuestion`.
**Multi-select**: n/a
**Skip when**: always skipped.
**Validation rule**: the agent must do **one specific job**. If the spec describes a generalist ("does everything for module X"), stop and propose splitting into focused subagents — description-based delegation fails on generalists.

### 4. Description triggers

**Question**: Should the description include an auto-delegation trigger phrase?
**Multi-select**: no
**Skip when**: the user already wrote the description and an explicit trigger phrase is present.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| None | The description states *what* and *when*, but Claude only delegates when the request strongly matches. Lowest risk of false-positive delegation. | ✅ (default) |
| "Use proactively" | Adds an opt-in encouragement — Claude is more likely to delegate without being asked. Good for review / audit / cleanup agents. | |
| "Use immediately after …" | Strongest trigger — Claude tries to delegate as soon as the named situation occurs (e.g. "use immediately after writing or modifying code"). | |

### 5. Tools strategy

**Question**: How should this subagent's tool access be scoped?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Allowlist via `tools:` | Subagent gets **only** the listed tools. Safest. Loses inherited MCP tools unless they are listed explicitly. | ✅ (default) |
| Denylist via `disallowedTools:` | Subagent inherits everything from the parent **except** the listed tools. Preserves inherited MCP tools. Use when the agent legitimately needs most of the parent's tools but should not write/edit. | |
| Inherit everything (omit both) | Subagent has every tool the parent has, including all MCP tools. Permissive — avoid unless the agent is a coordinator. | |

### 6. Tools — which ones?

**Question**: Which tools does this subagent need?
**Multi-select**: yes
**Skip when**: strategy is "Inherit everything".

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Read | Read files. Required for almost every subagent. | |
| Glob | Filename pattern search. | |
| Grep | Content search. | |
| Bash | Run shell commands — highest blast radius; review carefully. | |
| Write | Create new files. Never include on a read-only reviewer. | |
| Edit | Modify existing files. Never include on a read-only reviewer. | |
| WebFetch | Outbound HTTP fetches. | |
| WebSearch | Web searches. | |
| Skill | Invoke skills during execution (separate from the `skills:` preload field). | |
| Agent | Spawn other subagents — **only relevant when this agent runs as the main thread** (`--agent`). Subagents cannot spawn subagents. | |
| Agent(name, name) | Restrict spawnable agents to an allowlist. Same caveat — only effective as the main thread. | |

(No single default — pick the minimal set the agent's workflow actually uses. Read-only reviewer = `Read, Grep, Glob`. Debug+fix = add `Edit, Bash`.)

### 7. Model

**Question**: Which model should this subagent run on?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| `inherit` | Uses the main conversation's model. Safest default; no surprise cost shift. | ✅ (default) |
| `haiku` | Fastest, cheapest. Right for high-volume read-only lookups (search, log scans). | |
| `sonnet` | Balanced. Right for review, analysis, data work. | |
| `opus` | Strongest reasoning, most expensive. Right for hard debugging or design analysis. | |
| Full model id | Pin to a specific version (e.g. `claude-opus-4-7`). Use when reproducibility matters. | |

### 8. Permission mode

**Question**: Which permission mode should the subagent run in?
**Multi-select**: no
**Skip when**: target scope is Plugin (the field is silently dropped).

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| `default` | Standard permission prompts surface for new tool calls. | ✅ (default) |
| `acceptEdits` | Auto-accepts file edits and common filesystem commands within CWD / `additionalDirectories`. Useful for high-volume edit agents. | |
| `auto` | Background classifier reviews commands and writes to protected directories. | |
| `dontAsk` | Auto-denies prompts. Explicitly allowed tools still work. | |
| `bypassPermissions` | Skips **all** prompts — including writes to `.git`, `.claude`, `.vscode`, `.idea`, `.husky`. Dangerous; require explicit user confirmation. | |
| `plan` | Plan-mode (read-only exploration). | |

Reminder: a parent session in `bypassPermissions` / `acceptEdits` / `auto` overrides the subagent's mode.

### 9. Persistent memory

**Question**: Should the subagent have a persistent memory directory?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| None | No persistent memory. The subagent restarts cold every invocation. | ✅ (default) |
| `project` | Memory at `.claude/agent-memory/<name>/` — committed to the repo, shareable. Auto-enables `Read`, `Write`, `Edit` so the agent can curate. | |
| `user` | Memory at `~/.claude/agent-memory/<name>/` — survives across all projects on this machine. | |
| `local` | Memory at `.claude/agent-memory-local/<name>/` — project-scoped but not version-controlled. | |

### 10. Preloaded skills

**Question**: Should the subagent preload any skills at startup?
**Multi-select**: yes
**Skip when**: the agent's body fully covers its workflow and no shared convention skill applies.

**Options**: dynamically built from skills in scope. Each option = one skill name (e.g. `api-conventions`, `error-handling-patterns`). The full skill content is injected at startup (not just the description). Skills with `disable-model-invocation: true` cannot be preloaded.

### 11. MCP servers

**Question**: Should the subagent scope any MCP servers?
**Multi-select**: yes
**Skip when**: target scope is Plugin (the field is silently dropped), OR the agent does not need MCP tools beyond what the parent provides.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| None | Inherits whatever MCP servers the parent has. | ✅ (default) |
| Inline | Defines servers inline in the agent file — connected when the subagent starts, disconnected when it finishes. Keeps server tool descriptions out of the main conversation. | |
| Reference by name | Reuses an already-configured server (e.g. `- github`). Shares the parent session's connection. | |

### 12. Lifecycle hooks

**Question**: Should the subagent run lifecycle hooks?
**Multi-select**: yes
**Skip when**: target scope is Plugin (the field is silently dropped), OR the workflow does not need pre/post tool validation.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| None | No hooks. | ✅ (default) |
| `PreToolUse` | Runs before each tool call. Common use: allow `Bash` only for read-only SQL. Exit code 2 blocks the call. | |
| `PostToolUse` | Runs after each tool call. Common use: lint after every `Edit`/`Write`. | |
| `Stop` | Runs when the subagent finishes (converted to `SubagentStop` at runtime). | |
| `SubagentStart` / `SubagentStop` (settings.json) | Project-level — fires in the main session when this agent type starts or stops. Configured in `.claude/settings.json`, not in frontmatter. | |

### 13. Run mode

**Question**: How should the subagent run by default?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Foreground | Blocks the main conversation until done; permission prompts surface to the user. | ✅ (default) |
| `background: true` | Always runs concurrently. Auto-denies any tool call that would prompt — relies on already-granted permissions. | |
| `isolation: worktree` | Runs inside a temporary git worktree (auto-cleaned if no changes). Use for parallel experiments or destructive trials. | |

### 14. Effort

**Question**: Should the subagent pin an effort level?
**Multi-select**: no
**Skip when**: the agent should follow the session's effort budget.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Inherit from session | No `effort` field. | ✅ (default) |
| `low` | Lowest cost, shortest reasoning. | |
| `medium` | Balanced. | |
| `high` | Longer reasoning budget. | |
| `xhigh` / `max` | Maximum reasoning. Model-dependent — only some models expose these. | |

### 15. `maxTurns`

**Question**: Should the subagent cap how many turns it can take?
**Multi-select**: no
**Skip when**: the workflow naturally bounds itself (e.g. single-shot review).

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No cap | Subagent runs until it returns or the session ends. | ✅ (default) |
| Numeric cap | Hard ceiling on agentic turns. Use when you want a guaranteed exit (e.g. background hourly agents). | |

### 16. `initialPrompt`

**Question**: Should the agent auto-submit a first-turn prompt when run as a main session (`claude --agent <name>`)?
**Multi-select**: no
**Skip when**: the agent is never intended to run as a main session.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | No `initialPrompt`. The user types their first message. | ✅ (default) |
| Yes | Auto-submitted first user turn (commands + skills are processed). Prepended to any user-provided prompt. | |

### 17. Color

**Question**: Pick a display color for the agent in the task list?
**Multi-select**: no
**Skip when**: aesthetics not requested.

**Options**: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. No default — leave unset unless the user asks for one.

---

## Update flow

### 1. Target scope when multiple matches

**Question**: The agent exists in multiple scopes — which one do you want to update?
**Multi-select**: no
**Skip when**: only one scope contains a matching `name:`.

**Options**: dynamically built from the matching scopes among Project / User / Plugin (omit scopes that don't match). One option per match; no default — the user must pick.

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Project | Edits `.claude/agents/<...>.md` — change is committed to the repo and affects every collaborator. | |
| User | Edits `~/.claude/agents/<...>.md` — change is local to the current user. | |
| Plugin | Edits `<plugin>/agents/<...>.md` — change ships with the next plugin release; `hooks`/`mcpServers`/`permissionMode` will be ignored. | |

### 2. Field(s) to change

**Question**: Which fields or sections do you want to change?
**Multi-select**: yes
**Skip when**: the user already named the exact target (e.g. "rewrite the body" — only one field implied).

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| description | Changes how Claude matches the agent against requests — high impact on auto-delegation. | |
| name | Renames the agent — changes the `agent_type` hooks see and the `@agent-<name>` id. | |
| tools / disallowedTools | Adjusts the blast radius. Removing a tool the body still references is a destructive change — confirm. | |
| model | Switches the model used to run the agent. | |
| permissionMode | Adjusts how permission prompts behave. Ignored on plugin agents. | |
| skills | Changes which skills preload at startup. | |
| mcpServers | Adjusts the MCP servers scoped to this agent. Ignored on plugin agents. | |
| hooks | Wires the agent into lifecycle events. Ignored on plugin agents. | |
| memory | Toggles or moves the persistent memory directory. | |
| effort / maxTurns / background / isolation / color / initialPrompt | Operational knobs — usually safe to change. | |
| body section | Edits a specific section of the markdown system prompt. | |

Note: changing `name:`, moving scope, or removing tools referenced by the body — chain into the confirmation steps below.

### 3. Confirm rename / move scope

**Question**: This change renames the agent or moves its scope — confirm?
**Multi-select**: no
**Skip when**: the user did not ask to rename or move scope.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Yes | Proceed. Renaming changes the `@agent-<name>` id, the `agent_type` hooks see, and any references in other configs. Scope move changes precedence and may collide with another scope. | |
| No | Abort the rename / scope move and ask the user for a different path. | ✅ (default) |

### 4. Confirm destructive delete

**Question**: This change removes a tool, hook, or section that the body still references — confirm?
**Multi-select**: no
**Skip when**: no removal is involved, OR the body does not reference the removed item.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Yes | Proceed. The body will reference something that no longer exists — at minimum, the body should be updated in the same edit. | |
| No | Abort the removal and ask the user for a non-destructive alternative. | ✅ (default) |
