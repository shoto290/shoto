---
name: init
description: 'Per-repo installer for the advisor system — sets up the out-of-repo ledger and makes the executant the repo default agent, without polluting or committing anything to the repo.'
when_to_use: 'Run once per repo before using advisor — "set up advisor here", "init advisor", "enable the executant in this repo". Installs durable state outside the repo and wires only a gitignored local settings key; nothing is staged or committed.'
user-invocable: true
allowed-tools: [Bash, Read, Edit, Write, AskUserQuestion]
---

# init

Installs the advisor system for the CURRENT repo so it works anywhere WITHOUT polluting the repo: all durable state lives OUTSIDE the tree under `~/.claude/advisor/`, and the only in-repo touch is a gitignored local settings key.

## 1. Confirm the git repo and compute the slug

```bash
git rev-parse --show-toplevel
slug="$(git rev-parse --show-toplevel | shasum | cut -c1-12)"
```

If not inside a git repo, report that and STOP.

## 2. Create the out-of-repo ledger

```bash
mkdir -p ~/.claude/advisor/state/$slug/
```

Seed an empty `~/.claude/advisor/state/<slug>/ledger.md` when it does not already exist — never overwrite an existing ledger. Tell the user this directory lives OUTSIDE the repo, is keyed by the repo slug, and is never committed.

## 3. Set the executant as the repo default agent

Merge the key `"agent": "executant"` into `<repo>/.claude/settings.local.json`:

- Read the existing JSON first when the file is present; if absent, create it as `{ "agent": "executant" }`.
- ADD or REPLACE only the `agent` key and PRESERVE every sibling key — never clobber the whole object.
- No `agent` key yet, or already `executant` → write it (or no-op) without asking.
- `agent` set to any OTHER value → STOP and ask via `AskUserQuestion`, surfacing the current value; replace it only on confirmation. If declined, leave the file untouched and go to step 5.

`settings.local.json` is gitignored by Claude Code convention, so this stays uncommitted and local to the user.

## 4. No per-repo hook wiring

The plugin ships the Stop gate hook itself and it SELF-GATES — a no-op unless this repo's ledger dir (`~/.claude/advisor/state/<slug>/`) exists. So there is nothing to wire per repo; step 2 alone arms it.

## 5. Report

Report exactly what was set or created, by absolute path:

- `~/.claude/advisor/state/<slug>/` and its seeded `ledger.md`
- `<repo>/.claude/settings.local.json` — whether `"agent": "executant"` was set, was already correct, or was left as-is because the replacement was declined

Confirm that nothing was staged or committed and that no tracked files were modified.
