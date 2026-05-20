# examples/ slot

## What it is

A directory of sample expected outputs, one file per shape Claude should produce. Per the official docs, `examples/` is for:

> example outputs showing the expected format

```
my-skill/
├── SKILL.md
└── examples/
    ├── create-output.md
    └── update-output.md
```

## Strict scope

Examples are **expected output samples only**. This skill enforces the rule in its own SKILL.md guidance: prompt recipes, complete sample `SKILL.md` files, workflow patterns, and API notes belong in `reference/`, not `examples/`.

If a file under `examples/` would not be a valid response Claude might produce, it does not belong here. Move it to `reference/` — see [slot-reference.md](./slot-reference.md).

## File naming

Free-form `.md` files inside `examples/`. The recommended convention is to name files after the output they show:

- `examples/create-output.md`
- `examples/update-output.md`
- `examples/pr-summary-output.md`
- `examples/commit-message-output.md`

Lowercase kebab-case keeps the filenames consistent with the rest of the skill layout.

## How Claude loads them

Files under `examples/` are loaded on demand — they do not enter context automatically. Always reference each example from `SKILL.md` so Claude knows the file exists and when to read it:

```markdown
When producing the output, follow the format shown in [examples/create-output.md](./examples/create-output.md).
```

If an example is never linked, Claude will not load it.

## Anti-patterns

- Putting prompt recipes or workflow patterns under `examples/` — those describe how to do something, not what the output should look like. They belong in `reference/`.
- Putting a complete sample `SKILL.md` under `examples/` — same reasoning: it is reference material, not an expected output of the current skill.
- Creating an `examples.md` (singular) file at the skill root. This skill standardises on the directory form `examples/` because the docs describe a folder of outputs, not a single file.
- Adding examples without linking them from `SKILL.md` — Claude cannot load what it does not know exists.

## Cross-links

- [slot-reference.md](./slot-reference.md) — for recipes, workflow patterns, and prompt notes
- [slot-template.md](./slot-template.md) — for fill-in skeletons that Claude completes per invocation
