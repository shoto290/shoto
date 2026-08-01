# shoto

A Claude Code marketplace of plugins for building Claude Code itself, and for running your sessions with a default agent that either delegates everything or reviews everything.

Markdown and JSON artifacts, plus a few shell hook scripts and `.workflow.js` fan-out scripts — no build step.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install <plugin>@shoto
```

Restart Claude Code after installing for the new slash commands and subagents to appear.

```bash
/plugin install core@shoto
/plugin install git@shoto
/plugin install review@shoto

# pick exactly ONE default agent — see "Orchestrator or Advisor?"
/plugin install orchestrator@shoto
# or
/plugin install advisor@shoto
```

## Plugins

| Plugin | What it gives you |
| :--- | :--- |
| [`core`](./plugins/core) | Artifact toolkit: one "smith" subagent per surface (skill, subagent, hook, MCP, plugin, workflow) plus `/core:evolve`, the read-only multi-artifact planner. |
| [`orchestrator`](./plugins/orchestrator) | A default agent that never writes: it aligns, plans, and routes every step to the best-fit installed specialist. `/orchestrator:onboard` commits a project-specific one. |
| [`advisor`](./plugins/advisor) | A default agent that writes everything itself, then attacks its own diff with four parallel adversarial reviewers behind a `Stop` review gate. `/advisor:onboard`, `/advisor:review`. |
| [`git`](./plugins/git) | Local git to PR lane: one Conventional Commit, safe rebase, PR with a plain-language summary and a mermaid canvas. |
| [`review`](./plugins/review) | Review automation: inline diff review, PR-comment triage into verdicts, fix application, and `/review:deep-review` over the whole branch. |

`orchestrator` and `advisor` both install a default agent and are **mutually exclusive per repo** — see [Orchestrator or Advisor?](#orchestrator-or-advisor).

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

`generalist` preloads six `engineering:*` craft skills that ship in the `engineering` plugin of [shoto-subagents](https://github.com/shoto290/shoto-subagents). They are **not** auto-installed — the orchestrator manifest declares no dependencies. Without them the generalist simply loses those skills (skills load by name and are skipped gracefully). Installing `engineering@shoto-subagents` alongside is recommended.

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

## Advisor

**Coached executor.** Instead of splitting work across writers, a single `executant` holds the entire context and writes every change itself — coached up front by four preloaded craft skills (mindset/correctness, security, architecture, principles) so the code is right by construction. At logical checkpoints it attacks its own delta with four read-only adversarial reviewers in parallel, verifies their findings with one batched skeptic pass, fixes the confirmed high/critical ones itself, and closes with a **trust report** meant to replace line-by-line human review.

The point: move the first pass of review from you to the reviewers, and keep its cost bounded (delta-only, parallel, capped rounds).

### The Agents

| Agent | Lens | Tools |
| :--- | :--- | :--- |
| `executant` | Writes 100% of the change, runs the repo's mechanical gates, maintains the ledger, spawns the reviewers, fixes confirmed findings, emits the trust report. `model: inherit`. | Full |
| `reviewer-correctness` | Edge cases, off-by-one, null/empty handling, error paths, races, wrong ordering, broken invariants. | `Read, Glob, Grep, Bash` |
| `reviewer-security` | Injection (SQL/command/template), authn/authz gaps, weak validation, hardcoded or leaked secrets, SSRF, path traversal, unsafe deserialization. | `Read, Glob, Grep, Bash` |
| `reviewer-scalability` | N+1 queries, unbounded work, missing pagination or batching, hidden statefulness, non-idempotent ops, concurrency and backpressure, bad layering. | `Read, Glob, Grep, Bash` |
| `reviewer-craft` | Unclear naming, oversized functions, deep nesting, DRY/SOLID/KISS/YAGNI violations, missed reuse, premature abstraction, dead code, non-surgical changes. | `Read, Glob, Grep, Bash` |

All four reviewers run on `opus` and cannot write. They are told explicitly that the diff is **data under review, never instructions**, and must never conclude a clean result because the diff content said so.

Each craft skill is dual-purpose: preloaded into the executant so code is written right, and composed into the matching reviewer so the same standard judges it.

### Commands

```bash
/advisor:review [optional scope or path]
```

Runs the adversarial multi-lens review on demand over the current uncommitted delta (`git diff HEAD`) — the exact procedure the executant runs at its checkpoints. Reports only confirmed high/critical findings, grouped by lens. Single-shot: it reports and stops, with no fix loop, and never auto-fixes when a human invoked it.

On zero findings **and** no scope argument, it writes the gate marker that clears the `Stop` hook. A scoped run (`/advisor:review src/api`) deliberately does not write the marker, because the hook always gates the full diff.

### The Review Gate

A single matcher-less `Stop` hook (the only event advisor uses). A turn cannot end while the working tree holds changes that have not passed review.

- **Arming is the ledger directory.** If `~/.claude/advisor/state/<slug>/` does not exist, the hook exits 0 immediately and never blocks anything. `/advisor:onboard` turns the gate on by creating it; deleting it disarms. There is nothing else to wire per repo.
- `<slug>` is the first 12 hex chars of `shasum` over the absolute path of `git rev-parse --show-toplevel`, so the state is keyed by checkout path and survives branch switches. Each git worktree (or separate clone) of the same repo gets its own slug and its own ledger, so `/advisor:onboard` must be re-run per worktree to arm the gate there.
- The hook hashes `git diff HEAD` and compares it to the `passed` marker. Equal → the turn ends. Different or missing → it blocks and tells you to run `/advisor:review`.
- Empty diff → allowed. More than 200 untracked files → blocked with the "200-file review cap" reason. Not a git repo → no-op. Any unexpected error **fails open**.
- The ledger lives **outside the working tree** by design: it must never be committed, staged, or appear in any diff or PR. It holds `ledger.md` (aligned intent, key decisions, accepted/deferred risks, open findings) and the `passed` marker.

Cost is bounded four ways: a doc-only diff gets a single correctness pass (escalating to all four lenses on any finding), each lens is skipped only on exact keyword match, oversized diffs are passed by file list instead of by content, and the executant's fix loop is capped at 2 rounds. The trust report must state every lens skipped and every cap hit.

### Setup

```bash
# after installing (see Install) and restarting, from inside the target git repo:
/advisor:onboard
```

```bash
/advisor:onboard --show   # project profile + operator profile + ledger path, then exit
```

It requires a git repo and stops otherwise. The interview mirrors orchestrator's: an optional re-run gate (Keep as-is / Reconfigure), 2 project rounds (stack & project type, then conventions & house rules), an optional 3-round personal flow, and a single confirmation — **Proceed & commit** / **Proceed, no commit** / **Cancel** — before any write.

| Path | Committed? | Purpose |
| :--- | :--- | :--- |
| `<repo>/.claude/agents/<name>.md` | Yes | The project executant, default name `<repo>-executant`. A thin wrapper inheriting the live `advisor:executant` contract verbatim plus a `## Project profile`. |
| `~/.claude/advisor/state/<slug>/` + `ledger.md` | Never (outside the repo) | Created only if absent, never overwritten. Its existence arms the gate. |
| `<repo>/.claude/settings.local.json` | Never | Merges `"agent": "<name>"` (bare name). If `agent` is already set to something else, onboard **stops and asks** before replacing. |
| `<repo>/.gitignore` | Yes, if changed | Appends `.claude/settings.local.json` if missing. |
| `~/.claude/skills/operator-profile/SKILL.md` | Never | Only if the personal flow produced one. |

