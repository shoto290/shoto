---
name: workflow
description: 'Understand and author Claude Code dynamic workflows (Workflow-tool scripts that orchestrate subagents in parallel via a deterministic JS script). Use when the user wants to create, scaffold, write, modify, refactor, or run a workflow, fan out subagents, pipeline/parallelize agents, run multi-agent orchestration, or edit files under `.claude/workflows/`. Triggers on: workflow, dynamic workflow, orchestrate subagents, fan-out, pipeline, parallel agents, multi-agent, .claude/workflows, Workflow tool.'
argument-hint: '[create|update|explain] [workflow-name or description]'
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Workflow

A **dynamic workflow** is a self-contained JavaScript script executed by the `Workflow` tool. The script spawns subagents — concurrently when you want — and deterministic control flow (loops, conditionals, fan-out, fan-in) lives in the script rather than in a model's head. This skill owns the create / update / explain flows; it **delegates actual script authoring to the `workflow-architect` subagent**, exactly as `/core:skill` delegates to `skill-architect`.

## What is a dynamic workflow

- The `Workflow` tool runs a single JS script that orchestrates subagents. The script decides what runs, in what order, and how many at once.
- Deterministic control flow (loops, conditionals, fan-out, fan-in) lives in the script — not in a prompt — so the orchestration is reproducible.
- Subagent results can be schema-validated (structured JSON) and verified adversarially before the script trusts them.
- Progress auto-saves: a run can be resumed, and the unchanged prefix returns cached results instead of re-spending tokens.
- This is a research-preview feature and token-heavy. Test on a scoped task first before pointing it at a large surface.

## Detect intent

If invoked as `/workflow <args>`, read the first token as the verb.

1. **Empty / ambiguous** → ask the user via `AskUserQuestion` whether they want to create, update, or have a workflow explained.
2. **"explain"** → teach how dynamic workflows work using [reference/scripting-api.md](./reference/scripting-api.md). Do not write any file.
3. **"create"** → route to the **Create flow**.
4. **"update"** (or a name / path that resolves under `.claude/workflows/`) → route to the **Update flow**.

## Create flow

### 1. Clarify the orchestration

Pin down the shape before writing anything:

- **What fans out** — the unit of parallel work (files, dimensions, candidates, chunks).
- **What verifies** — the adversarial check that confirms a finding before it is trusted.
- **What synthesizes** — how independent results merge into one answer.
- **Budget** — the explicit token ceiling the run must respect.

For codebase exploration that the workflow needs to ground itself in, delegate to [explore:explore](../../../explore/skills/explore/SKILL.md) rather than re-implementing search. To discover canonical mappings for other intents, invoke `core:skills-suggest`.

### 2. Pick a reference pattern

Choose a pattern from [reference/scripting-api.md](./reference/scripting-api.md) (pipeline review, loop-until-dry) and adapt it. `pipeline()` is the default for multi-stage work; reserve `parallel()` for true barriers.

### 3. Delegate authoring to `workflow-architect`

Hand the full spec to the architect — do not hand-write the script:

```
Agent({ subagent_type: "workflow-architect", prompt: "<full spec: fan-out unit, verify step, synthesis, budget, chosen pattern, target path under .claude/workflows/>" })
```

### 4. Verify the script

Confirm the returned script: `export const meta = {...}` is present as a pure literal, phase titles in `meta.phases` match the `phase()` calls, structured returns are schema-validated, and the budget is set.

### 5. Test on a scoped run

Run the workflow against a small, bounded input first. Confirm the orchestration behaves and the token spend is acceptable before scaling up.

## Update flow

1. **Locate** the script under `.claude/workflows/` (CWD up to repo root, then `~/.claude/workflows/`).
2. **Read** the whole script — `meta`, every `phase()`, every `agent()`, the synthesis tail.
3. **Identify** the change (new stage, different fan-out, tighter budget, schema fix, parallel ↔ pipeline swap).
4. **Delegate** the edit to `workflow-architect` with the current script and the requested change.
5. **Re-validate** against the same checks as Create step 4, then re-test on a scoped run.

## Critical principles

- **Pipeline by default** — use `pipeline()` so each item flows through stages independently. Reserve `parallel()` for true barriers (dedup, merge, early-exit-on-zero).
- **Schema-validate structured returns** — pass `opts.schema` whenever an agent should return data, not prose. Filter null results with `.filter(Boolean)`.
- **Adversarially verify before trusting** — add a verification stage that challenges findings before synthesis treats them as fact.
- **Cap the token budget explicitly** — set `budget.total` and check `budget.remaining()` before fan-out. Never let a run spend without a ceiling.
- **Never silently truncate coverage** — if the script drops items to fit the budget or cap, `log()` exactly what was dropped.
- **`meta` must be a pure literal** — no variables, calls, or spreads. Phase titles in `meta.phases` must match the `phase()` calls.

## Reference

- [reference/scripting-api.md](./reference/scripting-api.md) — the Workflow scripting API cheat-sheet, plus the pipeline-review and loop-until-dry patterns.

## Output Examples

- [examples/create-workflow-output.md](./examples/create-workflow-output.md) — a well-formed fan-out audit workflow with its `meta` block.
