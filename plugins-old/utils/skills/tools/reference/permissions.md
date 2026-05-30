# Permission rules

Claude Code resolves tool permissions against `allow`, `ask`, and `deny` lists in settings. The format for a single rule is:

```text
Tool(<specifier>)
```

Empty specifier (or bare tool name) matches every invocation of that tool. Rules merge across enterprise, user, project, and skill scope; `deny` always wins.

## Where rules live

| Scope | File | Notes |
| :-- | :-- | :-- |
| User | `~/.claude/settings.json` | Personal defaults. |
| Project | `.claude/settings.json` (committed) and `.claude/settings.local.json` (gitignored) | Requires workspace trust for project-scope `allow`. |
| Enterprise | Managed setting | Takes precedence over user / project. |
| Skill | `allowed-tools:` frontmatter | Pre-approves listed tools while the skill runs. |
| Hooks | Settings `hooks.<event>[].matcher` | Regex against tool name + input. |

## `Tool(specifier)` grammar by family

### Shell — `Bash`, `PowerShell`

Specifier is a **command prefix**, anchored at the start of the command line. Use `:*` to match arbitrary trailing args.

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(npm run:*)",
      "Bash(pytest:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)"
    ]
  }
}
```

### Filesystem — `Read`, `Edit`, `Write`, `Glob`, `Grep`, `NotebookEdit`

Specifier is a **path glob** (absolute or workspace-relative).

```jsonc
{
  "allow": [
    "Read(/Users/me/repo/**)",
    "Edit(/Users/me/repo/src/**)",
    "Glob(**/*.ts)"
  ],
  "deny": [
    "Edit(**/.env)",
    "Read(**/secrets/**)",
    "Write(**/*.key)"
  ]
}
```

### Network — `WebFetch`

Specifier is `domain:<host>` — no scheme, no path. Wildcards in host are not officially supported; use multiple rules instead.

```jsonc
{
  "allow": [
    "WebFetch(domain:docs.claude.com)",
    "WebFetch(domain:github.com)"
  ],
  "deny": ["WebFetch(domain:*)"]
}
```

### Search — `WebSearch`

No specifier; bare tool name. Use `allowed_domains` / `blocked_domains` parameters at call time for finer control.

```jsonc
{ "allow": ["WebSearch"] }
```

### Agents and skills — `Agent`, `Skill`

Specifier is the agent or skill `name:`.

```jsonc
{
  "allow": ["Agent(Explore)", "Skill(tools)"],
  "deny": ["Agent(*)", "Skill(deploy)"]
}
```

### Bare tools

Tools without a meaningful specifier (TodoWrite, TaskCreate, CronCreate, …) match on the bare tool name:

```jsonc
{
  "allow": [
    "TodoWrite",
    "TaskCreate",
    "TaskGet",
    "TaskList",
    "Monitor"
  ],
  "deny": ["CronDelete"]
}
```

## Precedence and merging

1. `deny` from any scope blocks the call.
2. Otherwise `ask` triggers a prompt.
3. Otherwise `allow` from any scope permits the call.
4. With no match, fall back to the default behaviour (prompt the user).

Enterprise scope wins over user; user wins over project for `deny`. For `allow`, project requires workspace trust.

## Skill `allowed-tools` frontmatter

A skill can pre-approve tools while it runs:

```yaml
---
name: my-skill
description: ...
allowed-tools: Read, Edit, Bash(npm run:*), WebFetch(domain:docs.claude.com)
---
```

This is **additive** — it does not override `deny`. Review carefully before committing project-scope skills with broad pre-approvals.

## Hook matchers

Hooks fire on tool lifecycle events. The `matcher` is a regex against the tool name, or — for some events — a pattern against the tool input.

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "./check-bash.sh" }]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "./check-write.sh" }]
      }
    ]
  }
}
```

**Pitfalls.**

- Forgetting that `matcher` is a regex — `Bash` matches `BashSomething` too. Anchor with `^Bash$` if needed.
- Hook script returning non-zero — blocks the tool call. Exit codes are load-bearing.

## Common patterns

**Read-only sandbox.** Allow file reads + searches, deny mutations.

```jsonc
{
  "allow": ["Read(**)", "Glob(**)", "Grep(**)"],
  "deny": ["Write(**)", "Edit(**)", "Bash(*)"]
}
```

**Build-and-test only.** Allow specific scripts; deny everything else shell-related.

```jsonc
{
  "allow": ["Bash(npm test:*)", "Bash(npm run build:*)"],
  "deny": ["Bash(*)"]
}
```

**Block secret access regardless of scope.**

```jsonc
{
  "deny": [
    "Read(**/.env*)",
    "Read(**/secrets/**)",
    "Edit(**/.env*)",
    "Write(**/.env*)"
  ]
}
```
