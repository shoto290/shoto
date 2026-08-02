# shoto

A Claude Code marketplace of plugins for building Claude Code itself, and for running your sessions with a default agent that delegates every write to a specialist.

Markdown and JSON artifacts, plus a few shell hook scripts and `.workflow.js` fan-out scripts — no build step.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install <plugin>@shoto
```

Restart Claude Code after installing for the new slash commands and subagents to appear.

```bash
/plugin install git@shoto
/plugin install review@shoto
/plugin install orchestrator@shoto
```

`core` is a hard dependency of every other plugin and installs automatically — you never install it by hand.

## Plugins

| Plugin | What it gives you |
| :--- | :--- |
| [`core`](./plugins/core) | Artifact toolkit: one "smith" subagent per surface (skill, subagent, hook, MCP, plugin, workflow) plus `/core:evolve`, the read-only multi-artifact planner. |
| [`orchestrator`](./plugins/orchestrator) | A default agent that never writes: it aligns, plans, and routes every step to the best-fit installed specialist. `/orchestrator:onboard` commits a project-specific one. |
| [`git`](./plugins/git) | Local git to PR lane: one Conventional Commit, safe rebase, PR with a plain-language summary and a mermaid canvas. |
| [`review`](./plugins/review) | Review automation: inline diff review, PR-comment triage into verdicts, fix application, and `/review:deep-review` over the whole branch. |

---

## Core — The Artifact Toolkit

`core` is for building Claude Code artifacts. Each surface gets a **knowledge skill** (authoring rules, frontmatter, references, validation gate) paired with a **smith subagent** that preloads it and does the writing. Under all of them sits `core:base`, the single canonical statement of principles, mandatory frontmatter, and validation rules — so conventions live in one file instead of six copies. Alongside it sits `core:response-style`, the shared answer format that user-facing agents preload.

Installing `core` creates nothing in your repo: 9 skills, 6 subagents, no `commands/` directory (`/core:evolve` is a user-invocable skill), no hooks.

### The Smiths

Smiths are **subagents, not slash commands**. Every skill in `core` except `evolve` is `user-invocable: false` — hidden from the `/` menu.

| Smith | Owns | Reach it with |
| :--- | :--- | :--- |
| `skill-smith` | `SKILL.md` files — frontmatter, scope, supporting files, validation gate | `@agent-core:skill-smith` |
| `subagent-smith` | Subagent definitions — description tuning so delegation fires, tool lockdown, skill preloading, seven-field gate | `@agent-core:subagent-smith` |
| `hooks-smith` | Lifecycle hooks — event/type/matcher choice, the `settings.json` or `hooks.json` entry, the hook script | `@agent-core:hooks-smith` |
| `mcp-smith` | Project-level MCP servers — transport and scope, secrets via env vars, `.mcp.json` entry, connection check | `@agent-core:mcp-smith` |
| `plugin-smith` | The plugin shell — `plugin.json`, directory layout, version bumps, marketplace distribution | `@agent-core:plugin-smith` |
| `workflow-smith` | `.workflow.js` fan-out scripts — phases, stage schemas, distribution model, wrapper `SKILL.md` | `@agent-core:workflow-smith` |

Three ways a smith actually runs:

1. **Automatic delegation** — Claude matches your request against the smith's `description` ("create a skill", "this hook does not fire").
2. **Forced mention** — `@agent-core:skill-smith`. Plugin subagents are namespaced `@agent-<plugin>:<name>`.
3. **Skill tool from another agent** — `Skill({ skill: "core:skill" })`.

All six run on `opus`.

### Evolve

The only user-typeable command in `core`.

```bash
/core:evolve [capability or feature description]
```

A smith is a **writer scoped to one artifact**. `evolve` is a **read-only surveyor scoped to a capability**: you know what you want the system to do, but not how many artifacts it takes, which paths they live at, what order to build them in, or whether something already covers it.

| | Use `evolve` | Go straight to a smith |
| :--- | :--- | :--- |
| You know | The capability | The artifact and its path |
| Output | A plan, nothing written | The file itself |
| Spans | Several surfaces | One surface |

**Read-only is enforced, not just stated:** `allowed-tools: [AskUserQuestion, Read, Glob, Grep]` — no Write, no Edit, no Bash. "Nothing is created, edited, or scaffolded — on any path, including 'just this one small file'."

It returns a markdown plan only — one numbered entry per artifact (path, why, restart, setup mode, full spec), ordered dependency-first, plus conflicts and a test plan. Each entry is self-contained and executor-agnostic, so you hand it straight to the matching smith.

---

## Orchestrator

**Conductor, never a builder.** Wired as the session's default agent, so every prompt lands on it first: it clarifies intent through an alignment gate, states a plan, then routes each step to the best-fit installed subagent, skill, or workflow. It never writes a file itself.

The write ban is enforced twice: the harness strips its write tools (`disallowedTools: Write, Edit, MultiEdit, NotebookEdit`) and the contract forbids laundering the same work through Bash — here-docs, `tee`, `sed -i`, `cp`, `git checkout`, `--write` formatters.

### How a Turn Runs

1. **Align** — `orchestrator:alignment` runs first on every new task. Restate the task in one sentence → enumerate every unstated dimension (goal, scope in/out, target files, inputs, output format, constraints, acceptance criteria, edge cases) → ask the maximum set of *genuinely useful* questions in one batched `AskUserQuestion`, each with 2-4 concrete options carrying implications and a recommended default → produce an "Aligned intent" recap → stop and hand control back. Questions already answered by the request are dropped. Skipping is allowed only for a trivial unambiguous task, and the orchestrator must say why.
2. **Plan** — state the steps.
3. **Delegate** — every create/edit/restore *and its verification* (tests, build, lint, format) goes to the most specific installed specialist. The specialist owns its own validation gate.
4. **Fall back** — `orchestrator:generalist` only when no specialist matches.

### How It Finds Delegates

There is no registry, no config file, no wiring step. The contract tells the orchestrator to scan the live lists already in its context — the Agent tool's subagents, the Skill tool's skills, the Workflow tool's workflows — name the capability the step needs, and route by `description` match. Verbatim: *"These lists reflect exactly what is installed right now and adapt to whatever plugins the user has, so never rely on a memorized or hardcoded roster."*

Selection rules: match on `description` / `when_to_use`; when several fit, pick the most specific; for fan-out at scale prefer a workflow over a single subagent; delegation is the default path, not a fallback. If files go missing or a step cannot be delegated, it stops and surfaces it — it never reconstructs a file from memory and never reports as verified work it did not delegate.

**Consequence:** installing more specialist plugins *is* the integration. See [Specialist subagents](#specialist-subagents).

### Agents

| Agent | Role |
| :--- | :--- |
| `orchestrator` | Default agent and coordinator. `disallowedTools: Write, Edit, MultiEdit, NotebookEdit`, `model: opus`. Never auto-delegated — it is wired as the default, not invoked by another agent. |
| `generalist` | Catch-all fallback **writer**. `tools: Read, Write, Edit, Bash, Grep, Glob`, `model: opus`. Restates the task and its success check, searches for existing patterns before writing, makes the smallest surgical change, and is instructed to STOP and name the missing capability when a task needs real expertise instead of forcing it through. Also the executor `/orchestrator:onboard` delegates all of its own writes to. |

`generalist` preloads only `orchestrator:base`, so it carries the marketplace's shared conventions and nothing out-of-marketplace.

### Setup

```bash
# after installing (see Install) and restarting:
/orchestrator:onboard
```

```bash
/orchestrator:onboard --show   # print the current project profile + operator profile, change nothing
```

Two independent flows, all questions via `AskUserQuestion` (≤4 options each, free-text "Other" always available):

| Step | What it asks |
| :--- | :--- |
| Re-run gate | Only if a project orchestrator already exists: **Keep as-is** or **Reconfigure**. "Keep as-is" skips the interview but still wires your local opt-in. |
| Flow A, round A | Project type · primary language · frameworks/runtime (multi) · package manager |
| Flow A, round B | Test command · lint/format · commit convention · house rules (multi) |
| Flow B gate | "Personalize for yourself too?" — yes / no, or Keep / Reconfigure / Skip if a profile exists |
| Flow B, 3 rounds | Role & expertise · communication & tone · output & workflow style |
| Naming | Defaults to `<repo>-orchestrator`; confirm or override. Reconfigure never renames. |
| Confirmation | **Proceed & commit** / **Proceed, no commit** / **Cancel** |

What it writes (all writes delegated to one `orchestrator:generalist` — the skill itself never writes):

| Path | Committed? | Purpose |
| :--- | :--- | :--- |
| `<repo>/.claude/agents/<name>.md` | Yes | The project orchestrator. Explicitly not gitignored. |
| `<repo>/.claude/settings.local.json` | Never | Merges only the top-level `"agent": "<name>"` key, preserving siblings. This is the per-user opt-in. |
| `<repo>/.gitignore` | Yes, if changed | Ensures `.claude/settings.local.json` is listed. |
| `~/.claude/skills/operator-profile/SKILL.md` | Never (outside the repo) | Your personal profile, only if Flow B ran. |

On "Proceed & commit": `git add` the agent file plus `.gitignore` if it changed, then `feat(orchestrator): add <name> project orchestrator` (or `chore(orchestrator): reconfigure <name>`). It never stages `settings.local.json` and never stages anything under `~/.claude/`.

**Nothing is hardcoded.** Onboard globs for the live `orchestrator.md` (marketplace copy first, then repo-local, then `~/.claude/agents/`) and mirrors its `disallowedTools`, `skills`, `color`, `model`, and its single operating sentence **verbatim**. Only `name`, `description`, and an injected `## Project profile` block are personalized. The generated wrapper is therefore a **snapshot** — re-run and choose Reconfigure to refresh it.

