# git

A Claude Code plugin for **commit and pull-request workflows** — stage and commit changes, open PRs with conventional-commit titles, and rebase branches onto the default branch with safety backups. Generic (no ticket-tracker integration); requires the `gh` CLI and a GitHub remote.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install git@shoto
```

After install, run `/help` to see the `git:` skills and `/agents` to confirm the `git-flow` sub-agent is registered.

## What's inside

### Skills (`/git:<name>`)

| Skill | Purpose |
| :--- | :--- |
| `/git:commit` | Stage the current changes and create a single commit with a conventional-commit title. Skips secrets (`.env`, keys, certs) and asks for confirmation before committing. |
| `/git:create` | Push the current branch and open a PR with a conventional-commit title and a concise changelog body. |
| `/git:rebase` | Rebase the current branch onto the default branch with a safety backup before rewriting history. |

### Sub-agents

| Agent | When it fires |
| :--- | :--- |
| `git-flow` | Ships the current work end-to-end — commit, rebase onto the default branch, then open a PR. Preloads the `commit`, `rebase`, and `create` skills. |

## Typical flow

1. `/git:commit` — stage the current changes and create a single conventional-commit.
2. `/git:create` — ship the current branch as a PR.
3. `/git:rebase` — rebase onto the default branch with a safety backup.

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