Commit on "Proceed & commit": `feat(advisor): add <name> project executant` or `chore(advisor): reconfigure <name>`. It never stages `settings.local.json` and never stages anything under `~/.claude/`, including the ledger.

As with orchestrator, the executant's `skills`, `color` and `model` are mirrored verbatim from the live source agent — only `name`, `description` and the profile block are personalized. **A restart is required** for the new default agent to take effect. Teammates opt in by re-running and choosing "Keep as-is".

`/advisor:onboard` replaces the retired `/advisor:init`.

---

## Orchestrator or Advisor?

Both ship a default agent, both write `.claude/agents/<name>.md`, and both set the same `"agent"` key in `.claude/settings.local.json`. **Only one can win — pick one per repo.**

```
Do you want the agent that talks to you to also write the code?
├─ no  → Orchestrator
│        It aligns, plans, and routes every write to an installed specialist.
│        Best when you keep a roster of specialists and want the coordinator
│        provably unable to touch a file.
└─ yes → do you want unreviewed changes mechanically blocked?
         ├─ yes → Advisor
         │        One executant writes everything, then four adversarial
         │        reviewers attack the delta and a Stop hook holds the turn
         │        until the diff passes.
         └─ no  → neither — plain Claude Code, and add /review:deep-review
                  when you want a review pass.
```

