---
name: onboard
description: 'Personalize and commit a project orchestrator. Runs a short professional interview and generates a thin-wrapper orchestrator agent — committed to `.claude/agents/` — that inherits the live core:orchestrator contract plus an operator profile. Each user opts in locally via `.claude/settings.local.json` (gitignored). Re-run to keep your local opt-in or reconfigure the committed orchestrator.'
when_to_use: "/workflow:onboard, 'set up my orchestrator', 'personalize my orchestrator', 'create my operator profile', 'tune how Claude works for me', 'onboard me'. NOT for adding or evolving skills/subagents/hooks (use /workflow:evolve), and NOT for generating a CLAUDE.md (use the built-in /init)."
argument-hint: '[--show]'
allowed-tools: [AskUserQuestion, Read, Glob, Bash, Agent]
---

# Onboard

`onboard` personalizes a **committed project orchestrator** and a **per-user local opt-in**. It runs a short professional interview (role, tone, output style, delegation rules), reads the live `core:orchestrator` contract as the source of truth, and assembles a thin-wrapper orchestrator agent that **inherits** that contract verbatim plus an injected operator-profile block. The agent is a committed artifact under `.claude/agents/`; each teammate opts in locally by setting `"agent": "<name>"` in the gitignored `.claude/settings.local.json`. The skill never writes files itself — it delegates every write and commit to a `core:generalist` subagent. On re-run, if an orchestrator already exists, the very first question is **Keep as-is vs Reconfigure**.

```
/workflow:onboard
 ├─ parse flags (--show)
 ├─ locate LIVE core:orchestrator (source of truth)            [unchanged]
 ├─ detect existing PROJECT orchestrator in .claude/agents/
 │    ├─ found → FIRST QUESTION: Keep as-is | Reconfigure
 │    │    ├─ Keep as-is → wire settings.local.json + gitignore → report (STOP; no interview)
 │    │    └─ Reconfigure → prefill from existing → interview → rewrite same file
 │    └─ none → fresh: interview
 ├─ interview (3 rounds)                                       [unchanged]
 ├─ resolve name (<repo>-orchestrator) → .claude/agents/<name>.md (committed)
 ├─ build content (mirrored contract + ## Operator profile)    [unchanged]
 ├─ confirm write + commit
 ├─ delegate to core:generalist: write agent + merge settings.local.json + ensure gitignore + targeted commit
 └─ report + restart reminder + opt-in note
```

This skill owns the interview, sourcing, name resolution, and rendering. All file writes and the commit are delegated, keeping `onboard` compatible with the no-write orchestrator contract.

## 1. Parse flags

- `--show` → locate the existing project orchestrator (see §3), Read its `## Operator profile` block, render it to the user, and **exit without changes**. If none is found, say so and stop.
- An unknown flag is ignored.

## 2. Locate the live orchestrator (source of truth)

`Glob` for the installed core orchestrator, in this order, and use the **first** match:

1. `~/.claude/plugins/marketplaces/*/plugins/core/agents/orchestrator.md`
2. `plugins/core/agents/orchestrator.md` (repo-local fallback)
3. `~/.claude/agents/orchestrator.md`

`Read` the matched file. From its **frontmatter**, capture the behavior-contract keys to mirror **verbatim** into the generated wrapper: `disallowedTools`, `skills`, `color`, and `model` only if it is present. From its **body**, capture the single-sentence operating instruction **verbatim** — the wrapper reuses it unchanged, before the profile block.

**Never hardcode the orchestrator's behavior or skills list.** Always read them live here so the generated wrapper tracks upstream changes to `core:orchestrator`. If no source matches, tell the user the `core` plugin must be installed and **stop** — there is nothing to inherit.

## 3. Detect existing project orchestrator (re-run aware)

Find any orchestrator this skill previously committed to the repo:

- `Glob` `.claude/agents/*.md`; `Read` each and select those whose body contains a `## Operator profile` block (the onboard signature).
- If **exactly one** → that is the existing project orchestrator; capture its `name:` and its `## Operator profile` block.
- If **multiple** → ask via `AskUserQuestion` which one is the target.
- If **none** → this is a fresh creation; skip the §4 gate and go straight to the interview (§5).

Also Read `.claude/settings.local.json` and capture any top-level `agent` value — it tells whether **this** user is already opted in.

## 4. First-question gate (re-run only)

Runs **only** when §3 found an existing orchestrator, **before** any interview. `AskUserQuestion` with two options:

- **Keep as-is** — no interview, agent untouched. Delegate a lightweight wiring step (the keep path of §9): merge `.claude/settings.local.json` `"agent": "<name>"` (preserve siblings); ensure `.gitignore` covers `.claude/settings.local.json` (append if missing); if `.gitignore` changed, confirm + commit ONLY `.gitignore`. Then report (§10) and **STOP**.
- **Reconfigure** — prefill the interview defaults from the detected `## Operator profile`, proceed to §5, and rewrite the **same file/name** in place (no rename).

## 5. Interview (3 rounds via AskUserQuestion)

Run three `AskUserQuestion` rounds. Each option set is ≤4 options; rely on the automatic free-text **Other** for anything outside the list. On a **Reconfigure** (§4), pre-select / pre-fill every option from the detected profile.

- **Round A — Role & expertise**
  1. Role/title — Backend eng · Frontend/Design eng · Full-stack · Lead/Staff
  2. Seniority — Junior · Mid · Senior · Staff+/Lead
  3. Primary stack/domains (multiSelect) — TypeScript/React · Node/backend · Python · Infra/DevOps
  4. Current focus — free-text via Other
