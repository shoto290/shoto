---
name: clean-code-craft
description: 'Clean-code craft: explicit self-documenting naming, the scope-length naming rule, short single-responsibility functions, readable control flow, refactoring discipline, and no dead code or comments.'
when_to_use: 'Reach for it when naming things, writing or refactoring functions, simplifying control flow, or deciding whether code is readable enough to ship.'
---

# Clean Code Craft

Write code that explains itself. Names carry intent, functions do one thing, control flow reads top to bottom, and nothing stays that does not earn its place.

## Naming

Names reveal intent. The reader should never decode them.

- Verbs for functions (`fetchUser`, `isExpired`), nouns for values (`user`, `retryCount`).
- Booleans as predicates: `isActive`, `hasAccess`, `shouldRetry`.
- No abbreviations, no single letters — except a loop index (`i`, `j`).

```ts
function d(u: User): number { return Date.now() - u.t; }
```

```ts
function accountAgeMs(user: User): number {
  return Date.now() - user.createdAt;
}
```

## Scope-length rule

Name length tracks scope. A tight, short-lived scope tolerates a short name; a wide or long-lived one demands a descriptive one.

```ts
for (let i = 0; i < items.length; i++) process(items[i]);
export const MAX_LOGIN_ATTEMPTS_BEFORE_LOCKOUT = 5;
```

## Self-documenting over comments

A comment that restates the code is a smell. Extract a well-named function or constant instead.

```ts
if (user.age >= 18 && user.country === "US") allow();
```

```ts
const isEligibleAdult = user.age >= LEGAL_AGE && user.country === "US";
if (isEligibleAdult) allow();
```

## Short functions & single responsibility

A function has one reason to change. Extract until each does one thing. Prefer early returns over nested conditionals.

- If you reach for a comment to separate "sections", split into functions.
- A function that mixes fetching, transforming, and rendering does three jobs — split it.

```ts
function save(user: User) {
  if (!user.email) throw new Error("email required");
  if (!user.name) throw new Error("name required");
  db.insert(user);
}
```

## Readable control flow

- Guard clauses first; return early to flatten nesting.
- No flag arguments — they hide two functions in one.
- No clever one-liners that trade clarity for brevity.

```ts
function render(node: Node, asDraft: boolean) {
  if (asDraft) return renderDraft(node);
  return renderPublished(node);
}
```

```ts
function renderDraft(node: Node) { /* ... */ }
function renderPublished(node: Node) { /* ... */ }
```

## Refactoring discipline

- Small, safe steps — one rename or extraction at a time, verify, repeat.
- Rename freely the moment a name stops fitting.
- Leave it cleaner, but only within the scope you are already touching — see AGENTS.md Surgical Changes. Do not refactor sections that are not broken.

## No dead code

- Delete unused functions, variables, and imports — version control remembers them.
- Never comment out code "for later"; delete it.
- No just-in-case parameters or branches that nothing exercises.

## Pass/fail checklist

- [ ] Every name reveals intent without a comment.
- [ ] Booleans read as predicates (`is`/`has`/`should`).
- [ ] Name length matches scope width.
- [ ] No comment restates what the code already says.
- [ ] Each function has one reason to change.
- [ ] Guard clauses replace nested conditionals; no flag arguments.
- [ ] No commented-out or unused code remains.
- [ ] Refactors stayed within the scope you were touching.
