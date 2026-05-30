---
name: versioning
description: Bump the semver `version` field in `plugins/<plugin>/.claude-plugin/plugin.json` from Conventional Commits since the last release. Load when the user mentions semver, semantic versioning, version bump, plugin version, releasing a plugin, cutting a release, Conventional Commits, changelog generation, or bumping major / minor / patch for one or more plugins in this marketplace.
argument-hint: "[plugin-name]"
disable-model-invocation: false
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# versioning

Decide and apply the next semver version for a plugin in this marketplace, based on Conventional Commits touching its directory since the last release.

If `[plugin-name]` is provided (e.g. `core`, `utils`), bump that plugin only. If omitted, bump every plugin whose directory has commits since its last release tag.

## What semver means

Versions follow `MAJOR.MINOR.PATCH` ([semver.org](https://semver.org)):

- **MAJOR** — incompatible / breaking change to the plugin's public contract.
- **MINOR** — new functionality added in a backwards-compatible way.
- **PATCH** — backwards-compatible bug fix or perf improvement.

## Conventional Commits → bump kind

| Commit prefix | Bump |
| :-- | :-- |
| `feat:` (or `feat(scope):`) | MINOR |
| `fix:` / `perf:` | PATCH |
| `feat!:`, `fix!:`, any `<type>!:`, or footer `BREAKING CHANGE:` | MAJOR |
| `chore` / `docs` / `refactor` / `test` / `style` / `build` / `ci` | none |

The **highest** bump kind across all qualifying commits wins (major > minor > patch > none).

## Pre-1.0 note

Plugins in this marketplace are at `0.x.y`. Semver allows looser rules before `1.0.0`, but we keep the standard mapping (`feat` = minor, breaking = major) so behavior is predictable today and remains correct after `1.0.0`.

## Procedure

To bump one plugin:

1. `git fetch --tags`
2. Determine the base ref:
   - last tag matching `<plugin>-v*` if one exists,
   - else `origin/main` when running on a PR branch,
   - else the repo root commit.
3. List commits touching the plugin:
   ```
   git log <base>..HEAD --format=%H -- plugins/<plugin>/
   ```
4. Compute and (optionally) write the bump:
   ```
   plugins/utils/skills/versioning/scripts/bump-plugin-version.sh <plugin> [--base <ref>] [--apply]
   ```
   Without `--apply`, the script only prints the proposed bump. With `--apply` and a non-`none` bump, it rewrites the `"version"` line in `plugins/<plugin>/.claude-plugin/plugin.json`.
5. Verify the manifest from the repo root:
   ```
   claude plugin validate
   ```
6. Commit:
   ```
   chore(<plugin>): release v<new-version>
   ```
   `chore` does not itself trigger a future bump.

## Automation

A GitHub Action at `.github/workflows/version-bump.yml` runs the same `scripts/bump-plugin-version.sh` on every PR, edits each affected manifest in place, and commits the bump back to the PR branch. Conventional Commits in the PR are the only input — keep commit subjects clean.

## Reference

- [reference/conventional-commits.md](./reference/conventional-commits.md) — full mapping with examples and worked scenarios.
- [scripts/bump-plugin-version.sh](./scripts/bump-plugin-version.sh) — the bump implementation invoked locally and from CI.
