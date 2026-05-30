# template.md slot

## What it is

A single fill-in template Claude uses as the canonical skeleton for the skill's output. The file sits at the skill root as `template.md` — singular, exact filename. There is no `templates/` directory and no plural variant.

```
my-skill/
├── SKILL.md
└── template.md     # the skill's one canonical output skeleton
```

## When to use

Only when the skill genuinely produces a fixed-shape document where Claude fills in the blanks — for example a structured commit-message format, a PR description scaffold, or a release-note template.

This is rare in practice. Most skills should describe the expected output inline in the SKILL.md body, or ship a worked sample under `examples/` (see [slot-examples.md](./slot-examples.md)). Reach for `template.md` only when the shape is rigid and reused on every invocation.

## How Claude reads it

Claude does not magically discover `template.md`. Reference it explicitly from `SKILL.md` so the model knows the file exists and when to load it. Claude reads it as additional context, not as an executable file — there is no rendering pass, no placeholder syntax, no validation. The file is just markdown the model is told to follow.

## Linking from SKILL.md

Always link with a relative path so the link resolves regardless of where the skill is installed:

```markdown
Fill in [template.md](./template.md) using the user's inputs.
```

Reference it from the body section that describes the output step — that is where Claude needs to know the template exists.

## Anti-patterns

- Calling the file `templates.md` (plural) — not the convention; Claude will not surface it.
- Putting the file inside a `templates/` directory — that directory is not part of the official skill layout.
- Using `template.md` for content that is really a sample output. Sample outputs belong under `examples/` — see [slot-examples.md](./slot-examples.md).
- Shipping multiple "templates" by adding `template-a.md`, `template-b.md` at the root. If the skill needs multiple shapes, the right slot is `examples/` (one file per shape) or `reference/` (named docs per concern) — see [slot-reference.md](./slot-reference.md).

## Cross-links

- [slot-examples.md](./slot-examples.md) — when the content is an example expected output, not a fill-in template
- [slot-reference.md](./slot-reference.md) — when the content is reference docs (recipes, patterns, API notes), not a template
