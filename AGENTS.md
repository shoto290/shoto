# AGENTS.md — Single Source of Truth

All AI agents working in this repo must follow these instructions.

This repo is the **shoto** Claude Code marketplace hosting one or more plugins under `plugins/`. It contains markdown artifacts plus a few validation and orchestration scripts — no build step, no package manager.

- `plugins/<plugin>/skills/<name>/SKILL.md` — skill definitions (+ supporting files)
- `plugins/<plugin>/agents/<name>.md` — sub-agent definitions (frontmatter + body)
- `plugins/<plugin>/hooks/hooks.json` — bundled plugin hooks (+ the scripts they call)
- `plugins/<plugin>/.claude-plugin/plugin.json` — plugin manifest
- `.claude-plugin/marketplace.json` — marketplace entry listing every plugin
- `evals/scenarios/<group>/<id>.json` — behavioral evaluation scenarios (+ `schema.json`)
- `evals/fixtures/<name>/` — throwaway repos copied to a workspace outside this repository for each live run
- `evals/run.sh`, `evals/verify.py` — the evaluation runner and verifier ([evals/README.md](evals/README.md))

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
| Skill (`plugins/<plugin>/skills/<name>/SKILL.md`) | `/core:skill` or the `skill-smith` sub-agent |
| Sub-agent (`plugins/<plugin>/agents/<name>.md`) | `/core:subagent` or the `subagent-smith` sub-agent |
| Hook (`.claude/hooks/*` or `plugins/<plugin>/hooks/hooks.json`) | `/core:hooks` skill |
| Coordinated multi-artifact change | `/core:evolve` to get the plan, then the matching author above for each entry |

The smiths own frontmatter, scope selection, and the validation gate. Don't bypass them when scaffolding new artifacts.

## House Rules

- **Check before creating** — Search for existing skills/agents/hooks before adding new ones. Reuse over duplication.
- **One concern per commit** — Each commit addresses a single logical change.
- **Keep the manifest in sync** — When adding or renaming a skill/agent, update the relevant `plugins/<plugin>/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- **Declare hard dependencies** — If a plugin's agent preloads a skill from another plugin, or one of its skills requires another plugin as a mandatory step, list that plugin in `dependencies` in `plugins/<plugin>/.claude-plugin/plugin.json`. Use the bare plugin name, never a version range — this repo publishes no `<plugin>--v<version>` git tags, and an unmatched range disables the plugin. Only hard edges count: optional or prose-only mentions are not dependencies, and `core` is the foundation so it declares none.
- **Match `name:` to the path** — A skill at `plugins/<plugin>/skills/foo/SKILL.md` must have `name: foo`. Same for agents.
- **The response-style card re-fires on every prompt on purpose** — `plugins/orchestrator/hooks/hooks.json` runs `response-style-card.sh` on `UserPromptSubmit`, which [reference/inject-context-on-compact.md](plugins/core/skills/hooks/reference/inject-context-on-compact.md) flags as an anti-pattern for static context. The deviation is deliberate: the answer contract is a per-turn obligation — verdict line plus a mandatory visual whose shape the contract picks — that decays when injected only at session boundaries, so ~455 tokens per prompt buys enforcement. The one genuinely static part, the five `classDef` colors, rides the `SessionStart` `startup|resume|clear|compact` branch instead. Don't "fix" the rest by moving it there too.

## Checks

Run `bash scripts/check-repo.sh` before opening a pull request — it is the only entry point, and every failure names the file, the reason, and the fix.

CI runs the same command, so a red local run is a red PR.

### Behavioral Evals

`scripts/check-repo.sh` also runs the evaluation harness's offline half in full — scenario schema validation, the verifier self-tests, and the fake-transcript replay. All three are free, need no credentials, and make no network call, so they belong in CI.

Live scenarios are opt-in and never run by the checks: `bash evals/run.sh <scenario-id>` calls the real model and **spends money** (capped per turn by `--max-budget-usd`, default 2, overridable with `EVAL_MAX_BUDGET_USD`). `bash evals/run.sh` with no argument is the free deterministic mode. A live run copies its fixture to a workspace outside this repository and refuses to start otherwise, so the agent under test never operates on your checkout. See [evals/README.md](evals/README.md).

## Enforced Rules

| Rule | Enforcement |
|------|-------------|
| `bash scripts/check-repo.sh` passes before a PR | BLOCKING |
| Files in kebab-case | BLOCKING |
| No destructive git ops without confirmation | BLOCKING |
| No `.env` / secrets access | BLOCKING |

## Naming

| Type | Convention | Example |
|------|------------|---------|
| Files & directories | kebab-case | `response-style/` |
| Skill / agent `name:` | kebab-case, matches path | `name: skill-smith` |
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
