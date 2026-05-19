# Example: codebase-visualizer

**Pattern**: Bundled script + `${CLAUDE_SKILL_DIR}` + visual output

Generates an interactive HTML tree view of a codebase by running a bundled Python script. The script does the work; the skill orchestrates.

## Directory layout

```text
codebase-visualizer/
├── SKILL.md
└── scripts/
    └── visualize.py
```

## SKILL.md

````yaml
---
name: codebase-visualizer
description: Generate an interactive collapsible tree visualization of your codebase. Use when exploring a new repo, understanding project structure, or identifying large files.
allowed-tools: Bash(python3 *)
---

# Codebase Visualizer

Generate an interactive HTML tree view of the project's file structure with collapsible directories.

## Usage

Run from the project root:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```

This creates `codebase-map.html` in the current directory and opens it in the default browser.

## What the visualization shows

- **Collapsible directories**: click folders to expand / collapse
- **File sizes**: displayed next to each file
- **Colors**: different colors per file type
- **Directory totals**: aggregate size per folder
````

## Why `${CLAUDE_SKILL_DIR}`

The skill's directory path varies by scope:
- Personal: `~/.claude/skills/codebase-visualizer/`
- Project: `<repo>/.claude/skills/codebase-visualizer/`
- Plugin: `<plugin>/skills/codebase-visualizer/`

`${CLAUDE_SKILL_DIR}` resolves to the actual directory at runtime so the same `SKILL.md` works in any scope without modification.

## Pattern extends to anything

Any script the user's environment can run — bash, node, python, ruby, deno. Visual outputs are popular (dependency graphs, coverage reports, schema diagrams) but the pattern works for any bundled tooling.

Use Python with standard-library-only when possible — no install step. The complete script for this example is in the Claude Code docs (≈100 lines, no third-party deps).
