---
name: mintlify-validate
description: Validates a Mintlify documentation site before pushing by running `mint validate` and `mint build`, then reports broken links, invalid MDX frontmatter, and pages missing from `docs.json` navigation. READ-ONLY — does not modify files. Use when the user types `/docs:mintlify-validate`, says `validate docs`, `check mintlify`, `verify docs build`, `broken links`, or asks to verify documentation before pushing.
argument-hint: (none — runs in the docs directory of the cwd)
allowed-tools: Bash, Read
---

# mintlify-validate

Run Mintlify's validator and builder against the docs site rooted at the nearest `docs.json`, cross-check navigation against the filesystem, and emit a structured report. READ-ONLY.

## Prerequisites

- `mint` CLI must be on PATH. Check with:

  ```bash
  which mint
  ```

  If the command fails, stop and tell the user: `mint CLI not found. Install with: npm i -g mint`. Do NOT auto-install.

## Steps

### 1. Locate `docs.json`

Walk up from the current working directory until a `docs.json` file is found. The directory containing it is the docs root.

```bash
dir="$PWD"
while [ "$dir" != "/" ] && [ ! -f "$dir/docs.json" ]; do dir="$(dirname "$dir")"; done
[ -f "$dir/docs.json" ] && echo "$dir" || echo "NOT_FOUND"
```

If not found, stop with: `No docs.json found — run /docs:mintlify-init first.`

### 2. Run `mint validate`

From the docs root, capture full stdout and stderr:

```bash
cd <docs-root> && mint validate 2>&1
```

Record the exit code and parse the output for issues (broken internal/external links, MDX syntax errors). Keep file paths and line numbers when present.

### 3. Run `mint build`

From the docs root, capture full stdout and stderr:

```bash
cd <docs-root> && mint build 2>&1
```

Record the exit code and parse the output for issues (missing pages, invalid frontmatter, navigation pointing to non-existent files). Keep file paths and line numbers when present.

### 4. Cross-check navigation vs filesystem

Read `<docs-root>/docs.json`. Enumerate every `pages` entry across all groups, tabs, anchors, and nested navigation structures. For each entry (which is a path relative to the docs root, without the `.mdx` extension), verify the corresponding `.mdx` file exists.

Record any entry whose `.mdx` file is missing as `missing-in-fs`.

### 5. Cross-check filesystem vs navigation

List every `.mdx` file under the docs root. For each, build its docs-root-relative path without the `.mdx` extension and check whether that path appears in any `pages` array in `docs.json`.

Record any `.mdx` file not referenced anywhere as `orphan`.

### 6. Emit the report

Print exactly:

```
Validation report
- mint validate: PASS / FAIL (N issues)
- mint build: PASS / FAIL (N issues)
- Missing files referenced in nav: <list or "none">
- Orphan files not in nav: <list or "none">

Issues
- <file>:<line>: <message>
```

End the report with:

- `All checks passed. Safe to push.` — when both commands exited 0, no missing files, no orphans.
- `Fix the issues above before committing.` — when ANY check failed.

## Hard rules

- READ-ONLY — never modify any file. No `Edit`, no `Write`. `allowed-tools` intentionally excludes them.
- Never run `mint deploy` or any push / publish command.
- Never auto-install `mint`. Instruct the user to install it manually.
- Never silently suppress errors. Every failure surfaces in the report with file and line when available.
- Always run commands from the resolved docs root, never from an unrelated directory.
