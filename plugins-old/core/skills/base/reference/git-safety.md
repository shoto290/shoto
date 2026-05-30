# Git Safety

Destructive operations that require explicit user confirmation. Never run any of these silently — surface the command, wait for approval, then execute.

## Always confirm

| Operation | Examples |
| :-- | :-- |
| Force push | `git push --force`, `git push -f`, `git push --force-with-lease` |
| Hard reset | `git reset --hard`, `git checkout .`, `git restore .`, `git clean -fd` |
| Branch delete | `git branch -D <name>`, `git push origin --delete <name>` |
| File destruction | `rm -rf` on any directory, `git rm -r` |
| History rewrite | `git rebase` of pushed commits, `git commit --amend` on shared branches |

## Branch protection

- Never push directly to `main` (or the repo's default branch). Always work on a feature branch.
- Never force-push to `main` under any circumstance, even with explicit user approval — refuse and ask for a safer path.

## Hooks and signing

- Do not bypass hooks (`--no-verify`) or signing (`--no-gpg-sign`) unless the user has explicitly asked for it. If a hook fails, fix the underlying issue and create a NEW commit rather than amending.

## Commit hygiene

- Stage files by name. Prefer `git add path/to/file` over `git add -A` or `git add .` to avoid accidentally committing secrets or large binaries.
- Never commit files that likely contain secrets: `.env`, `.env.*`, `credentials.json`, `*.pem`, `*.key`, `*.cert`.
