---
name: ultraplan
description: Produce a concrete, codebase-grounded execution plan for a specific code change, mirroring the local patterns and conventions discovered in the repo. Use when the user asks to "ultraplan", "make a plan", "plan this", "plan an implementation", "plan a refactor", runs "/core:ultraplan", or invokes the "ultraplanner". Reads the repo via `Skill({ skill: "explore:explore", args: "..." })` to anchor every step on `path:line` precedents, then emits a stable markdown brief at `.claude/plans/<slug>.md`. Intensity dial via `--mode quick|standard|deep` controls how many explorer calls run, which step fields are required, and whether the mirroring gate is soft or hard. Different from `core:evolve` (meta-coordinator that decides which artifact types to create across the marketplace) — `ultraplan` writes the direct, step-by-step execution plan once the artifact and scope are already known.
argument-hint: '[--mode quick|standard|deep] <goal in one sentence>'
allowed-tools: [Read, Glob, Write, AskUserQuestion, Skill]
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Ultraplan

`ultraplan` writes a codebase-grounded execution plan for a single, concrete code change. Every step cites the local precedent it mirrors, and the final brief lands in `.claude/plans/<slug>.md` ready to drive an implementation session.

## Detect intent

- **`$ARGUMENTS` empty** → ask the user, via `AskUserQuestion`, for the one-sentence goal of the plan. Do not guess.
- **`$ARGUMENTS` too vague** (one or two words with no scope, e.g. "auth", "refactor") → ask exactly **one** clarifying question via `AskUserQuestion` to convert it into a one-sentence goal. No second clarification round.
- **`$ARGUMENTS` concrete** → proceed.

## Phase 1 — Frame

1. Restate the user's input as one crisp goal in a single sentence. Confirm the restatement out loud before continuing.
2. Resolve `--mode`:
   - If `$ARGUMENTS` contains an explicit `--mode quick|standard|deep`, adopt it as-is and announce the active mode in one short line. Skip the prompt.
   - Otherwise, infer the most coherent mode from the restated goal using the "Mode inference rubric" in [reference/mode-calibration.md](./reference/mode-calibration.md), then call `AskUserQuestion` with all three options (`quick`, `standard`, `deep`); tag the inferred option's label with the suffix ` (Recommended)`. The user's answer (including an "Other" override) becomes the active mode. Announce the active mode in one short line.

   Do not re-explain the modes — calibration lives in [reference/mode-calibration.md](./reference/mode-calibration.md).

Do not skip Phase 1 even if the user's goal seems unambiguous.

## Phase 2 — Ground

Call `Skill({ skill: "explore:explore", args: "..." })` per the mode calibration table. For `standard` and `deep`, dispatch the calls in parallel (multiple `Skill` calls in a single message).

| Mode | Explorer calls | Step shape | Mirroring gate |
| :-- | :-- | :-- | :-- |
| quick | 1 | `action` + `verify` + `mirrors` | soft |
| standard *(default)* | 2 parallel | `action` + `verify` + `mirrors` | hard |
| deep | 4 parallel | `action` + `verify` + `mirrors` + `risk` + `rollback` | hard |

Per-mode argument templates and how to derive `topic`/`area`/`entry` from the goal: [reference/mode-calibration.md](./reference/mode-calibration.md).

Collect the returned `path:line`-anchored reports. They feed two things: the `## Reuse-first` section of the final plan, and the `mirrors:` slot of every step in Phase 3.

## Phase 3 — Draft steps

For each action needed to reach the goal, emit a step with the fields required by the active mode:

- **action** — concrete imperative (verb + object). Always required.
- **verify** — how to check the action worked end-to-end. Always required.
- **mirrors** — `<path:line-range>` cited from Phase 2 output, OR the literal escape hatch `mirrors: no precedent — creating new pattern`. Always required.
- **risk** — `low|medium|high` with one-line justification. Required in `deep` only.
- **rollback** — how to undo the step. Required in `deep` only.

