# Examples

The [templates/](../templates/) directory holds copy-paste starting points for new subagents. Open the matching template before drafting a new agent of that type:

- `templates/basic.md` — minimum viable
- `templates/code-reviewer.md` — read-only review
- `templates/debugger.md` — analyze + fix
- `templates/data-scientist.md` — domain specialist with pinned model
- `templates/db-reader-hooks.md` — hook-validated read-only SQL
- `templates/coordinator.md` — main-thread agent that spawns specific workers

The reference docs in [../reference/](../reference/) cover the *why* behind each template — frontmatter fields, scopes, tools, permissions, context loading, and invocation patterns.
