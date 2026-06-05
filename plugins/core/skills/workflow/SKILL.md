---
name: workflow
description: 'Create or update a .workflow.js orchestration script that fans out subagents at scale.'
when_to_use: 'Use to write or edit a workflow that parallelizes agents - not for explaining workflows in the abstract.'
argument-hint: '[workflow name or description of what to orchestrate]'
allowed-tools: [Agent, AskUserQuestion, Read, Glob, Grep]
---

# Workflow

A **dynamic workflow** is a JavaScript script run by Claude Code's Workflow runtime in the background. It orchestrates many subagents at scale: the plan lives in code (loops, branching, and intermediate results held in script variables), and only the **final return value** flows back into Claude's context. The canonical worked example is the bundled deep-research workflow — see [examples/deep-research.md](./examples/deep-research.md).

This skill is the **smith for workflows** — it authors and updates the script and its wrapper. It is a sibling of `core:skill`, `core:subagent`, `core:hooks`, `core:mcp`, and `core:plugin`. The actual authoring is delegated to the `workflow-smith` subagent ([agents/workflow-smith.md](../../agents/workflow-smith.md)). This skill clarifies the orchestration shape, delegates, and validates — it does **not** write the workflow files itself.

If the user only wants to *understand* how workflows work in the abstract, answer conceptually from [reference/dsl.md](./reference/dsl.md) and [reference/constraints.md](./reference/constraints.md) and write nothing.

## Detect intent

If invoked as `/workflow <name-or-description>`, treat `$ARGUMENTS` as the workflow name or a description of what to orchestrate.

1. **Search for the name** in plugin-bundled (`<plugin>/skills/<name>/scripts/<name>.workflow.js`) and native saved (`.claude/workflows/<name>.js`, `~/.claude/workflows/<name>.js`) locations. Match on the script `meta.name` as well as the filename.
2. **Match found** → propose **update flow** (confirm before editing).
3. **No match** → propose **create flow** (validate the name: lowercase letters, digits, hyphens; starts with a letter).
4. **Empty / ambiguous** → ask the user, or route to the conceptual answer above.

## Two distribution models

