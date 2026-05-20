# Shell tools

Covers: `Bash`, `Monitor`, `PowerShell`.

## Bash

**Summary.** Executes a shell command and returns its stdout/stderr. The default shell is initialised from the user's profile.

**Permission rule.** `Bash(<command-prefix>:*)` — anchored at the start of the command line. The `:*` wildcard matches any trailing arguments.

Examples:

- `Bash(git status:*)` — allows `git status`, `git status -s`, …
- `Bash(npm run:*)` — allows any `npm run …`.
- `Bash(rm -rf:*)` — best used in a `deny` rule.

**Parameters.**

- `command` (required).
- `description` — short active-voice summary shown to the user.
- `timeout` — milliseconds. Default **120 000** (2 min). Max **600 000** (10 min).
- `run_in_background` — return immediately and notify on completion.
- `dangerouslyDisableSandbox` — bypass sandbox; require explicit user buy-in.

**Behaviour.**

- The working directory persists between calls **within the project root**. Use absolute paths for cross-directory work.
- Environment variables do NOT persist between calls — re-export per call.
- `cd` outside the project root triggers a permission prompt.
- Quote paths containing spaces with double quotes.
- Prefer dedicated tools over shell equivalents:
  - `Read` over `cat`/`head`/`tail`.
  - `Edit` over `sed`/`awk`.
  - `Write` over `echo > file` / heredocs.

**Polling and long-running commands.**

- Long leading `sleep` is blocked. To wait for a state change, use `Monitor` with an `until` loop.
- For one-shot completion (e.g. a build), set `run_in_background: true` — you are notified once when it finishes. Do not poll.
- For multiple independent commands, issue them as parallel `Bash` tool calls in the same message.
- For dependent commands, chain with `&&` in a single call. Use `;` only when failures should not stop the chain.
- Never separate commands with raw newlines unless inside a quoted string.

**Pitfalls.**

- Assuming `export FOO=bar` persists to the next call — it does NOT.
- Expecting `find /` to return — scans the whole filesystem; always anchor at `.` or a known subtree.
- `find -regex` with shortest-alternation-first silently skips longer matches; put the longest alternative first.
- Running `git push --force` / `git reset --hard` without explicit confirmation — repo policy treats these as blocking destructive ops.
- Forgetting to quote a path with spaces → cryptic "No such file or directory".

**Worked example.**

```text
Bash(
  command="npm run build && npm test",
  description="Build project then run tests",
  timeout=300000
)
```

## Monitor

**Summary.** Watches a background process and delivers each stdout line as a notification. Use for streaming logs, tailing builds, or waiting on a state change.

**Permission rule.** `Monitor` (bare). No specifier needed.

**Behaviour.**

- Pair with `Bash run_in_background` to start the watched process.
- For "wait until condition met" loops, use `until <check>; do sleep 2; done` — `Monitor` notifies when the loop exits.

**Pitfalls.**

- Using `Monitor` for one-shot completion when `Bash run_in_background` already notifies on exit — duplicate notifications.
- Spawning many background processes without bounded `Monitor` watchers — output may be lost.

## PowerShell

**Summary.** Windows equivalent of `Bash`. Executes a PowerShell command.

**Permission rule.** `PowerShell(<command-prefix>:*)`.

**Behaviour.**

- Same persistence rules as `Bash` (cwd persists, env does not).
- Use `;` instead of `&&` between commands (PowerShell's `&&` requires v7+).

**Pitfalls.**

- Assuming POSIX semantics — `ls`, `cat`, etc. are aliases with different flags.
- Path separators: prefer forward slashes; PowerShell accepts both.
