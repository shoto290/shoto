# Naming

Portable naming rules for skills, subagents, and supporting files.

## Files and directories

- Use `kebab-case` for every file and directory: lowercase letters, digits, and hyphens. No spaces, no underscores, no camelCase.
- Examples: `skill-architect/`, `git-safety.md`, `pr-summary.md`.

## Skill and subagent `name:`

- The `name:` field in frontmatter must be `kebab-case` and must match the directory or filename that holds it.
  - A skill at `<plugin>/skills/foo/SKILL.md` must declare `name: foo`.
  - A subagent at `<plugin>/agents/bar.md` must declare `name: bar`.
- Renaming the directory or file without updating `name:` (or vice versa) breaks discovery.

## Headings

- Use Title Case for top-level and section headings (`## Typical Flow`, not `## typical flow`).
- Keep heading depth shallow — prefer two or three levels over five.

## Slash commands

- A skill's slash command is derived from its directory name unless overridden by `name:` in frontmatter.
- Keep names short and unambiguous; aim for one or two words.
