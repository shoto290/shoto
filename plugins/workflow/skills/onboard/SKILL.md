---
name: onboard
description: "Set up a committed project orchestrator and, optionally, your personal operator profile. Runs a short PROJECT interview (stack + conventions) and generates a thin-wrapper orchestrator agent — committed to `.claude/agents/` — that inherits the live core:orchestrator contract plus a `## Project profile`. Optionally runs a personal interview and writes a preloadable `operator-profile` skill to `~/.claude/skills/` (per-user, never committed). Each user opts in locally via `.claude/settings.local.json` (gitignored). Re-run to keep or reconfigure either."
when_to_use: "/workflow:onboard, 'set up my orchestrator', 'configure the project orchestrator', 'set the project stack and conventions', 'personalize for myself', 'create my operator profile', 'tune how Claude works for me', 'onboard me'. NOT for adding or evolving skills/subagents/hooks (use /workflow:evolve), and NOT for generating a CLAUDE.md (use the built-in /init)."
argument-hint: '[--show]'
allowed-tools: [AskUserQuestion, Read, Glob, Bash, Agent]
---

# Onboard

`onboard` runs **two independent flows**. **Flow A** sets up a **committed project orchestrator**: a short PROJECT interview (stack + conventions) produces a thin-wrapper agent under `.claude/agents/` that **inherits** the live `core:orchestrator` contract verbatim plus an injected `## Project profile` block; each teammate opts in locally by setting `"agent": "<name>"` in the gitignored `.claude/settings.local.json`. **Flow B** is optional and per-user: if the user wants to personalize for themselves, the SAME 3-round personal interview produces a user-scope `operator-profile` skill written to `~/.claude/skills/` — outside the repo, never committed, preloaded into orchestrators by name. The skill never writes files itself — it delegates every write and commit to a `core:generalist` subagent. On re-run, if an orchestrator already exists, the very first question is **Keep as-is vs Reconfigure**.

