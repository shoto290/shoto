---
name: mintlify-page
description: Authors a new Mintlify MDX page (optionally documenting existing source code via `--from-code <path>`), delegates the draft to the `docs-architect` sub-agent, and writes the result under the docs directory. The architect wires the new page into `docs.json` navigation automatically. Use when the user types `/docs:mintlify-page`, says `add docs page`, `write a docs page`, `document this code`, `create mdx page`, or asks to add new documentation content.
argument-hint: <page-title> [group] [--from-code <path>]
allowed-tools: Bash, Read, Write, AskUserQuestion, Agent, Skill
---

# mintlify-page

Author a new Mintlify MDX page, delegate the draft to the `docs-architect` sub-agent, write the file under the docs root, and let the architect register it in `docs.json` under the chosen navigation group.

## Prerequisites

- Run from a directory that contains (or has an ancestor containing) `docs.json`. If none is found by walking up from cwd, stop with:

  ```
  docs.json not found — run this from a Mintlify docs site (a directory with docs.json, or any descendant).
  ```

- The `docs-architect` sub-agent must be available — this skill never writes MDX content inline.

## Steps

### 1. Parse arguments

From `<page-title> [group] [--from-code <path>]`:

- `<page-title>` — required, positional 1. Quoted strings are honored. Reject if missing with: `Usage: /docs:mintlify-page <page-title> [group] [--from-code <path>]`.
- `[group]` — optional, positional 2 (the second non-flag token).
- `--from-code <path>` — optional flag pointing to source code to document.

Store as `<title>`, `<group-arg>`, and `<code-path>`.

### 2. Locate `docs.json`

Walk up from cwd until a `docs.json` is found:

```bash
dir="$PWD"
while [ "$dir" != "/" ] && [ ! -f "$dir/docs.json" ]; do dir="$(dirname "$dir")"; done
test -f "$dir/docs.json" && echo "$dir"
```

Store the directory as `<docs-root>`. If nothing was found, stop with the Prerequisites error.

### 3. Read existing groups

Read `<docs-root>/docs.json`. Extract every `group` name across every tab in `navigation.tabs[].groups[]` (and any nested groups). Build a flat list `<existing-groups>` preserving discovery order.

### 4. Choose the group

- If `<group-arg>` was provided and matches an entry in `<existing-groups>` (case-insensitive), use it.
- If `<group-arg>` was provided but does NOT match, ask via `AskUserQuestion`:
  - (a) Create a new group named `<group-arg>`
  - (b) Pick an existing group from `<existing-groups>`
- If `<group-arg>` was NOT provided, ask via `AskUserQuestion` with one option per entry in `<existing-groups>` plus a final `Create new group` option. If `Create new group` is chosen, prompt for the group name.

Store the result as `<group>`.

### 5. Gather source context (only if `--from-code` was provided)

Invoke the `explore:explore` skill via the Skill tool with `<code-path>` and the focus:

```
documentation context: what this module does, public API, typical usage
```

Capture the returned report as `<explore-report>`. If `--from-code` was not provided, leave `<explore-report>` empty.

### 6. Determine target audience

If the audience is obvious from the title or `<explore-report>` (e.g. clearly an API reference, a tutorial, a concepts page), use that and skip the question. Otherwise ask via `AskUserQuestion`:

- (a) End users
- (b) Developers integrating the API
- (c) Internal contributors

Store as `<audience>`.

### 7. Delegate the draft to `docs-architect`

Spawn:

```
Agent({
  subagent_type: "docs-architect",
  prompt: <see below>
})
```

Prompt contents:

- The page title: `<title>`.
- The docs root: `<docs-root>` (the directory containing `docs.json`).
- The navigation group it belongs to: `<group>`.
- The target audience: `<audience>`.
- The starter skeleton from [template.md](./template.md) (read it and include it verbatim as the format hint).
- The `<explore-report>` block if `<code-path>` was given, framed as `Source context to document:`.
- Constraints: output MUST be valid Mintlify MDX with frontmatter (`title:` and `description:` strings), use Mintlify components only from this set — `<Card>`, `<CardGroup>`, `<CodeGroup>`, `<Tabs>` / `<Tab>`, `<Note>`, `<Warning>`, `<Tip>`, `<Steps>` / `<Step>`, `<Accordion>` / `<AccordionGroup>`, `<Frame>`.

Capture the agent's returned MDX as `<mdx>`. If the agent did not return a string starting with a `---` frontmatter block, stop with: `docs-architect returned an MDX draft without frontmatter — aborting.`

### 8. Compute slug and target path

Slugify `<title>`:

- Lowercase.
- Replace any run of non-alphanumeric characters with a single hyphen.
- Trim leading and trailing hyphens.

Slugify the group similarly for the directory name. Resulting path:

```
<docs-root>/<group-dir>/<slug>.mdx
```

Store the relative navigation entry (no extension) as `<nav-entry>` — e.g. `<group-dir>/<slug>`.

### 9. Write the MDX file

```bash
test -f "<docs-root>/<group-dir>/<slug>.mdx"
```

If the file already exists, ask via `AskUserQuestion`:

- (a) Overwrite
- (b) Abort

If the parent directory does not exist, create it:

```bash
mkdir -p "<docs-root>/<group-dir>"
```

Write `<mdx>` to the target path with `Write`.

### 10. Verify the navigation patch

`docs-architect` is responsible for updating `<docs-root>/docs.json` to include `<nav-entry>` under `<group>`. After the architect returns, `Read` `<docs-root>/docs.json` and confirm:

- A page entry matching `<nav-entry>` exists in the `pages` array of the `<group>` group.
- That `<group>` lives in the expected tab (the first tab if no specific tab was chosen).
- No other fields were invented.

Report the resulting diff (the new entry and its enclosing group) to the user. If the entry is missing, stop with: `docs-architect did not register <nav-entry> under <group> in docs.json — please patch manually or rerun.`

### 11. Print next steps

Output:

- The absolute path of the MDX file that was written.
- The navigation entry that was added (`<nav-entry>`) and the group it was added to.
- A reminder: `Run /docs:mintlify-validate before committing.`

## Hard rules

- NEVER overwrite an existing MDX file without explicit user confirmation via `AskUserQuestion`.
- NEVER push or commit — this skill only writes files.
- NEVER patch `docs.json` directly — that is `docs-architect`'s job. This skill only verifies the result.
- The MDX draft MUST come from the `docs-architect` sub-agent — do not write MDX content inline.
- NEVER write outside `<docs-root>` or modify any file other than the new MDX file.

## Reference

- [template.md](./template.md) — minimal MDX skeleton passed to `docs-architect` as the starting format.
