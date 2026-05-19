---
description: Create or update a Claude Code skill (a SKILL.md that extends Claude's capabilities). Use when the user wants to create, build, scaffold, write, modify, edit, refactor, rename, improve, fix, or change a skill, slash command, /command, or /name. Handles both new skills and updates to existing ones; walks through scope, frontmatter, supporting files, and testing.
argument-hint: '[skill-name]'
---

# Skill

A skill is a `SKILL.md` file with YAML frontmatter + markdown instructions. Users invoke it with `/skill-name`; Claude auto-loads it when the `description` matches the request.

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
| **Live context** | Shell output to inject with `` !`<command>` ``? |
| **Subagent** | Run in an isolated fork (`context: fork`)? |
| **Pre-approved tools** | List for `allowed-tools` |

### 2. Pick a template

Start from [templates/](./templates/):
- `basic.md` — minimal (description + instructions)
- `task.md` — action skill (deploy, commit), often with `disable-model-invocation: true`
- `reference.md` — knowledge skill (style guide, conventions)
- `advanced.md` — dynamic context + arguments + fork + tools

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

Keep `SKILL.md` under 500 lines. Move detail into:
- `reference/*.md` — docs Claude loads on demand
- `examples/*.md` — sample outputs
- `scripts/*` — files Claude executes (reference via `${CLAUDE_SKILL_DIR}`)
- `templates/*.md` — fill-in templates

Always reference supporting files from `SKILL.md` so Claude knows when to load them.

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

Read `SKILL.md` and every supporting file it references (`reference/`, `examples/`, `templates/`, `scripts/`). Don't propose changes blind.

### 3. Identify the change

Ask what to update (or infer from the user's request). Route to the relevant doc before editing:

| Change | Where to look |
| :-- | :-- |
| Description, `name`, `when_to_use`, `argument-hint`, `arguments`, `model`, `effort`, `paths`, `shell`, `hooks` | [reference/frontmatter.md](./reference/frontmatter.md) |
| Add / change `$ARGUMENTS` / `$N` / `$name` | [reference/frontmatter.md](./reference/frontmatter.md) + [examples/fix-issue.md](./examples/fix-issue.md) |
| Inject `!command` (dynamic context) | [reference/advanced.md](./reference/advanced.md) + [examples/summarize-changes.md](./examples/summarize-changes.md) |
| Convert to `context: fork` | [reference/advanced.md](./reference/advanced.md) + [examples/pr-summary.md](./examples/pr-summary.md) |
| Bundle a script (`${CLAUDE_SKILL_DIR}`) | [reference/advanced.md](./reference/advanced.md) + [examples/codebase-visualizer.md](./examples/codebase-visualizer.md) |
| `allowed-tools` / `disable-model-invocation` / `user-invocable` / `skillOverrides` | [reference/invocation.md](./reference/invocation.md) |
| Split long SKILL.md into supporting files | [reference/locations.md](./reference/locations.md) (directory layout section) |
| Rename the skill | Rename the directory — the new name becomes the command unless `name:` overrides it |
| Move scope (personal ↔ project ↔ plugin) | Move the directory; mind precedence and discovery in [reference/locations.md](./reference/locations.md) |
| Compaction / behavior across turns | [reference/lifecycle.md](./reference/lifecycle.md) |
| Doesn't trigger / triggers too often | [reference/troubleshooting.md](./reference/troubleshooting.md) |

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

## Examples

[examples/](./examples/) contains complete `SKILL.md` files for each pattern. Read the matching one before drafting a new skill or refactoring an existing one of that type.
