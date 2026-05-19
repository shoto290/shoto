# Template: reference

Knowledge skill — supplies conventions, style, or domain knowledge Claude applies to current work. Often invoked automatically by Claude rather than the user.

```yaml
---
description: <what knowledge this provides + when it's relevant>
---

When <doing X>:
- <convention 1>
- <convention 2>
- <convention 3>

<additional guidelines, examples, or anti-patterns>
```

Variants:
- Add `user-invocable: false` if `/skill-name` isn't a meaningful action (pure background context)
- Add `paths: <glob>` to scope auto-invocation to specific files (e.g. `paths: 'src/api/**/*.ts'`)

Use when:
- Style guides, naming conventions, architectural patterns
- Domain knowledge (legacy system explanations, business rules)
- "Always use X when doing Y" guidance

Avoid for actions — reference content should be applicable across many tasks, not a single procedure.
