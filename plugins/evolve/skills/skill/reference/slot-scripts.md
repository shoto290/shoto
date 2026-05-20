# scripts/ slot

## What it is

A directory of executable files the skill runs, not files Claude reads as context. The official docs describe this slot as:

> Scripts Claude can execute

```
my-skill/
├── SKILL.md
└── scripts/
    ├── visualize.py
    └── validators/
        └── check.sh
```

Unlike `reference/` or `examples/`, the contents of `scripts/` never enter the conversation directly — Claude invokes them via the `Bash` tool and reads their stdout.

## `${CLAUDE_SKILL_DIR}` expansion

Scripts must be invoked with the `${CLAUDE_SKILL_DIR}` substitution so the path resolves no matter where the skill is installed. From the docs:

> The directory containing the skill's SKILL.md file. For plugin skills, this is the skill's subdirectory within the plugin, not the plugin root. Use this in bash injection commands to reference scripts or files bundled with the skill, regardless of the current working directory.

Always invoke a bundled script via the substitution:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```

Never hardcode the absolute path — it will break the moment the skill is installed at a different scope.

## `allowed-tools` requirement

To let Claude run the script without a permission prompt on every invocation, the `SKILL.md` frontmatter must pre-approve the matching tool pattern, for example:

```yaml
allowed-tools: Bash(python3 *)
```

Without `allowed-tools`, the user is prompted on every run, which defeats the point of bundling the script. Pick the narrowest pattern that still covers the invocation — see [invocation.md](./invocation.md) for the permission model.

## Language and packaging

Any language is allowed: Python, Node, Bash, Ruby, a precompiled Go binary, anything the host can execute. Recommendations:

- **Prefer built-in libs** (Python stdlib, plain POSIX shell, Node built-ins) so the script runs without a dependency install.
- **If install is needed**, document it explicitly in `SKILL.md` — the user has to bring the deps themselves; the skill does not install them automatically.

## Runtime dependency

Flag the runtime requirement clearly in `SKILL.md` (e.g. "requires Python 3", "requires `jq`"). The user's machine must have the runtime available; if it does not, the script call fails at the `Bash` tool level. Documenting the dependency up front prevents silent failures during a real invocation.

## Naming conventions

- Lowercase kebab-case or snake_case for filenames.
- Use the right extension (`.py`, `.sh`, `.js`, `.rb`) — `Bash(python3 *)` and friends pattern-match on the command, not the extension, but the extension is a clear hint for the reader.
- Group sub-scripts in nested directories when the count grows (`scripts/validators/foo.py`, `scripts/generators/bar.py`).

## Anti-patterns

- Hardcoding absolute paths instead of `${CLAUDE_SKILL_DIR}` — breaks the moment the skill is installed at a different scope.
- Forgetting `allowed-tools` — every run prompts the user, which defeats the point of bundling the script.
- Shipping scripts that require a heavyweight install (large pip dep tree, npm install, system packages) without documenting it explicitly in `SKILL.md`.
- Using `scripts/` for files Claude is supposed to **read** as context. Those belong in `reference/` — see [slot-reference.md](./slot-reference.md).

## Cross-links

- [advanced.md](./advanced.md) — bundled-script patterns and other dynamic features
- [examples/codebase-visualizer.md](../examples/codebase-visualizer.md) — complete worked example of a script-bundled skill
- [invocation.md](./invocation.md) — the `allowed-tools` permission model