| Model | Layout | How it runs | Best for |
| :-- | :-- | :-- | :-- |
| **Plugin-bundled** (recommended) | a thin wrapper `SKILL.md` + `scripts/<name>.workflow.js` in the same skill dir | the wrapper invokes the **Workflow** tool with `scriptPath` set to the bundled script and `args` | shipping a reusable, named workflow in a plugin (the deep-research model, and what this repo's `workflow` plugin uses) |
| **Native saved** | a bare script at `.claude/workflows/<name>.js` (project) or `~/.claude/workflows/<name>.js` (personal) | auto-becomes a `/<name>` command | a personal or project-local workflow without a wrapper |

For the plugin-bundled model, the wrapper resolves the bundled script via the plugin-root env var — the same form deep-research uses:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<name>.workflow.js",
  args: "<refined input>"
})
```

The wrapper does scope-clarification (`AskUserQuestion`) **before** the run and renders the structured result **after**. See [examples/deep-research.md](./examples/deep-research.md).

**Awaiting a background run.** The `Workflow` tool launches the script as a harness-tracked **background** task and returns immediately with a task ID. The wrapper must **block on it with a single synchronous wait** — `TaskOutput({ task_id, block: true })` — then render the result **exactly once**. Never `ScheduleWakeup` or poll the run: harness-tracked tasks re-invoke the wrapper on completion, so a fallback wakeup fires a *second* time and re-renders a redundant `already completed` report. One run → one wait → one render. (The wrapper skill must include `TaskOutput` in its `allowed-tools`.)

## The script DSL (summary)

Full reference: [reference/dsl.md](./reference/dsl.md). A workflow script is JavaScript (not TypeScript) with:

- `export const meta = { name, description, whenToUse?, phases?, model? }` — a **pure object literal**: no variables, calls, or spreads. `phases` entries are `{ title, detail }` and their titles **must** match the `phase()` calls.
- `phase(title)` — marks a phase boundary for progress display.
- `agent(prompt, opts)` — spawns a subagent. `opts`: `{ label?, phase?, schema?, model?, isolation?, agentType? }`. Returns the agent's text, a validated object when `schema` (a JSON Schema) is given, or `null` if the agent was skipped.
- `parallel(thunks)` — a **barrier**: runs all thunks, waits for all. A thrown task becomes `null` (filter with `.filter(Boolean)`).
- `pipeline(items, ...stages)` — **no barrier**: each stage callback receives `(prevResult, originalItem, index)`.
- `log(msg)` — progress logging.
- Globals: `args` (the wrapper's `args` string), `budget` (`{ total, spent(), remaining() }`), and `workflow(nameOrRef, args)` for an inline sub-workflow (**one level deep only**).

A ready-to-edit skeleton lives at [template.workflow.js](./template.workflow.js).

## Hard constraints

These are enforced by `workflow-smith` and stated to the user. Full list: [reference/constraints.md](./reference/constraints.md).

- **No mid-run user input.** ALL `AskUserQuestion` (clarification, approval gates) lives in the wrapper skill, **never** in the `.workflow.js`. For sign-off between stages, split into separate workflows.
- **No direct filesystem or shell access from the script.** Only spawned agents touch files or the shell; the script only coordinates.
- **≤16 concurrent agents; 1000 agents max per run.**
- **JavaScript only.** `meta` is a pure literal. No `Date.now()`, `Math.random()`, or `new Date()` in the script.
- **Spawned subagents run in `acceptEdits` mode**, inherit the tool allowlist, and use the session model unless a stage routes to another.
- **Prefer `pipeline()` over a `parallel()` barrier** unless a stage genuinely needs all prior results at once.
- **Every write/apply workflow should end with a deep-review of its own diff** (strong recommendation, not enforced). If a workflow writes or mutates files (it has a write/apply phase — any stage that authors, edits, or deletes files, directly or via spawned agents), prefer to chain a deep-review over the freshly authored diff before returning. Read-only workflows (search, analysis, planning, reporting — no file mutations) are exempt.

## Recommended review chain for write workflows

Any authored workflow that mutates files can finish by reviewing its own diff, reusing the bundled deep-review + apply-fixes workflows rather than re-implementing review logic. The pattern has two parts.

1. **Wrapper injects the script paths via args.** The wrapper skill cannot let the sandboxed script resolve cross-skill sibling paths (no fs/`__dirname`), so it passes them in the args object. The exact injection shape used by evolve:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<name>.workflow.js",
  args: JSON.stringify({
    ...input,
    deepReviewScriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-review/scripts/deep-review.workflow.js",
    applyFixesScriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-review/scripts/apply-fixes.workflow.js",
    base: "origin/main"
  })
})
```

The deep-review + apply-fixes scripts live in the workflow plugin (`plugins/workflow/skills/deep-review/scripts/`). A workflow bundled in a DIFFERENT plugin must reference them by the path the wrapper can resolve at its plugin root, or the user must have the workflow plugin installed — state this as a prerequisite; do not over-engineer cross-plugin resolution.

2. **The script runs deep-review READ-ONLY, then calls apply-fixes directly.** Because `workflow()` nesting is ONE LEVEL DEEP, the script must NOT trigger deep-review's own `--auto-fix` path (that would call `workflow(apply-fixes)` at a second level and throw). Instead it:
   - (a) reads `deepReviewScriptPath` / `applyFixesScriptPath` / `base` from the parsed args (skip the review chain silently if `deepReviewScriptPath` is absent);
   - (b) in a `Review` phase, `await workflow({ scriptPath: deepReviewScriptPath, args: JSON.stringify({ autoFix: false, base }) })`;
   - (c) if any returned verdict is `FIX` or `FIX-STYLE` AND `applyFixesScriptPath` is present, in a `Fix` phase `await workflow({ scriptPath: applyFixesScriptPath, args: JSON.stringify({ comments, verdicts, base }) })`;
   - (d) wrap BOTH calls in try/catch so a review failure never discards the apply report — the files are already written.

   Add the `review` (`{ comments[], verdicts[], summary }` or `null`) and `fixReport` (`{ applied[], skipped[], verification, newTickets[] }` or `null`) fields to the script's final return object, and add matching `{ title, detail }` entries `Review` and `Fix` to `meta.phases` (titles must match the `phase()` calls per the existing meta-alignment rule).

## Create flow

### 1. Clarify the orchestration shape

Surface these with `AskUserQuestion` only if the request is ambiguous; pre-select any value the prompt already supplied:

