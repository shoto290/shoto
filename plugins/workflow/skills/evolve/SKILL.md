---
name: evolve
description: 'Analyze the project''s existing skills, subagents, hooks, and MCP to propose and apply what to create or update for a new capability. Use when the user describes a high-level need ("I want to add X", "how should I structure Y", "what''s the cleanest way to evolve our setup for Z") or when a feature spans multiple artifact types (skill + agent + hook). When invoked without arguments, infers the capability from the current conversation so the user does not have to repeat themselves.'
when_to_use: 'Use when the user describes a capability or feature to add and it may span several artifact surfaces (skill, subagent, hook, MCP, plugin). Triggers on: "I want to add X", "how should I structure Y", "evolve our setup for Z", "add a /command plus a hook", a feature that needs both an agent and a skill. When invoked with no args, infer the capability from the current conversation.'
argument-hint: '[capability or feature description — optional; inferred from conversation if omitted]'
allowed-tools: [AskUserQuestion, Workflow, Read, Glob, Grep, Skill]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# Evolve

`evolve` plans and applies a coordinated set of skill/subagent/hook/MCP changes for a capability. It is a **thin wrapper** around two bundled workflows: `evolve-plan` (read-only inventory + plan) and `evolve-apply` (fan-out authoring). The approval gate lives here, in the main thread, **between** the two runs — the workflows themselves never ask the user anything.

```
/evolve
 ├─ clarify capability + target (AskUserQuestion)
 ├─ Workflow(evolve-plan.workflow.js)   → structured PLAN   (read-only)
 ├─ render plan + APPROVE / EDIT / CANCEL gate (AskUserQuestion)
 ├─ Workflow(evolve-apply.workflow.js)  → structured REPORT (authors via core smiths)
 └─ render report; offer to run deferred MCP / secret-hook setup in the main thread
```

This skill only clarifies, gates, and renders. It holds **no** orchestration logic — that lives entirely in the two scripts.

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

Invoke the plan workflow:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/evolve/scripts/evolve-plan.workflow.js",
  args: JSON.stringify({ capability, targetRoot, repoType, surfaces })
})
```

It returns a structured PLAN: `entries[]` (each with `artifactType`, `action`, `name`, `targetPath`, `spec`, `why`, `restartRequired`, `needsSecret`, `order`), `conflicts[]`, `restartRequired`, and `testPlan[]`.

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

## 6. Apply (fan-out)

Invoke the apply workflow with the **approved** plan:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/evolve/scripts/evolve-apply.workflow.js",
  args: JSON.stringify(approvedPlan)
})
```

It drops `reuse` entries, routes each executable entry (skill / subagent / hook-without-secret / plugin) to the matching core smith with a full no-questions spec, verifies the authored files, and returns a REPORT: `applied[]`, `deferred[]`, `restartRequired`, `testCommands[]`.

## 7. Render report

Render the REPORT:

- **Applied** — what was created/updated, each path and its verify status.
- **Restart required** — flag if any applied artifact needs a Claude Code restart (new top-level skill dir, new subagent file, or a `settings.json` hook change) or `/reload-plugins` for plugin-bundled changes.
- **Test commands** — the checks the user should run.
- **Deferred** — for each `deferred` item (MCP servers, secret-dependent hooks), explain why it was deferred and offer to run it **now in the main thread**: route MCP items to `core:mcp` and secret-hook items to `core:hooks` via the `Skill` tool, passing the item's ready-to-run spec.

## Critical principles

- **Thin wrapper.** Clarification, the approval gate, and rendering only. No inventory, classification, or authoring logic here — that lives in the two scripts.
- **The approval gate lives in the main thread** between the two runs. The workflows never ask the user anything.
- **Read-only plan, then apply.** Cancelling after the plan leaves the repo untouched.
- **Defer what an agent cannot wire.** MCP servers and secret-dependent hooks come back as `deferred` for `core:mcp` / `core:hooks` in the main thread — the apply run never attempts them.
