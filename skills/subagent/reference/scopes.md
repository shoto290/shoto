# Scopes & locations

Subagents are Markdown files. Where you put them determines who can use them and which one wins when names collide.

## Precedence table

| Location | Scope | Priority | How to create |
| :-- | :-- | :-- | :-- |
| Managed settings directory | Organization-wide | 1 (highest) | Deployed by IT admin |
| `--agents` CLI flag | Current session only | 2 | Inline JSON when launching `claude` |
| `.claude/agents/` | Current project | 3 | File or `/agents` UI |
| `~/.claude/agents/` | All your projects | 4 | File or `/agents` UI |
| `<plugin>/agents/` | Where plugin is enabled | 5 (lowest) | Installed via plugin |

Higher priority wins when names collide.

## Choosing a scope

**Project (`.claude/agents/`)** — *recommended default*. Check into git so the team gets the same subagents. Discovered by walking up from CWD to the repo root.

**User (`~/.claude/agents/`)** — personal subagents available in every project. Use for workflows that aren't project-specific.

**Plugin** — distribute to many users. Plugin subagents **ignore** `hooks`, `mcpServers`, and `permissionMode` — those fields are silently dropped. If you need them, copy the file out of the plugin into `.claude/agents/` or `~/.claude/agents/`.

**`--agents` CLI flag** — ephemeral, session-only. Useful for testing or scripts. Multiple subagents in one JSON blob:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist for errors and test failures.",
    "prompt": "You are an expert debugger..."
  }
}'
```

The JSON keys are the agent names. Values accept the same fields as file frontmatter, except `prompt` replaces the markdown body.

## Subdirectories

`.claude/agents/` and `~/.claude/agents/` are scanned **recursively**. You can organize:

```
.claude/agents/
├── review/
│   ├── code.md
│   └── security.md
└── research/
    └── architecture.md
```

The subfolder path does **not** affect the subagent's id — identity comes from the `name` frontmatter only. Names must be unique across the whole tree within a scope; duplicates within one scope are silently discarded.

**Plugin paths are different**: a file at `agents/review/security.md` in `my-plugin` registers as `my-plugin:review:security` — the subfolder becomes part of the scoped identifier.

## `--add-dir` does not extend agent discovery

Paths added with `--add-dir` grant file access only. They are **not scanned** for subagents. To share subagents across projects, use `~/.claude/agents/` or a plugin.

## Discovery + naming gotchas

- Filename ≠ agent name. Identity is `name:` in frontmatter.
- Two files with the same `name:` in one scope → one silently wins.
- `name` must be lowercase letters and hyphens only.
- Restart the session after creating new files on disk; `/agents` UI edits take effect immediately.
