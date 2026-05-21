---
name: base
description: Foundation rules, workflows, and reference docs shared by all skills and subagents in this plugin. Loaded explicitly via Markdown link from other skills, or via `skills:` preload from subagents.
disable-model-invocation: true
---

# Base

This skill is the portable foundation other skills and subagents extend from. It does not auto-trigger from user prompts — it is loaded explicitly, the same way a parent class is imported by a subclass.

Use it to keep one canonical statement of principles, behavioral guidelines, and shared workflows instead of duplicating them in every artifact.

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

## 3. Common workflows

- **Inventory before proposing** — read existing artifacts before writing new ones. Reuse over duplication.
- **Get explicit approval before destructive operations** — `git push --force`, `git reset --hard`, `git branch -D`, `rm -rf`. Never run without confirmation. See [reference/git-safety.md](./reference/git-safety.md).
- **Validation gate before returning** — for any skill or subagent that produces files, verify: the file exists at the expected path, frontmatter is valid YAML with the required fields, every internal link resolves. See [reference/frontmatter.md](./reference/frontmatter.md).

## 4. How to extend from this base

Two integration patterns:

- **From a skill**: add a quoted line at the top of the `SKILL.md` body:

  ```markdown
  > Apply the rules from [core:base](../base/SKILL.md) in addition to those below.
  ```

- **From a subagent**: preload it via the `skills:` field in frontmatter:

  ```yaml
  skills: [base, foo]
  ```

## Reference

- [reference/naming.md](./reference/naming.md) — kebab-case files and directories, `name:` must match path, headings in title case.
- [reference/git-safety.md](./reference/git-safety.md) — destructive git operations that require explicit confirmation.
- [reference/frontmatter.md](./reference/frontmatter.md) — YAML must parse, `name` and `description` are mandatory for skills and subagents.
