# Troubleshooting

## Teammates not appearing

You asked for a team but don't see teammates. Walk through:

1. **In-process mode** — they may already be running but not visible. Press **Shift+Down** to cycle through them. The active teammate's session shows when you press Enter.
2. **Task complexity** — Claude decides whether to spawn teammates based on the task. A trivial task may not warrant a team; if so, give it a clearly parallel task or say "spawn a team with 3 teammates" explicitly.
3. **Feature enabled?** — confirm `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set and the session was restarted after. See [enable.md](./enable.md).
4. **Version** — `claude --version` must be ≥ 2.1.32.
5. **Split panes** — if you forced `tmux` mode:
   - `which tmux` to confirm it's installed and on PATH
   - For iTerm2: confirm the `it2` CLI is installed and Python API is enabled in **Settings → General → Magic**

## Too many permission prompts

Every teammate's permission request bubbles up to the lead, which interrupts your flow. Mitigations, in order:

1. Pre-approve common operations in `.claude/settings.json` **before** spawning the team
2. Bulk-allow common read-only Bash and MCP calls if your local setup provides a permission-helper skill
3. Spawn teammates with restrictive [subagent definitions](../../subagent/SKILL.md) so their `tools` allowlist itself prevents the prompt-triggering calls

Avoid `bypassPermissions` on the lead unless you've fully audited what each teammate may do — it propagates to all teammates.

## Teammates stopping on errors

A teammate may stop after an error instead of recovering. Look at its output (Shift+Down in in-process; click pane in split mode) and either:

- **Redirect directly** — message the teammate with what to do instead
- **Replace** — ask the lead to spawn a fresh teammate with an updated prompt

A `TeammateIdle` hook returning exit code `2` can also push the teammate to keep working. See [coordination.md](./coordination.md#hooks).

## Lead shuts down the team before work is done

The lead may decide the team is finished while tasks are still open. Tell it to keep going. Common variants:

```text
Wait for your teammates to finish before proceeding.
```

```text
Don't shut down yet — task #5 is still pending.
```

If the lead has started doing the work itself instead of delegating, the same message works: "wait for your teammates".

## Task status can lag

Teammates sometimes fail to mark tasks complete, blocking dependents. Check whether the work is actually done. If yes:

- Tell the lead: "Nudge `<name>` to mark task #3 complete."
- Or update the task manually (use the `/agent-team` task list UI; don't hand-edit files in `~/.claude/tasks/`)

## Orphaned tmux sessions

If a tmux session persists after the team ended:

```bash
tmux ls
tmux kill-session -t <session-name>
```

The team-created sessions are typically named with the team name as a prefix.

## `/resume` doesn't restore in-process teammates

After resuming a session, the lead's memory of the team may not match reality. Teammates that were in-process are gone. If the lead tries to message ghosts:

- Tell it: "Spawn fresh teammates for the remaining tasks."
- Or clean up and restart cleanly: "Clean up the team."

This is a known limitation — not a bug to debug.

## Known limitations recap

- **One team per lead** at a time. Clean up before creating a new one.
- **No nested teams.** Teammates can't spawn their own teams.
- **Lead is fixed.** The session that creates the team is the lead for the team's lifetime.
- **Permissions set at spawn.** All teammates start with the lead's permission mode; you can adjust per-teammate after spawning, but not at spawn time.
- **Split-pane requires tmux or iTerm2.** No support in VS Code's integrated terminal, Windows Terminal, or Ghostty.
- **No session resumption with in-process teammates** — see above.
- **Shutdown can be slow** — teammates finish their current request before exiting.
