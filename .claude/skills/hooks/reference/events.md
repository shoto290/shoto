# Hooks — events

Each event has a key under the top-level `hooks` block in `settings.json`. The value is an array of *handler groups* (each with a `matcher` and a `hooks` array of handlers).

## Session and prompt lifecycle

| Event | Fires when | Matcher filters | Blockable with `exit 2`? |
| :-- | :-- | :-- | :-- |
| `SessionStart` | Session begins or resumes | `startup`, `resume`, `clear`, `compact` | No — stderr surfaced to user, run continues. stdout becomes Claude's context. |
| `Setup` | `--init-only`, `--init`, or `--maintenance` (used in CI / scripts) | `init`, `maintenance` | No |
| `UserPromptSubmit` | User submits a prompt, before Claude sees it | none | Yes — blocks the prompt. stdout becomes context |
| `UserPromptExpansion` | A user-typed `/command` expands into a prompt | command name | Yes — blocks the expansion |
| `Stop` | Claude finishes responding (not on user interrupts) | none | Use `decision: "block"` (top-level JSON) to keep Claude working; `reason` is fed back so it continues |
| `StopFailure` | Turn ends due to API error | error type (`rate_limit`, `server_error`, …) | Output and exit code **ignored** |
| `SessionEnd` | Session terminates | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` | No |

## Tool lifecycle

| Event | Fires when | Matcher filters | Blockable with `exit 2`? |
| :-- | :-- | :-- | :-- |
| `PreToolUse` | Before a tool call executes | tool name (e.g. `Bash`, `Edit&#124;Write`, `mcp__.*`) | **Yes** — most useful for policy. Supports `if` field |
| `PermissionRequest` | When a permission dialog is about to appear | tool name | Yes — `exit 2` denies, or return `hookSpecificOutput.decision.behavior` to allow/deny. Doesn't fire in `-p` mode |
| `PermissionDenied` | A tool call was denied by the auto-mode classifier | tool name | Return `{retry: true}` to let the model retry |
| `PostToolUse` | After a tool call succeeds | tool name | Cannot undo the call; `decision: "block"` only feeds reason back |
| `PostToolUseFailure` | After a tool call fails | tool name | Same as `PostToolUse` |
| `PostToolBatch` | After a batch of parallel tool calls resolves, before next model call | none | Use `decision: "block"` (JSON output) to feed `reason` back to Claude before the next model call |

## Compaction

| Event | Fires when | Matcher filters | Blockable? |
| :-- | :-- | :-- | :-- |
| `PreCompact` | Just before context compaction | `manual`, `auto` | Yes |
| `PostCompact` | After compaction finishes | `manual`, `auto` | No |

## Subagents and tasks

| Event | Fires when | Matcher filters | Blockable? |
| :-- | :-- | :-- | :-- |
| `SubagentStart` | A subagent is spawned | agent type (`general-purpose`, `Explore`, `Plan`, or custom) | No — can inject context, not block creation |
| `SubagentStop` | A subagent finishes | agent type | Same semantics as `Stop` |
| `TaskCreated` | A task is being created via `TaskCreate` | none | Not documented as blockable; treat as observational |
| `TaskCompleted` | A task is being marked completed | none | Same as `Stop` (`decision: "block"` feeds reason back) |
| `TeammateIdle` | An agent-team teammate is about to idle | none | Same as `Stop` (`decision: "block"` feeds reason back) |

## Filesystem and config

| Event | Fires when | Matcher filters | Blockable? |
| :-- | :-- | :-- | :-- |
| `ConfigChange` | A settings or skill file changes during a session | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` | Yes (`exit 2` or `decision: "block"`), except `policy_settings` |
| `FileChanged` | A watched file changes on disk | **literal filenames split on `|`** — not regex (e.g. `.envrc&#124;.env`) | No |
| `CwdChanged` | Claude's working directory changes (e.g. `cd`) | none | No |
| `WorktreeCreate` | A worktree is created (`--worktree` or `isolation: "worktree"`) | none | Replaces default git behavior |
| `WorktreeRemove` | A worktree is removed at session exit or subagent finish | none | No |

## Notifications and elicitation

| Event | Fires when | Matcher filters | Blockable? |
| :-- | :-- | :-- | :-- |
| `Notification` | Claude Code emits a notification | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`, `elicitation_complete`, `elicitation_response` | No |
| `Elicitation` | An MCP server requests user input during a tool call | MCP server name | Behavior not explicitly documented — verify against the live `/en/hooks` reference if you intend to block |
| `ElicitationResult` | After user responds to an MCP elicitation, before sending back | MCP server name | Behavior not explicitly documented — verify against the live `/en/hooks` reference if you intend to block |

## Instructions loading

| Event | Fires when | Matcher filters | Blockable? |
| :-- | :-- | :-- | :-- |
| `InstructionsLoaded` | `CLAUDE.md` or `.claude/rules/*.md` loads into context (session start or lazy load) | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact` | No |

## Exit-code-2 behavior summary

For most events, `exit 2` blocks the action and feeds stderr back to Claude. For these events, **`exit 2` does NOT block** — stderr is shown to the user (or logged) and execution continues:

- `SessionStart`, `Setup`, `SessionEnd`
- `Notification`
- `SubagentStart`
- `PostToolUse`, `PostToolUseFailure` (tool already ran; use `decision: "block"` to feed reason to Claude)
- `PermissionDenied` (denial already happened; use `hookSpecificOutput.retry: true` to let the model retry)
- `StopFailure` (API error already happened)
- `CwdChanged`, `FileChanged`
- `ConfigChange` only for `policy_settings` sources; other sources can be blocked — see table
- `WorktreeRemove`
- `InstructionsLoaded`
- `PostCompact`

When in doubt, use structured JSON output and check the response field in [io.md](./io.md#decision-control).
