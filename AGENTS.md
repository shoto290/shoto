# AGENTS.md — Single Source of Truth

All AI agents working in this repo must follow these instructions.

This repo is the **shoto** Claude Code marketplace hosting one or more plugins under `plugins/`. It contains markdown artifacts only — no runtime, no build step.

- `plugins/<plugin>/skills/<name>/SKILL.md` — skill definitions (+ supporting files)
- `plugins/<plugin>/agents/<name>.md` — sub-agent definitions (frontmatter + body)
- `plugins/<plugin>/.claude-plugin/plugin.json` — plugin manifest
- `.claude-plugin/marketplace.json` — marketplace entry listing every plugin

## SIMPLE — Core Principles (Absolute Priority)

Every decision must pass through these six principles:

- **S — Simple** — Favor the simplest solution that solves the problem. Less code, fewer abstractions, no over-engineering.
- **I — Intentional** — Every line of code exists for a reason. No speculative features, no "just in case" logic.
- **M — Measurable** — Changes must have observable impact. If you can't verify it works, rethink the approach.
- **P — Pragmatic** — Ship what works today. Perfect is the enemy of done. Choose proven patterns over clever ones.
- **L — Layered** — Build incrementally. Each change should be a stable, shippable layer on top of what exists.
- **E — Envisioned** — Keep the end goal in sight. Short-term decisions should align with the long-term product vision.

## Behavioral Guidelines

Four rules that govern HOW you work. SIMPLE defines WHAT to build; these define how to approach the task. Adapted from [Karpathy's observations on LLM coding pitfalls](https://github.com/forrestchang/andrej-karpathy-skills).

**Tradeoff:** These bias toward caution over speed. For trivial tasks (typo, one-liner, obvious rename), use judgment — not every change needs the full rigor.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. If uncertain, ask rather than guess.
- If multiple interpretations exist, present them — never pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask 1-2 clarifying questions before writing.

### 2. Simplicity First

**Minimum content that solves the problem. Nothing speculative.**

- No sections beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- If 200 lines could be 50, rewrite it.
- Self-check: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing files:
- Don't "improve" adjacent content, comments, or formatting.
- Don't refactor sections that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead content, mention it — don't delete it.

When your changes create orphans:
- Remove references/links that YOUR changes made unused.
- Don't remove pre-existing unused content unless asked.

Self-check: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

For multi-step tasks, state a brief plan with verification:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") force constant clarification.

**These guidelines are working if:** diffs contain only requested changes, content is simple the first time, clarifying questions arrive before implementation rather than after mistakes.

## Authoring Rules

This repo exists to build skills, sub-agents, and hooks for Claude Code. **Use the dedicated authors instead of hand-crafting:**

| Artifact | Author |
|----------|--------|
| Skill (`plugins/<plugin>/skills/<name>/SKILL.md`) | `/core:skill` or the `skill-architect` sub-agent |
| Sub-agent (`plugins/<plugin>/agents/<name>.md`) | `/core:subagent` or the `subagent-architect` sub-agent |
| Hook (`.claude/hooks/*`) | `/core:hooks` skill |
| Coordinated multi-artifact change | `/core:evolve` (plans across skill / sub-agent / hook) |

The architects own frontmatter, scope selection, and the validation gate. Don't bypass them when scaffolding new artifacts.

## House Rules

- **Check before creating** — Search for existing skills/agents/hooks before adding new ones. Reuse over duplication.
- **One concern per commit** — Each commit addresses a single logical change.
- **Keep the manifest in sync** — When adding or renaming a skill/agent, update the relevant `plugins/<plugin>/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- **Match `name:` to the path** — A skill at `plugins/<plugin>/skills/foo/SKILL.md` must have `name: foo`. Same for agents.

## Enforced Rules

| Rule | Enforcement |
|------|-------------|
| Files in kebab-case | BLOCKING |
| No destructive git ops without confirmation | BLOCKING |
| No `.env` / secrets access | BLOCKING |

## Naming

| Type | Convention | Example |
|------|------------|---------|
| Files & directories | kebab-case | `skill-architect/` |
| Skill / agent `name:` | kebab-case, matches path | `name: skill-architect` |
| Headings | Title Case | `## Typical Flow` |

## Safety

### Destructive Operations — NEVER without confirmation

| Operation | Examples |
|-----------|----------|
| Force push | `git push --force`, `git push -f` |
| Hard reset | `git reset --hard`, `git checkout .`, `git clean -fd` |
| Branch delete | `git branch -D` |
| File destruction | `rm -rf` on any directory |

### Protected Files

- **Never read/modify:** `.env`, `.env.*`, `secrets/`, `*.pem`, `*.key`, `*.cert`
- **Confirm before modifying:** `plugins/<plugin>/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.github/workflows/`

### Branch Protection

Never push to `main`. Always work on feature branches.
