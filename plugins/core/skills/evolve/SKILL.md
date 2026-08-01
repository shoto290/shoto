---
name: evolve
description: 'Plan a coordinated set of skill, subagent, hook, MCP, and plugin changes for a new capability, inferred from the conversation if no args. Read-only: it renders a plan and writes nothing.'
when_to_use: 'Use when a capability may span several artifact surfaces at once and you need to know what to create, update, or reuse — with exact paths and full authoring specs — before anything is written. Not for authoring a single artifact you have already scoped.'
argument-hint: '[capability or feature description — optional; inferred from conversation if omitted]'
allowed-tools: [AskUserQuestion, Read, Glob, Grep]
---

# Evolve

Turn a capability request into an executable plan of artifact changes: what to create, what to update, what to reuse, in what order, at which exact path, with a spec complete enough to author from blind. Detect intent, detect the target root, clarify, survey what exists, classify against the rules, render the plan — you read, ask, and classify, and you write nothing.

## 1. Detect intent

- **`$ARGUMENTS` non-empty and concrete** → that is the capability.
- **`$ARGUMENTS` empty** → infer from the conversation: pain points, friction, repeated manual steps, "I wish…" / "we need…" gaps. Synthesize 1–3 sentences and carry them into §3 — do not ask here.
- **Ambiguous, or nothing actionable surfaced** → carry the ambiguity into §3 as well. Never plan against a guess.

## 2. Detect target

`Glob` for `.claude-plugin/marketplace.json` and `plugins/*/.claude-plugin/plugin.json`. Either matches → **plugin repo**, `targetRoot` is `plugins/<plugin>/`; if several plugins exist, carry the choice into §3 rather than asking here. Neither matches → **normal repo**, `targetRoot` is `.claude/`.

| Artifact | Heading noun | Path |
| :-- | :-- | :-- |
| skill | `skill (SKILL.md)` | `<targetRoot>/skills/<name>/SKILL.md` |
| subagent | `subagent definition` | `<targetRoot>/agents/<name>.md` |
| hook | `lifecycle hook (<event>)` | plugin repo `<targetRoot>/hooks/hooks.json` · normal repo `.claude/settings.json` |
| mcp | `MCP server entry` | plugin repo `<targetRoot>/.mcp.json` or `mcpServers` in `plugin.json` · normal repo `.mcp.json` |
| plugin | `plugin manifest` | `<targetRoot>/.claude-plugin/plugin.json` |
| workflow | `workflow script (.workflow.js)` | `<targetRoot>/skills/<name>/scripts/<name>.workflow.js` |

Hook and MCP paths follow the repo type: in a plugin repo both live under `targetRoot`; in a normal repo they stay at `.claude/settings.json` and `.mcp.json`. Every entry names one primary path, never a directory or a pattern.

## 3. Clarify

One `AskUserQuestion` round — the only interrupt in the flow. Confirm the capability sentence from §1 (confirm / adjust / replace), which surfaces are in play, who or what triggers it (slash command, description match, lifecycle event), and which plugin if §2 found several. Fold the answers into one capability string, a surfaces list, and a settled `targetRoot`.

## 4. Survey

Map every in-scope surface yourself with `Glob` / `Grep` / `Read`, issuing all in-scope surface reads in a single message rather than one surface at a time.

