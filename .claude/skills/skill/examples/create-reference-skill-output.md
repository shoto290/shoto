# Expected Output: Reference Skill

Use this as the shape of the output when creating a compact reference-style skill.

## Files

```text
.claude/skills/api-conventions/
└── SKILL.md
```

## `.claude/skills/api-conventions/SKILL.md`

```markdown
---
description: API conventions for this codebase. Use when creating, reviewing, or refactoring API endpoints, request validation, response formats, or error handling.
---

# API Conventions

When working on API endpoints:

1. Use resource-oriented route names.
2. Validate request input before calling domain logic.
3. Return errors in the shared `{ error: { code, message } }` shape.
4. Keep transport concerns out of service modules.

Read the surrounding API code before adding new conventions.
```

## Final Response Shape

```text
Created `.claude/skills/api-conventions/SKILL.md`.

It is a reference skill with a concise description for automatic loading and no extra supporting files.
```
