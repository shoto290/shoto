# Repo archetypes

Each archetype maps a detection signal to a ≤3-item starter set of skills/agents/hooks. The ≤3 cap enforces the SIMPLE constraint structurally — never propose a fourth artifact in a single `/core:init` run; defer it to a follow-up.

Refer to [../../evolve/reference/decision-matrix.md](../../evolve/reference/decision-matrix.md) for `Need → Artifact type` mapping. This file only owns the per-archetype starter-set picks.

### Claude Code marketplace

- **Signal**: `plugins/**/.claude-plugin/plugin.json` exists at repo root (≥1 plugin).
- **Starter set (≤3)**:
  1. `release-notes` skill — generate a changelog entry from Conventional Commits across plugins.
  2. `manifest-sync` hook — PostToolUse on edits to `plugins/**/SKILL.md` / `plugins/**/agents/*.md` to remind/verify `marketplace.json` consistency.
  3. *(third slot left open; suggest `skill-author-check` subagent only if the user explicitly requests artifact-quality auditing.)*

### Node/TypeScript monorepo

- **Signal**: root `package.json` AND (`pnpm-workspace.yaml` OR `turbo.json` OR `nx.json` OR a `packages/` directory with sub-`package.json` files).
- **Starter set (≤3)**:
  1. `lint-fix` skill — run the workspace linter (eslint / biome) and apply autofixes scoped to changed files.
  2. `pr-check` subagent — run typecheck + tests + lint before opening a PR; report pass/fail per package.
  3. *(third slot: pre-commit format hook only if `prettier`/`biome` is detected in the root `package.json`.)*

### Python library

- **Signal**: `pyproject.toml` at repo root.
- **Starter set (≤3)**:
  1. `pytest` skill — run the test suite with coverage and surface the lowest-covered module.
  2. `release` skill — bump version per Conventional Commits, build the wheel, generate changelog.
  3. *(third slot: coverage-report hook only if `pytest-cov` is in `pyproject.toml`.)*

### Generic codebase with no `.claude/` setup

- **Signal**: none of the above archetypes match.
- **Starter set (≤1, intentionally minimal)**:
  1. `/core:evolve` — recommend the user invoke it directly on a concrete capability. No skill/agent/hook is auto-proposed; the repo isn't recognizable enough to assume needs.

> Adding a new archetype: pick a high-confidence detection signal (file presence is most reliable; package-manifest content is acceptable). Keep the starter set ≤3 items. Reference `../../evolve/reference/decision-matrix.md` for the `Need → Artifact type` mapping rather than restating it.
