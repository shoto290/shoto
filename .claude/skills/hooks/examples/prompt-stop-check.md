# Prompt-based Stop check

**Goal.** When Claude says "I'm done," have a small LLM check whether all requested tasks really are complete. If not, send Claude back to work with a specific instruction.

**Event.** `Stop`

**Scope.** Project (`.claude/settings.json`) so the policy travels with the repo.

**Type.** `prompt` — single-turn LLM call, no codebase access needed.

## Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "model": "haiku",
            "prompt": "Review the conversation. Did Claude complete every task the user asked for? If yes, respond exactly with {\"ok\": true}. If something is missing or unresolved, respond with {\"ok\": false, \"reason\": \"<concrete next step Claude should take>\"}."
          }
        ]
      }
    ]
  }
}
```

## How `ok: false` is interpreted

For `Stop` and `SubagentStop`, the model's `reason` is fed to Claude as instructions to keep working. Claude won't stop until either the prompt returns `ok: true`, or the block cap of 8 consecutive blocks is hit.

## Avoiding the block-cap surprise

If your hook returns `ok: false` more than 8 times in a row without Claude making progress, Claude Code overrides it to let the session end. For `prompt`-typed hooks, you don't need to handle `stop_hook_active` yourself — the runtime tracks it and provides it in the hook input automatically.

If you switch this to a `command` hook later, check it manually:

```bash
INPUT=$(cat)
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0   # already triggered a continuation — let Claude stop
fi
```

## Move to `agent` when judgment isn't enough

If "did Claude complete the task" really requires running tests, switch to `agent`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Run the test suite. If anything fails, respond with {\"ok\": false, \"reason\": \"<failing tests + suggested fix>\"}. If all pass, {\"ok\": true}.",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

Agent hooks get tool access and up to 50 turns. **Experimental** — for production, prefer a `command` hook that shells out to your test runner.

## Timeouts and cost

- `prompt` default timeout = 30 s. Override with `"timeout": <seconds>`.
- The model defaults to Haiku. Override with `"model": "sonnet"` if Haiku misclassifies often.
- Every `Stop` event triggers an LLM call. If you stop the session frequently, this adds up — keep the prompt short and cache-friendly.

## When NOT to use a prompt hook here

If the policy is *rule-based* ("don't stop if `package.json` differs from `git HEAD`"), a `command` hook is cheaper and deterministic:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-clean.sh" }
        ]
      }
    ]
  }
}
```

Reserve prompt/agent hooks for cases where the decision genuinely needs LLM judgment.
