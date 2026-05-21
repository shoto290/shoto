---
name: mintlify-init
description: Scaffolds a new Mintlify documentation site in the current repo by running `mint new`, then patches `docs.json` with the user's site name, primary color, and GitHub repo URL. Use when the user types `/docs:mintlify-init`, says `scaffold docs`, `create mintlify site`, `set up mintlify`, `bootstrap documentation`, or asks to start a new docs site. Requires the `mint` CLI (`npm i -g mint`).
argument-hint: [target-directory]
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# mintlify-init

Scaffold a Mintlify documentation site locally with `mint new`, then patch the generated `docs.json` with site name, primary color, and an optional GitHub link.

## Prerequisites

- `mint` CLI on PATH. If `which mint` fails, stop and tell the user to run:

  ```bash
  npm i -g mint
  ```

  Do NOT auto-install.

## Steps

### 1. Resolve the target directory

Use the first positional argument; default to `./docs` if none was given. Store as `<dir>`.

```bash
test -e "<dir>"
```

If `<dir>` exists and is non-empty, ask via `AskUserQuestion`:

- (a) Abort
- (b) Pick a different directory name (re-prompt and re-resolve)

Never overwrite an existing directory.

### 2. Verify `mint` is available

```bash
which mint
```

If the command fails, stop with the install instruction from Prerequisites.

### 3. Run `mint new`

```bash
mint new "<dir>"
```

Capture stdout and stderr. If the exit code is non-zero, stop and surface the failure verbatim.

### 4. Locate `docs.json`

Expected path: `<dir>/docs.json`. If the file is missing after `mint new`, stop with:

```
docs.json not found at <dir>/docs.json — `mint new` may have failed or changed its output layout.
```

### 5. Collect site configuration

One `AskUserQuestion` call gathering:

- Site name — default: the basename of `<dir>`
- Primary hex color — default: `#0D9373`
- GitHub repo URL — default: empty (skip the navbar link)

### 6. Patch `docs.json`

`Read` the file, apply the patches, then `Write` it back:

- Set top-level `name` to the chosen site name.
- Set `colors.primary` to the chosen hex color.
- If a GitHub URL was provided, append to `navbar.links` the entry:

  ```json
  { "label": "GitHub", "href": "<github-url>" }
  ```

  Create `navbar` and `navbar.links` if they don't already exist. Do NOT touch any other field.

Preserve every other field, key order where possible, and the surrounding formatting.

### 7. Print next steps

Emit a final block:

```
Done. Next:

  cd <dir> && mint dev          # preview locally
  /docs:mintlify-page "<title>" <group>   # add a page
  /docs:mintlify-validate       # validate before committing
```

## Hard rules

- NEVER overwrite an existing `docs.json` without explicit user confirmation.
- NEVER run `npm i -g mint` automatically — print the command and let the user run it.
- NEVER push to GitHub or invoke `git` — this skill only scaffolds local files.
- NEVER overwrite an existing target directory; ask for a new name or abort.
- The CLI binary is `mint` (not `mintlify`); the scaffold command is `mint new` (there is no `mint init`); the config file is `docs.json` (not `mint.json`).