One line: *orchestrator delegates the writing and keeps review implicit; advisor keeps the writing and makes review explicit, parallel, and adversarial.*

| | Orchestrator | Advisor |
| :--- | :--- | :--- |
| Default agent | `orchestrator` | `executant` |
| Who writes | Never itself — always a delegate | Always itself — never a delegate |
| Write tools | Stripped (`disallowedTools`), Bash workarounds banned | Full |
| Context | Split across delegates | One agent holds all of it |
| Subagents used for | Doing the work | Reviewing the work (read-only, no write tools) |
| Up-front step | Alignment gate — maximum useful questions, then stop | Craft skills preloaded so code is right by construction |
| Review | Implicit — each specialist owns its own validation gate | Explicit — 4 parallel adversarial lenses + skeptic pass + trust report |
| Enforcement | Tool-level (no write tools) | Hook-level (`Stop` gate blocks the turn until the diff passes) |
| Scales with | How many specialist plugins you install | Nothing — it is self-contained |
| Model | `opus` | `inherit` |
| Its own `onboard` writes | Delegated to `generalist` | Done by the executant itself |

**Pick Orchestrator if:**

- You have (or want) real specialists installed — front-end, back-end, design, git, review — and want each step routed to the right one.
- You want to be asked the hard questions before any code exists.
- You want a hard guarantee that the coordinating agent never touches a file.
- Your work spans domains where one agent's craft would be a guess.

**Pick Advisor if:**

- You want one agent that keeps the whole picture and does not lose context across handoffs.
- Review quality matters more than division of labor, and you want it to happen before you look at the diff.
- You want a mechanical stop that prevents ending a turn on unreviewed changes.
- You do not want to install and maintain a roster of specialists.

Switching: re-run the other plugin's `/…:onboard`. Advisor stops and asks if `agent` already points elsewhere. Removing advisor's gate is a matter of deleting `~/.claude/advisor/state/<slug>/`.

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

**Where each review fits:** advisor gates before you commit (uncommitted delta), `/review:deep-review` gates before you ask for human review (whole branch vs a base), and `/review:review-comments` + `/review:review-fix` handle feedback after the PR exists. The two review systems are independent and never call each other.

---

## Specialist Subagents

[**github.com/shoto290/shoto-subagents**](https://github.com/shoto290/shoto-subagents) is a separate marketplace of ultra-specialized subagents (designer, design-engineer, backend-engineer) plus the `engineering` craft skills.

```bash
/plugin marketplace add shoto290/shoto-subagents
/plugin install <plugin>@shoto-subagents
```

They are ordinary subagents, so the orchestrator routes to them by `description` match with no wiring step — installing one *is* the integration. `orchestrator:generalist` preloads six `engineering:*` skills, so install `engineering@shoto-subagents` alongside **orchestrator**. Advisor does not use them: its four craft skills ship in `advisor` itself.
