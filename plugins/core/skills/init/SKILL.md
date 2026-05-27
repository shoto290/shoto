---
name: init
description: Bootstrap a repo-specific `.claude/` setup by inventorying the codebase, matching it to a starter-set archetype (≤3 artifacts), and delegating every approved write to `core:evolve`. Use when the user types `/core:init`, says `initialize claude code for this repo`, `bootstrap claude setup`, `propose skills for this project`, `set up .claude/`, or invokes it with no arguments after entering a new repo. Composition-only — never re-implements analysis, ideation, or artifact authoring.
argument-hint: '[optional constraint or focus area — inferred from repo if omitted]'
allowed-tools: [Read, Glob, Skill, AskUserQuestion]
---
> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Init

`/core:init` reads the repo signals, matches them to a starter-set archetype (≤3 artifacts), and proposes the smallest useful set of skills/agents/hooks to add. The user has the final say on every choice. The skill is a pure composition of `explore:explore` (inventory), `core:brainstorm` (optional ideation), `core:skills-list` (catalog), and `core:evolve` (write path) — it never authors artifact files itself.

## Detect intent

Three branches based on `$ARGUMENTS`:

- **Empty** → proceed directly to Phase 1 with **zero clarifying questions**. The empty-args path is the canonical use of `/core:init`.
- **Vague keyword** (e.g. `improve`, `setup`, `bootstrap`) → fire exactly one `AskUserQuestion` to convert it into a concrete focus area, then proceed to Phase 1. No second clarification.
- **Concrete constraint** (e.g. `skills only`, `no hooks`, `focus on testing`) → adopt as a Phase 3 filter and proceed to Phase 1 immediately.

## Phase 1 — Repo inventory

Delegate every read to `explore:explore`. Never `Read` repo source files from the main thread — delegation only.

```
Skill({ skill: "explore:explore", args: "inventory languages, build tool, test framework, CI, existing .claude/ artifacts under .claude/skills/, .claude/agents/, .claude/settings.json, AGENTS.md and CLAUDE.md presence, plugin manifests under plugins/**/.claude-plugin/plugin.json" })
```

The returned inventory is the only signal source for Phase 2 archetype matching and Phase 3 classification.

## Phase 2 — Target detection

Run `Glob plugins/**/.claude-plugin/plugin.json` against the repo root.

- **≥1 match** → marketplace repo. Fire `AskUserQuestion` with one option per detected plugin directory (e.g. `plugins/core/`, `plugins/git/`, `plugins/explore/`) plus a final `Local .claude/` option. User selects the write target.
- **Zero matches** → silently target `.claude/` in the repo root. No question needed.

The selected target is the implicit write-destination for every artifact downstream.

## Phase 3 — Preliminary classification

Two steps:

1. `Skill({ skill: "core:skills-list" })` — get the installed-artifact catalog for the selected target.
2. Match the inventory against the archetype starter sets in [reference/repo-archetypes.md](./reference/repo-archetypes.md). For each candidate artifact, compare it against the catalog using the 70% reuse threshold from [../evolve/reference/decision-matrix.md](../evolve/reference/decision-matrix.md). Classify each candidate as one of:
   - `reuse` — existing artifact covers ≥70% of the need; recommend invoking it instead.
   - `update` — existing artifact partially covers; route to `core:evolve` for amendment.
   - `create` — no overlap; route to `core:evolve` for fresh authoring.

## Phase 4 — Targeted brainstorm *(optional)*

Single round, four-option `AskUserQuestion`: `Approfondir l'inventaire` / `Élargir avec brainstorm` / `Converger vers la proposition` / `Stop`.

- `Approfondir` → one more targeted `Skill({ skill: "explore:explore", args: "<specific area>" })` call.
- `Élargir` → `Skill({ skill: "core:brainstorm", args: "<focus seeded from inventory + classification gaps>" })`.
- `Converger` → proceed to Phase 5.
- `Stop` → exit cleanly with no delegation.

Never auto-loop. Always end on user input. One round by default; user must explicitly request a second.

## Phase 5 — Final classification

If Phase 4 returned `Converger` immediately, this phase is a pass-through using the Phase 3 result. Otherwise re-run the Phase 3 classification logic with the new ideas (from `Approfondir` or `Élargir`) folded in.

## Phase 6 — Batch approval gate

Single `AskUserQuestion` presenting the full proposal as a numbered list (≤3 artifacts, each annotated with its `reuse` / `update` / `create` classification and target plugin or local `.claude/`).

Options:

- `Accept (Recommended)` — forward everything to Phase 7.
- `Edit` — open a per-artifact override loop. User adjusts one entry at a time, then the full batch is re-presented for re-approval.
- `Reject` — exit cleanly with no delegation.

If more than 3 artifacts seem warranted, present only the top 3 and offer to defer the rest to a follow-up `/core:init` run. SIMPLE constraint is structural, not advisory.

## Phase 7 — Delegate to `core:evolve`

Single `Skill({ skill: "core:evolve", args: "<consolidated approved proposal, including target plugin or local .claude/>" })` call.

> Never write artifact files directly — `core:evolve` owns the entire write path, which routes to `skill-architect` / `subagent-architect` / `hooks` per [../evolve/reference/delegation-routing.md](../evolve/reference/delegation-routing.md).

After delegation, `/core:init` is done — `core:evolve` produces the only execution report. Do not summarize, do not echo, do not write anything to disk.

## Anti-patterns

- Don't re-implement repo analysis — always delegate to `explore:explore`.
- Don't write any SKILL.md, agent, or hook file directly — `core:evolve` owns the write path.
- Don't exceed the archetype's ≤3-item starter set without explicit user request.
- Don't write any brief or summary file to disk — `core:evolve`'s own report is the single execution record.
- Don't batch-skip the `AskUserQuestion` between phases — every phase ends on user input or proceeds based on a deterministic signal (Glob result).

## Reference

- [reference/repo-archetypes.md](./reference/repo-archetypes.md) — signal → ≤3-item starter set
- [../evolve/reference/decision-matrix.md](../evolve/reference/decision-matrix.md) — Need → Artifact type table + 70% reuse threshold (linked, not copied)
- [../evolve/reference/delegation-routing.md](../evolve/reference/delegation-routing.md) — routing from artifact type to executor (linked, not copied)
