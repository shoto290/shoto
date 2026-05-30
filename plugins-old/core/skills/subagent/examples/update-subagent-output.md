Updated `.claude/agents/code-reviewer.md` to tighten the auto-delegation trigger ("Use immediately after writing or modifying code") and dropped `Edit` from `tools:` so it can no longer modify files.

Verification:
- frontmatter parses as valid YAML
- `name:` unchanged
- `tools:` no longer includes `Edit` / `Write`
- internal Markdown links still resolve
- restart Claude Code (or use `/agents`) to reload the file
