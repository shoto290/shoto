---
name: evolve
description: 'Analyze the project''s existing skills, subagents, hooks, and MCP to propose and apply what to create or update for a new capability. Use when the user describes a high-level need ("I want to add X", "how should I structure Y", "what''s the cleanest way to evolve our setup for Z") or when a feature spans multiple artifact types (skill + agent + hook). When invoked without arguments, infers the capability from the current conversation so the user does not have to repeat themselves.'
when_to_use: 'Use when the user describes a capability or feature to add and it may span several artifact surfaces (skill, subagent, hook, MCP, plugin). Triggers on: "I want to add X", "how should I structure Y", "evolve our setup for Z", "add a /command plus a hook", a feature that needs both an agent and a skill. When invoked with no args, infer the capability from the current conversation.'
argument-hint: '[capability or feature description — optional; inferred from conversation if omitted]'
allowed-tools: [AskUserQuestion, Agent, Workflow, TaskOutput, Read, Glob, Grep, Skill]
---

# Evolve

`evolve` plans and applies a coordinated set of skill/subagent/hook/MCP changes for a capability. It **plans inline** in the main thread by spawning read-only subagents (inventory + planner), runs the approval gate, then **applies** — inline via subagents for small plans, or via the bundled `evolve-apply` workflow for big plans. The approval gate lives here, in the main thread, **between** planning and applying.

```
/evolve
 ├─ clarify capability + target (AskUserQuestion)
 ├─ PLAN inline (main thread):
 │    ├─ spawn read-only inventory:inventory-context subagents in PARALLEL (one per surface)
 │    └─ spawn ONE planner subagent → fenced JSON PLAN   (read-only)
 ├─ render plan + APPROVE / EDIT / CANCEL gate (AskUserQuestion)
 ├─ APPLY (size-gated):
 │    ├─ ≤2 executable entries → spawn matching core smith subagent per entry (inline)
 │    └─ ≥3 executable entries → Workflow(evolve-apply.workflow.js) → structured REPORT
 └─ render report; offer deferred MCP / secret-hook setup
```

This skill owns clarification, inline planning, the approval gate, the apply size-gate, and rendering. Only big-plan execution is delegated to the `evolve-apply` workflow.

## 1. Detect intent

- **`$ARGUMENTS` is non-empty and concrete** → use it as the capability description; proceed to step 2.
- **`$ARGUMENTS` is empty** → infer from the current conversation: scan for pain points, friction, repeated manual steps, "I wish…" / "we need…" gaps between skills/agents/hooks. Synthesize a 1–3 sentence capability description and confirm it with `AskUserQuestion` (options: confirm, adjust, replace). Wait for confirmation.
- **`$ARGUMENTS` is ambiguous, or nothing actionable surfaced** → ask one targeted clarifying question with `AskUserQuestion` (what capability, which surface, who triggers it). Do not proceed until the intent is concrete.

## 2. Detect target

Determine whether this is a plugin repo or a normal repo:

- `Glob` for `.claude-plugin/marketplace.json` and `plugins/*/.claude-plugin/plugin.json`. If either matches → **plugin repo**.
- **Plugin repo** → `targetRoot` is `plugins/<plugin>/` (skills under `skills/`, agents under `agents/`). If more than one plugin exists, use `AskUserQuestion` to pick which plugin to target.
- **Normal repo** → `targetRoot` is `.claude/` (skills under `.claude/skills/`, agents under `.claude/agents/`, hooks in `.claude/settings.json`).

Record `repoType` (`plugin` | `normal`) and `targetRoot` for the args.

## 3. Clarify up front

Use `AskUserQuestion` to align before any run:

- the capability (confirm the refined sentence),
- which artifact surfaces are in play (skill / subagent / hook / MCP / plugin),
- who or what triggers it (user slash command, auto-trigger, lifecycle event).

Weave the answers into one refined `capability` string and a `surfaces` list.

## 4. Plan (read-only)

Plan inline in the main thread by spawning read-only subagents. **No files are written during planning.**

### Step a — Inventory (parallel, read-only)

Spawn read-only `inventory:inventory-context` subagents **in parallel** — issue multiple `Agent` calls in ONE message, one per surface in scope. Each subagent maps its surface under `targetRoot` and returns a read-only anchored contract. **None of them may modify any file.** Use these prompt strings, substituting `targetRoot`:

