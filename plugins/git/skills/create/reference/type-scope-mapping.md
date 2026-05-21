# Conventional Commit Types and Scopes

## Types

| Type | When to use |
| :-- | :-- |
| `feat` | New user-facing functionality. |
| `fix` | Bug fix that changes observable behavior. |
| `refactor` | Internal restructure with no behavior change. |
| `chore` | Tooling, CI, dependency bumps, version bumps. |
| `docs` | Documentation-only changes. |
| `test` | Test-only changes (no production code touched). |
| `style` | Formatting, whitespace, lint fixes. No logic change. |

## Scope-selection rules

- **Single top-level directory touched** → use that directory name as scope.
- **Two directories, one clearly primary by line count** → use the primary scope.
- **Three or more directories, or cross-cutting** → omit scope parentheses entirely.
- Scope is always a short identifier from the repo layout, not a free-form label.

## Title examples

```
feat(apps/web): add password reset flow
fix(packages/api): return 404 when project is archived
refactor(packages/api): extract billing logic into its own module
chore(deps): bump axios to 1.7.7
docs: clarify deployment steps in the contributor guide
test(packages/api): cover edge cases in invoice rounding
```

## Title format

- `type(scope): description` or `type: description` when scope is omitted.
- ≤72 characters total.
- Lowercase after the colon.
- No trailing period.
- Imperative mood: `add`, `fix`, `update` — not `added`, `fixes`.
- Describes WHAT changed, not HOW.