- **Round B — Communication & tone**
  1. Concision — Very concise · Balanced · Detailed
  2. Register — Direct/no-fluff · Diplomatic/nuanced · Casual/fun
  3. Response language — French · English · Match my message
  4. Emojis — None · Sparing · OK
- **Round C — Output & workflow style**
  1. Format — Bullets-first · Prose · Code-first
  2. Explanation depth — Minimal/essentials · Moderate · Deep/teaching
  3. Autonomy — Ask before acting · Act then report · By risk level
  4. Verification rigor — Always test/lint · By impact · Fast

Collect the answers into a single resolved profile used in §7.

## 6. Resolve name & location

- Location is **always** `.claude/agents/<name>.md` in the repo — a committed artifact. There is no global/project question.
- On **Reconfigure** → reuse the detected name/path; do **not** rename.
- On **fresh** → derive the default name `<repo>-orchestrator`, where `<repo>` is the kebab-cased basename of `git rev-parse --show-toplevel`. Confirm it or let the user override via `AskUserQuestion` (with Other). The name MUST be kebab-case and unique among existing agents.
- The `settings.local.json` `agent` value equals the **bare** `name:` — NOT plugin-namespaced, since this is not a plugin agent.

## 7. Build the generated orchestrator content

Assemble the file content from the mirrored values captured in §2 and the profile from §5. Only `name`, `description`, and the `## Operator profile` block are personalized — the body sentence and the behavior-contract frontmatter are mirrored, **never invented**:

```
---
name: <name>
description: "<personalized one-liner — e.g. '<Handle>'s personal orchestrator: generalist coordinator tuned to their operator profile. Inherits the full core:orchestrator contract; never writes files, delegates to writer subagents.'>"
disallowedTools: <mirrored verbatim from source>
skills: <mirrored verbatim from source>
color: <mirrored from source>
---

<verbatim one-sentence body from the source orchestrator>

## Operator profile

- **Role**: <…>  **Seniority**: <…>  **Stack/domains**: <…>  **Focus**: <…>
- **Tone**: <concision> · <register> · responds in <language> · emojis: <…>
- **Output**: <format> · <depth> · autonomy: <…> · verification: <…>

Apply this profile to every task: shape tone, verbosity and output format to it. This profile refines HOW you communicate and decide — it never overrides the core:orchestrator operating contract above.
```

If the source declared `model`, include the mirrored `model` line; otherwise omit it.

## 8. Confirm write + commit

Before any write, `AskUserQuestion` summarizing the planned effect — the agent will be committed to `.claude/agents/<name>.md`; `settings.local.json` stays local/gitignored; `.gitignore` is ensured — with three options:

- **Proceed & commit** — write everything and run the targeted commit (§9.4).
- **Proceed, no commit** — write everything, skip the commit.
- **Cancel** — stop with nothing written.

## 9. Delegate the writes + commit (core:generalist)

This skill MUST NOT Write/Edit itself — it may run under the no-write orchestrator. Spawn **one** `core:generalist` subagent via `Agent`, passing the full resolved file content from §7 and these exact instructions:

1. Write/overwrite the orchestrator markdown to `<repo>/.claude/agents/<name>.md` (create parent dirs). This is a **COMMITTED** artifact — do NOT add it to `.gitignore`.
2. Merge into `<repo>/.claude/settings.local.json`: set the top-level key `"agent": "<name>"`. If the file is absent, create it as `{ "agent": "<name>" }`. If present, ADD/REPLACE only the `agent` key and PRESERVE all sibling keys (e.g. `ultracode`) — never replace the whole object.
3. Ensure `.gitignore` covers `.claude/settings.local.json` (append the line if missing). The agent file is NOT gitignored.
4. If the user chose **Proceed & commit**: run a targeted commit — `git add .claude/agents/<name>.md` plus `.gitignore` ONLY if it changed, then `git commit` with a Conventional Commit message: `feat(orchestrator): add <name> project orchestrator` (fresh) or `chore(orchestrator): reconfigure <name>` (reconfigure). NEVER `git add` `settings.local.json`. No co-author line, no "Generated with Claude Code".
5. Return the list of paths written/updated and the commit result (or "no commit").

After the subagent returns, report what changed.

## 10. Report & restart

Summarize:

- the committed orchestrator path,
- the local `settings.local.json` wiring (`"agent": "<name>"`),
- the `.gitignore` touch, if any,
- the commit result, if any,
- the captured `## Operator profile`.

Flag that a Claude Code **restart is required** for the new default agent to take effect, and that `/reload-plugins` (or a restart) was needed for `/workflow:onboard` itself to appear. Note that **teammates opt in** by re-running `/workflow:onboard` and choosing **Keep as-is**.

## Critical principles

- **Commits the orchestrator, never the opt-in.** The orchestrator agent is a committed project artifact; `.claude/settings.local.json` is the per-user opt-in — never committed, always gitignored.
- **No hardcoding.** Behavior, skills, and the body sentence are always read live from the installed core orchestrator (§2); only identity and the `## Operator profile` block are personalized.
- **The skill never writes files itself.** It delegates every write and the commit to `core:generalist`, staying compatible with the no-write orchestrator contract.
- **Re-runnable with a first-question gate.** An existing orchestrator → Keep as-is (local opt-in only) or Reconfigure (rewrite the committed file in place).
