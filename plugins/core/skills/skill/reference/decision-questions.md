# Decision Questions Catalog

This catalog is consumed by [`skill-architect`](../../../agents/skill-architect.md). The agent must walk every applicable entry in order, present the options + implications + recommended option via `AskUserQuestion`, and treat any value already supplied in the user prompt as a pre-selection (not a reason to skip the question — surface the pre-selection for confirmation when it materially affects scope, invocation, or destructive actions).

---

## Create flow

### 1. Name (validation step — not an `AskUserQuestion`)

**Question**: not asked via `AskUserQuestion`.
**Multi-select**: n/a
**Skip when**: always skipped as a question — applied as a validation step on the proposed name.
**Validation rule**: lowercase letters, digits, and hyphens only; must start with a letter; max 64 chars. Reject and ask the user to rename if the proposal fails. The chosen name becomes both the directory name and the slash command (unless overridden by `name:` in frontmatter).

### 2. Scope

**Question**: Where should this skill live?
**Multi-select**: no
**Skip when**: never — always ask.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Personal | Installed at `~/.claude/skills/<name>/` — available only to the current user, survives across every project on this machine. | |
| Project | Installed at `.claude/skills/<name>/` — committed to the repo, scoped to this project, shared with every collaborator. | ✅ (default) |
| Plugin | Installed at `<plugin>/skills/<name>/` — shipped as part of a plugin marketplace; discoverable only when the plugin is enabled. | |

### 3. Type

**Question**: Is this a reference (passive knowledge) or a task (performs work)?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Reference | Passive knowledge document loaded on demand. No tool calls, no side-effects — Claude reads it as context. | ✅ (default) |
| Task | Performs concrete work — may invoke tools, run commands, write files. Treat tool permissions carefully. | |

### 4. Invoker

**Question**: Who should be able to invoke this skill?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Both | Claude auto-loads when the `description` matches a request, AND the user can run `/skill-name` manually. | ✅ (default) |
| User only | Sets `disable-model-invocation: true` — Claude never auto-loads it. Recommended for side-effectful actions like deploy, commit, send-message. | |
| Claude only | Sets `user-invocable: false` — no slash command, only Claude can load it. Recommended for background-knowledge skills that shouldn't pollute the user's command list. | |

### 5. Arguments

**Question**: What arguments does this skill accept?
**Multi-select**: no
**Skip when**: never (default to None for reference skills).

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| None | No argument placeholders in the body. The skill runs the same way every time. | ✅ (default) |
| Free-form `$ARGUMENTS` | Everything typed after `/skill-name` is interpolated as a single string. | |
| Positional `$0 $1 $2…` | Whitespace-separated tokens after `/skill-name` map to numbered placeholders. Use when the skill expects a fixed argument shape. | |

### 6. Dynamic context (`!command` substitution)

**Question**: Should the skill inject live shell output before Claude reads the body?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | Body is static markdown. Lowest cost, no shell dependency. | ✅ (default) |
| Yes | Each `` !`command` `` runs once before the body is shown to Claude; output is interpolated literally and is NOT re-scanned for nested placeholders. Adds runtime cost and requires the command to be safe to run. | |

### 7. Isolation (`context: fork`)

**Question**: Should the skill run in an isolated subagent fork?
**Multi-select**: no
**Skip when**: never.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | Runs inline in the current turn — sees the full conversation, adds no extra token cost. | ✅ (default) |
| Yes | Runs in an isolated subagent fork — clean context window, can be parallelised, but loses access to current conversation turns and costs extra tokens. Requires an explicit task in the body (guidelines alone return nothing). | |

### 8. Pre-approved tools (`allowed-tools`)

**Question**: Which tools should be pre-approved for this skill?
**Multi-select**: yes
**Skip when**: type is Reference and no shell or file operations are needed.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Read | Skips the permission prompt for file reads. | |
| Write | Skips the permission prompt for file writes — review carefully for project-scope skills. | |
| Edit | Skips the permission prompt for in-place edits. | |
| Glob | Pre-approves filename pattern searches. | |
| Grep | Pre-approves content searches. | |
| Bash | Pre-approves shell commands — highest blast radius; review carefully. | |
| WebFetch | Pre-approves outbound HTTP fetches. | |
| WebSearch | Pre-approves web searches. | |
| Agent | Pre-approves spawning sub-agents. | |

(No single default — pick the minimal set the skill actually uses. Default to empty for reference skills.)

### 9. `template.md`

**Question**: Should the skill ship a single fill-in template that Claude uses to produce output?
**Multi-select**: no
**Skip when**: type is Reference, OR the skill does not produce structured output from a fixed template.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | No template file. The skill body itself describes the output format inline. Simpler and the default for almost every skill. | ✅ (default) |
| Yes | Adds `template.md` at the skill root. Claude reads it as the canonical output skeleton and fills in the blanks. Use only when the output truly is a fill-in-the-blank document (rare). |  |

See [slot-template.md](./slot-template.md) for the full slot reference.

