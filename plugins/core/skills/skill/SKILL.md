---
name: skill
description: Create or update a Claude Code skill (a SKILL.md that extends Claude's capabilities). Use when the user wants to create, build, scaffold, write, modify, edit, refactor, rename, improve, fix, or change a skill, slash command, /command, or /name. Handles both new skills and updates to existing ones; walks through scope, frontmatter, supporting files, and testing.
argument-hint: '[skill-name]'
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Skill

A skill is a `SKILL.md` file with YAML frontmatter + markdown instructions. Users invoke it with `/skill-name`; Claude auto-loads it when the `description` matches the request.

## Skill structure (canonical)

A skill is a directory. Only `SKILL.md` is required. Every other file is optional and serves a precise role per the official docs:

```
my-skill/
├── SKILL.md            # required — frontmatter + instructions (entry point)
├── template.md         # optional — a single fill-in template Claude uses to produce output
├── examples/           # optional — sample outputs showing the expected format
│   └── create-skill-output.md
├── reference.md        # optional — detailed docs Claude loads on demand
│   (or reference/      #   may be a directory for larger reference sets)
└── scripts/            # optional — files Claude executes (referenced via ${CLAUDE_SKILL_DIR})
    └── helper.py
```

**Use documented resource folders.** Prefer the slots above for supporting material. Avoid `templates/` (plural) and `docs/`; use `template.md`, `reference.md` / `reference/`, `examples/`, or `scripts/` instead. Reserve `examples/` for expected output examples only; put prompt recipes, complete sample `SKILL.md` files, API notes, and workflow patterns in `reference/`. Every supporting file must be linked from `SKILL.md` so Claude knows what it contains and when to load it.

For this skill's own expected outputs, use [examples/create-reference-skill-output.md](./examples/create-reference-skill-output.md), [examples/create-task-skill-output.md](./examples/create-task-skill-output.md), and [examples/update-skill-output.md](./examples/update-skill-output.md).

## Detect intent

If invoked as `/skill <name>`, treat `$ARGUMENTS` as the target name.

1. **Search for the name** in personal (`~/.claude/skills/<name>/SKILL.md`), project (`.claude/skills/<name>/SKILL.md` from CWD up to repo root), and enabled plugin (`<plugin>/skills/<name>/SKILL.md`) scopes
2. **Match found** → propose **update flow** (confirm with user before editing)
3. **No match** → propose **create flow** (validate the name: lowercase + digits + hyphens, max 64 chars)
4. **Empty / ambiguous** → ask the user

## When to suggest each flow

**Create** when the user:
- Pastes the same instructions, checklist, or procedure repeatedly
- Has a `CLAUDE.md` section that has grown into a procedure rather than a fact
- Wants a reusable workflow with a `/name` entry point
- Needs to inject live data (git diff, PR data, file listings) into a prompt

**Update** when the user wants to:
- Strengthen `description` so Claude auto-loads correctly
- Add or change arguments (`$ARGUMENTS`, `$N`, `$name`)
- Inject live shell output (`!command`)
- Convert to subagent execution (`context: fork`)
- Bundle a script and reference it via `${CLAUDE_SKILL_DIR}`
- Pre-approve tools (`allowed-tools`)
- Restrict who can invoke (`disable-model-invocation`, `user-invocable`)
- Split a long SKILL.md into supporting files
- Rename or move scope (personal ↔ project ↔ plugin)
- Diagnose why a skill doesn't trigger

---

## Create flow

### 1. Clarify the skill

Propose defaults from the user's request; confirm before writing:

| Decision | Options |
| :-- | :-- |
| **Name** | lowercase + digits + hyphens, max 64 chars (e.g. `summarize-pr`) |
| **Scope** | Personal `~/.claude/skills/<name>/`, Project `.claude/skills/<name>/`, Plugin `<plugin>/skills/<name>/` |
| **Type** | Reference (knowledge) or Task (action) |
| **Invoker** | User only, Claude only, or both (default: both) |
| **Arguments** | None, free-form (`$ARGUMENTS`), or positional (`$0`, `$1`...) |
| **Live context** | Shell output to inject via the `` !`command` `` substitution? |
| **Subagent** | Run in an isolated fork (`context: fork`)? |
| **Pre-approved tools** | List for `allowed-tools` |

See [reference/decision-questions.md](./reference/decision-questions.md) for the canonical list of decisions to surface to the user, with options, implications, and recommended defaults. `skill-architect` uses it to drive `AskUserQuestion` calls.

### 2. Pick a reference pattern

Start from a complete pattern reference:

- [reference/summarize-changes.md](./reference/summarize-changes.md) — auto-invocable + dynamic context (`` !`command` `` substitution)
- [reference/deploy.md](./reference/deploy.md) — task action + `disable-model-invocation` + `allowed-tools` + `$ARGUMENTS`
- [reference/fix-issue.md](./reference/fix-issue.md) — single argument via `$ARGUMENTS`; positional via `$0` / `$1`
- [reference/pr-summary.md](./reference/pr-summary.md) — `context: fork` + `agent: Explore` + multiple `` !`command` `` injections
- [reference/codebase-visualizer.md](./reference/codebase-visualizer.md) — bundled script + `${CLAUDE_SKILL_DIR}`

### 3. Create the directory and `SKILL.md`

```bash
mkdir -p <scope>/<skill-name>
```

Write `SKILL.md` with frontmatter between `---` markers, then the body:

```yaml
---
description: <what the skill does + when to use it, with trigger phrases>
---

<instructions, kept concise>
```

`description` is the only recommended field. See [reference/frontmatter.md](./reference/frontmatter.md) for every field.

### 4. Add supporting files (only if needed)

Keep `SKILL.md` under 500 lines. Move detail into documented resource folders:

- `reference.md` (or `reference/*.md`) — detailed docs Claude loads on demand
- `examples/*.md` — sample outputs showing the expected format only
- `scripts/*` — files Claude executes (reference via `${CLAUDE_SKILL_DIR}`)
- `template.md` — a single fill-in template (rare; only if the skill produces output from a template)

Put complete sample `SKILL.md` files, prompt recipes, and workflow patterns in `reference/`, not `examples/`. Always reference supporting files from `SKILL.md` so Claude knows when to load them. Do **not** create a `templates/` directory — it is not part of the official skill layout.

### 5. Test

- **Direct**: type `/skill-name` (with arguments if expected)
- **Automatic**: phrase a request matching the `description`
- Live edits propagate within the session; only **new top-level skill directories** require restart

---

## Update flow

### 1. Locate the target

Search for `<name>/SKILL.md` in:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/` from CWD up to the repo root
- Plugin: any enabled `<plugin>/skills/`

If matches exist in multiple scopes, ask which one (enterprise > personal > project takes precedence at runtime).

### 2. Read current state

Read `SKILL.md` and every supporting file it references (`reference/`, `examples/` for output samples, `template.md`, `scripts/`). Don't propose changes blind.

### 3. Identify the change

Ask what to update (or infer from the user's request). Route to the relevant doc before editing:

| Change | Where to look |
| :-- | :-- |
| Description, `name`, `when_to_use`, `argument-hint`, `arguments`, `model`, `effort`, `paths`, `shell`, `hooks` | [reference/frontmatter.md](./reference/frontmatter.md) |
| Add / change `$ARGUMENTS` / `$N` / `$name` | [reference/frontmatter.md](./reference/frontmatter.md) + [reference/fix-issue.md](./reference/fix-issue.md) |
| Inject `!command` (dynamic context) | [reference/advanced.md](./reference/advanced.md) + [reference/summarize-changes.md](./reference/summarize-changes.md) |
| Convert to `context: fork` | [reference/advanced.md](./reference/advanced.md) + [reference/pr-summary.md](./reference/pr-summary.md) |
| Bundle a script (`${CLAUDE_SKILL_DIR}`) | [reference/advanced.md](./reference/advanced.md) + [reference/codebase-visualizer.md](./reference/codebase-visualizer.md) |
| `allowed-tools` / `disable-model-invocation` / `user-invocable` / `skillOverrides` | [reference/invocation.md](./reference/invocation.md) |
| Split long SKILL.md into supporting files | [reference/locations.md](./reference/locations.md) (directory layout section) |
| Rename the skill | Rename the directory — the new name becomes the command unless `name:` overrides it |
| Move scope (personal ↔ project ↔ plugin) | Move the directory; mind precedence and discovery in [reference/locations.md](./reference/locations.md) |
| Compaction / behavior across turns | [reference/lifecycle.md](./reference/lifecycle.md) |
| Doesn't trigger / triggers too often | [reference/troubleshooting.md](./reference/troubleshooting.md) |

See [reference/decision-questions.md](./reference/decision-questions.md) for the update-flow decisions (target scope when multiple matches, fields to change, rename / scope-move confirmation, destructive-delete confirmation).

### 4. Apply the change

- Edit files via `Edit` — preserve what already works
- **Warn before** renaming or moving scope; both change the slash command and the discovery scope
- Live edits propagate within the session; re-invoke the skill to refresh its content mid-session

### 5. Test

- **Direct**: `/skill-name` (with new args if changed)
- **Automatic**: phrase a request matching the new `description`
- For trigger-related tweaks: ask `What skills are available?` to confirm the new wording is listed

---

## Critical principles

- **Body is recurring token cost** — rendered content stays in the session. Keep tight; state what to do, don't narrate.
- **Description sells the skill** — put the key use case first. Combined `description` + `when_to_use` cap = 1,536 chars.
- **Side effects → manual** — `disable-model-invocation: true` for skills like deploy, commit, send-message.
- **Knowledge → background** — `user-invocable: false` for context-only skills (e.g. `legacy-system-context`).
- **Pre-approve carefully** — `allowed-tools` skips approval prompts. Review before committing project skills.
- **Stick to documented resource folders** — use the slots above (`SKILL.md`, `template.md`, `examples/`, `reference.md` or `reference/`, `scripts/`). `examples/` is for output samples; workflow and prompt patterns belong in `reference/`. Don't invent new top-level folders.
- **Interactive by default** — when invoked via `skill-architect`, every key decision is surfaced to the user via `AskUserQuestion` with options + recommendation + implications. See [reference/decision-questions.md](./reference/decision-questions.md).

## Common gotchas

- Name validation: lowercase + digits + hyphens, max 64 chars
- `context: fork` requires an explicit task — guidelines alone return nothing
- New top-level skill directories need Claude Code restart to be watched
- `!command` substitution runs once before Claude sees the content; output is not re-scanned for nested placeholders
- Project skills' `allowed-tools` requires workspace trust
- Renaming the directory changes the slash command (unless `name:` is set in frontmatter)

## Reference

- [reference/frontmatter.md](./reference/frontmatter.md) — every frontmatter field + string substitutions
- [reference/locations.md](./reference/locations.md) — scopes, discovery, `--add-dir`, live detection
- [reference/invocation.md](./reference/invocation.md) — who can invoke, tool permissions, settings overrides
- [reference/lifecycle.md](./reference/lifecycle.md) — content across turns, compaction behavior
- [reference/advanced.md](./reference/advanced.md) — dynamic context, subagent execution, bundled scripts
- [reference/troubleshooting.md](./reference/troubleshooting.md) — when skills don't trigger

## Pattern References

- [reference/summarize-changes.md](./reference/summarize-changes.md) — dynamic context injection
- [reference/deploy.md](./reference/deploy.md) — manual task action
- [reference/fix-issue.md](./reference/fix-issue.md) — arguments and positional substitutions
- [reference/pr-summary.md](./reference/pr-summary.md) — subagent execution
- [reference/codebase-visualizer.md](./reference/codebase-visualizer.md) — bundled script

## Output Examples

- [examples/create-reference-skill-output.md](./examples/create-reference-skill-output.md) — expected output for a compact reference skill
- [examples/create-task-skill-output.md](./examples/create-task-skill-output.md) — expected output for a manually invoked task skill
- [examples/update-skill-output.md](./examples/update-skill-output.md) — expected final response after updating a skill

## Slot References

- [reference/slot-skill-md.md](./reference/slot-skill-md.md) — `SKILL.md` entry point: structure, body conventions, lifecycle
- [reference/slot-template.md](./reference/slot-template.md) — `template.md`: single fill-in template
- [reference/slot-examples.md](./reference/slot-examples.md) — `examples/`: sample expected outputs
- [reference/slot-reference.md](./reference/slot-reference.md) — `reference.md` / `reference/`: on-demand detailed docs
- [reference/slot-scripts.md](./reference/slot-scripts.md) — `scripts/`: executables invoked via `${CLAUDE_SKILL_DIR}`
