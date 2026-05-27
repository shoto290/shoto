---
name: skills-list
description: List the skills installed and available in the current context (current working directory + git repo). Distinguishes between (a) globally-installed skills under `~/.claude/skills/`, (b) skills shipped by an enabled marketplace plugin (under `~/.claude/plugins/cache/**/skills/`), and (c) skills defined in the project's local `.claude/skills/` directory. Use when the user or an agent asks "what skills do I have here?", "what's available in this repo?", "list installed skills", "where am I in terms of skills?". READ-ONLY listing — does NOT install new skills (that's `find-skills`) and does NOT recommend a specific skill for a task (that's `core:skills-suggest`). Triggers on `/core:skills-list`, "list my skills", "what skills are installed", "show installed skills", "where am I in terms of skills".
allowed-tools: [Read, Glob, Bash]
---

> Apply the rules from [core:base](../base/SKILL.md) in addition to those below.

# Skills list

This skill answers "what skills are available to me in this exact context" by enumerating every source Claude Code looks at — global user-level, project-level, and marketplace plugin cache — and emitting a compact report. Read-only by design.

## When invoked

1. **Detect the current context** — run `pwd` to capture the current working directory, then `git rev-parse --show-toplevel 2>/dev/null` to detect the enclosing git repo (if any). If the repo root contains `.claude-plugin/marketplace.json`, note that the current repo is itself a Claude Code marketplace — local marketplace plugins may differ from cached ones.
2. **Enumerate sources** — for each of the four sources below, use `Glob` to find `SKILL.md` files and `Read` only the first 10 lines of each to extract `name` and `description` from the frontmatter. Do not load full bodies.
   - **Global** (user): `~/.claude/skills/*/SKILL.md`
   - **Project** (current repo): `.claude/skills/*/SKILL.md`
   - **Plugin cache** (marketplace-installed): `~/.claude/plugins/cache/**/skills/*/SKILL.md` — the path encodes `owner/plugin/version`; capture that namespace per entry.
   - **Local marketplace** (only if the current repo has `.claude-plugin/marketplace.json` at its root): `plugins/*/skills/*/SKILL.md`
3. **Group and de-duplicate** — group skills by source. If the same skill `name` appears in more than one source, list it under each source and flag the conflict (this matters when developing a plugin that is also installed via the cache).
4. **Render the report** — produce markdown with one section per source. Each section contains a table with columns `| Skill | Plugin | Description (one line) |`. Truncate description to ~80 chars, single line, no trailing ellipsis past the limit.
5. **Footer** — emit one summary line of counts, e.g. `X global · Y project · Z plugin-cache · N total skills available in this context`.

## Output format

```markdown
### Global (`~/.claude/skills/`)

| Skill          | Plugin | Description                                                                       |
| -------------- | ------ | --------------------------------------------------------------------------------- |
| note-taker     | —      | Capture quick notes into the daily journal. Triggers on "take a note", "jot this" |
| screenshot-ocr | —      | Extract text from a screenshot file and copy it to the clipboard                  |

### Project (`.claude/skills/`)

| Skill         | Plugin | Description                                                              |
| ------------- | ------ | ------------------------------------------------------------------------ |
| release-notes | —      | Draft release notes for the current branch from conventional commits     |

### Plugin cache (`~/.claude/plugins/cache/`)

| Skill        | Plugin            | Description                                                                       |
| ------------ | ----------------- | --------------------------------------------------------------------------------- |
| base         | shoto/core@0.8.0  | Canonical rules every skill in the marketplace inherits from                      |
| brainstorm   | shoto/core@0.8.0  | Iteratively explore, ideate, and specify an idea before any planning              |
| skills-list  | shoto/core@0.8.0  | List the skills installed and available in the current context                    |

2 global · 1 project · 3 plugin-cache · 6 total skills available in this context
```

## Anti-patterns

- Don't try to install a new skill — that's `find-skills`'s job.
- Don't recommend a specific skill for a task — that's `core:skills-suggest`'s job.
- Don't modify any skill — this skill is read-only.
- Don't recursively read entire `SKILL.md` bodies — only the frontmatter (first 10 lines) is needed for the listing.

## Reference

- [core:base section 5](../base/SKILL.md#5-delegation-targets) — canonical delegation map; this skill is one of the entries in it.
- `find-skills` (sibling/global) — for installing new skills into the current context.
- [`core:skills-suggest`](../skills-suggest/SKILL.md) — for getting a recommendation tailored to a specific task.
