# Worked Example: the bundled deep-research workflow

The bundled `deep-research` workflow is the gold-standard reference for both the **plugin-bundled wrapper pattern** and the **script DSL**. A new workflow should follow this shape rather than inventing a different one.

## Layout

```
deep-research/
├── SKILL.md                       # thin wrapper — clarifies, invokes, renders
└── scripts/
    └── research.workflow.js       # the orchestration script
```

## The wrapper skill (shape)

The wrapper is thin. It does three things and nothing else:

1. **Clarify scope before the run.** If the question is underspecified, it asks 2-3 clarifying questions (this is where `AskUserQuestion` belongs — never in the script) and weaves the answers into one refined question.
2. **Invoke the bundled script via the Workflow tool**, resolving the script through the plugin-root env var:

   ```
   Workflow({
     scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/deep-research/scripts/research.workflow.js",
     args: "<refined question>"
   })
   ```

   The script's `meta.name` is `deep-research`; the refined question passed as `args` is the only input it needs. The skill firing is itself the opt-in to the Workflow tool.
3. **Render the structured result after the run** — an executive summary, findings with confidence and cited sources, caveats, and open questions. It never dumps raw JSON.

## The script (DSL shape)

`meta` is a pure literal whose `phases` titles match the `phase()` calls exactly:

```js
export const meta = {
  name: 'deep-research',
  description: 'Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.',
  whenToUse: '...',
  phases: [
    { title: 'Scope', detail: 'Decompose question (from args) into 5 search angles' },
    { title: 'Search', detail: '5 parallel WebSearch agents, one per angle' },
    { title: 'Fetch', detail: 'URL-dedup, fetch top 15 sources, extract falsifiable claims' },
    { title: 'Verify', detail: '3-vote adversarial verification per claim' },
    { title: 'Synthesize', detail: 'Merge semantic dupes, rank by confidence, cite sources' },
  ],
}
```

Five phases, all internal to the script:

1. **Scope** — one `agent(..., { schema: SCOPE_SCHEMA })` decomposes the question (read from `args`) into search angles. Guards `if (!scope) return { error }`.
2. **Search → Fetch** — a `pipeline(scope.angles, searchStage, fetchStage)` with **no barrier**: each angle's search results flow straight into URL-dedup and per-source fetch+extract. The fetch stage uses `parallel(...)` to fan out one extractor per novel source.
3. **Verify** — a `parallel(...)` **barrier** (intentional: the claim pool must be fully assembled and ranked before voting), with a nested `parallel(...)` running `VOTES_PER_CLAIM` adversarial voters per claim. Null votes are treated as abstentions via `.filter(Boolean)`.
4. **Synthesize** — one `agent(..., { schema: REPORT_SCHEMA })` merges duplicates and ranks by confidence.

Every stage that the next stage parses uses a JSON Schema (`SCOPE_SCHEMA`, `SEARCH_SCHEMA`, `EXTRACT_SCHEMA`, `VERDICT_SCHEMA`, `REPORT_SCHEMA`). Every empty / skipped / failed path returns a salvage object rather than throwing, so a partial run still yields a usable result. The final `return` is a structured report object — the only thing that reaches Claude.

## What to copy from it

- **Thin wrapper, fat script.** Clarification and rendering in the wrapper; all orchestration in the script.
- **`pipeline()` for the streaming middle, `parallel()` only where a barrier is needed** (assembling + ranking the claim pool before verification).
- **A JSON Schema per parsed stage**, and a guard / salvage return on every branch that could be empty.
- **`args` read once at the top**, with an early `return { error }` when it is empty.
