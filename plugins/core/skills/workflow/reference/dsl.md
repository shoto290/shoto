# Workflow Script DSL

A dynamic workflow is a single JavaScript file (not TypeScript) executed by Claude Code's Workflow runtime in the background. The runtime injects the DSL functions and globals below — you do not import them. The script's job is to orchestrate subagents; only its `return` value flows back into Claude's context.

> Authoritative source: the `Workflow` tool description. The public docs at code.claude.com/docs/en/workflows omit the script API, so this file mirrors the tool description.

## `meta`

```js
export const meta = {
  name: 'my-workflow',            // kebab-case, matches the filename
  description: 'What it does',
  whenToUse: 'When to invoke it', // optional
  phases: [                       // optional, but titles must match phase() calls
    { title: 'Plan', detail: 'Decompose the input' },
    { title: 'Work', detail: 'One agent per item' },
  ],
  model: 'sonnet',                // optional default model for the run
}
```

- `meta` MUST be a **pure object literal** — no variables, no function calls, no spreads (`...`). The runtime reads it statically.
- `phases` entries are `{ title, detail }`. Every `title` MUST correspond to a `phase()` call in the body, and every `phase()` call should have a matching entry. Misalignment breaks progress display.
- `name` is the workflow identity; for native saved scripts it also drives the `/<name>` command.

## `phase(title)`

Marks a phase boundary for progress display. Call it once per phase, in order, before that phase's agents.

```js
phase('Plan')
```

## `agent(prompt, opts)`

Spawns a single subagent and awaits its result.

```js
const result = await agent('## Worker\n\n' + instruction + '\n\nStructured output only.', {
  label: 'work:item-1',   // short progress label
  phase: 'Work',          // which phase this agent belongs to
  schema: WORK_SCHEMA,    // JSON Schema — when present, returns a validated object
  model: 'haiku',         // route this stage to a specific model (else session model)
  isolation: 'worktree',  // run in an isolated worktree
  agentType: 'Explore',   // use a specific subagent type
})
```

Returns:

- the agent's **text** when no `schema` is given,
- a **validated object** matching `schema` when one is given,
- **`null`** when the agent was skipped (e.g. user-skip) — always guard with `if (!result)` or `.filter(Boolean)`.

Spawned agents run in `acceptEdits` mode, inherit the tool allowlist, and use the session model unless `model` routes them elsewhere.

## `parallel(thunks)` — barrier

Runs an array of **thunks** (zero-arg functions returning promises) concurrently and waits for **all** of them. This is a barrier: nothing after it runs until every task settles.

```js
const verdicts = await parallel(
  claims.map(claim => () => agent(VERIFY_PROMPT(claim), { schema: VERDICT_SCHEMA }))
)
const valid = verdicts.filter(Boolean)   // a thrown task becomes null
```

A task that throws becomes `null` in the result array — filter with `.filter(Boolean)`. Use `parallel()` only when the next stage genuinely needs the **whole pool at once** (e.g. ranking before verification).

## `pipeline(items, ...stages)` — no barrier

Streams each item through a sequence of stage callbacks **without** a barrier, so fast items reach later stages while slow ones are still in earlier ones.

```js
const out = await pipeline(
  items,
  (prevResult, originalItem, index) => agent(/* stage 1 */),
  (prevResult, originalItem, index) => agent(/* stage 2 */),
)
```

Each stage callback receives `(prevResult, originalItem, index)`. Prefer `pipeline()` over a `parallel()` barrier unless a stage needs all prior results simultaneously.

## `log(msg)`

Emits a progress line. Use it to surface counts and decisions, not to return data.

```js
log('Planned ' + plan.items.length + ' items')
```

## Globals

- **`args`** — the string passed by the wrapper's `Workflow({ args })` call (or the `/<name>` command). Read it once: `const INPUT = (typeof args === 'string' && args.trim()) || ''`.
- **`budget`** — `{ total, spent(), remaining() }`. Check `budget.remaining()` to throttle fan-out under a cap.
- **`workflow(nameOrRef, args)`** — runs an inline sub-workflow, **one level deep only** (a sub-workflow cannot itself call `workflow()`).

## Return value

The script's `return` is the **only** thing that reaches Claude's context. Return a structured object (not raw text) so the wrapper can render it. Always provide salvage returns for the empty / skipped / failed paths rather than throwing.
