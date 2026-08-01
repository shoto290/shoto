---
name: onboard
description: 'Set up a committed project executant from a short stack-and-conventions interview, arm the out-of-repo review ledger, and optionally a per-user operator profile.'
when_to_use: 'When you want to install advisor in this repo or personalize an operator profile — interview the stack and conventions to build a committed project executant, create the out-of-repo ledger that arms the review gate, optionally a per-user profile. Not to run adversarial review (use /advisor:review); it replaces the retired /advisor:init.'
argument-hint: '[--show]'
allowed-tools: [AskUserQuestion, Read, Glob, Bash, Write, Edit]
---

# Onboard

`onboard` runs **two independent flows**. **Flow A** sets up a **committed project executant**: a short PROJECT interview (stack + conventions) produces a thin-wrapper agent under `.claude/agents/` that **inherits** the live `advisor:executant` contract verbatim plus an injected `## Project profile` block, and creates the out-of-repo ledger at `~/.claude/advisor/state/<slug>/` that arms the self-gating review hook; each teammate opts in locally by setting `"agent": "<name>"` in the gitignored `.claude/settings.local.json`. **Flow B** is optional and per-user: if the user wants to personalize for themselves, the SAME 3-round personal interview produces a user-scope `operator-profile` skill written to `~/.claude/skills/` — outside the repo, never committed, preloaded into agents by name. The skill writes every file itself: the executant IS the writer, so there is nothing to delegate. On re-run, if an executant already exists, the very first question is **Keep as-is vs Reconfigure**.

