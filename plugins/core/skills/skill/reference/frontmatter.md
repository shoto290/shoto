# Frontmatter reference

Configure skill behavior via YAML between `---` markers at the top of `SKILL.md`. Upstream (Anthropic spec) all fields are optional and only `description` is recommended. **In this marketplace, `name`, `description`, and `when_to_use` are mandatory on every skill** — see the Required column.

## Fields

| Field | Required | Description |
| :-- | :-- | :-- |
| `name` | **Yes** | Marketplace rule (optional upstream). kebab-case, must match the directory. Defaults to the directory name when omitted, but we always set it. |
| `description` | **Yes** | What the skill does + when to use it. Claude uses this to auto-invoke. Combined with `when_to_use`, capped at 1,536 chars in the listing. Put the key use case first. Keep it to one sentence; no parenthetical definitions or file-path lists. The cap is a ceiling, not a target. |
| `when_to_use` | **Yes** | Marketplace rule (optional upstream). Additional invocation context (trigger phrases, example requests). Appended to `description` in the listing; counts toward the 1,536-char cap. Keep it to one sentence of distinctive scenarios; no exhaustive keyword/trigger dumps. |
| `argument-hint` | No | Autocomplete hint, e.g. `[issue-number]` or `[filename] [format]`. |
| `arguments` | No | Named positional arguments. Space-separated string or YAML list. Names map to positions in order, enabling `$name` substitution. |
| `disable-model-invocation` | No | `true` blocks Claude from auto-loading. User can still invoke via `/name`. Also blocks preload into subagents. Default: `false`. |
| `user-invocable` | No | `false` hides from `/` menu. Use for background knowledge skills. Default: `true`. |
| `allowed-tools` | No | Tools pre-approved while skill is active. Space-separated string or YAML list. |
| `disallowed-tools` | No | Tools removed from Claude's available pool while the skill is active (e.g. block `AskUserQuestion` in an autonomous loop). Space/comma-separated string or YAML list. Clears on your next message. |
| `model` | No | Model override for this turn. Same values as `/model`, or `inherit`. |
| `effort` | No | Effort override (`low`, `medium`, `high`, `xhigh`, `max`). Available levels depend on model. |
| `context` | No | Set to `fork` to run in a subagent context (see [advanced.md](./advanced.md)). |
| `agent` | No | Which subagent type when `context: fork` (built-in: `Explore`, `Plan`, `general-purpose`; or custom from `.claude/agents/`). Default: `general-purpose`. |
| `hooks` | No | Hooks scoped to this skill's lifecycle. See Claude Code hooks docs. |
| `paths` | No | Glob patterns limiting auto-invocation to matching files. Comma-separated string or YAML list. |
| `shell` | No | `bash` (default) or `powershell` for inline `` !`command` `` execution. `powershell` requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`. |

## String substitutions

Substitutions render in the skill body before Claude sees it.

| Variable | Description |
| :-- | :-- |
| `$ARGUMENTS` | All arguments passed when invoking the skill. If absent from body, arguments are appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]` | Argument by 0-based index. |
| `$N` | Shorthand for `$ARGUMENTS[N]` — `$0` is the first, `$1` the second. |
| `$name` | Named argument from the `arguments` frontmatter list. With `arguments: [issue, branch]`, `$issue` = first arg, `$branch` = second. |
| `${CLAUDE_SESSION_ID}` | Current session ID. |
| `${CLAUDE_EFFORT}` | Current effort level. |
| `${CLAUDE_SKILL_DIR}` | Absolute path to the skill's directory. Use this to reference bundled scripts regardless of CWD. |

Indexed arguments use shell-style quoting: `/my-skill "hello world" second` → `$0` = `hello world`, `$1` = `second`. `$ARGUMENTS` always expands to the full input string as typed.

## Visibility states (via settings)

Outside frontmatter, the `skillOverrides` setting in `.claude/settings.local.json` controls visibility without editing `SKILL.md`:

| Value | Listed to Claude | In `/` menu |
| :-- | :-- | :-- |
| `"on"` (default) | Name + description | Yes |
| `"name-only"` | Name only | Yes |
| `"user-invocable-only"` | Hidden | Yes |
| `"off"` | Hidden | Hidden |

The `/skills` menu writes this for you (Space to cycle, Enter to save). Plugin skills are not affected.

## Example: rich frontmatter

```yaml
---
name: pr-summary
description: Summarize a pull request with diff + comments. Use when the user asks for a PR review, PR overview, or what changed in a PR.
argument-hint: '[pr-number]'
arguments: pr
disable-model-invocation: true
allowed-tools: Bash(gh *)
context: fork
agent: Explore
---
```
