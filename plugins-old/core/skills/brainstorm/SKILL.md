---
name: brainstorm
description: Iteratively explore, ideate, and specify an idea before any planning. Use when the user wants to "brainstorm", "brainstormer", "remue-méninges", "ideate", "explorer une idée", "itérer sur une idée", "spécifier une idée", or runs "/brainstorm". Applies the MIT brainstorming rules (suspended judgment, quantity over quality, wild ideas welcome, duplicates OK) and a curated technique catalog (Starbursting, 5 Whys, SCAMPER, SWOT, How-Now-Wow, Reverse, Six Hats, What-if, Crazy 8). Drives a Frame → Diverge → Organize → Converge → Decide loop, asks the user between rounds, and produces a generic Markdown brief any downstream planning skill can consume.
argument-hint: '[idea or question — optional; asked if absent]'
allowed-tools: [Read, Write, AskUserQuestion, Glob]
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Brainstorm

`brainstorm` runs an iterative ideation session on a single question, then writes a stable, generic Markdown brief that any downstream planning skill can consume.

## Detect intent

- **`$ARGUMENTS` empty** → ask the user, via `AskUserQuestion`, for the idea or question to brainstorm. Do not guess.
- **`$ARGUMENTS` too vague** (one or two words with no problem framing, e.g. "auth", "mobile") → ask exactly **one** clarifying question via `AskUserQuestion` to convert it into a one-sentence question. No second clarification round.
- **`$ARGUMENTS` concrete** → proceed.

## Phase 1 — Frame

1. Restate the user's input as one crisp question in a single sentence. Confirm the restatement out loud before continuing.
2. Surface the four MIT rules to the user (transparency: explain that during divergence rounds, the skill will **not** criticize or evaluate — judgment is suspended until the converge step):
   - All ideas welcome.
   - No judgment during the brainstorm.
   - More ideas the better (aim for quantity).
   - Duplicates are OK.
3. Cite the canonical source: [reference/mit-framework.md](./reference/mit-framework.md).

Do not skip Phase 1 even if the user provides a fully-formed one-liner.

## Phase 2 — Round loop

Repeat the four sub-steps below until the user converges or drops. Always end each round with `AskUserQuestion` — never auto-loop.

### 2.a Diverge

1. Pick **1 or 2** techniques from [reference/techniques.md](./reference/techniques.md) using the "When to use what" matrix in that file.
2. Announce the chosen technique(s) by name.
3. Generate ideas following the technique's prompt template. Aim for **≥ 8 ideas**.
4. Output a numbered list. No evaluation, no commentary, no qualifiers ("this might be hard", "this is risky" — forbidden here).

### 2.b Organize

Cluster the ideas by theme, deduplicate, and renumber the shortlist down to **3–5 candidates**. Show the clustered list to the user.

### 2.c Converge (light)

Apply **How-Now-Wow** OR **SWOT** to the shortlist (whichever fits the idea type — see [reference/techniques.md](./reference/techniques.md)). Present the evaluation as a Markdown table.

### 2.d Decision

Ask the user via `AskUserQuestion` with these four options:

- **Approfondir #X** — sub-brainstorm sur l'idée X retenue du shortlist.
- **Élargir un autre angle** — nouvelle technique, autre framing, nouveau round.
- **Converger → brief** — écrire le brief Markdown final (go to Phase 3, CONVERGED).
- **Dropper → kill-note** — sauvegarder une note expliquant pourquoi l'idée est abandonnée (go to Phase 3, DROPPED).

## Phase 3 — Output

1. **Slug** — compute a kebab-case slug from the question (≤ 40 chars, lowercase letters/digits/hyphens only).
2. **Path** — `.claude/brainstorms/<slug>.md`. Use `Glob` to check for an existing file with that slug. If it exists, append `-2`, `-3`, … until the path is free.
3. **Write the brief** — use the schema from [reference/brief-template.md](./reference/brief-template.md) **exactly**, in section order. For CONVERGED, fill the `## Retained idea` section. For DROPPED, replace it with `## Drop reason`. Everything else is identical.
4. **Print inline** — after `Write`, also print the full brief inline in the response, using the same schema, so the caller has both the file path and the structured content available immediately.

Examples of well-formed briefs: [examples/brief-converged.md](./examples/brief-converged.md), [examples/brief-rejected.md](./examples/brief-rejected.md).

## Anti-patterns

- **No auto-loop.** Always ask the user via `AskUserQuestion` between rounds. Never chain rounds silently.
- **No judgment during divergence.** Even gentle critique ("this could be risky", "might not scale") is forbidden inside Phase 2.a. Save all evaluation for Phase 2.c.
- **No mention of downstream skills by name** in the brief or in the schema. The brief is generic — it must be consumable by any planning skill, present or future. Do not name specific planners in the output.
- **Don't enumerate all 29 Asana techniques.** Stick to the curated catalog in [reference/techniques.md](./reference/techniques.md). Group-only techniques (Charrette, Brainwriting, eyes-closed image, change of scenery, brain-netting) are explicitly excluded.
- **Don't skip Phase 1.** Even a fully-formed one-line idea gets framed and surfaced against the MIT rules before any divergence.
- **Don't pad the divergence.** ≥ 8 ideas is a floor, not a ceiling — but duplicates count, vague filler does not.

## Reference

- [reference/mit-framework.md](./reference/mit-framework.md) — MIT rules and 7-step process, mapped to this skill's phases.
- [reference/techniques.md](./reference/techniques.md) — curated 9-technique catalog with "When to use what" matrix.
- [reference/brief-template.md](./reference/brief-template.md) — stable Markdown schema for the saved brief.

## Examples

- [examples/brief-converged.md](./examples/brief-converged.md) — realistic 2-round session ending in CONVERGED.
- [examples/brief-rejected.md](./examples/brief-rejected.md) — realistic session ending in DROPPED with a clear drop reason.