Steps must come from analyzing the goal against the grounding output. Do not invent steps. Do not synthesize anchors — every `mirrors:` value is either a real `path:line-range` from a Phase 2 report or the literal escape hatch string.

## Phase 4 — Coherence check

Before writing the file, walk every drafted step:

- **quick mode** — soft gate. If any step has no real `mirrors:` anchor and no escape hatch, emit a warning in the inline output but proceed.
- **standard mode** and **deep mode** — hard gate. If any step has no real `mirrors:` anchor and no escape hatch, refuse to write and re-draft the offending step until compliance. Do the same for missing `risk` or `rollback` in `deep`.

No coherence-check narration in the final plan file — the gate runs in this skill's reasoning, not in the output.

## Phase 5 — Output

1. **Slug** — compute a kebab-case slug from the goal (≤ 40 chars, lowercase letters/digits/hyphens only).
2. **Path** — `.claude/plans/<slug>.md`. Use `Glob` on `.claude/plans/<slug>*.md` to check for collisions. If a file exists, append `-2`, `-3`, … until the path is free.
3. **Write the plan** — use the schema from [reference/plan-template.md](./reference/plan-template.md) **exactly**, in section order. Fill the frontmatter (`name`, `mode`, `patterns`, `created`), the `## Context`, `## Reuse-first`, `## Steps`, and `## Verification` sections.
3.5. **Meta-artifact pointer** — if either (a) the restated goal contains a meta-keyword (`skill`, `subagent`/`sub-agent`/`agent`, `hook`/`hooks`, `plugin`, `SKILL.md`, or a `/<plugin>:<skill>` slash-command reference), or (b) any drafted step's `action` or `verify` field references a path under `plugins/**/skills/*/SKILL.md`, `plugins/**/agents/*.md`, `.claude/hooks/**`, `.claude/settings.json`, or `.claude-plugin/**`, append the `## Next` section to the plan body before writing the file. Use the canonical text from [reference/plan-template.md](./reference/plan-template.md). Skip the section otherwise.
4. **Print inline** — after `Write`, also print the full plan inline in the response, using the same schema, so the caller has both the file path and the structured content available immediately.

Examples of well-formed plans: [examples/plan-quick.md](./examples/plan-quick.md), [examples/plan-deep.md](./examples/plan-deep.md).

## Anti-patterns

- **Don't skip Phase 2 grounding.** Even an "obvious" goal gets the explorer calls per the mode table. The whole value of this skill is anchoring steps on real precedents.
- **Don't invent `mirrors:` anchors.** Every `mirrors:` value is either a real `path:line-range` returned by Phase 2 or the literal `mirrors: no precedent — creating new pattern`. Synthesizing a plausible-looking anchor defeats the audit trail.
- **Don't narrate internal reasoning in the plan file.** The brief is for execution, not for showing how the plan was made. No "I chose X because…", no recap of the coherence check, no commentary on the explorer output.
- **Don't enumerate all 8 explore specialists.** Use the per-mode argument templates in [reference/mode-calibration.md](./reference/mode-calibration.md). Calling more specialists than the active mode prescribes inflates token cost without changing the output.
- **Don't create a sub-agent wrapper.** v0 calls `explore:explore` directly in-skill. Promotion to a dedicated sub-agent is deferred until a second consumer (`/git:review-diff`, `/code-review`, …) needs the same pattern detection.
- **Don't soften the gate in `standard` or `deep`.** The hard gate is the contract. If a step genuinely has no precedent, use the escape hatch literal — do not weaken the rule.

## Reference

- [reference/mode-calibration.md](./reference/mode-calibration.md) — full mode table, per-mode explorer argument templates, escape hatch literal, deferred-mode notes.
- [reference/plan-template.md](./reference/plan-template.md) — stable markdown schema for the saved plan.

## Examples

- [examples/plan-quick.md](./examples/plan-quick.md) — realistic `quick` mode plan with the soft gate exercised.
- [examples/plan-deep.md](./examples/plan-deep.md) — realistic `deep` mode plan with `risk` + `rollback` per step and no escape hatch used.
