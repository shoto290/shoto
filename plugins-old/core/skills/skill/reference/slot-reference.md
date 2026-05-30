# reference.md / reference/ slot

## What it is

Detailed docs Claude loads on demand. Two equivalent shapes are supported:

- **Single file `reference.md`** at the skill root — use when there is one coherent body of doc to offload.
- **Directory `reference/`** containing focused `.md` files — use when the offloaded content splits naturally into multiple topics (one per concern).

```
my-skill/
├── SKILL.md
└── reference.md            # one coherent doc

# or:

my-skill/
├── SKILL.md
└── reference/
    ├── frontmatter.md      # one file per topic
    ├── advanced.md
    └── troubleshooting.md
```

Both shapes are documented; pick whichever matches the content. Mixing them at the same level is not standard — pick one.

## When to use

The official docs are explicit about the 500-line ceiling on the SKILL.md body:

> Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

Triggers to offload into `reference.md` / `reference/`:

- The SKILL.md body would otherwise exceed ~500 lines (see [slot-skill-md.md](./slot-skill-md.md)).
- A section is only relevant for a sub-task and should not pay the recurring token cost on every invocation.
- The content is a long-form spec (API list, frontmatter field catalog, troubleshooting tree) that Claude only needs in narrow situations.

## Progressive disclosure

The whole point of this slot is progressive disclosure. From the docs:

> Large reference docs, API specifications, or example collections don't need to load into context every time the skill runs.

Reference files are linked from `SKILL.md` so Claude knows they exist; the content is only pulled in when the model decides it needs it. That is what keeps the recurring token cost bounded while still letting the skill ship deep documentation.

## Linking from SKILL.md

Every supporting reference file must be linked from `SKILL.md` — unlinked files are invisible to Claude. The conventional shape is an "Additional resources" (or "Reference") section near the bottom of the body:

```markdown
## Additional resources

- For complete API details, see [reference.md](./reference.md)
- For frontmatter fields, see [reference/frontmatter.md](./reference/frontmatter.md)
```

Use relative paths so the links resolve regardless of where the skill is installed.

## Naming conventions inside `reference/`

- Lowercase kebab-case `.md` files (e.g. `frontmatter.md`, `advanced.md`, `troubleshooting.md`).
- Group by topic — one file per concern — not by lifecycle phase. `frontmatter.md` is good; `step-1.md` is not.
- Keep filenames short and predictable; Claude reads the filename as a hint to what is inside.

## Anti-patterns

- Putting expected output samples under `reference/` — those go in `examples/`. See [slot-examples.md](./slot-examples.md).
- Creating a `docs/` directory instead of using `reference/` — `docs/` is not part of the official skill layout.
- Forgetting to link the file from `SKILL.md` — Claude cannot load what it does not know exists.
- One giant `reference.md` when the content clearly splits into multiple topics — break it into `reference/<topic>.md` files for cleaner on-demand loading.

## Cross-links

- [slot-skill-md.md](./slot-skill-md.md) — the 500-line ceiling and body conventions
- [slot-examples.md](./slot-examples.md) — the recipes-vs-samples distinction
