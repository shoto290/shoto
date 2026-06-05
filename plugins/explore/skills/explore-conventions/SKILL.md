---
name: explore-conventions
description: 'Research the external best practice for a technology, reconcile it against how this repo does it, and recommend a fit. READ-ONLY.'
when_to_use: 'Use to learn the community convention for something and how it compares to this repo''s current patterns.'
argument-hint: '[topic or tech]'
allowed-tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion
---

# explore-conventions

Answer "what's the convention for X here?" by grounding in how this repo already does the thing, researching the external best practice, and reconciling the two with a clear, cited recommendation. READ-ONLY — never edit repo files.

## Hard rules

- **READ-ONLY.** Never modify files. `allowed-tools` excludes `Edit` and `Write` by design.
- **Ground before researching.** Always capture the in-repo convention first so the comparison is concrete, not abstract.
- **Cite authoritative sources.** Prefer official docs, framework guides, and widely-adopted standards over blog SEO.
- **Never silently pick.** Present external best practice vs the current repo pattern side by side; show the tradeoff, then recommend.
- **Thin coordinator.** No agent fan-out, no scripts — just the four steps below.

## Steps

1. **Ground** — read how the repo currently does the thing.
   - Search existing patterns with `Glob`/`Grep`, then `Read` the representative files.
   - Read `AGENTS.md`, `CLAUDE.md`, and `README` (root and any nearer the topic) plus neighboring code to capture the established in-repo convention.
   - If the topic is ambiguous (multiple plausible technologies or surfaces), ask one focused `AskUserQuestion` before researching.

2. **Research** — find the external convention.
   - Use `WebSearch` to locate the community/official best practice for that technology, then `WebFetch` the authoritative pages to confirm specifics.
   - Capture the canonical recommendation and the source URL for each claim.

3. **Reconcile** — compare external best practice **vs** the current repo pattern.
   - Put them side by side; flag drift or conflicts explicitly.
   - Recommend the option that best fits the repo's SIMPLE principles (from `core:base`). Do not silently pick — surface the tradeoff behind the recommendation.

4. **Render** — output the cited comparison and recommendation using the contract below.

## Output contract

```
## Convention: <topic>

### In this repo
<how the repo does it today — cite the files/lines that establish it>

### External best practice
<the community/official convention — cite source URLs>

### Reconciliation
| Aspect | Repo today | External best practice |
| :-- | :-- | :-- |
| ... | ... | ... |

Drift / conflicts: <explicit list, or "none">

### Recommendation
<the option that best fits the repo's SIMPLE principles, with the tradeoff stated>
```

If the repo has no existing pattern for the topic, say so in `In this repo` and base the recommendation on the external best practice adapted to the repo's SIMPLE principles.
