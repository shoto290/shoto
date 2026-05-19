# Example skills

Each file shows a complete `SKILL.md` for one common pattern. Read the matching example before drafting a new skill of that type.

| Example | Pattern shown |
| :-- | :-- |
| [summarize-changes.md](./summarize-changes.md) | Dynamic context (`` !`command` ``) + auto-invocable |
| [deploy.md](./deploy.md) | Task action + `disable-model-invocation` + `allowed-tools` + `$ARGUMENTS` |
| [fix-issue.md](./fix-issue.md) | Single argument via `$ARGUMENTS`; positional arguments via `$0` / `$1` / ... |
| [pr-summary.md](./pr-summary.md) | `context: fork` + `agent: Explore` + multiple `` !`command` `` injections |
| [codebase-visualizer.md](./codebase-visualizer.md) | Bundled Python script + `${CLAUDE_SKILL_DIR}` |
