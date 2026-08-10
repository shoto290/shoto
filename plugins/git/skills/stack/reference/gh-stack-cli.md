# gh stack CLI Reference

Command surface, machine-readable output, exit codes, constraints, and troubleshooting for the official [`github/gh-stack`](https://github.com/github/gh-stack) extension. Canonical docs: [CLI command reference](https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands) · [About stacked PRs](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) · [Quickstart](https://docs.github.com/en/pull-requests/get-started/stacked-prs-quickstart).

## Version floor

The two official pages disagree: the CLI command reference states the extension requires `gh` **2.0 or later**; the quickstart states `gh` **2.90.0 or later** and Git 2.20 or later. `2.0` is the extension's own hard requirement and is what a pre-flight check keys on. `2.90.0` is the recommended floor — that release added `gh skill` and official-extension install suggestions, which the documented flow assumes.

## Commands

| Command | Flags | Does |
| :--- | :--- | :--- |
| `gh stack init [branches...]` | `-b, --base <branch>` | Creates a stack from branches listed bottom → top. Adopts or creates branches; it never distributes commits or diffs across layers. See [Branch creation](#branch-creation). |
| `gh stack add [branch]` | `-A, --all` · `-u, --update` · `-m, --message <msg>` | Adds a branch on top of the current stack, creating it if it does not exist. See [Branch creation](#branch-creation). |
| `gh stack view` | `-s, --short` · `--json` | Shows branches, order, and PR links. See [View behavior](#view-behavior). |
| `gh stack submit` | `--auto` · `--open` · `--remote <name>` | Pushes every branch, creates or updates the PRs and the stack on GitHub. See [Submit behavior](#submit-behavior). |
| `gh stack checkout [<stack-number>\|<pr-number>\|<pr-url>\|<branch>]` | — | Switches to a branch in a stack. |
| `gh stack sync` | `--remote <name>` · `--prune` | Syncs local stack state with the remote. |
| `gh stack rebase [branch]` | `--downstack` · `--upstack` · `--no-trunk` · `--continue` · `--abort` | Rebases part or all of the stack. |
| `gh stack push` | `--remote <name>` | Pushes the stack's branches without touching PRs. |
| `gh stack link <args...>` | `--base <branch>` · `--open` · `--remote <name>` | Pushes, opens PRs, retargets bases, and writes the stack on GitHub. A publishing command, not a local one — see [Link behavior](#link-behavior). Minimum 2 arguments. |
| `gh stack merge` | — | Merges the stack. **Never invoke it from this skill** — see [Merge footgun](#merge-footgun). |
| `gh stack modify` | — | Interactive TUI; needs a clean tree, no rebase in progress, and no PR queued for merge. |
| `gh stack unstack` / `gh stack delete` | — | Removes a branch from a stack / deletes the stack. |
| `gh stack up` / `down` / `top` / `bottom` / `trunk` / `switch` | — | Navigation within the stack. |
| `gh stack alias` | — | Manages command aliases. |
| `gh stack version` | — | Prints the extension version. It does **not** distinguish `github/gh-stack` from same-named third-party extensions, so `gh extension list` is the presence check. |

## View behavior

`gh stack view` branches on whether stdout is a terminal:

- **On a TTY, without `--json`** — a full-screen Bubble Tea TUI (alt screen + mouse motion). Human-only; not drivable.
- **Without a TTY, without `--json`** — static plain text written straight to stdout, which returns immediately. The documented "piped through a pager" behavior does not apply on this path: the pager helper short-circuits to a direct write when the session is non-interactive, so the `less -R` branch is unreachable for `view`. A bare `gh stack view` therefore does not hang an agent.
- **With `--json`** — the machine-readable schema below, with typed exit codes. JSON mode never shows an interactive prompt by design, so agents and scripts always receive parseable output. This is the only form to use programmatically, on that contract — not because the bare form blocks.

## Machine-readable state

```json
{
  "trunk": "main",
  "currentBranch": "feat-api",
  "branches": [
    {
      "name": "feat-schema",
      "head": "feat-schema",
      "base": "main",
      "isCurrent": false,
      "isMerged": false,
      "isQueued": false,
      "needsRebase": false,
      "pr": { "number": 1, "url": "https://github.com/owner/repo/pull/1", "state": "OPEN" }
    }
  ]
}
```

- `branches[]` is ordered **bottom → top**.
- The full branch object is `name`, `head`, `base`, `isCurrent`, `isMerged`, `isQueued`, `needsRebase`, `pr`; the full PR object is `number`, `url`, `state`. That is the whole payload.
- **No draft field exists anywhere in it.** `state` is computed locally as exactly one of `OPEN`, `MERGED`, `QUEUED`, and a draft PR reports `OPEN` — indistinguishable from ready for review. Draft state only comes from `gh pr view <number> --json isDraft`.
- There is **no CI or check field**, and no `gh stack checks` subcommand. To report check status, iterate `.branches[].pr.number` and run `gh pr checks <number>` per PR.
- `needsRebase: true` on a branch means the layer below it moved — rebase before submitting.

## Submit behavior

`gh stack submit` takes exactly three flags — `--auto`, `--open`, `--remote`. There is no title flag, no body flag, and no draft flag.

| Flag | Effect | Not |
| :--- | :--- | :--- |
| `--auto` | Uses auto-generated PR titles without prompting, skipping the interactive editor. The editor is gated on "interactive AND not `--auto`", so a session with no TTY skips it regardless — pass `--auto` anyway as the only protection when a PTY is allocated. | Not auto-merge, and not what makes PRs drafts. |
| `--open` | Marks new **and existing** PRs as ready for review. | Not scoped to new PRs — it calls the ready-for-review mutation on drafts already in the stack. |
| `--remote <name>` | Remote to push to. Defaults to the auto-detected remote. | — |

**Draft state** comes from `isDraft := !opts.open`: new PRs are drafts unless `--open` is passed. `--auto` has no bearing on it.

**Title and body are derived, never supplied:**

- The branch carries exactly one commit → title is that commit's subject, body is its message body (trimmed).
- The branch carries zero or several commits → title is the humanized branch name, body is empty.
- The repository's PR template is merged in, and a `gh-stack` attribution footer is appended.

Consequence: one commit per layer is the only lever on the generated text. Anything else needs `gh pr edit <number> --body ...` as a separate, explicit step after submit.

## Branch creation

Neither `init` nor `add` has any code path that errors because a branch is missing. Existence is an adopt-or-create branch in the logic, never a failure, and there is no adopt-only flag. `link` is the opposite: it never creates one.

| Command | Branch exists | Branch missing | Name validation |
| :--- | :--- | :--- | :--- |
| `gh stack init` | Adopted as that layer. | Created on its parent — the trunk for the first argument, the previous argument's branch for the rest. | `ValidateRefName` only, which checks ref-name **shape**, not existence. |
| `gh stack add` | Adopted as the new top layer. | Created at the current `HEAD`. | **None at all** — no `ValidateRefName` call. |
| `gh stack link` | Pushed, and adopted as that layer. | **Never created** — there is no branch-creation path in `link`. The name is carried to the PR-creation API and fails there. | Existence is only ever tested, never required: the push filters the argument list down to the names that exist locally. |

Consequence for `init` and `add`: a mistyped branch name is not an error, it is a new empty branch that joins the stack as a real layer. `git show-ref --verify refs/heads/<branch>` per intended layer is the non-mutating pre-check. For `link`, a local ref is needed only by branch arguments — PR numbers and URLs need none.

## Link behavior

`gh stack link` takes a minimum of 2 arguments, each a branch name, a PR number, or a PR URL. It is not a local bookkeeping command: it publishes. It creates no local branch — see [Branch creation](#branch-creation).

### Phase order

The push is the **first** remote write, and it runs before any argument has been validated:

1. Read the existing stacks; decide whether the first argument is a stack number. Local, read-only.
2. **Push** — the argument list filtered down to the names that exist as local branches, so PR numbers and URLs drop out. Nothing survives the filter → no push. **First remote write.**
3. Resolve each argument to a PR. A PR URL whose number does not exist is a hard `PR #<n> not found` — raised here, after the push.
4. **Create** the missing PRs, one API call per argument, sequentially.
5. **Retarget** the bases that are wrong, and flip pre-existing drafts to ready under `--open`.
6. **Upsert** the stack.

So a bad PR URL costs a push before it is caught, and no later phase undoes it.

### Argument resolution

| Argument | Resolved as | Fallback |
| :--- | :--- | :--- |
| PR URL | Always a PR — only the number is parsed out of the URL. | None. A missing PR is a hard error; it never falls back to a branch name. |
| Numeric | A PR with that number, if one exists. | Otherwise a branch name. As the **first** argument it is read as a stack number only when it is `> 0`, is not a local branch name, and matches an existing stack's number. |
| Anything else | A branch name. | None. An unresolvable name is indistinguishable from a real branch with no PR yet. |

**No cross-repository check exists.** URL parsing keeps only the number and discards the owner and repository; the lookup then binds to the current repository. `https://github.com/other-org/other-repo/pull/41` therefore resolves to PR #41 **of the current repository**, silently and with no warning.

**A PR's base repository is not its head-branch repository.** The `url` returned by `gh pr view` names the repository the PR was opened **against**. A PR opened from a fork — base `owner/repo`, head `contributor/repo-fork:feature` — has a URL in `owner/repo`, so **comparing the URL against the current `nameWithOwner` cannot detect a fork**: it passes while the head branch lives elsewhere. `gh repo view --json isFork` cannot detect it either, since that flag describes only the current repository. The head repository comes from separate `gh pr view --json` fields:

| Field | Value on a same-repo PR | Note |
| :--- | :--- | :--- |
| `isCrossRepository` | `false` | First-class boolean, purpose-built for this question. |
| `headRepository.name` | `"shoto"` | The head repository's name — the field to compare. |
| `headRepository.nameWithOwner` | `""` | **Empty string** on gh 2.83.1. Never compare it. |
| `headRepositoryOwner.login` | `"shoto290"` | The head owner's account — the field to compare. |
| `headRepositoryOwner.name` | `"Shoto"` | The account's **display name**, not its login. Comparing it yields false refusals. |

`headRepository` and `headRepositoryOwner` are both null when the head fork has been deleted, which leaves the head repository unknowable from the API.

Observed on gh 2.83.1 for a same-repository PR:

```json
{"baseRefName":"main","headRefName":"pr-recap-oneliner","headRepository":{"id":"R_kgDOShrdDw","name":"shoto","nameWithOwner":""},"headRepositoryOwner":{"id":"MDQ6VXNlcjM4NTAxOTYz","name":"Shoto","login":"shoto290"},"isCrossRepository":false,"number":98,"url":"https://github.com/shoto290/shoto/pull/98"}
```

**An unresolvable name fails server-side, mid-run.** It reaches phase 4 indistinguishable from a real branch awaiting its first PR, and only the API rejects it. Creation is sequential and returns on the first error, so the PRs already created for earlier arguments survive while the stack upsert (phase 6) never runs — they are left orphaned, outside any stack.

**A numeric argument that is also a local branch name is doubly interpreted:** phase 2 pushes the branch and phase 3 links the same-numbered PR, whose head may be an unrelated branch — and in first position the same text can instead be read as a stack number. Numeric is the only genuinely ambiguous form. A non-numeric branch name is read as a branch, full stop, and `gh pr view` accepts `[<number> | <url> | <branch>]`, so a PR coming back for a branch name simply identifies that branch's PR.

### Per-argument effects

| Argument form | Push | Create PR | Retarget base | Stack upsert | Local ref needed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Local branch, no PR | yes | yes | no | yes | yes |
| Local branch, existing PR | yes | no | only if the base is wrong | yes | yes, for the push |
| Branch name with a PR but no local ref | no | no | only if the base is wrong | yes | **no** |
| PR number that resolves | no | no | only if the base is wrong | yes | **no** |
| PR URL that resolves | no | no | only if the base is wrong | yes | **no** |

A PR created by this same run is skipped by the retarget phase, and `--open` never flips it — it was created ready.

| Flag | Effect |
| :--- | :--- |
| `--base <branch>` | Base of the bottom PR. Defaults to the repository's default branch. |
| `--open` | New PRs are created ready instead of draft, **and pre-existing draft PRs in the stack are flipped to ready**. |
| `--remote <name>` | Remote to push to. |

There is **no confirmation prompt and no `--dry-run`** in `link`. The only prompt it can raise is remote disambiguation, and only when several remotes exist and `--remote` was not given. Nothing is reversible by declining a prompt, because there is no prompt.

## Merge footgun

`gh stack merge` merges the stack **without any confirmation** when it runs non-interactively or is given `--yes` — exactly the conditions an agent runs under. There is no prompt that would catch a mistaken invocation, so it stays out of scope entirely.

## Exit codes

| Code | Meaning | Response |
| :--- | :--- | :--- |
| `0` | Success | Continue. |
| `1` | Generic failure | Surface the CLI output verbatim and stop. |
| `2` | Not in a stack / stack not found | Expected on a first run — treat as "no stack yet", not an error. |
| `3` | Rebase conflict | Resolve the conflicted files, `git add` them, then `gh stack rebase --continue`. `gh stack rebase --abort` walks it back. |
| `4` | GitHub API failure | Transient or permissions. Re-check `gh auth status`; do not retry blindly. |
| `5` | Invalid arguments | Fix the invocation — do not guess a different flag. |
| `6` | Disambiguation required | The branch belongs to several stacks. Re-run naming the stack number or PR explicitly. |
| `7` | Rebase already in progress | Finish or abort the in-flight rebase first. |
| `8` | Stack locked by another process | Another `gh stack` command is running. Wait, then retry. |
| `9` | Stacked PRs not enabled for this repository | Stop. Only a repository admin can enable them. |
| `10` | Modify session interrupted | This skill never runs `gh stack modify` — surface the CLI output verbatim and stop. |

## Model and constraints

- A stack is a **linear chain** rooted on a trunk. Each PR's base is the head branch of the PR directly below it.
- The trunk need not be the default branch: a stack's trunk (the base branch of the bottom PR) can be any branch in the repository.
- Stacked PRs currently require all branches to be in the same repository. Cross-fork stacks are not supported.
- Linear history is required between each branch in the stack.
- There is **no way to express independent siblings**. Branches with no real dependency still get chained bottom-up, which misrepresents them.
- Minimum 2 PRs per stack; maximum 100.
- Auto-merge and rule-bypass are unavailable for stacked PRs.
- Closing a mid-stack PR blocks everything above it.
- Once a stack fully lands, it cannot be extended — start a new stack.

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `needsRebase: true` after submitting | A lower layer changed | `gh stack rebase --upstack`, then `gh stack submit --auto` again. |
| A wrong-looking base on the bottom PR | The trunk is not the default branch | Confirm `trunk` in `gh stack view --json`; re-`init` with `--base` if it is wrong. |
| A PR title reads like a branch name | That layer carries zero or several commits | Squash the layer to one well-written commit, re-submit, or fix the title with `gh pr edit`. |
| A draft PR silently became ready | `--open` was passed and converts existing drafts too | Re-draft it with `gh pr ready --undo <number>`; drop `--open` from the submit. |
