# Hooks — matchers

A handler group's `matcher` decides which occurrences of an event fire the hooks inside that group. Empty string fires on every occurrence. Otherwise the value is interpreted per event.

## Matcher per event

| Event(s) | Matcher type | Example values |
| :-- | :-- | :-- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` | Regex on tool name | `Bash`, `Edit&#124;Write`, `mcp__.*`, `mcp__github__.*`, `mcp__.*__write.*` |
| `SessionStart` | Source enum | `startup`, `resume`, `clear`, `compact` |
| `Setup` | CLI flag | `init`, `maintenance` |
| `SessionEnd` | Reason enum | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `Notification` | Notification kind | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response` |
| `SubagentStart`, `SubagentStop` | Agent name | `general-purpose`, `Explore`, `Plan`, or any custom agent name |
| `PreCompact`, `PostCompact` | Trigger | `manual`, `auto` |
| `ConfigChange` | Source | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `StopFailure` | Error type | `rate_limit`, `authentication_failed`, `oauth_org_not_allowed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, `unknown` |
| `InstructionsLoaded` | Load reason | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact` |
| `Elicitation`, `ElicitationResult` | MCP server name | configured MCP server names |
| `UserPromptExpansion` | Command name | your skill/command names |
| `FileChanged` | **Literal filenames** separated by `|` | `.envrc&#124;.env` — split, NOT regex |
| `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `CwdChanged` | **No matcher** — always fires | — |

> `FileChanged` is the exception: its matcher is a `|`-separated list of literal filenames, not a regex. `.envrc|.env` watches those two files, not "anything containing those letters".

## Tool name regex

Tool-event matchers are full regex. Common patterns:

| Want | Matcher |
| :-- | :-- |
| One tool | `Bash` |
| A few tools | `Edit&#124;Write` |
| All built-in file tools | `Edit&#124;MultiEdit&#124;Write&#124;NotebookEdit` |
| All MCP tools | `mcp__.*` |
| One MCP server's tools | `mcp__github__.*` |
| Write-shaped tools across servers | `mcp__.*__write.*` |
| Every tool (with caveats) | `.*` |

Matchers are **case-sensitive**. `bash` won't match `Bash`. For pipe alternation, the JSON value is `Edit|Write`. Only escape or encode the pipe when you are writing inside Markdown table syntax; don't put a backslash in the actual settings JSON.

## MCP tool naming

MCP tools follow the pattern `mcp__<server>__<tool>` where `<server>` and `<tool>` are the configured MCP server name and the tool it exposes. Examples:

- `mcp__github__search_repositories`
- `mcp__filesystem__read_file`
- `mcp__notion__create_page`

## The `if` field

Requires Claude Code v2.1.85+. Earlier versions silently ignore the field and fire on every matched call.

`matcher` filters at the **group** level by tool name only. `if` filters at the **handler** level by tool name AND arguments, using permission-rule syntax. The hook process only spawns when the call matches the `if` pattern (or when a Bash command is too complex to parse — fail-open, so a hook always sees ambiguous commands).

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git *)",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-git-policy.sh"
          }
        ]
      }
    ]
  }
}
```

Patterns:

- `Bash(git *)` — matches any Bash command whose subcommand starts with `git`
- `Bash(rm *)` — `rm` subcommands
- `Edit(*.ts)` — `Edit` calls on `.ts` files
- `Write(.env*)` — `Write` calls to `.env` family files

### Rules and constraints

- **Exactly one permission rule per `if`.** There is no `&&`, `||`, or list syntax. To combine conditions, define a separate handler for each.
- **Bash subcommand matching strips leading `VAR=value` assignments.** `if: "Bash(git push *)"` matches both `FOO=bar git push` and `npm test && git push`.
- **Runs if ANY subcommand matches.** For compound commands like `npm test && git push`, Claude Code evaluates each subcommand and the hook fires if any match.
- **Runs when the Bash command is too complex to parse.** Fail-open: ambiguous commands always reach the hook so policy is never silently bypassed.
- **Tool events only.** `if` is honored on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`. **Adding `if` to any other event prevents the handler from firing at all** — silently. Don't put `if` on `SessionStart`, `Notification`, etc.

To match multiple tool names with `if`, use separate handlers each with their own `if`, or alternate at the `matcher` level (matcher supports `|`, `if` does not).

## Multiple groups, multiple handlers

You can register multiple groups under one event with different matchers, and each group can have multiple handlers:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "jq -r .tool_input.command >> ~/.claude/bash.log" },
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-rm-rf.sh" }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }
        ]
      }
    ]
  }
}
```

All matching handlers run in parallel. See [io.md](./io.md#combine-results-from-multiple-hooks) for how their outputs combine.
