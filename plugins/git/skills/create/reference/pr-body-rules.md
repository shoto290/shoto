# PR body rules

Rules and sample outputs for the PR body skeleton in [../template.md](../template.md).

## Rules

- 1 to 4 bullets max.
- One short sentence per bullet, starting with an imperative verb.
- Audience is non-developers — explain WHAT and WHY, never HOW.
- No file paths, no function names, no class names, no internal jargon.

## Example — feat

```
## Summary

- Add a password reset flow so users locked out of their account can recover access.
- Email a one-time link valid for 30 minutes.
```

## Example — fix

```
## Summary

- Stop archived projects from showing up in the dashboard list.
- Return a clear error when someone tries to open one directly.
```

## Optional — Test plan (opt-in)

Only add this section when the user explicitly asks for it:

```
## Test plan

- [ ] <verifiable check>
- [ ] <verifiable check>
```

## What to avoid

- File paths (`src/foo/bar.ts`).
- Function or class names (`resetPassword()`, `BillingService`).
- Implementation jargon (`refactored the reducer`, `bumped the lockfile`).
- Marketing fluff or vague verbs (`improve`, `enhance`, `tweak`).
