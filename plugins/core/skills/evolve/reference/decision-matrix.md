# Decision matrix

## Pick the artifact type

| Need | Pick | Why |
| :-- | :-- | :-- |
| Reusable workflow with a `/name` entry point | Skill | Slash command + auto-trigger |
| Static knowledge / project context Claude should know in the background | Skill with `user-invocable: false` | Background reference |
| Specialized delegate with sandboxed tools | Subagent | One focused job, allowlisted tools |
| Multi-step plan that must run in isolation from main thread | Subagent OR Skill with `context: fork` | Token isolation |
| Automatic enforcement (format-on-save, block edits, validate Bash) | Hook | Deterministic, pre-execution |
| Inject context at session start | Hook (`SessionStart` event) | Runs before user prompt |
| External service/tool integration (DB, browser, live docs, issue tracker, error tracking) Claude must query directly | MCP server (via `core:mcp`) | External capability — not authored as a skill/agent/hook |
| Multi-asset feature (e.g., a `/deploy` flow + safety hook + deployer agent) | Combination — coordinate via `evolve` | Orchestration is the whole point |

## Update vs create heuristics

- If an existing artifact's description covers **≥70%** of the request → propose `update`.
- If the existing artifact would need a near-rewrite to fit → propose `create` new + deprecate old.
- If two existing artifacts together cover the need → propose `reuse` + a small extension to one.
- Never duplicate functionality across artifacts.

## When to reject

- Reject creating a skill that duplicates an existing one — push the user toward `update` or `reuse`.
- Reject creating a subagent for a one-off task — that belongs in the main thread or a skill.
- Reject hooks that re-implement what `permissions` in `settings.json` already enforce.
- Reject artifacts whose description is too broad to auto-trigger reliably.
