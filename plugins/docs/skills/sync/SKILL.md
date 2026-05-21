---
name: docs:sync
description: Reconciles `docs/plugins/**` MDX pages with the current state of `plugins/**` artifacts (skills, sub-agents, plugin manifests, marketplace entry). Detects added, modified, renamed, and deleted artifacts via `git diff`, proposes a per-page reconciliation plan, then delegates the actual MDX writing to the `docs-architect` sub-agent and finishes by invoking `docs:mintlify-validate`. Use when the user types `/docs:sync`, says `sync docs`, `sync the docs`, `update docs for plugin`, `docs out of date`, `regenerate plugin docs`, `docs drift`, or `rebuild docs after plugin change`.
allowed-tools: Bash, Read, AskUserQuestion, Agent, Skill
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# docs:sync

## What this skill does

Reconciles `docs/plugins/**` MDX pages against the current state of `plugins/**`. It diffs plugin artifacts against the docs tree, proposes a per-page plan, delegates every MDX edit to the `docs-architect` sub-agent, and validates the result. This skill never writes MDX content itself.

## Mapping convention

| Source artifact | Target docs page |
| :-- | :-- |
| `plugins/<plugin>/skills/<name>/SKILL.md` | `docs/plugins/<plugin>/skills/<name>.mdx` |
| `plugins/<plugin>/agents/<name>.md` | `docs/plugins/<plugin>/agents/<name>.mdx` |
| `plugins/<plugin>/.claude-plugin/plugin.json` | `docs/plugins/<plugin>/overview.mdx` |
| `.claude-plugin/marketplace.json` | every plugin overview page + top-level nav in `docs/docs.json` |

## Flow

### 1. Determine the diff range

Prefer the branch range when on a feature branch:

```bash
git diff --name-status --diff-filter=ACDMR main...HEAD -- plugins/ .claude-plugin/marketplace.json
```

If the output is empty (user is on `main` or only has working-tree changes), fall back to:

```bash
git status --porcelain -- plugins/ .claude-plugin/marketplace.json
```

If both report no changes, exit cleanly with: `docs are already in sync`.

### 2. Classify changes

For each path in the diff output, classify as `create`, `update`, `rename`, or `delete` using the mapping table. Group entries by plugin. Mark changes scoped to internal-only files (e.g. files under `plugins/<plugin>/skills/<name>/reference/` or `examples/` that do not alter the public-facing frontmatter or trigger phrases) as `no doc impact: skip` — keep them visible in the plan but do not delegate them.

### 3. Confirm the plan

Present the grouped plan to the user via `AskUserQuestion`. For each actionable entry, offer:

- `Apply` — delegate to `docs-architect`.
- `Skip` — drop from this run.
- `Defer` — record for a later sync, do nothing now.

If the diff was non-empty but every entry is `no doc impact: skip`, report that and exit without spawning any sub-agent.

### 4. Delegate writes to `docs-architect`

For each approved entry, spawn the `docs-architect` sub-agent with the `Agent` tool — one call per page. Spawn calls in parallel only when the pages are independent (different plugins, or distinct artifacts within the same plugin). Pass:

- Source artifact path (relative to repo root).
- Target MDX path (relative to repo root).
- Mode: `create`, `update`, `rename`, or `delete`.
- Plugin context — the plugin slug, so the architect can place the page in the correct nav group.

`docs-architect` is the sole writer for `docs/plugins/**/*.mdx` and `docs/docs.json`. It handles file moves on `rename` and nav cleanup on `delete`.

### 5. Validate

After every delegation returns, invoke the existing `docs:mintlify-validate` skill via the `Skill` tool. It runs `mint validate` and `mint build` and cross-checks `docs.json` against the filesystem.

### 6. Report

Emit a short summary:

```
docs:sync summary
- created: <n> (<paths>)
- updated: <n> (<paths>)
- renamed: <n> (<old> -> <new>)
- deleted: <n> (<paths>)
- skipped (no doc impact): <n>
- validation: PASS / FAIL
```

## Critical principles

- NEVER write to `docs/plugins/**/*.mdx` or `docs/docs.json` directly — always go through `docs-architect`.
- NEVER write to `plugins/**` — this skill is one-way (plugins → docs).
- Internal-only artifact edits (changes under `reference/` or `examples/` that do not touch frontmatter or trigger phrases) surface in the plan as `no doc impact: skip` and are not delegated.
- When `git` reports no diff in the selected range, exit cleanly with `docs are already in sync`.
- No auto-commit, no auto-push, no batching across plugins beyond what dependency order requires. Nav group conventions belong to `docs-architect`.

## Reuse

- [`plugins/docs/agents/docs-architect.md`](../../agents/docs-architect.md) — the sub-agent invoked for every MDX create / update / rename / delete. Sole writer of `docs/plugins/**` and `docs/docs.json`.
- [`plugins/docs/skills/mintlify-validate/SKILL.md`](../mintlify-validate/SKILL.md) — called at the end of every successful sync.
- [`plugins/docs/skills/mintlify-page/SKILL.md`](../mintlify-page/SKILL.md) — NOT called by this skill. Still the right tool for ad-hoc one-off pages outside the plugin reconciliation flow.