### 10. `examples/`

**Question**: Should the skill ship sample expected outputs under `examples/`?
**Multi-select**: no
**Skip when**: the skill body already shows the output format clearly inline.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | No `examples/` directory. Keeps the skill self-contained. | ✅ (default) |
| Yes | Adds an `examples/` directory of sample expected outputs (e.g. `examples/create-output.md`). Loaded for format reference only. Anti-pattern: do NOT put prompt recipes, workflow patterns, or complete sample `SKILL.md` files here — those belong in `reference/`. |  |

See [slot-examples.md](./slot-examples.md) for the full slot reference.

### 11. `reference.md` or `reference/`

**Question**: Should the skill ship detailed reference docs loaded on demand?
**Multi-select**: no
**Skip when**: the SKILL.md body is expected to stay under ~500 lines and is self-contained.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | Everything lives in `SKILL.md`. Recommended while the skill is small. | ✅ (default) |
| Yes — single `reference.md` | One flat reference file at the skill root. Use when there's a single coherent doc to offload (e.g. a frontmatter reference). |  |
| Yes — `reference/` directory | A directory of focused reference files (e.g. `reference/frontmatter.md`, `reference/patterns.md`). Use when offloaded content splits naturally into multiple topics. Each file MUST be linked from `SKILL.md` so Claude knows when to load it. |  |

See [slot-reference.md](./slot-reference.md) for the full slot reference.

### 12. `scripts/`

**Question**: Should the skill bundle executable scripts invoked via `${CLAUDE_SKILL_DIR}`?
**Multi-select**: no
**Skip when**: type is Reference, OR the skill performs no deterministic computation that benefits from being in code.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| No | No bundled executables. The skill drives everything through prompt instructions and tool calls. | ✅ (default) |
| Yes | Adds a `scripts/` directory; the body invokes them via `${CLAUDE_SKILL_DIR}/scripts/<name>`. Use when the skill needs deterministic logic Claude shouldn't re-derive each run (parsers, validators, generators). Adds an execution dependency (Python / Node / shell must be available at runtime). |  |

See [slot-scripts.md](./slot-scripts.md) for the full slot reference.

---

## Update flow

### 1. Target scope when multiple matches

**Question**: The skill exists in multiple scopes — which one do you want to update?
**Multi-select**: no
**Skip when**: only one scope contains a matching skill.

**Options**: dynamically built from the matching scopes among Personal / Project / Plugin (omit scopes that don't match). One option per match; no default — the user must pick.

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Personal | Edits `~/.claude/skills/<name>/` — change is local to the current user. | |
| Project | Edits `.claude/skills/<name>/` — change is committed to the repo and affects every collaborator. | |
| Plugin | Edits `<plugin>/skills/<name>/` — change ships with the next plugin release. | |

### 2. Field(s) to change

**Question**: Which fields or sections do you want to change?
**Multi-select**: yes
**Skip when**: the user already named the exact target (e.g. "rewrite the body" — only one field implied).

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| description | Changes how Claude matches the skill against requests — high impact on auto-loading. | |
| name | Renames the skill — changes the slash command and discovery key. | |
| argument-hint | Updates the inline hint shown next to the slash command. | |
| arguments | Changes the argument shape (`$ARGUMENTS` vs positional). May break existing invocations. | |
| model | Pins the model used to run the skill. | |
| effort | Pins the thinking effort budget. | |
| paths | Restricts the skill to specific file paths. | |
| shell | Pins the shell used for `!command` substitution. | |
| hooks | Wires the skill into hook events. | |
| allowed-tools | Adjusts pre-approved tools — review carefully before committing. | |
| disable-model-invocation | Toggles whether Claude can auto-load the skill. | |
| user-invocable | Toggles whether the user can run `/skill-name`. | |
| context | Switches inline vs fork execution. | |
| agent | Pins the subagent used when `context: fork`. | |
| supporting files | Adds, removes, or rewrites files under `examples/`, `reference/`, `scripts/`. | |
| body section | Edits a specific section of the markdown body. | |

Note: changing `name:` or moving scope changes the slash command and discovery — chain into the rename / scope-move confirmation below.

### 3. Confirm rename / move scope

**Question**: This change renames the skill or moves its scope — confirm?
**Multi-select**: no
**Skip when**: the user did not ask to rename or move scope.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Yes | Proceed with the rename or scope move. Directory rename changes the `/command`; scope move changes discovery precedence. | |
| No | Abort the rename / scope move and ask the user for a different path. | ✅ (default) |

### 4. Confirm destructive delete

**Question**: This change deletes a section or supporting file — confirm?
**Multi-select**: no
**Skip when**: no deletion is involved.

**Options**:

| Label | Implication | Recommended? |
| :-- | :-- | :-- |
| Yes | Proceed with the deletion. Removed content cannot be silently recovered; outbound links to the removed file/section will break. | |
| No | Abort the deletion and ask the user for a non-destructive alternative. | ✅ (default) |
