# Repo archetypes

Each archetype maps a detection signal to a ≤3-item starter set of skills/agents/hooks. The ≤3 cap enforces the SIMPLE constraint structurally — never propose a fourth artifact in a single `/core:init` run; defer it to a follow-up.

The ≤3 cap applies **only to authored artifacts** (skills/agents/hooks that get created). In addition, each archetype may suggest **existing MCP servers** and **existing plugins to install** — these have zero authoring cost, are surfaced in a separate list, and do **not** count against the ≤3 cap. The authoritative MCP catalog lives in `core:mcp`'s [reference/mcp-server-catalog.md](../../mcp/reference/mcp-server-catalog.md); reference it rather than duplicating the full list.

Refer to [../../evolve/reference/decision-matrix.md](../../evolve/reference/decision-matrix.md) for `Need → Artifact type` mapping. This file only owns the per-archetype starter-set picks.

### Claude Code marketplace

- **Signal**: `plugins/**/.claude-plugin/plugin.json` exists at repo root (≥1 plugin).
- **Starter set (≤3)**:
  1. `release-notes` skill — generate a changelog entry from Conventional Commits across plugins.
  2. `manifest-sync` hook — PostToolUse on edits to `plugins/**/SKILL.md` / `plugins/**/agents/*.md` to remind/verify `marketplace.json` consistency.
  3. *(third slot left open; suggest `skill-author-check` subagent only if the user explicitly requests artifact-quality auditing.)*
- **MCP servers** (install, not counted in ≤3): none typically needed.
- **Existing plugins** (install, not counted in ≤3): none — this repo authors them.

### Node/TypeScript monorepo

- **Signal**: root `package.json` AND (`pnpm-workspace.yaml` OR `turbo.json` OR `nx.json` OR a `packages/` directory with sub-`package.json` files).
- **Starter set (≤3)**:
  1. `lint-fix` skill — run the workspace linter (eslint / biome) and apply autofixes scoped to changed files.
  2. `pr-check` subagent — run typecheck + tests + lint before opening a PR; report pass/fail per package.
  3. *(third slot: pre-commit format hook only if `prettier`/`biome` is detected in the root `package.json`.)*
- **MCP servers** (install, not counted in ≤3): `context7` for popular-library docs; add `GitHub MCP` if a GitHub remote is detected. Cross-signals: `@supabase/supabase-js` → Supabase MCP, `convex`/`convex.json` → Convex MCP (see `core:mcp` catalog).
- **Existing plugins** (install, not counted in ≤3): `frontend-design` if React/Vue/Angular deps are present, else point the user to `find-skills`.

### Python library

- **Signal**: `pyproject.toml` at repo root.
- **Starter set (≤3)**:
  1. `pytest` skill — run the test suite with coverage and surface the lowest-covered module.
  2. `release` skill — bump version per Conventional Commits, build the wheel, generate changelog.
  3. *(third slot: coverage-report hook only if `pytest-cov` is in `pyproject.toml`.)*
- **MCP servers** (install, not counted in ≤3): `context7` for popular-library docs.
- **Existing plugins** (install, not counted in ≤3): point the user to `find-skills`.

### Generic codebase with no `.claude/` setup

- **Signal**: none of the above archetypes match.
- **Starter set (≤1, intentionally minimal)**:
  1. `/core:evolve` — recommend the user invoke it directly on a concrete capability. No skill/agent/hook is auto-proposed; the repo isn't recognizable enough to assume needs.
- **MCP servers** (install, not counted in ≤3): suggest running `/core:mcp recommend` for a signal-driven scan.
- **Existing plugins** (install, not counted in ≤3): point the user to `find-skills`.

> Adding a new archetype: pick a high-confidence detection signal (file presence is most reliable; package-manifest content is acceptable). Keep the starter set ≤3 items. Reference `../../evolve/reference/decision-matrix.md` for the `Need → Artifact type` mapping rather than restating it.
