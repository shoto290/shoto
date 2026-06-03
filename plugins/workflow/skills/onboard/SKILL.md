---
name: onboard
description: 'Personalize your Claude Code orchestrator. Runs a short professional interview (role, communication tone, output style, delegation rules) and generates a thin-wrapper orchestrator agent that inherits the live core:orchestrator contract plus your operator profile, then wires it as the default agent in .claude/settings.local.json. The generated orchestrator is personal and never committed; re-run anytime to update your profile.'
when_to_use: "/workflow:onboard, 'set up my orchestrator', 'personalize my orchestrator', 'create my operator profile', 'tune how Claude works for me', 'onboard me'. NOT for adding or evolving skills/subagents/hooks (use /workflow:evolve), and NOT for generating a CLAUDE.md (use the built-in /init)."
argument-hint: '[--global | --project] [--show]'
allowed-tools: [AskUserQuestion, Read, Glob, Bash, Agent]
---

# Onboard

`onboard` personalizes the default Claude Code orchestrator for one operator. It runs a short professional interview (role, tone, output style, delegation rules), reads the live `core:orchestrator` contract as the source of truth, and assembles a thin-wrapper orchestrator agent that **inherits** that contract verbatim plus an injected operator-profile block. It never writes files itself — it delegates all writes to a `core:generalist` subagent — and wires the result as the default agent in `.claude/settings.local.json`. The generated orchestrator is personal and gitignored; re-running updates the embedded profile in place.

```
/workflow:onboard
 ├─ parse flags (--global | --project | --show)
 ├─ locate the LIVE core orchestrator (source of truth) → mirror its contract + body
 ├─ detect existing generated profile → prefill interview defaults (re-run aware)
 ├─ interview (4 rounds via AskUserQuestion): role · tone · output · delegation
 ├─ resolve name + output location (global vs project)
 ├─ build generated orchestrator content (mirrored contract + ## Operator profile)
 ├─ delegate the writes to ONE core:generalist subagent (agent file + settings + gitignore)
 └─ report what changed + restart reminder
```

This skill owns the interview, sourcing, name/location resolution, and rendering. All file writes are delegated, keeping `onboard` compatible with the no-write orchestrator contract.

## 1. Parse flags

- `--global` → preset output location to `~/.claude/agents/<name>.md`; skip the location question.
- `--project` → preset output location to `.claude/agents/<name>.md`; skip the location question.
- `--show` → locate the current generated orchestrator (see §3), Read its `## Operator profile` block, render it to the user, and **exit without changes**. If none is found, say so and stop.
- Flags are not combined beyond the above; an unknown flag is ignored.

## 2. Locate the live orchestrator (source of truth)

`Glob` for the installed core orchestrator, in this order, and use the **first** match:

1. `~/.claude/plugins/marketplaces/*/plugins/core/agents/orchestrator.md`
2. `plugins/core/agents/orchestrator.md` (repo-local fallback)
3. `~/.claude/agents/orchestrator.md`

`Read` the matched file. From its **frontmatter**, capture the behavior-contract keys to mirror **verbatim** into the generated wrapper: `disallowedTools`, `skills`, `color`, and `model` only if it is present. From its **body**, capture the single-sentence operating instruction **verbatim** — the wrapper reuses it unchanged, before the profile block.

**Never hardcode the orchestrator's behavior or skills list.** Always read them live here so the generated wrapper tracks upstream changes to `core:orchestrator`. If no source matches, tell the user the `core` plugin must be installed and **stop** — there is nothing to inherit.

## 3. Detect existing profile (re-run aware)

Look for a previously generated orchestrator so a re-run prefills, not restarts:

- Read `.claude/settings.local.json` (if present) and capture any existing top-level `agent` value.
- For that name, look for `~/.claude/agents/<that-name>.md` and `.claude/agents/<that-name>.md`.

If one is found, Read its `## Operator profile` block and use it to **prefill** the interview defaults in §4. Re-running **updates** the embedded profile and regenerates the file — the embedded block is the single source of truth, so there is no separate profile artifact to reconcile.

## 4. Interview (3 rounds via AskUserQuestion)

Run three `AskUserQuestion` rounds. Each option set is ≤4 options; rely on the automatic free-text **Other** for anything outside the list. **Pre-select / pre-fill** from any profile detected in §3.

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

Collect the answers into a single resolved profile used in §6.

## 5. Resolve name & output location

- Derive a default agent name from the role/identity — a short kebab-case `<handle>-orchestrator`. Confirm it or let the user override via `AskUserQuestion` (with Other). The name MUST be kebab-case and unique among existing agents.
- If neither `--global` nor `--project` was passed, ask the output location via `AskUserQuestion`:
  - **Global** — `~/.claude/agents/<name>.md` (per-user, applies to every project, never lives in a repo).
  - **Project** — `.claude/agents/<name>.md` (this repo only, will be gitignored).
- The `settings.local.json` `agent` value equals the **bare** `name:` for a user/project agent — NOT plugin-namespaced, since these are not plugin agents.

## 6. Build the generated orchestrator content

Assemble the file content from the mirrored values captured in §2 and the profile from §4. Only `name`, `description`, and the `## Operator profile` block are personalized — the body sentence and the behavior-contract frontmatter are mirrored, **never invented**:

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

## 7. Delegate the writes (core:generalist)

This skill MUST NOT Write/Edit itself — it may run under the no-write orchestrator. Spawn **one** `core:generalist` subagent via `Agent`, passing the full resolved file content from §6 and these exact instructions:

1. Write the generated orchestrator markdown to the chosen path (`~/.claude/agents/<name>.md` or `<repo>/.claude/agents/<name>.md`); create parent directories if needed.
2. Merge into `<repo>/.claude/settings.local.json`: set the top-level key `"agent": "<name>"`. If the file is absent, create it as `{ "agent": "<name>" }`. If present, ADD/REPLACE only the `agent` key and PRESERVE all sibling keys (e.g. `ultracode`) — never replace the whole object.
3. If the output location is project-local, ensure `.claude/agents/<name>.md` is gitignored: if `.gitignore` does not already cover it, append a line. (For global output there is nothing to gitignore — `settings.local.json` is already gitignored.)
4. Return the list of paths written or updated.

After the subagent returns, report what changed.

## 8. Report & restart

Summarize:

- the generated orchestrator path,
- the `settings.local.json` wiring (`"agent": "<name>"`),
- the `.gitignore` touch, if any,
- the captured `## Operator profile`.

Flag that a Claude Code **restart is required** for the new default agent to take effect, and that `/reload-plugins` (or a restart) was needed for `/workflow:onboard` itself to appear.

## Critical principles

- **No hardcoding.** Behavior, skills, and the body sentence are always read live from the installed core orchestrator (§2); only identity and the `## Operator profile` block are personalized.
- **Never commits anything personal.** The generated orchestrator goes to a user or gitignored location; `settings.local.json` is already gitignored.
- **The skill never writes files itself.** It delegates every write to `core:generalist`, staying compatible with the no-write orchestrator contract.
- **Re-runnable.** The embedded `## Operator profile` block is the single source; re-running updates it in place rather than spawning a second artifact.
