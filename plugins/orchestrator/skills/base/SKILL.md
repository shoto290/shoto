---
name: base
user-invocable: false
description: Global foundation rules, principles, and shared conventions.
---

# Base

This skill is the global foundation everything in this plugin builds on — the canonical statement of how work is done here. Launch it deliberately (`/orchestrator:base`, or `Skill({skill:"orchestrator:base"})` from an agent) to load a clean, principled prompt. It is not meant to fire automatically on vague prompt matches.

Use it to keep one canonical statement of principles, behavioral guidelines, and shared workflows instead of duplicating them everywhere.

## 1. Core principles (SIMPLE)

Every decision must pass through these six principles:

- **S — Simple**: prefer the simplest solution that solves the problem. Less code, fewer abstractions, no over-engineering.
- **I — Intentional**: every line of code exists for a reason. No speculative features, no "just in case" logic.
- **M — Measurable**: changes must have observable impact. If you cannot verify it works, rethink the approach.
- **P — Pragmatic**: ship what works today. Proven patterns over clever ones.
- **L — Layered**: each change is a stable, shippable layer on top of what exists.
- **E — Envisioned**: short-term decisions align with the long-term product vision.

## 2. Behavioral guidelines

Four rules that govern HOW work is approached. SIMPLE defines WHAT to build; these define how to get there. For trivial tasks (typo, one-liner, obvious rename), use judgment — not every change needs the full rigor.

### Think Before Coding

- State assumptions explicitly. If uncertain, ask rather than guess.
- If multiple interpretations exist, present them — never pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing, and ask 1-2 clarifying questions before writing.

### Simplicity First

- Minimum content that solves the problem. Nothing speculative.
- No sections beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that was not requested.
- Self-check: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### Surgical Changes

- Touch only what you must. Match existing style even if you would do it differently.
- Do not "improve" adjacent content, comments, or formatting.
- Do not refactor sections that are not broken.
- Remove references and links that YOUR changes made unused. Do not remove pre-existing unused content unless asked.
- Self-check: every changed line should trace directly to the user's request.

### Goal-Driven Execution

For multi-step tasks, state a brief plan with verification:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria enable independent looping. Weak criteria ("make it work") force constant clarification.

## 3. Mandatory frontmatter

Every skill in this marketplace MUST declare these three fields:

| Field | Role |
| :-- | :-- |
| `name` | kebab-case identifier, matches the directory or filename. |
| `description` | What the skill does. The trigger Claude matches against requests — put the key use case first. |
| `when_to_use` | Additional context for when Claude should invoke the skill: trigger phrases or example requests. Appended to `description` in the skill listing and counts toward the 1,536-character cap. |

Optional fields (`disable-model-invocation`, `allowed-tools`, `argument-hint`, …) remain permitted on top of the three required ones. Full rules and the validation gate live in [reference/frontmatter.md](./reference/frontmatter.md).

## 4. Common workflows

- **Inventory before proposing** — read existing artifacts before writing new ones. Reuse over duplication.
- **Get explicit approval before destructive operations** — `git push --force`, `git reset --hard`, `git branch -D`, `rm -rf`. Never run without confirmation. See [reference/git-safety.md](./reference/git-safety.md).
- **Validation gate before returning** — for any skill that produces files, verify: the file exists at the expected path, frontmatter is valid YAML carrying the three mandatory fields, every internal link resolves. See [reference/frontmatter.md](./reference/frontmatter.md).

## 5. Delegation by composition

Skills compose by delegating to one another instead of re-implementing capabilities that already exist. When this skill needs a capability another skill provides, delegate via `Skill({ skill: "<name>", args: "<topic>" })`.

Re-implementation duplicates logic, drifts over time, and bypasses the careful structure of the canonical skill. Do not re-implement.

## Reference

- Read [reference/naming.md](./reference/naming.md) when naming a file, a directory, or a `name:` field, to get the kebab-case rule and the path-matching requirement.
- Read [reference/git-safety.md](./reference/git-safety.md) when a task reaches for force push, hard reset, branch delete, or `rm -rf`.
- Read [reference/frontmatter.md](./reference/frontmatter.md) when writing or reviewing a frontmatter block.