**How it becomes the default agent:** not agent frontmatter, not `.claude/settings.json`. It is the top-level `"agent"` key in the gitignored `<repo>/.claude/settings.local.json`, holding the **bare** agent name (e.g. `{ "agent": "shoto-orchestrator" }`), matching `name:` in `.claude/agents/<name>.md`. Deliberately not plugin-namespaced, because it is a project agent. **A Claude Code restart is required** for it to take effect.

**Teammates opt in** by re-running `/orchestrator:onboard` and choosing "Keep as-is" — that writes only `settings.local.json` and `.gitignore`, touching no committed file.

---

## Git & Review

Neither plugin has an onboard command, writes config, or installs hooks. Installing them just adds the commands and subagents.

### git

```bash
/git:commit
/git:rebase [base-branch]
/git:create
```

| Command | Does |
| :--- | :--- |
| `/git:commit` | Reads `CLAUDE.md`/`AGENTS.md`, inspects the tree, creates exactly **one** Conventional Commit from staged + unstaged changes. Stops cleanly on a clean tree; refuses to stage `.env`, `*.pem`, `*.key`, `*.cert`, `secrets/`. Never pushes. |
| `/git:rebase [base-branch]` | Creates a UTC-timestamped `backup/<branch>-<ts>` branch, rebases onto the default branch (or the given base), auto-resolves trivial conflicts and escalates the rest via `AskUserQuestion`, verifies the commit count, shows the diff vs the backup. Ends by offering a confirmed `--force-with-lease` push — declining just prints the command. |
| `/git:create` | Resolves the default branch via `gh`, `git push -u origin HEAD`, then `gh pr create` with a Conventional Commit title, a non-developer-friendly summary, and, when the change moves structure, a mermaid canvas of it. Never pushes to main/master/the default branch, never force-pushes. |

