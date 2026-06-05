---
name: explore-documentations
description: 'Fetch precise, version-accurate docs for a library, framework, SDK, CLI, or API, pinned to the repo''s version via context7. READ-ONLY.'
when_to_use: 'Use when the user wants current, exact docs for a dependency the repo actually uses, pinned to its installed version.'
argument-hint: '[library or topic]'
allowed-tools: Read, Glob, Grep, mcp__context7__resolve-library-id, mcp__context7__query-docs, WebFetch, WebSearch, AskUserQuestion
---

# explore-documentations

A thin coordinator that returns precise, version-accurate documentation for a library the repo uses. Ground the lookup in the repo's real dependency version first, then fetch exact docs via context7. READ-ONLY — never edits repo files.

## Hard rules

- **READ-ONLY.** Only read repo files to ground the version. Never edit or create files. `allowed-tools` excludes `Edit` and `Write` by design.
- **Ground before fetching.** Always resolve the real version from the repo before answering. Never answer from memory when a version is knowable.
- **No fan-out, no scripts.** This is a coordinator over existing tools — no subagents, no helper scripts.
- **Cite everything.** Every claim ties back to a context7 result or an official docs URL, plus the version it applies to.

## Steps

1. **Ground** — identify the target library and its version from the repo:
   - Manifests / lockfiles: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile` / `Gemfile.lock`.
   - If no manifest pins it, confirm actual usage and version hints via `Grep` on import statements.
   - If the user named no library, infer the most relevant one from the repo. If still ambiguous, ask one targeted question via `AskUserQuestion`.
2. **Resolve** — call `mcp__context7__resolve-library-id` to get the context7 library id for the grounded library.
3. **Query** — call `mcp__context7__query-docs` with the resolved id and the user's specific question, scoped to the grounded version where context7 supports it.
4. **Fallback** — if context7 cannot resolve the library or returns nothing, use `WebSearch` to find the official docs site, then `WebFetch` the relevant page(s).
5. **Render** — return a concise, cited answer: the exact API/usage, the version it applies to, and source links. Tie it back to how this repo uses the library.

## Output contract

Render to the user:

```
### <library> @ <grounded version>
<concise answer: exact API / usage for that version>

Repo usage: <where/how this repo uses it>
Sources: <context7 id or official docs URL(s)>
```

If the version cannot be grounded from the repo, state that explicitly and answer against the latest stable version instead.