```
/advisor:onboard
 ├─ parse flags (--show) + confirm git repo, compute ledger slug
 ├─ locate LIVE advisor:executant (source of truth)                  [§2 unchanged]
 ├─ FLOW A — PROJECT executant (committed)
 │   ├─ detect existing by `## Project profile` + `advisor:executant` signature
 │   │    └─ found → gate: Keep as-is | Reconfigure
 │   └─ PROJECT interview (2 rounds) → build agent (mirror + ## Project profile)
 ├─ FLOW B — personal operator-profile (optional, user-scope)
 │   ├─ gate: "personalize for yourself too?" yes | no
 │   └─ yes → detect existing ~/.claude/skills/operator-profile → Keep | Reconfigure | Skip
 │            → PERSONAL interview (today's 3 rounds, prefilled) → build skill
 ├─ confirm write + commit (one prompt, covers both flows)
 ├─ write directly (agent + profile + ledger + settings.local + gitignore + commit)
 └─ report (both flows) + ledger path + restart reminder + opt-in note
```

This skill owns the interviews, sourcing, name resolution, rendering, and every write. It replaces the retired `/advisor:init` — the ledger and the local settings key it used to install are absorbed into §11 here.

## 1. Parse flags

Precondition, before anything else: the whole skill is repo-scoped. Confirm the git repo and compute the ledger slug. Shell state does not persist between Bash calls, so **recompute the slug in each Bash block that needs it** — the value captured here is only for prose and reporting:

```bash
git rev-parse --show-toplevel
slug="$(git rev-parse --show-toplevel | shasum | cut -c1-12)"
echo "$slug"
```

If not inside a git repo, report that and **stop**.

- `--show` → render the existing project executant's `## Project profile` block (locate it via §3), AND, if present, the body of `~/.claude/skills/operator-profile/SKILL.md`, AND the ledger path `~/.claude/advisor/state/<slug>/` with whether it exists, then **exit without changes**. If none of the three exists, say so and stop.
- An unknown flag is ignored.

## 2. Locate the live executant (source of truth)

`Glob` for the installed advisor executant, in this order, and use the **first** match:

1. `~/.claude/plugins/marketplaces/*/plugins/advisor/agents/executant.md`
2. `plugins/advisor/agents/executant.md` (repo-local fallback)
3. `~/.claude/agents/executant.md`

`Read` the matched file. From its **frontmatter**, capture the behavior-contract keys to mirror **verbatim** into the generated wrapper: `skills`, `color`, and `model` / `disallowedTools` only if they are present. From its **body**, capture the single-sentence operating instruction **verbatim** — the wrapper reuses it unchanged, before the profile block. The mirrored `skills:` list carries `operator-profile` from upstream automatically, so the generated wrapper inherits the personal profile by name with no special-casing here.

**Never hardcode the executant's behavior or skills list.** Always read them live here so the generated wrapper tracks upstream changes to `advisor:executant`. If no source matches, tell the user the `advisor` plugin must be installed and **stop** — there is nothing to inherit.

## 3. Detect existing project executant (re-run aware)

Find any executant this skill previously committed to the repo:

- `Glob` `.claude/agents/*.md`; `Read` each and select those that carry **both** signatures: a `## Project profile` block in the body AND `advisor:executant` in the frontmatter `skills:` list. The second signature is required — a repo can hold both a `<repo>-orchestrator` and a `<repo>-executant` wrapper, and both carry a `## Project profile` block, so the profile block alone does not disambiguate.
- If **exactly one** → that is the existing project executant; capture its `name:` and its `## Project profile` block.
- If **multiple** → ask via `AskUserQuestion` which one is the target.
- If **none** → this is a fresh creation; skip the §4 gate and go straight to the PROJECT interview (§5).

Also Read `.claude/settings.local.json` and capture any top-level `agent` value — it tells whether **this** user is already opted in, and it feeds the replacement gate in §11.

## 4. First-question gate (re-run only)

Runs **only** when §3 found an existing executant, **before** the PROJECT interview. `AskUserQuestion` with two options:

- **Keep as-is** — no PROJECT interview, agent untouched. Wire the local opt-in (the keep path of §11): create the ledger `~/.claude/advisor/state/<slug>/`; merge `.claude/settings.local.json` `"agent": "<name>"` (preserve siblings, honour the replacement gate); ensure `.gitignore` covers `.claude/settings.local.json`. This path does **NOT** stop here — it skips the PROJECT interview but STILL proceeds to FLOW B (§6) and the final writes/report.
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
- On **fresh** → derive the default name `<repo>-executant`, where `<repo>` is the kebab-cased basename of `git rev-parse --show-toplevel`. Confirm it or let the user override via `AskUserQuestion` (with Other). The name MUST be kebab-case and unique among existing agents.
- The `settings.local.json` `agent` value equals the **bare** `name:` — NOT plugin-namespaced, since this is not a plugin agent.

## 8. Build the generated executant content

Assemble the file content from the mirrored values captured in §2 and the project profile from §5. Only `name`, `description`, and the `## Project profile` block are personalized — the body sentence and the behavior-contract frontmatter are mirrored, **never invented**:

```
---
name: <name>
description: "<repo>'s project executant: the single context-holding writer tuned to this project's stack and conventions. Inherits the full advisor:executant contract; writes every change itself and self-reviews each delta with the adversarial reviewers."
skills: <mirrored verbatim from source>
color: <mirrored from source>
---

<verbatim one-sentence body from the source executant>

## Project profile

- **Type**: <…>  **Language**: <…>  **Frameworks**: <…>  **Package mgr**: <…>
- **Test**: <…>  **Lint/format**: <…>  **Commits**: <…>
- **House rules**: <rule · rule · …>

Apply this profile to every task: respect this project's stack, test/lint commands, commit convention, and house rules. This profile refines HOW work fits THIS project — it never overrides the advisor:executant operating contract above.
```

If the source declared `model` or `disallowedTools`, include the mirrored lines; otherwise omit them.

## 9. Build the operator-profile skill content

Produced **only** when §6 ran with personalize=**yes** AND the user chose **Reconfigure** or it is a fresh personal profile. Assemble the user-scope skill from the operator profile resolved in §6. This file is SHARED with `/orchestrator:onboard` — the rendering below must stay byte-identical between the two skills, or the two commands flip-flop the same file:

```
---
name: operator-profile
description: "The operator's personal working profile — role, seniority, stack, tone, language, and output preferences. Preloaded into orchestrators to shape HOW Claude communicates and decides for this user."
when_to_use: "Auto-loaded as background context whenever an orchestrator or executant agent runs; not a manual command. Re-run /orchestrator:onboard or /advisor:onboard and choose to personalize to (re)generate it."
user-invocable: false
---

# Operator profile

- **Role**: <…>  **Seniority**: <…>  **Stack/domains**: <…>  **Focus**: <…>
- **Tone**: <concision> · <register> · responds in <language> · emojis: <…>
- **Output**: <format> · <depth> · autonomy: <…> · verification: <…>

Apply this profile to every task: shape tone, verbosity and output format to it. This profile refines HOW you communicate and decide — it never overrides the agent's operating contract.
```

This skill MUST stay **preloadable**: never add `disable-model-invocation: true` here. `user-invocable: false` hides it from the `/` menu while leaving it loadable by name from the executant's mirrored `skills:` list — a future editor must not add `disable-model-invocation`, or the agent can no longer preload it.

## 10. Confirm write + commit

Before any write, one `AskUserQuestion` summarizing the planned effect of BOTH flows — the agent committed to `.claude/agents/<name>.md`; the out-of-repo ledger `~/.claude/advisor/state/<slug>/`; the optional `~/.claude/skills/operator-profile/SKILL.md` if §6 produced one; `settings.local.json` stays local/gitignored; `.gitignore` is ensured — with three options:

- **Proceed & commit** — write everything and run the targeted commit (§11.6).
- **Proceed, no commit** — write everything, skip the commit.
- **Cancel** — stop with nothing written.

## 11. Write the files + commit (direct)

The executant is the writer, so this skill performs every write itself with `Write` / `Edit` / `Bash` — no subagent is spawned:

1. Write/overwrite the executant markdown to `<repo>/.claude/agents/<name>.md` (create parent dirs). This is a **COMMITTED** artifact — do NOT add it to `.gitignore`.
2. IF §6 produced an operator profile to write: write/overwrite `~/.claude/skills/operator-profile/SKILL.md` (expand `~`, create parent dirs). This lives OUTSIDE the repo and is **per-user** — NEVER `git add` it, NEVER add it to `.gitignore`. Skip this step entirely when personalize=no, or Keep, or Skip.
3. Create the out-of-repo ledger and seed its `ledger.md` **only when it does not already exist** — NEVER overwrite an existing ledger. The slug is recomputed inside this block because shell state does not survive between Bash calls, and the `[ -f ] ||` guard enforces the no-overwrite rule mechanically:

   ```bash
   slug="$(git rev-parse --show-toplevel | shasum | cut -c1-12)"
   mkdir -p ~/.claude/advisor/state/$slug/
   [ -f ~/.claude/advisor/state/$slug/ledger.md ] || : > ~/.claude/advisor/state/$slug/ledger.md
   ```

   This directory is what arms the self-gating Stop hook: the hook is a no-op until it exists, so there is nothing else to wire per repo. It lives OUTSIDE the repo, is keyed by the repo slug, and is never committed.
4. Merge into `<repo>/.claude/settings.local.json`: set the top-level key `"agent": "<name>"`. Read the existing JSON first when the file is present; if absent, create it as `{ "agent": "<name>" }`. ADD/REPLACE only the `agent` key and PRESERVE all sibling keys (e.g. `ultracode`) — never replace the whole object. Replacement safety:
   - no `agent` key yet, or already equal to `<name>` → write it (or no-op) silently;
   - `agent` set to ANY other value (e.g. a `<repo>-orchestrator` wrapper) → **STOP** and ask via `AskUserQuestion`, surfacing the current value; replace it only on confirmation. If declined, leave the file untouched and say so in the §12 report.
5. Ensure `.gitignore` covers `.claude/settings.local.json` (append the line if missing). The agent file is NOT gitignored.
6. If the user chose **Proceed & commit**: run a targeted commit — `git add .claude/agents/<name>.md` plus `.gitignore` ONLY if it changed, then `git commit` with a Conventional Commit message: `feat(advisor): add <name> project executant` (fresh) or `chore(advisor): reconfigure <name>` (reconfigure). NEVER `git add` `settings.local.json`; NEVER `git add` anything under `~/.claude/`, including the ledger. No co-author line, no "Generated with Claude Code".

## 12. Report & restart

Summarize, by absolute path:

- the committed executant path and the captured `## Project profile`,
- the ledger `~/.claude/advisor/state/<slug>/` and whether its `ledger.md` was seeded or already existed,
- whether an `operator-profile` skill was written (with its `~/.claude/skills/operator-profile/SKILL.md` path) or skipped,
- the local `settings.local.json` wiring — whether `"agent": "<name>"` was set, was already correct, or was left as-is because the replacement was declined,
- the `.gitignore` touch, if any,
- the commit result, if any.

State that nothing was staged from the ledger — it lives outside the repo — and that no tracked file other than the agent (and possibly `.gitignore`) was modified. Flag that a Claude Code **restart is required** for the new default agent (and a freshly created `operator-profile` skill) to take effect, and that `/reload-plugins` (or a restart) was needed for `/advisor:onboard` itself to appear. Note that **teammates opt in** by re-running `/advisor:onboard` and choosing **Keep as-is**.

## Critical principles

- **Commits the executant, never the opt-in.** The executant agent is a committed project artifact; `.claude/settings.local.json` is the per-user opt-in — never committed, always gitignored.
- **The ledger lives outside the repo.** `~/.claude/advisor/state/<slug>/` is durable per-user state keyed by the repo slug: never staged, never committed, never overwritten when it already exists — and its mere existence is what arms the self-gating review hook.
- **The personal profile is a separate per-user skill.** Flow B writes a USER-SCOPE `operator-profile` skill to `~/.claude/skills/`, never committed, always preloaded by name via the mirrored `skills:` list — shared with `/orchestrator:onboard`, so its rendering stays identical from either entry point, and graceful (skipped with a debug warning) when the user never created it.
- **No hardcoding.** Behavior, skills, and the body sentence are always read live from the installed advisor executant (§2); only identity and the `## Project profile` block are personalized.
- **The skill writes directly.** The executant IS the writer, so there is no delegation and no subagent hop — every write and the commit happen here.
- **Re-runnable with a first-question gate.** An existing executant → Keep as-is (skip the project interview, still arm the ledger and personalize) or Reconfigure (rewrite the committed file in place).