| Decision | Options |
| :-- | :-- |
| **Name** | lowercase letters, digits, hyphens; starts with a letter |
| **Distribution model** | Plugin-bundled (wrapper + bundled script, recommended) or Native saved (bare `.claude/workflows/<name>.js`) |
| **Fan-out** | what is decomposed and parallelized (the work items, one agent each) |
| **Verify / synthesize** | what checks or merges the fan-out results into the final return |
| **Structured output** | the JSON Schema(s) for stages whose output the next stage parses |
| **Budget / model** | concurrency limits, a default `meta.model`, or per-stage model routing |

### 2. Delegate authoring

Spawn the `workflow-smith` subagent via the **Agent** tool, passing a full spec (name, distribution model, phases, fan-out shape, schemas, constraints) so it needs no follow-ups. The smith writes the wrapper `SKILL.md` + `scripts/<name>.workflow.js` (plugin-bundled) or the bare native script, then validates. If the workflow writes or mutates files, the spec passed to `workflow-smith` should recommend the review chain (deep-review read-only → apply-fixes for `FIX`/`FIX-STYLE`, one-level nesting) and have the wrapper inject `deepReviewScriptPath` + `applyFixesScriptPath` + `base` in its args.

### 3. Validate

Confirm the smith's validation gate passed: `meta` is a pure literal, `meta.phases` titles align one-to-one with the `phase()` calls, every `schema` is valid JSON Schema, no banned constructs (`Date.now`/`Math.random`/`new Date`/filesystem/shell/`AskUserQuestion` in the script), and the concurrency / agent-count constraints are respected. For any write/apply workflow, the deep-review chain is recommended but not required; if present, confirm it is wired correctly (`Review`/`Fix` phases, `deepReviewScriptPath` read from args, deep-review invoked with `autoFix:false`, apply-fixes called directly only on `FIX`/`FIX-STYLE` verdicts) and that read-only workflows correctly omit it.

## Update flow

### 1. Locate the target

Find the script by `meta.name` and filename in plugin-bundled and native saved locations (see Detect intent). If multiple match, ask which one.

### 2. Read current state

Read the full `.workflow.js` AND, for the plugin-bundled model, its wrapper `SKILL.md`. Don't propose changes blind.

### 3. Delegate the change

Spawn `workflow-smith` with the target path and the requested change. Warn before renaming or moving distribution model — both change how the workflow is invoked (the `meta.name`, the wrapper path, or the `/<name>` command).

### 4. Validate

Same gate as create. Preserve `meta` fields and stage structure unless the user explicitly asked to change them.

## Critical principles

- **The script orchestrates; agents act.** The script holds the plan and the intermediate state in variables. Only spawned agents read files, run shells, or search the web — and only the final `return` reaches Claude.
- **No user prompts inside the script.** Mid-run input would block a background run. Clarify in the wrapper before, render the result after; split workflows for between-stage sign-off.
- **`meta` is a pure literal, phases must align.** A variable, call, or spread in `meta`, or a `phases` title that doesn't match a `phase()` call, breaks the run.
- **Prefer pipelines.** A `parallel()` barrier blocks on the slowest task; `pipeline()` lets each item flow through stages independently. Use a barrier only when a stage needs the whole pool at once.
- **Delegate, don't hand-write.** This skill clarifies and validates; `workflow-smith` authors the files.
- **One run → one wait → one render.** A wrapper blocks on its background `Workflow` run with a single `TaskOutput(block=true)` and renders once. Never `ScheduleWakeup` or poll a harness-tracked run — it re-invokes you on completion, and a redundant wakeup re-renders the report.

## Reference

- [reference/dsl.md](./reference/dsl.md) — the full script DSL: `meta`, `phase`, `agent`, `parallel`, `pipeline`, `log`, `args`, `budget`, `workflow`, and structured-output schemas.
- [reference/constraints.md](./reference/constraints.md) — the hard constraints plus the meta-facts (availability, enabling/disabling, triggering, saving a run's script).
- [template.workflow.js](./template.workflow.js) — a ready-to-edit skeleton (meta literal + phase / pipeline / parallel / agent / schema scaffold).

## Examples

- [examples/deep-research.md](./examples/deep-research.md) — the canonical worked example: the bundled deep-research workflow's wrapper-skill shape and the script's phase / pipeline / parallel / schema structure.