| Surface | Read | Capture |
| :-- | :-- | :-- |
| skills | `Grep` frontmatter across `<targetRoot>/skills/*/SKILL.md`; `Read` in full only those whose description overlaps the capability | `name`, `description`, `when_to_use`, `argument-hint`, `disable-model-invocation`, `user-invocable`; whether the body already implements the flow |
| subagents | `Grep` frontmatter across `<targetRoot>/agents/*.md`; `Read` in full only those whose description overlaps the capability | `name`, `description`, `tools`, `model`, preloaded skills; broad (auto-trigger risk) vs narrow |
| hooks | `<targetRoot>/hooks/hooks.json` in a plugin repo; `.claude/settings.json`, `.claude/settings.local.json` otherwise | each hook's event, matcher, type, command or prompt; `permissions.allow` and `permissions.deny` |
| mcp | `.mcp.json`, `mcpServers` in `plugin.json` or settings | server name, transport, what it exposes |
| plugin | `<targetRoot>/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — both already located in §2 | declared artifacts, version, marketplace entry |

Then match the capability's nouns and verbs against every `description` and `when_to_use` already collected — no further reads. Every hit is an overlap candidate for the rules below.

Skip out-of-scope surfaces, and never read the repo's protected files — record that a secret is needed, never its value.

## Rules

### Which artifact

| The capability is | Artifact |
| :-- | :-- |
| A reusable procedure with a `/name` entry point | skill |
| Static project knowledge Claude should carry in the background | skill (`user-invocable: false`) |
| A specialized delegate needing its own context window or a tool sandbox | subagent |
| Automatic enforcement at a lifecycle event (format on save, block an edit, validate a bash call), session-start context, or anything that must run whether or not the model chooses it | hook |
| An external service or tool Claude must query live | mcp |
| Whole-plugin packaging, manifest, or distribution | plugin |
| Fan-out across many agents running in parallel, at a scale one skill cannot drive | workflow |

### Create, update, or reuse

Prefer the smallest change that works. Never duplicate what exists.

| Existing coverage of the need | Action |
| :-- | :-- |
| ≥70%, and a small delta closes the gap | `update` that artifact |
| ≥70%, but adapting it means a near-rewrite | `create` new, and record the overlap under Conflicts |
| Two artifacts together cover it | `reuse` both, plus one small extension entry |
| <70%, or nothing close | `create` |

A `reuse` entry carries no spec — it names what already covers the need and states that nothing is to be done.

### Order

Number entries dependency-first: reuse, then updates, then creates. A plugin manifest before the artifacts it declares. A skill before any subagent that preloads or wraps it. Hooks last, unless a hook gates something else in the plan.

### Restart and setup

**Restart: yes** for a new top-level artifact directory, for any new *or edited* subagent file, and for any `settings.json` hook change; **`/reload-plugins`** for edits to plugin-bundled skills, agents, hooks, or MCP config; **no** otherwise. The full matrix lives in [`../plugin/reference/debugging.md`](../plugin/reference/debugging.md). Every entry states its reason; the plan header is yes if any entry is yes.

**Setup: interactive** for every `mcp` entry and for anything needing a secret, a credential, or a live running service — it cannot be completed unattended. The entry states exactly what human input it needs (which key, which service, where it goes) and stops there. Everything else is **autonomous**.

### Conflicts

Name every collision the survey found — overlapping descriptions that would mis-trigger, duplicate names, a hook already bound to the same event and matcher, a `permissions.deny` that blocks the plan — and state the resolution you chose. Never resolve one silently; omit the section entirely when there are none.

### Spec completeness

Every non-`reuse` entry carries a spec its reader can execute with zero follow-up questions. If a spec forces a question, it is unfinished.

| Artifact | The spec states |
| :-- | :-- |
| skill | `name`, `description`, `when_to_use`, `argument-hint`, invocation flags, body section outline, any supporting files |
| subagent | every mandatory frontmatter field required by [`../subagent/SKILL.md`](../subagent/SKILL.md), each with its decided value, plus the body outline and validation gate |
| hook | event, matcher, type, the exact command or prompt, any script file with its path, where it is registered, what happens on failure |
| mcp | server name, transport, command or URL, required env vars by name, what it must expose |
| plugin | manifest fields, directory layout, marketplace entry |
| workflow | phases, fan-out shape, stage schemas, distribution model, wrapper `SKILL.md` |

For an `update`, the spec also states exactly which sections change and which stay untouched.

### Test plan

Concrete, runnable checks: one direct invocation per created or updated artifact, one trigger check for anything that must fire on its own, and one regression check per reused artifact.

## Plan output

The rendered markdown plan is the entire output. Every entry is read alone, by someone who saw neither this conversation nor the other entries:

- **Self-contained** — no back-references ("same as above", "the skill from entry 2"), no pronouns crossing entries. Repeat context rather than pointing at it.
- **Named in artifact terms** — the heading carries the artifact's heading noun from §2.
- **Executor-agnostic** — describe the artifact to build, never who or what builds it. Name no tool, no command, no agent.

```markdown
# Plan — <capability>

Target `<targetRoot>` · <plugin|normal> repo · Restart required: <yes|no>

## 1. <Create|Update|Reuse> <heading noun> — `<name>`

- **Path** `<repo-relative path>`
- **Why** <what it contributes, and what it deliberately does not duplicate>
- **Restart** <yes|no> — <reason>
- **Setup** <autonomous | interactive — the exact human input required>
- **Spec** <every field listed for this artifact type under Spec completeness, with its value; for an update, which sections change and which stay untouched>

## Conflicts
- <collision> → <resolution>

## Test plan
- <check>
```

Nothing is created, edited, or scaffolded — on any path, including "just this one small file".
