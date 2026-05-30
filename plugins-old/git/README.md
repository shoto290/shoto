# git

A Claude Code plugin for **commit and pull-request workflows** — stage and commit changes, open PRs with conventional-commit titles, triage review comments, and apply the resulting fixes. Generic (no ticket-tracker integration); requires the `gh` CLI and a GitHub remote.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install git@shoto
```

After install, run `/help` to see the `git:` skills and `/agents` to confirm the `reviewer` sub-agent is registered.

## What's inside

### Skills (`/git:<name>`)

| Skill | Purpose |
| :--- | :--- |
| `/git:commit` | Stage the current changes and create a single commit with a conventional-commit title. Skips secrets (`.env`, keys, certs) and asks for confirmation before committing. |
| `/git:create` | Push the current branch and open a PR with a conventional-commit title and a concise changelog body. |
| `/git:review-comments` | Read-only triage of PR comments into a structured decision list (`FIX` / `FIX-STYLE` / `INTENTIONAL` / `OUT-OF-SCOPE` / `DISCUSS`) with confidence. Fans out to the `reviewer` sub-agent in parallel when there are 4+ comments. |
| `/git:review-fix` | Applies only the `FIX` / `FIX-STYLE` decisions produced by `/git:review-comments`, one at a time, then runs auto-detected verification commands. |

### Sub-agents

| Agent | When it fires |
| :--- | :--- |
| `reviewer` | Auto-delegated by `git:review-comments` to evaluate a single PR comment in isolation and return a structured verdict block. |

## Typical flow

1. `/git:commit` — stage the current changes and create a single conventional-commit.
2. `/git:create` — ship the current branch as a PR.
3. `/git:review-comments @<pr-url>` — produce the decision list (no files touched).
4. `/git:review-fix` — paste the decision list back; only `FIX` / `FIX-STYLE` items are applied, then verification runs.

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
