# Where skills live

Storage location determines who can use a skill.

| Location | Path | Applies to |
| :-- | :-- | :-- |
| Enterprise | Managed settings | All users in the org |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All the user's projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project only |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where the plugin is enabled |

When names collide across scopes:
- Enterprise > Personal > Project
- Plugin skills use a `plugin-name:skill-name` namespace and can never conflict

Files in `.claude/commands/` still work and follow the same rules. If a skill and a command share a name, the skill wins.

## Skill directory layout

Each skill is a directory with `SKILL.md` as the entrypoint. Optional supporting files live alongside it:

```text
my-skill/
├── SKILL.md           # required, main instructions
├── template.md        # optional, single fill-in template for Claude to populate
├── reference.md       # optional, loaded on demand (or use reference/ for larger sets)
├── examples/
│   └── sample.md
└── scripts/
    └── helper.py      # executed, not loaded
```

The slots above are the **only** ones documented. No `templates/` (plural) directory: if you need a fill-in template, use a single `template.md` file. Larger reference material can live in a `reference/` directory.

Reference supporting files from `SKILL.md` so Claude knows when to read them.

## Live change detection

Claude Code watches these directories:
- `~/.claude/skills/`
- Project `.claude/skills/`
- Any `.claude/skills/` inside an `--add-dir` directory

Add / edit / remove a skill in any watched directory → effect within the current session, no restart. Creating a **top-level** skills directory that did not exist at session start requires restart so the new directory can be watched.

## Automatic discovery from parents and subdirectories

Project skills load from `.claude/skills/` in the starting directory **and every parent up to the repo root** — starting Claude in a subdirectory still picks up root-level skills.

When working with files in subdirectories below the starting directory, Claude Code also discovers `.claude/skills/` on demand. Useful for monorepos: `packages/frontend/.claude/skills/` is loaded when editing files in `packages/frontend/`.

## Skills from additional directories

`--add-dir <path>` grants file access but **not** general configuration discovery. Exception: `.claude/skills/` inside an added directory is loaded automatically. Live change detection applies.

Other `.claude/` configuration — subagents, commands, output styles — is **not** loaded from additional directories. CLAUDE.md files require `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to load.
