# Advanced patterns

## Dynamic context injection

The `` !`<command>` `` syntax runs shell commands **before** the skill content is sent to Claude. The output replaces the placeholder; Claude sees the rendered result, not the command itself.

Inline form:

```markdown
## Current changes
!`git diff HEAD`
```

Multi-line form using a fenced block opened with `` ```! ``:

````markdown
## Environment
```!
node --version
npm --version
git status --short
```
````

Execution order when the skill runs:
1. Every `` !`command` `` / `` ```! `` block runs immediately, before Claude sees anything
2. Output replaces the placeholder in the skill content
3. Claude receives the fully-rendered prompt

This is preprocessing — Claude never sees the unexecuted command. Substitution runs **once** over the original file; command output is plain text and is not re-scanned for further placeholders.

To disable globally: `"disableSkillShellExecution": true` in settings. Each command is replaced with `[shell command execution disabled by policy]`. Most useful in managed settings. Bundled and managed skills are not affected.

> Include `ultrathink` anywhere in the skill body to request deeper reasoning when it runs.

## Subagent execution (`context: fork`)

Run a skill in an isolated subagent context. The skill content becomes the subagent's prompt. No access to your conversation history.

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

When invoked:
1. New isolated context created
2. Subagent receives the skill content as its prompt
3. `agent` field determines model, tools, permissions (built-in `Explore`, `Plan`, `general-purpose`, or any custom from `.claude/agents/`; default `general-purpose`)
4. Results are summarized and returned to the main conversation

> `context: fork` **requires an explicit task** in the body. Guidelines alone (e.g. "use these API conventions") give the subagent no actionable prompt — it returns without meaningful output.

### Skills vs. subagents

Two ways skills and subagents combine:

| Approach | System prompt | Task | Also loads |
| :-- | :-- | :-- | :-- |
| Skill with `context: fork` | From agent type | SKILL.md content | CLAUDE.md, **except** when agent is `Explore` or `Plan` |
| Subagent with `skills` field | Subagent's markdown body | Claude's delegation message | Preloaded skills + CLAUDE.md |

`Explore` and `Plan` skip CLAUDE.md and git status to keep context small. A forked skill using `agent: Explore` sees only the SKILL.md content + the agent's own system prompt.

## Bundle scripts (`${CLAUDE_SKILL_DIR}`)

Skills can ship executables. Reference them with `${CLAUDE_SKILL_DIR}` so the path resolves regardless of CWD or scope (personal / project / plugin).

```yaml
---
name: codebase-visualizer
description: Generate an interactive collapsible tree visualization of your codebase
allowed-tools: Bash(python3 *)
---

Run from the project root:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```
```

The bundled script does the work; Claude orchestrates and runs it.

Common patterns:
- Visual output (HTML reports, graphs, schema diagrams)
- Data processing (CSV → summary, log → metrics)
- Codebase analysis tools

Use Python with standard-library-only when possible — no install step.