```
/workflow:onboard
 ├─ parse flags (--show)
 ├─ locate LIVE core:orchestrator (source of truth)           [§2 unchanged]
 ├─ FLOW A — PROJECT orchestrator (committed)
 │   ├─ detect existing by `## Project profile` signature
 │   │    └─ found → gate: Keep as-is | Reconfigure
 │   └─ PROJECT interview (2 rounds) → build agent (mirror + ## Project profile)
 ├─ FLOW B — personal operator-profile (optional, user-scope)
 │   ├─ gate: "personalize for yourself too?" yes | no
 │   └─ yes → detect existing ~/.claude/skills/operator-profile → Keep | Reconfigure | Skip
 │            → PERSONAL interview (today's 3 rounds, prefilled) → build skill
 ├─ confirm write + commit (one prompt, covers both flows)
 ├─ delegate to ONE core:generalist (both writes + settings.local + gitignore + commit)
 └─ report (both flows) + restart reminder + opt-in note
```

This skill owns the interviews, sourcing, name resolution, and rendering. All file writes and the commit are delegated, keeping `onboard` compatible with the no-write orchestrator contract.

## 1. Parse flags

- `--show` → render the existing project orchestrator's `## Project profile` block (locate it via §3) AND, if present, the body of `~/.claude/skills/operator-profile/SKILL.md`, then **exit without changes**. If neither exists, say so and stop.
- An unknown flag is ignored.

## 2. Locate the live orchestrator (source of truth)

`Glob` for the installed core orchestrator, in this order, and use the **first** match:

1. `~/.claude/plugins/marketplaces/*/plugins/core/agents/orchestrator.md`
2. `plugins/core/agents/orchestrator.md` (repo-local fallback)
3. `~/.claude/agents/orchestrator.md`

`Read` the matched file. From its **frontmatter**, capture the behavior-contract keys to mirror **verbatim** into the generated wrapper: `disallowedTools`, `skills`, `color`, and `model` only if it is present. From its **body**, capture the single-sentence operating instruction **verbatim** — the wrapper reuses it unchanged, before the profile block. The mirrored `skills:` list now carries `operator-profile` from upstream automatically, so the generated wrapper inherits the personal profile by name with no special-casing here.

**Never hardcode the orchestrator's behavior or skills list.** Always read them live here so the generated wrapper tracks upstream changes to `core:orchestrator`. If no source matches, tell the user the `core` plugin must be installed and **stop** — there is nothing to inherit.

## 3. Detect existing project orchestrator (re-run aware)

Find any orchestrator this skill previously committed to the repo:

- `Glob` `.claude/agents/*.md`; `Read` each and select those whose body contains a `## Project profile` block (the onboard signature).
- If **exactly one** → that is the existing project orchestrator; capture its `name:` and its `## Project profile` block.
- If **multiple** → ask via `AskUserQuestion` which one is the target.
- If **none** → this is a fresh creation; skip the §4 gate and go straight to the PROJECT interview (§5).

Also Read `.claude/settings.local.json` and capture any top-level `agent` value — it tells whether **this** user is already opted in.

## 4. First-question gate (re-run only)

Runs **only** when §3 found an existing orchestrator, **before** the PROJECT interview. `AskUserQuestion` with two options:

- **Keep as-is** — no PROJECT interview, agent untouched. Wire the local opt-in (the keep path of §11): merge `.claude/settings.local.json` `"agent": "<name>"` (preserve siblings); ensure `.gitignore` covers `.claude/settings.local.json`. This path does **NOT** stop here — it skips the PROJECT interview but STILL proceeds to FLOW B (§6) and the final delegation/report.
- **Reconfigure** — prefill the PROJECT interview defaults from the detected `## Project profile`, proceed to §5, and rewrite the **same file/name** in place (no rename).

## 5. PROJECT interview (Flow A — 2 rounds via AskUserQuestion)

Run two `AskUserQuestion` rounds. Each option set is ≤4 options; rely on the automatic free-text **Other** for anything outside the list. On a **Reconfigure** (§4), pre-select / pre-fill every option from the detected `## Project profile`.

- **Round A — Stack & project type**
  1. Project type — Web app · API/Backend service · CLI/Tool · Library/SDK
  2. Primary language — TypeScript/JS · Python · Go · Rust
  3. Frameworks/runtime (multiSelect) — React/Next · Node · Django/FastAPI · None/other
  4. Package manager — npm/pnpm · yarn · uv/pip · cargo/go
- **Round B — Conventions & house rules**
  1. Test command — npm test/vitest · pytest · go test · None/manual
  2. Lint/format — ESLint+Prettier · Biome · Ruff/Black · None
  3. Commit convention — Conventional Commits · Free-form · Squash-only · Other
  4. House rules (multiSelect) — No comments · English only · No new deps without ask · Surgical diffs only

Collect the answers into a single resolved **project profile** used in §8.

## 6. PERSONAL interview (Flow B — optional, user-scope)

First, an `AskUserQuestion` gate: **"Personalize for yourself too?"** — `yes` | `no`.

- **no** → skip to §10 (no personal profile is written).
- **yes** → detect an existing `~/.claude/skills/operator-profile/SKILL.md` (`Glob` + `Read`). If found, `AskUserQuestion` with **Keep | Reconfigure | Skip** (prefill the rounds from it on Reconfigure). **Keep** and **Skip** write no personal file; **Reconfigure** (or a fresh run with no existing file) runs the three rounds below.

Run three `AskUserQuestion` rounds. Each option set is ≤4 options; rely on the automatic free-text **Other** for anything outside the list. On a **Reconfigure**, pre-select / pre-fill every option from the detected profile.

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

Collect the answers into a single resolved **operator profile** used in §9.

## 7. Resolve name & location

- Location is **always** `.claude/agents/<name>.md` in the repo — a committed artifact. There is no global/project question.
- On **Reconfigure** → reuse the detected name/path; do **not** rename.
- On **fresh** → derive the default name `<repo>-orchestrator`, where `<repo>` is the kebab-cased basename of `git rev-parse --show-toplevel`. Confirm it or let the user override via `AskUserQuestion` (with Other). The name MUST be kebab-case and unique among existing agents.
- The `settings.local.json` `agent` value equals the **bare** `name:` — NOT plugin-namespaced, since this is not a plugin agent.

## 8. Build the generated orchestrator content

Assemble the file content from the mirrored values captured in §2 and the project profile from §5. Only `name`, `description`, and the `## Project profile` block are personalized — the body sentence and the behavior-contract frontmatter are mirrored, **never invented**:

```
---
name: <name>
description: "<repo>'s project orchestrator: generalist coordinator tuned to this project's stack and conventions. Inherits the full core:orchestrator contract; never writes files, delegates to writer subagents."
disallowedTools: <mirrored verbatim from source>
skills: <mirrored verbatim from source>
color: <mirrored from source>
---

<verbatim one-sentence body from the source orchestrator>

## Project profile

- **Type**: <…>  **Language**: <…>  **Frameworks**: <…>  **Package mgr**: <…>
- **Test**: <…>  **Lint/format**: <…>  **Commits**: <…>
- **House rules**: <rule · rule · …>

Apply this profile to every task: respect this project's stack, test/lint commands, commit convention, and house rules. This profile refines HOW work fits THIS project — it never overrides the core:orchestrator operating contract above.
```

If the source declared `model`, include the mirrored `model` line; otherwise omit it.

## 9. Build the operator-profile skill content

Produced **only** when §6 ran with personalize=**yes** AND the user chose **Reconfigure** or it is a fresh personal profile. Assemble the user-scope skill from the operator profile resolved in §6:

```
---
name: operator-profile
description: "The operator's personal working profile — role, seniority, stack, tone, language, and output preferences. Preloaded into orchestrators to shape HOW Claude communicates and decides for this user."
when_to_use: "Auto-loaded as background context whenever an orchestrator runs; not a manual command. Re-run /workflow:onboard and choose to personalize to (re)generate it."
user-invocable: false
---

# Operator profile

- **Role**: <…>  **Seniority**: <…>  **Stack/domains**: <…>  **Focus**: <…>
- **Tone**: <concision> · <register> · responds in <language> · emojis: <…>
- **Output**: <format> · <depth> · autonomy: <…> · verification: <…>

Apply this profile to every task: shape tone, verbosity and output format to it. This profile refines HOW you communicate and decide — it never overrides the orchestrator's operating contract.
```

This skill MUST stay **preloadable**: never add `disable-model-invocation: true` here. `user-invocable: false` hides it from the `/` menu while leaving it loadable by name from the orchestrator's mirrored `skills:` list — a future editor must not add `disable-model-invocation`, or the orchestrator can no longer preload it.

## 10. Confirm write + commit

Before any write, one `AskUserQuestion` summarizing the planned effect of BOTH flows — the agent committed to `.claude/agents/<name>.md`; the optional `~/.claude/skills/operator-profile/SKILL.md` if §6 produced one; `settings.local.json` stays local/gitignored; `.gitignore` is ensured — with three options:

- **Proceed & commit** — write everything and run the targeted commit (§11.5).
- **Proceed, no commit** — write everything, skip the commit.
- **Cancel** — stop with nothing written.

## 11. Delegate the writes + commit (core:generalist)

This skill MUST NOT Write/Edit itself — it may run under the no-write orchestrator. Spawn **one** `core:generalist` subagent via `Agent`, passing the full resolved file content(s) from §8 (and §9 when produced) and these exact instructions:

1. Write/overwrite the orchestrator markdown to `<repo>/.claude/agents/<name>.md` (create parent dirs). This is a **COMMITTED** artifact — do NOT add it to `.gitignore`.
2. IF §6 produced an operator profile to write: write/overwrite `~/.claude/skills/operator-profile/SKILL.md` (expand `~`, create parent dirs). This lives OUTSIDE the repo and is **per-user** — NEVER `git add` it, NEVER add it to `.gitignore`. Skip this step entirely when personalize=no, or Keep, or Skip.
3. Merge into `<repo>/.claude/settings.local.json`: set the top-level key `"agent": "<name>"`. If the file is absent, create it as `{ "agent": "<name>" }`. If present, ADD/REPLACE only the `agent` key and PRESERVE all sibling keys (e.g. `ultracode`) — never replace the whole object.
4. Ensure `.gitignore` covers `.claude/settings.local.json` (append the line if missing). The agent file is NOT gitignored.
5. If the user chose **Proceed & commit**: run a targeted commit — `git add .claude/agents/<name>.md` plus `.gitignore` ONLY if it changed, then `git commit` with a Conventional Commit message: `feat(orchestrator): add <name> project orchestrator` (fresh) or `chore(orchestrator): reconfigure <name>` (reconfigure). NEVER `git add` `settings.local.json`; NEVER `git add` anything under `~/.claude/`. No co-author line, no "Generated with Claude Code".
6. Return the list of paths written/updated and the commit result (or "no commit").

After the subagent returns, report what changed.

## 12. Report & restart

Summarize:

- the committed orchestrator path and the captured `## Project profile`,
- whether an `operator-profile` skill was written (with its `~/.claude/skills/operator-profile/SKILL.md` path) or skipped,
- the local `settings.local.json` wiring (`"agent": "<name>"`),
- the `.gitignore` touch, if any,
- the commit result, if any.

Flag that a Claude Code **restart is required** for the new default agent (and a freshly created `operator-profile` skill) to take effect, and that `/reload-plugins` (or a restart) was needed for `/workflow:onboard` itself to appear. Note that **teammates opt in** by re-running `/workflow:onboard` and choosing **Keep as-is**.

## Critical principles

- **Commits the orchestrator, never the opt-in.** The orchestrator agent is a committed project artifact; `.claude/settings.local.json` is the per-user opt-in — never committed, always gitignored.
- **The personal profile is a separate per-user skill.** Flow B writes a USER-SCOPE `operator-profile` skill to `~/.claude/skills/`, never committed, always preloaded by name via the mirrored `skills:` list — and graceful (skipped with a debug warning) when the user never created it.
- **No hardcoding.** Behavior, skills, and the body sentence are always read live from the installed core orchestrator (§2); only identity and the `## Project profile` block are personalized.
- **The skill never writes files itself.** It delegates every write and the commit to `core:generalist`, staying compatible with the no-write orchestrator contract.
- **Re-runnable with a first-question gate.** An existing orchestrator → Keep as-is (skip the project interview, still personalize) or Reconfigure (rewrite the committed file in place).