Subagent: `git-flow` — delegate for shipping current work end-to-end; owns the commit → rebase → create sequence. `model: sonnet`.

### review

```bash
/review:review-diff
/review:review-comments [paste comments or @PR-url]
/review:review-fix [paste /review:review-comments output]
/review:deep-review [--auto-fix] [--base <branch>]
```

| Command | Does |
| :--- | :--- |
| `/review:review-diff` | One read-only pass over the current workspace diff against the 8 bug criteria, posting one inline `mcp__conductor__DiffComment` per finding plus a numbered summary. |
| `/review:review-comments` | Triages PR comments into one verdict block each — FIX, FIX-STYLE, INTENTIONAL, OUT-OF-SCOPE, DISCUSS — with reason, action, and confidence. With no argument it auto-fetches the branch's unresolved threads via `gh`; with pasted text or a URL it never calls `gh`. Read-only. |
| `/review:review-fix` | Keeps only FIX and FIX-STYLE, delegates each item to its own subagent one at a time with minimal surgical edits, then runs auto-detected verification. Never re-opens INTENTIONAL/OUT-OF-SCOPE/DISCUSS, stops on the first regression, never commits or pushes. |
| `/review:deep-review` | Fans out one reviewer per lens (correctness, security, performance, style/maintainability) over the branch diff in parallel, dedupes, triages every finding into a verdict, renders findings + verdict blocks + decision counts. Default `--base` is `origin/main`. Read-only by default: it asks (Apply now / Skip) before applying fixes; `--auto-fix` skips that gate. |

Subagents: `review-diff` (`opus`), `review-comments` (`sonnet`), `review-fix` (`sonnet`) — `/review:deep-review` fans these out; they are also delegable directly.

**Prerequisites:** `gh` installed and authenticated for `/git:create` and `/review:review-comments` auto-fetch; the Conductor MCP tools `mcp__conductor__GetWorkspaceDiff` and `mcp__conductor__DiffComment` for `/review:review-diff` (it falls back to the git CLI for the diff, but inline comments need the MCP tool).

**Where each review fits:** `/review:deep-review` gates before you ask for human review (whole branch vs a base), and `/review:review-comments` + `/review:review-fix` handle feedback after the PR exists.

---

## Specialist Subagents

[**github.com/shoto290/shoto-subagents**](https://github.com/shoto290/shoto-subagents) is a separate marketplace of ultra-specialized subagents (designer, design-engineer, backend-engineer) plus the `engineering` craft skills.

```bash
/plugin marketplace add shoto290/shoto-subagents
/plugin install <plugin>@shoto-subagents
```

They are ordinary subagents, so the orchestrator routes to them by `description` match with no wiring step — installing one *is* the integration.
