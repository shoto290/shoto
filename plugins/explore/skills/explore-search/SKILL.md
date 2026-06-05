---
name: explore-search
description: 'Lightweight single-pass web search: ground the question in current repo usage, search the web, and return a short cited answer.'
when_to_use: 'Use for a quick cited external answer tied to current repo usage; for heavy multi-source research, defer to deep-research.'
argument-hint: '[topic]'
allowed-tools: Read, Glob, Grep, WebSearch, WebFetch, AskUserQuestion
---

# explore-search

Answer one external question by grounding it in how this repo uses the thing, running a focused web search, and returning a short cited answer. Single-pass, read-only. No agent fan-out, no scripts.

## Scope boundary

- **In scope:** a quick, cited external answer linked to current repo usage — one focused search pass.
- **Out of scope → defer:** broad multi-source coverage, claims that need cross-checking, or anything resembling a report. Hand off to the `deep-research` skill when available (`Skill({ skill: "deep-research", args: "<topic>" })`). Do not try to replicate it here.

## Flow

1. **Ground.** Extract the relevant context from the repo: what library, feature, error, config, or version this is actually about. Use `Glob`/`Grep`/`Read` (e.g. find the dependency in a manifest, the call site, the error string, the pinned version). If the target is still unclear after looking, ask one targeted question via `AskUserQuestion` — do not guess.
2. **Search.** Run a focused `WebSearch` shaped by the grounded context (include the specific version, API, or error). Then `WebFetch` a few of the most relevant and authoritative results (official docs, changelogs, the project's own issues) — not a wide crawl.
3. **Synthesize.** Return a short answer that links back to the repo's usage: what it means for this codebase, at the version/call site found in step 1. Cite each source inline.
4. **Defer.** If the question turns out to need broad multi-source coverage or fact-checking to answer responsibly, STOP and recommend the `deep-research` skill rather than fanning out here.

## Output

- A short answer (a few sentences to a few bullets), grounded in the repo usage found in step 1.
- Inline citations: source title + URL for each claim that came from the web.
- When deferring: one line stating why the scope exceeds a single pass, plus the pointer to the `deep-research` skill.

## Constraints

- Read-only — never modify files. `allowed-tools` excludes `Edit` and `Write` by design.
- No agent fan-out and no scripts — this is a single search pass.
- Keep it lightweight. The moment the work needs verification or many sources, defer to the `deep-research` skill.
- English only. House rules apply (no co-author or generated-by lines).