- **skills** — `Agent({ agentType: "inventory:inventory-context", … })`:
  > Read-only inventory. Do NOT modify any file.
  >
  > Scan every skill under `<targetRoot>` (skills/*/SKILL.md). For each, read the YAML frontmatter and capture: name, description, argument-hint, disable-model-invocation, user-invocable, context, agent. Note whether the body implements a create/update flow (look for "detect intent", "create flow", "update flow"). List description overlaps that could conflict with new auto-triggering artifacts.
  >
  > Return surface="skills" with one item per skill (name, path, summary, detail) and any constraints. Structured output only.

- **subagents** — `Agent({ agentType: "inventory:inventory-context", … })`:
  > Read-only inventory. Do NOT modify any file.
  >
  > Scan every subagent under `<targetRoot>` (agents/*.md). For each, read the frontmatter and capture: name, description, tools, model. Flag whether each description is broad (auto-trigger risk) or narrow (focused).
  >
  > Return surface="subagents" with one item per agent (name, path, summary, detail) and any constraints. Structured output only.

- **hooks** — `Agent({ agentType: "inventory:inventory-context", … })`:
  > Read-only inventory. Do NOT modify any file.
  >
  > Read settings.json and settings.local.json under `<targetRoot>` (and .claude/ if present). Parse the hooks block: for each hook capture event, matcher, type, and command/prompt. List permissions.allow and permissions.deny entries as constraints, and flag any global config that would conflict with the requested capability.
  >
  > Return surface="hooks" with one item per hook (name, path, summary, detail) and constraints holding the permission entries. Structured output only.

- **plugins** — `Agent({ agentType: "inventory:inventory-context", … })`:
  > Read-only inventory. Do NOT modify any file.
  >
  > Scan plugin manifests under `<targetRoot>` (.claude-plugin/plugin.json) and any MCP config (.mcp.json, mcpServers in plugin.json or settings). For each plugin/MCP server capture its name, path, and what it provides.
  >
  > Return surface="plugins" with one item per plugin/MCP server (name, path, summary, detail) and any constraints. Structured output only.

Collect every returned inventory contract.

### Step b — Plan (one planner subagent)

Spawn ONE planner subagent via `Agent({ agentType: "general-purpose", … })`, passing `capability` + `targetRoot` + `repoType` + `surfaces` + the gathered inventory contracts, with the merged classify + plan instructions below. It must return **ONLY** a fenced ```json block matching the PLAN shape — no prose around it.

> ## Planner
>
> Repo type: `<repoType>`. Target root: `<targetRoot>`.
> Requested capability:
> `<capability>`
>
> Surfaces in scope: `<surfaces joined by ", ">`.
>
> Existing inventory (read-only):
> `<JSON of gathered inventory contracts>`
>
> First, classify the capability into one or more artifact entries using these rules:
> - Reusable workflow with a /name entry point → skill.
> - Static project knowledge Claude should know in the background → skill (user-invocable: false).
> - Specialized delegate with sandboxed tools / token isolation → subagent.
> - Automatic enforcement (format-on-save, block edits, validate bash) or session-start context → hook.
> - External service/tool integration Claude queries directly → mcp.
> - Whole-plugin packaging/distribution → plugin.
> - Update vs create: if an existing artifact covers ≥70% of the need → update; if it would need a near-rewrite → create new; if two together cover it → reuse + a small extension. Never duplicate functionality.
>
> Then produce the final PLAN:
> - Surface every overlap/conflict explicitly. If an existing artifact covers ≥70% of an entry, prefer update or reuse over create — never duplicate.
> - For each entry, resolve a concrete `targetPath` under `<targetRoot>` (skills under skills/<name>/, subagents under agents/<name>.md, hooks in settings.json). For a normal repo use .claude/ paths instead.
> - Write a full authoring `spec` string per entry detailed enough that an autonomous smith can author/edit the files with NO further questions: name, type, description/trigger, argument-hint if any, tools/model for subagents, event/matcher/command for hooks, body/section outline.
> - Order entries by dependency (`order` field, ascending): reuse first, then updates, then creates with a skill before any agent that wraps it; hooks last unless they block something else.
> - Set `restartRequired` per entry (new top-level skill dir, new subagent file, or any settings.json hook change → true; in-place edits to an existing SKILL.md → false) and a top-level `restartRequired` if any entry needs it.
> - Set `needsSecret` true for any hook that requires secrets/auth and for any mcp entry.
> - Write a `testPlan[]` of concrete commands/checks (manual invocation, end-to-end trigger, reuse-still-works check).
>
> Return ONLY a fenced ```json block with this shape:
> ```json
> {
>   "capability": "string",
>   "entries": [
>     {
>       "artifactType": "skill | subagent | hook | mcp | plugin",
>       "action": "create | update | reuse",
>       "name": "string",
>       "targetPath": "string",
>       "spec": "string",
>       "why": "string",
>       "restartRequired": true,
>       "needsSecret": false,
>       "order": 1
>     }
>   ],
>   "conflicts": ["string"],
>   "restartRequired": true,
>   "testPlan": ["string"]
> }
> ```

### Step c — Parse

Parse the planner's fenced JSON into the plan object: `capability`, `entries[]` (each with `artifactType`, `action`, `name`, `targetPath`, `spec`, `why`, `restartRequired`, `needsSecret`, `order`), `conflicts[]`, `restartRequired`, and `testPlan[]`. This is the plan object used downstream.

## 5. Render plan + approval gate

Render the PLAN as markdown, grouped like the old evolve output:

- **Reuse** (no action needed)
- **Update**
- **Create** (in dependency order, by `order`)
- **Restart required** (per entry + overall)
- **Test plan**
- **Conflicts / overlaps** surfaced by the planner.

Then `AskUserQuestion`: **Approve** / **Edit** / **Cancel**.

- **Approve** → go to step 6 with the plan unchanged.
- **Edit** → let the user adjust, remove, or re-scope entries; apply their edits to the plan object before proceeding.
- **Cancel** → stop. Nothing has been written (the plan run is read-only).

## 6. Apply (size-gated)

First, derive the work set from the **approved** plan:

- Drop every `reuse` entry.
- Split the rest into:
  - **deferred** — entries with `artifactType: mcp`, or `artifactType: hook` with `needsSecret: true`.
  - **executable** — entries with `artifactType` `skill` / `subagent` / `hook`-without-secret / `plugin`.

The **executable entries count** drives the branch.

### Branch A — ≤ 2 executable entries → apply inline

Spawn the matching core smith subagent per executable entry via the `Agent` tool, routing by `artifactType`:

| `artifactType` | smith subagent |
| :-- | :-- |
| `skill` | `core:skill-smith` |
| `subagent` | `core:subagent-smith` |
| `hook` | `core:hooks-smith` |
| `plugin` | `core:plugin-smith` |

Give each smith the entry's **full no-questions spec** (`name`, `targetPath`, `action`, `why`, `spec`). After authoring, **verify each file** by Reading it and confirming its `name:` frontmatter matches its path. Build the `deferred` list for §7.

### Branch B — ≥ 3 executable entries → delegate to the workflow

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/evolve/scripts/evolve-apply.workflow.js",
  args: JSON.stringify(approvedPlan)
})
```

Do NOT inject `deepReviewScriptPath`, `applyFixesScriptPath`, or `base`. **Block on this run with a single `TaskOutput({ task_id, block: true })`** and render the REPORT exactly once. Never `ScheduleWakeup` or poll — the apply run is harness-tracked and re-invokes you when it finishes.

## 7. Render report

Render the REPORT:

- **Applied** — what was created/updated, each path and its verify status.
- **Restart required** — flag if any applied artifact needs a Claude Code restart (new top-level skill dir, new subagent file, or a `settings.json` hook change) or `/reload-plugins` for plugin-bundled changes.
- **Test commands** — the checks the user should run.
- **Deferred** — for each `deferred` item (MCP servers, secret-dependent hooks), explain why it was deferred and offer to run it **now in the main thread**: route MCP items to `core:mcp` and secret-hook items to `core:hooks` via the `Skill` tool, passing the item's ready-to-run spec.

## Critical principles

- **Owns inline planning and the apply size-gate.** This skill runs inventory + planning inline via read-only subagents and decides the apply route by executable-entry count. Only big-plan execution is delegated to the `evolve-apply` workflow. Clarification, the approval gate, and rendering stay here.
- **The approval gate lives in the main thread** between planning and applying.
- **Read-only plan, then apply.** Cancelling after the plan leaves the repo untouched.
- **Defer what an agent cannot wire.** MCP servers and secret-dependent hooks come back as `deferred` for `core:mcp` / `core:hooks` in the main thread — apply never attempts them.
- **Await the big-plan run once — never schedule a fallback wakeup.** The `evolve-apply` workflow run (Branch B) is a harness-tracked background task. Block on it with a single `TaskOutput(block=true)` and render exactly once. Do NOT `ScheduleWakeup` or poll: the run already re-invokes you on completion, so a redundant wakeup fires a *second* time and re-renders an `already completed, nothing to do` report. One run → one wait → one render. Planning and small applies are inline subagent calls, not background workflow runs.
