---
name: stack
description: 'Creates and publishes a chain of dependent pull requests with the official github/gh-stack CLI extension; never merges.'
when_to_use: 'The user asks to open stacked pull requests from branches that already depend on one another, or to publish, sync, or inspect an existing gh stack. Not for a single standalone pull request — use /git:create instead. Not for splitting one branch into layers — this skill only orchestrates branches that already exist.'
argument-hint: '(none — operates on the current branch and its stack)'
allowed-tools: Bash, Read, AskUserQuestion
---

# stack

Build and publish a **stack** — a linear chain of pull requests where each PR's base is the head branch of the PR directly below it — using the official [`github/gh-stack`](https://github.com/github/gh-stack) CLI extension. Complements `/git:commit` (one commit per layer), `/git:rebase` (sync a single branch onto the default branch), and `/git:create`, which stays the path for an ordinary standalone PR.

Background: [About stacked PRs](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) · [Quickstart](https://docs.github.com/en/pull-requests/get-started/stacked-prs-quickstart) · [CLI command reference](https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands).

## Prerequisites

- `gh` CLI **2.0 or later** (the floor the extension itself requires) and Git 2.20 or later. `gh` **2.90.0 or later** is recommended — the full documented flow assumes it.
- The `github/gh-stack` extension installed: `gh extension install github/gh-stack`. Third-party extensions also named `gh-stack` exist — only `github/gh-stack` is the official one, so always match on the full `github/` owner.
- `gh` authenticated (`gh auth status`). The extension reuses the existing `gh` credentials.
- A GitHub repository with stacked PRs enabled, and every branch of the stack living in **that same repository** — cross-fork stacks are not supported.
- Current branch is not the repository's default branch.

## Steps

### 1. Read repo conventions

Read `AGENTS.md` and `CLAUDE.md` at the repo root in parallel if they exist. Absorb naming, PR, and language conventions before drafting any branch name or commit message.

### 2. Inspect the workspace

Run these in parallel:

- `gh --version`
- `gh auth status`
- `gh extension list`
- `git branch --show-current`
- `git status --porcelain`
- `gh repo view --json defaultBranchRef,isFork,nameWithOwner`
- `gh stack view --json` (exit code `2` here just means "no stack yet" — not a failure)

### 3. Pre-flight checks

In order. Every one of these fails **before** any remote write:

- If `gh --version` does not run, stop with: `gh CLI not found. Install gh 2.0 or later yourself, then retry — this skill never installs or upgrades gh.`
- If the reported `gh` version is below `2.0`, stop with: `gh <current-version> is installed; gh stack needs 2.0 or later. Upgrade gh yourself, then retry — this skill never upgrades it for you.`
- If `gh auth status` fails, stop with: `gh is not authenticated. Run: gh auth login`
- If no line of `gh extension list` matches `github/gh-stack`, stop with: `The github/gh-stack extension is not installed. Run: gh extension install github/gh-stack — this skill never installs it for you.`
- If `gh repo view` fails or resolves no remote, stop with: `No GitHub repository resolved for this workspace. Add a GitHub remote, then retry.`
- If `.isFork` is `true`, stop with: `<name-with-owner> is a fork. Stacked PRs currently require all branches to be in the same repository; cross-fork stacks are not supported. Use /git:create for a standalone PR instead.`
- If the current branch equals `main`, `master`, or `.defaultBranchRef.name`, stop with: `On <branch> — refusing to build a stack from the default branch. Switch to a feature branch and retry.`
- If the step-2 `gh stack view --json` probe exited with code `9`, stop with: `Stacked PRs are not enabled for <name-with-owner>. Enable them in the repository settings, then retry.`

Exit code `2` from `gh stack view` is expected and needs no lookup, and `3` and `9` are handled inline by this skill. For any other non-zero exit code, read [reference/gh-stack-cli.md](./reference/gh-stack-cli.md) before interpreting it.

### 4. Resolve the mode

Resolve exactly one mode from the request and **state it explicitly** (`Mode: inspect`) before acting. This step runs after the pre-flight checks and before any `gh stack init`, `add`, `link`, `submit`, `sync`, `rebase`, or `push` — no mutation happens before the mode is stated.

| Mode | The request asks to | Commands this mode owns |
| :--- | :--- | :--- |
| `inspect` | see the stack: its order, branches, PRs, checks (**the default** when nothing else is asked) | `gh stack view --json`, `gh pr view`, `gh pr checks` |
| `create` | build the stack locally from branches that already exist | `gh stack init`, `gh stack add` |
| `publish` | push the branches and open or update the PRs, or link existing branches and PRs into a stack on GitHub | `gh stack submit --auto`, `gh stack link`, `gh stack push` |
| `sync` | reconcile with the remote or rebase the layers | `gh stack sync`, `gh stack rebase` |

- `inspect` is **strictly read-only**: no branch created or modified, no PR created or modified, no push, and none of `gh stack init`, `add`, `link`, `submit`, `sync`, `rebase`, `push`, `merge`.
- `create` is **local**: `gh stack init` and `gh stack add` write branches and stack metadata in this clone and never contact the remote. Every command that touches the remote belongs to `publish` — including `gh stack link`, which despite its name pushes, opens PRs, and writes the stack on GitHub (step 8).
- Each mutation belongs only to the mode that asks for it. A request that genuinely needs both runs `create`, states the switch, then runs `publish`.
- Before executing **any** remote operation, print the exact list of planned remote operations — one line per command with the branches and PRs it touches — and run nothing outside that list.

Mode routing:

- `inspect` → skip straight to step 9.
- `create` → steps 5, 6, 7, then 9.
- `publish` → step 6 before `gh stack submit` or `gh stack push`, step 6b before `gh stack link`, then step 5 over the layer records step 6b produced, then step 8, then step 9. The layers come from `gh stack view --json`, plus every argument passed to `gh stack link`. **Every** resolved `link` argument goes through the step-5 dependency verification — a layer given as a PR number or a PR URL is checked exactly like a branch, never waved through.
- `sync` → step 8, then step 9. The layers come from `gh stack view --json`.

### 5. Map the layers and verify real dependency

Determine the layers, ordered **bottom → top** (the bottom layer sits on the trunk). Every layer is a git branch that **already exists** — locally, or, on the `link` path, as the head branch of an existing PR. This skill never splits one branch into several. `gh stack init` adopts or creates branches; it does not distribute commits or diffs across layers.

If fewer than two layers come out — including work that still sits on a single branch — stop with: `Only one layer of work found — a stack needs at least 2 pull requests. Use /git:create for a standalone PR instead.` A stack also caps at 100 PRs.

If the intended branches do not all live in `<name-with-owner>`, stop with: `Branches <branch-list> are not all in <name-with-owner>. Stacked PRs currently require all branches to be in the same repository. Use /git:create for a standalone PR instead.`

Then verify **each adjacent pair** bottom → top, all pairs in a single parallel batch, whatever form each layer was supplied in. Read the pair's content from whichever source its layer records offer:

- Both layers available locally → `git diff <lower>..<upper>`.
- A layer supplied by PR with no local branch → read its content with `gh pr diff <number>`, plus the `gh pr view` metadata already resolved in step 6b.
- Mixed → compare the local layer's changes against the available PR diff.

What is being verified is **dependency, not chaining**: the current bases need not already point at one another — retargeting them is precisely what `link` is for. The question is only whether the upper layer's changes genuinely build on the lower layer's.

Judge whether the upper layer actually builds on the lower one: it extends a file the lower layer created, calls a symbol the lower layer introduced, or is otherwise unmergeable before it. If the two file sets are disjoint and nothing in the upper layer references what the lower one added, that pair has **no real dependency**.

Report every such pair explicitly:

> `<upper>` shows no dependency on `<lower>` — their changes are disjoint. A stack imposes a linear order these branches do not have, which misrepresents the review order and blocks the upper PR behind the lower one for no reason. Open them as separate independent PRs with `/git:create` instead.

Never silently stack independent work. When the diffs available are not enough to establish the dependency, present the evidence — the files each layer touches and the symbols they share or do not share — and ask via `AskUserQuestion` before proceeding. On the `link` path this decision comes **before** `link` runs, never after:

- (a) Open independent PRs with `/git:create` (Recommended when the diffs are disjoint)
- (b) Stack anyway — the dependency is real but not visible in the diff
- (c) Abort

### 6. Verify every layer branch exists

`gh stack init` and `gh stack add` **never fail on a branch that does not exist — they create it**. `gh stack init` creates a missing branch on top of the layer below it and only checks that the name is a well-formed ref, never that it exists; `gh stack add` creates it at the current `HEAD` and does not even check the name's shape. So a mistyped branch name is not rejected, it is silently created as an empty branch and the stack carries a layer nobody wrote. That is the reason this check exists.

`gh stack link` is **not** one of them: it has no branch-creation path at all, and its PR-number and PR-URL arguments need no local ref. It gets step 6b instead — this blanket check does not apply to it.

Before **any** command that creates a branch or pushes the layers — `gh stack init`, `gh stack add`, `gh stack submit`, `gh stack push` — verify every expected layer. One call per branch, all in a single parallel batch:

```bash
git show-ref --verify refs/heads/<branch>
```

A non-zero exit means that branch does not exist locally. If any layer is missing, stop **before** running any of those commands, with:

> `Missing branches: <missing-branch-list>. gh stack creates missing branches instead of rejecting them — gh stack add would make an empty branch at HEAD, so a typo becomes a real layer. This skill never creates or splits layers: create each branch with its commits yourself, or fix the spelling, then retry.`

### 6b. Classify every `gh stack link` argument

`gh stack link` only. `link` **pushes before it validates anything** — the push is its first remote write, and a bad PR URL only errors after it. So every argument is resolved here, read-only, before `link` runs.

Probe each argument, all probes in a single parallel batch (skip the `git show-ref` probe for an argument that is a PR URL):

```bash
git show-ref --verify refs/heads/<arg>
gh pr view <arg> --json number,url,state,isDraft,headRefName,baseRefName,headRepository,headRepositoryOwner,isCrossRepository
```

Classify each argument by its **syntactic form first**, and only then read the probes. `gh pr view` accepts `[<number> | <url> | <branch>]`, so a PR resolving for a branch name is the ordinary `link` input, not a conflict.

**PR URL** — no local ref required. Resolve it with the same `gh pr view --json` field list, and verify the owner and repository of the returned `.url` match the current `nameWithOwner`. Class: existing PR, no local branch push. Its layer branch is `.headRefName`.

**Numeric argument** — check `refs/heads/<arg>` first. If a numeric local branch exists, **always refuse as ambiguous**: `link` may push that branch while reading the same text as a PR number, or as a stack number in first position. With no local branch of that name, resolve it as a PR number, and refuse if no PR carries that number. Class: existing PR, no local branch push. Its layer branch is `.headRefName`.

**Non-numeric branch name** — the local ref, the PR, and `.headRefName` together give five outcomes:

| Local ref | PR resolves | `.headRefName` | Class | Effects to announce |
| :--- | :--- | :--- | :--- | :--- |
| yes | yes | `== <arg>` | local branch, existing PR | push: yes · create PR: no · retarget: only if needed |
| yes | no | — | local branch, no PR | push: yes · create PR: yes |
| no | yes | `== <arg>` | remote branch, existing PR | no local push |
| yes | yes | `!= <arg>` | inconsistent resolution — refuse | — |
| no | no | — | unresolvable — refuse | — |

Every class above that resolved a PR is **PR-backed**, as is every PR number and every PR URL argument, and all of them go through both checks below. Only `local branch, no PR` is exempt from the head-repository check.

For a PR argument, compare the owner and repository in the returned `.url` against the `nameWithOwner` from step 2. `link` keeps **only the number** out of a PR URL and looks it up in the current repository, so a URL pointing at another repository silently links this repository's PR of that number. This comparison is the only thing that catches it.

**Then check the head repository — the `.url` comparison does not.** `.url` identifies the PR's **base** repository, not the repository hosting its **head branch**. A PR shown as `<name-with-owner>#<number>` can have base `<name-with-owner>` and head `contributor/repo-fork:feature`: its URL is genuinely in `<name-with-owner>`, so the comparison above passes while the layer branch sits on a fork. The step-3 `.isFork` check cannot see it either — it only inspects the current repository. So **comparing the PR URL alone does not detect a fork**, and every resolved PR — from a URL, from a number, or from a branch name, local or remote — is checked here, in order:

1. `.isCrossRepository` is `true` → refuse.
2. `.headRepository` or `.headRepositoryOwner` is null or absent → refuse. The head fork was deleted, so the layer cannot be verified and cannot be trusted.
3. Otherwise `.headRepositoryOwner.login` must equal the owner of `nameWithOwner`, **and** `.headRepository.name` must equal its repository name.

Use those two fields and no others: `headRepository.nameWithOwner` comes back as an **empty string** on this `gh` version, and `headRepositoryOwner.name` is the account's **display name** rather than its login, so comparing either produces a wrong verdict.

A **local branch with no PR is exempt** — nothing to check. `link` pushes it to the current remote and creates its PR there, so its head repository is `<name-with-owner>` by construction. Do not "fix" this by refusing it.

This runs before the step-5 dependency verification and before `link`, like every other check here. Refuse before running `link`, with:

- Unresolvable argument → `Cannot resolve <arg>: no local branch refs/heads/<arg>, and no PR by that number or URL in <name-with-owner>. gh stack link would push the other branch arguments and create their PRs first, then fail server-side on this one — leaving those new PRs orphaned outside any stack. Fetch or create <arg> locally, or pass the number or URL of its existing PR, then retry.`
- Argument in another repository → `<arg> resolves to <other-name-with-owner>#<number>, not <name-with-owner>. gh stack link parses only the number out of a PR URL, so it would silently link <name-with-owner>#<number> instead. Pass a PR of <name-with-owner>, then retry.`
- Head branch on a fork → `PR #<number> has head <head-owner>/<head-repo>:<head-branch>, but this stack belongs to <name-with-owner>. GitHub stacked PRs require every layer branch to live in the same repository; cross-fork layers are unsupported. Move the branch into <name-with-owner> or use /git:create for a standalone PR.`
- Head repository unverifiable → `PR #<number> reports no head repository, so its head branch <head-branch> cannot be confirmed to live in <name-with-owner> — this is what a deleted head fork looks like. GitHub stacked PRs require every layer branch to live in the same repository, and an unverifiable layer is not stacked on trust. Recreate the branch in <name-with-owner> or use /git:create for a standalone PR.`
- Ambiguous numeric argument → `<arg> is numeric and is also the local branch refs/heads/<arg>. gh stack link would push branch <arg> while reading the same text as PR #<arg>, or as a stack number in first position, and their heads need not match. Rename the branch, or pass the PR URL of the layer you mean, then retry.`
- Inconsistent resolution → `<arg> is a local branch, but gh pr view <arg> returns PR #<number> whose head is <head-ref-name>. gh stack link would push branch <arg> and link a PR that is not its own. Pass the PR URL of the layer you mean, then retry.`
- Fewer than two arguments resolved → `gh stack link needs at least 2 resolved layers, got <count>. Add the missing layer as a local branch, a PR number, or a PR URL, then retry.`

Finally, normalise each resolved argument into a **layer record** — head branch, PR number and URL if it has one, repository, position bottom → top, and the diff source available for it (a local branch, a PR diff, or both). That order is what step 8 prints and passes to `link`, and those records are what step 5 verifies.

### 7. Create the stack

`create` mode only. Every branch listed here already exists — step 6 proved it.

Create the stack, listing the branches bottom → top:

```bash
gh stack init --base <trunk> <bottom-branch> <next-branch> <top-branch>
```

The trunk need not be the default branch — a stack's trunk can be any branch in the repository. To append a layer on top of an existing stack:

```bash
gh stack add <branch>
```

Keep one branch and one PR per layer, each layer's diff kept narrow. Linear history is required between each branch in the stack.

### 8. Publish or sync the stack

`publish` mode — submit the stack:

```bash
gh stack submit --auto
```

This pushes every branch and creates or updates the PRs and the stack on GitHub. Pass `--auto` explicitly every time: it auto-generates the PR titles instead of opening the editor. Without a TTY the editor is skipped anyway, but `--auto` is the only protection if a PTY is ever allocated, where a bare `gh stack submit` opens a full-screen mouse-driven editor and blocks indefinitely. `--auto` is not auto-merge and has nothing to do with draft state.

**There is no title or body flag.** `gh stack submit` derives them itself: exactly one commit on a branch → the PR title is that commit's subject and the body is its message body; more than one commit → a humanized branch name and an empty body. The repo's PR template is merged in and a `gh-stack` attribution footer is appended. So **one commit per layer** is how the PR text is controlled — write that commit well via `/git:commit`. An arbitrary body requires a separate explicit `gh pr edit <number> --body ...` after submit, which this skill does not run on its own.

New PRs are created as **drafts** unless `--open` is passed. `--open` also flips **already-existing** draft PRs in the stack to ready for review, so it is unsafe on a stack holding PRs left as drafts on purpose — pass it only when the user explicitly asks, and say what it will convert.

`publish` mode — link branches and PRs into a stack:

```bash
gh stack link <pr-or-branch> <pr-or-branch> [--base <trunk>] [--open] [--remote <name>]
```

`link` takes at least two arguments and is a **publishing** command, not a local one. It has **no confirmation prompt and no `--dry-run`**, and it pushes before it validates a single PR — which is why step 6b resolves every argument first. Four remote effects are **possible**; which ones occur depends on how each argument resolved:

1. **Push** — every argument that names an existing local branch is pushed to the remote. PR numbers and URLs are filtered out and never pushed.
2. **Create PRs** — a branch argument with no open PR gets a new one, based on the layer below it and created as a **draft** unless `--open` is passed.
3. **Retarget** — an existing PR whose base is not the layer below it is retargeted to that layer. A PR `link` just created is never retargeted.
4. **Stack upsert** — the PRs become a new stack, or are added to the existing one. Existing PRs are never removed.

| Step-6b class | Push | Create PR | Retarget | Stack upsert |
| :--- | :--- | :--- | :--- | :--- |
| Local branch, no PR | yes | yes | no | yes |
| Local branch, existing PR | yes | no | only if the base is wrong | yes |
| Remote branch, existing PR (no local ref) | no | no | only if the base is wrong | yes |
| PR number | no | no | only if the base is wrong | yes |
| PR URL | no | no | only if the base is wrong | yes |

Every class here except `Local branch, no PR` is PR-backed, so it reaches `link` only after passing the step-6b head-repository check. The exempt class has no PR yet: `link` creates it in `<name-with-owner>`.

`--base` sets the bottom PR's base and defaults to the repository's default branch. `--open` additionally flips **already-existing** draft PRs to ready for review — the same footgun as on `submit`, so pass it only on explicit request and say what it will convert. It never re-flips a PR from this same run: those were created ready.

Nothing here is gated by a prompt, so print two lists **before** running it:

- **Resolved arguments** — one line per argument: the repository it belongs to, its head branch, and its PR number if it has one.
- **Effects for this invocation** — read off the table above, per argument: which branches get pushed, which PRs get created, which bases get retargeted, and the stack upsert.

Then run `link`, and execute nothing outside those two lists.

`sync` mode:

```bash
gh stack sync
gh stack rebase [--downstack|--upstack]
```

If `gh stack rebase` reports a conflict (exit code `3`), resolve it and continue per [reference/gh-stack-cli.md](./reference/gh-stack-cli.md).

### 9. Print the result

Re-read the stack state:

```bash
gh stack view --json
```

Use it for the layer order — `branches[]` comes back ordered bottom → top — and for `.branches[].pr.number` and `.pr.url`. Use it for nothing else here: `pr.state` is computed locally as exactly one of `OPEN`, `MERGED`, or `QUEUED`, and **the payload carries no draft field at all**, so a draft PR reports `OPEN` and is indistinguishable from one that is ready for review. There is no CI field either, and no `gh stack checks` subcommand.

So fetch the real state and the checks per PR, all calls in a single parallel batch:

```bash
gh pr view <pr-number> --json state,isDraft,url
gh pr checks <pr-number>
```

Immediately after `gh stack submit` or `gh stack link` the checks are often not yet reported — print `checks not yet reported` for those PRs and do not poll.

Then print, in bottom → top order, one line per layer:

- Position in the stack and the branch name
- PR number and URL from `gh pr view`
- State from `.state`, and `draft` or `ready` from `.isDraft`
- Check status from `gh pr checks`, or `checks not yet reported`

Close with a suggested next step:

- Any failing checks → "Fix the failing checks on `<branch>` first — everything above it in the stack is blocked behind it."
- All green and still drafts → "Mark them ready for review when you are — bottom PR first."
- Otherwise → "Review lands bottom-up: `<bottom-branch>` merges first, and the stack retargets the rest automatically."

## Hard rules

- NEVER install, upgrade, or modify `gh` or the `github/gh-stack` extension — report the missing prerequisite and the exact command for the user to run.
- NEVER run `gh stack merge`, `gh pr merge`, or otherwise merge any PR in the stack. `gh stack merge` merges **without asking** when it runs non-interactively or with `--yes` — there is no confirmation prompt to fall back on.
- NEVER mutate anything in `inspect` mode, and never run a remote operation that was not in the printed plan.
- NEVER run `gh stack init`, `add`, `submit`, or `push` before the step-6 `git show-ref --verify` check passes for every layer — `init` and `add` create a missing branch instead of rejecting it, and `submit` and `push` push the layers.
- NEVER run `gh stack link` before every argument is resolved per step 6b, every resolved PR has passed the step-6b head-repository check, **and** every adjacent pair has passed the step-5 dependency check. It creates no branch, but it pushes before it validates anything, so a PR number or URL must be resolved read-only first — a PR URL from another repository must be caught here, because `link` keeps only the number and links this repository's PR instead, and a PR whose head branch lives on a fork must be caught here too, because its own URL is in this repository and the `.url` comparison passes it.
- NEVER refuse a branch argument just because a PR resolves for it. `gh pr view` takes `[<number> | <url> | <branch>]`, so a branch with an open PR is the most ordinary `link` input. Only a **numeric** argument that is also a local branch is ambiguous.
- NEVER treat `gh stack link` as a local command. It pushes, opens draft PRs, retargets existing PR bases, and writes the stack on GitHub, with no confirmation prompt and no `--dry-run` — print all of it first.
- NEVER report draft state from `gh stack view --json`. That payload has no draft field and reports a draft PR as `OPEN`; read `isDraft` from `gh pr view` instead.
- NEVER run `gh stack view` without `--json`. `--json` is the documented machine-readable contract, with typed exit codes and a guarantee that JSON mode never prompts, so agents always get parseable output. The bare form does not hang — it renders a full-screen TUI on a terminal and plain static text with no TTY — but its output is not a contract.
- NEVER promise or invent a PR title or body — `gh stack submit` generates both from the layer's commits and the repo PR template.
- NEVER force-push (`--force`, `-f`, `--force-with-lease`) without explicit user confirmation.
- NEVER change, retarget, or push to the repository's default branch.
- NEVER stack layers that have no real dependency — say so and point at `/git:create`. This binds identically to a layer given as a PR number or a PR URL: with no local branch, read its content with `gh pr diff <number>` rather than skipping the check.
- NEVER add a "Generated with Claude Code" footer or a `Co-authored-by` line to any PR body.
- `gh stack submit` and `gh stack link` both create drafts unless `--open`; on either command `--open` also converts existing drafts to ready — pass it only on explicit user request.

## Reference

- [reference/gh-stack-cli.md](./reference/gh-stack-cli.md) — full `gh stack` command and flag surface, the `--json` payload shape, the exit-code table, and troubleshooting.
