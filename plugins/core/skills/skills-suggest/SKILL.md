---
name: skills-suggest
description: Given a natural-language intent (e.g. "I want to understand the auth flow", "I need to commit my changes", "find a date-picker component"), recommend the canonical, already-installed skill(s) to invoke, with a one-line justification per candidate. ROUTES among skills you already have installed — does NOT install new skills (use `find-skills` for that) and does NOT create new skills (use `core:skill` or `core:evolve` for that). Reads the delegation table in `core:base` section 5 as the primary input. Triggers on `/core:skills-suggest`, "which skill should I use for X", "what's the right skill for…", "route this task", "recommend a skill".
argument-hint: '<intent>'
allowed-tools: Read, Glob, Skill
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Skills suggest

With dozens of installed skills, picking the right one is non-trivial. This skill maps a free-form intent to the canonical, already-installed skill(s), based on the delegation table in `core:base` section 5 and a contextual check of what's actually available locally.

## When invoked

1. **Read the intent** — argument is `$1`. If empty, ask via `AskUserQuestion` for the intent in one sentence. Otherwise proceed silently.
2. **Read the canonical delegation map** — open `../base/SKILL.md` and parse section 5 ("Delegation targets"). This is the source of truth for intent → skill mapping.
3. **Check local availability** — invoke `Skill({ skill: "core:skills-list" })` to get the list of installed skills in the current context. Don't recommend a skill that isn't actually installed here.
4. **Match the intent to candidates** — find the row(s) in the delegation table whose "Intent / capability" cell best matches the user's intent (keyword overlap, semantic match). Cap at 3 candidates max, ordered by best-fit first.
5. **Render the recommendation** — for each candidate skill, produce:
   - **Name** (e.g. `explore:explore`)
   - **Why it fits** — one short sentence tying the user's intent to the skill's purpose.
   - **Invocation** — a copy-pasteable `Skill({ skill: "...", args: "..." })` snippet with `args` filled in from the user's intent.
   - **Boundary** — one sentence stating what this skill does NOT do (e.g. "explore:explore reads the codebase — it does not edit files").
6. **Handle no-match** — if no canonical skill fits the intent, say so explicitly. Recommend:
   - `find-skills` if the user might want to install an external skill, OR
   - `core:evolve` if the gap should be filled by creating a new skill.
7. **Handle overlap** — if two candidates overlap significantly, surface the overlap explicitly with the boundary of each — never silently pick one.

## Output format

Intent: `I need to find an existing component for a date picker`

**1. `explore:explore`**
- **Why it fits**: The codebase-exploration plugin includes a component-explorer specialist that surfaces existing UI components matching a description.
- **Invocation**: `Skill({ skill: "explore:explore", args: "find an existing date-picker component" })`
- **Boundary**: `explore:explore` reads the codebase to locate and describe components — it does not scaffold new components or edit existing ones.

## Anti-patterns

- Don't invent skill names. Only recommend skills that exist in the delegation table AND are confirmed available by `core:skills-list`.
- Don't install. Don't create. This is strictly routing.
- Don't pick silently when two skills overlap — surface the overlap.
- Don't skip step 3 (the availability check). Without it, you may recommend a skill the user doesn't have.

## Reference

- [`core:base` section 5](../base/SKILL.md#5-delegation-targets) — canonical delegation map (primary input).
- [`core:skills-list`](../skills-list/SKILL.md) — local availability check (called in step 3).
- `find-skills` (sibling/global) — for installing new skills if no match.
- `core:evolve` — for creating new skills if the gap is structural.
