Updated `.claude/agents/code-reviewer.md` to tighten the delegation trigger (the description now names the situations that should route here — reviewing recent edits, a diff, or a branch before merge) and dropped `Edit` from `tools:` so it can no longer modify files.

Verification:
- frontmatter parses as valid YAML
- `name:` unchanged
- `tools:` no longer includes `Edit` / `Write`
- internal Markdown links still resolve
- restart Claude Code (or use `/agents`) to reload the file
