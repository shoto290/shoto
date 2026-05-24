# Inventory checklist (Phase 1)

This phase is read-only. Do not modify any file.

**Preferred path:** delegate the whole inventory to `explore:explore` (see SKILL.md Phase 1) — it runs in `context: fork` with the `Explore` agent and returns a compact report. Only run the inline steps below as a fallback for tiny `.claude/` setups or when `explore:explore` is unavailable.

1. **Skills** — for each `.claude/skills/*/SKILL.md`:
   - Read the YAML frontmatter.
   - Capture: `description`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `context`, `agent`.
   - Note whether it implements a create/update flow (look for "detect intent" / "create flow" / "update flow" sections in the body).

2. **Subagents** — for each `.claude/agents/*.md`:
   - Read the frontmatter.
   - Capture: `name`, `description`, `tools`, `model`.
   - Note whether the description is broad (auto-trigger risk) or narrow (focused).

3. **Hooks** — read `.claude/settings.json` and `.claude/settings.local.json` (if it exists):
   - Parse the `hooks` block.
   - For each entry, capture: `event`, `matcher`, `type`, `command` or `prompt`.

4. **Settings constraints** — from the same files:
   - List `permissions.deny` entries (these constrain what new artifacts can do).
   - List `permissions.allow` entries.
   - Flag any global config that would conflict with the user's request.

This inventory is read-only. Do not modify any file during Phase 1.
