# Conventional Commits → semver bump

This is the full mapping used by [`scripts/bump-plugin-version.sh`](../scripts/bump-plugin-version.sh).

## Mapping

| Commit subject | Bump | Example |
| :-- | :-- | :-- |
| `feat: <subject>` | MINOR | `feat: add /utils:versioning skill` |
| `feat(<scope>): <subject>` | MINOR | `feat(core): add subagent-architect` |
| `fix: <subject>` | PATCH | `fix: handle missing tag on first release` |
| `fix(<scope>): <subject>` | PATCH | `fix(utils): correct manifest path resolution` |
| `perf: <subject>` | PATCH | `perf: skip log walk when base equals HEAD` |
| `perf(<scope>): <subject>` | PATCH | `perf(core): cache skill discovery` |
| `<type>!: <subject>` | MAJOR | `feat!: drop pre-1.0 manifest layout` |
| `<type>(<scope>)!: <subject>` | MAJOR | `refactor(utils)!: rename plugin.json fields` |
| Any commit with footer `BREAKING CHANGE: …` | MAJOR | `feat: rework hook contract` + footer `BREAKING CHANGE: hooks must now return JSON.` |
| `chore` / `docs` / `refactor` / `test` / `style` / `build` / `ci` | none | `chore(utils): release v0.2.0` |

The **highest** bump across all commits in `base..HEAD` that touched `plugins/<plugin>/` wins.

## How `!` and `BREAKING CHANGE:` interact

Both flags promote the bump to MAJOR. They can be used independently or together:

- `!` after the type/scope in the subject (`feat!:`, `fix(api)!:`) is the short form.
- `BREAKING CHANGE: <text>` as a footer in the commit body is the long form and lets you explain the break.
- If either is present in any commit since the last release, the bump is MAJOR even if every other commit is a `feat` or `fix`.

## Worked examples

### Example 1 — patch bump

Current version: `0.2.0`.

Commits since last tag, touching `plugins/utils/`:

```
fix(utils): handle missing plugin.json gracefully
chore(utils): tidy reference docs
docs(utils): clarify --apply flag
```

Highest bump = `fix` → PATCH. New version: `0.2.1`.

### Example 2 — minor bump

Current version: `0.2.1`.

Commits:

```
feat(utils): add /utils:versioning skill
fix(utils): correct argument parsing
perf(utils): cache git log lookup
```

Highest bump = `feat` → MINOR. New version: `0.3.0`.

### Example 3 — major bump

Current version: `0.3.0`.

Commits:

```
feat(utils): support per-plugin bump filtering
refactor(utils)!: rename `plugin.json` `version` field
fix(utils): off-by-one in base ref detection
```

Highest bump = `!` in the refactor → MAJOR. New version: `1.0.0`.
