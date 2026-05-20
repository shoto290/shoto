# Pattern: fix-issue

**Pattern**: Single argument via `$ARGUMENTS`

Fixes a GitHub issue by number. The number passes in as `$ARGUMENTS`.

## SKILL.md

```yaml
---
description: Fix a GitHub issue
disable-model-invocation: true
argument-hint: '[issue-number]'
---

Fix GitHub issue $ARGUMENTS following our coding standards.

1. Read the issue description
2. Understand the requirements
3. Implement the fix
4. Write tests
5. Create a commit
```

## Invocation

```text
/fix-issue 123
```

Claude receives: "Fix GitHub issue 123 following our coding standards..."

## Notes

If `$ARGUMENTS` is absent from the body and the user passes arguments, Claude Code appends `ARGUMENTS: <input>` to the end of the skill content. Use the placeholder explicitly when you want the argument inline with the prose.

For multiple positional arguments, use `$0`, `$1`, ... or `$ARGUMENTS[0]`, `$ARGUMENTS[1]`. Example:

```yaml
---
name: migrate-component
description: Migrate a component from one framework to another
---

Migrate the $0 component from $1 to $2.
```

Invocation: `/migrate-component SearchBar React Vue` → `$0` = `SearchBar`, `$1` = `React`, `$2` = `Vue`.

Multi-word values: wrap in quotes — `/my-skill "hello world" second` → `$0` = `hello world`, `$1` = `second`.

You can also name positional arguments in frontmatter for readability:

```yaml
---
arguments: [component, from, to]
---

Migrate the $component component from $from to $to.
```
