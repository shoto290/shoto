# Workflow Scripting API

Authoritative cheat-sheet for scripts run by the `Workflow` tool. Plain JavaScript (not TypeScript).

## `meta` block

Every script begins with a `meta` export that is a **pure literal** — no variables, calls, or spreads:

```js
export const meta = {
  name: 'review-changes',
  description: 'Fan out reviewers across dimensions, then verify',
  whenToUse: 'Multi-dimension review of a change set',
  phases: [
    { title: 'Review', detail: 'One reviewer per dimension' },
    { title: 'Verify', detail: 'Adversarial check of each finding' },
  ],
  model: 'sonnet',
};
```

- Required: `name`, `description`.
- Optional: `whenToUse`, `phases` (array of `{title, detail}`), `model`.
- Phase titles in `meta.phases` must match the `phase()` calls in the script body.

## Core functions

### `agent(prompt, opts?)`

Spawns a subagent. Returns the final text string, or a validated object when `opts.schema` (a JSON Schema) is given. Returns `null` if the user skips — filter with `.filter(Boolean)`.

```js
const finding = await agent('Review for security issues', {
  label: 'security',
  phase: 'Review',
  schema: { type: 'object', properties: { issues: { type: 'array' } }, required: ['issues'] },
});
```

`opts`: `{ label, phase, schema, model, isolation: 'worktree', agentType }`.

### `pipeline(items, stage1, stage2, ...)`

**The default for multi-stage work.** Each item flows through all stages independently — there is NO barrier between stages. Each stage callback receives `(prevResult, originalItem, index)`. A stage that throws drops that item to `null`.

```js
const results = await pipeline(
  dimensions,
  (dim) => agent(`Review for ${dim}`, { phase: 'Review', schema: findingSchema }),
  (finding, dim) => agent(`Verify this ${dim} finding: ${JSON.stringify(finding)}`, { phase: 'Verify', schema: verdictSchema }),
);
const confirmed = results.filter(Boolean);
```

### `parallel(thunks)`

Runs thunks concurrently and **awaits all (a barrier)**. A thunk that throws resolves to `null`. Use only when you need every result together — dedup, merge, or early-exit-on-zero.

```js
const all = await parallel(files.map((f) => () => agent(`Audit ${f}`, { phase: 'Audit' })));
```

### `phase(title)` and `log(message)`

`phase(title)` groups the subsequent agents under a progress group. `log(message)` emits a narrator line — use it to record what was dropped when truncating coverage.

### `workflow(nameOrRef, args?)`

Runs another workflow inline. One level only — a nested workflow cannot call a further workflow.

## Globals

- `args` — the passed input, verbatim JSON.
- `budget` — `{ total, spent(), remaining() }`. `total` is the hard token ceiling, or `null` if unset. Check `budget.remaining()` before fanning out.

## Limits and constraints

- Concurrency cap ≈ `min(16, cores - 2)`. Lifetime cap 1000 agents per run.
- Plain JS, NOT TypeScript: no type annotations, interfaces, or generics.
- `Date.now()`, `Math.random()`, and argless `new Date()` throw — they would break resume. Pass timestamps via `args`; vary randomness by index.
- No filesystem or Node APIs.

## Resume

Relaunch with `{ scriptPath, resumeFromRunId }`. The unchanged prefix returns cached results instead of re-spending tokens.

## Canonical patterns

### Pipeline review (dimensions → review → adversarial verify)

```js
export const meta = {
  name: 'review-changes',
  description: 'Review a change set across dimensions, then adversarially verify each finding',
  phases: [
    { title: 'Review', detail: 'One reviewer per dimension' },
    { title: 'Verify', detail: 'Challenge each finding before trusting it' },
  ],
};

const findingSchema = { type: 'object', properties: { issues: { type: 'array' } }, required: ['issues'] };
const verdictSchema = { type: 'object', properties: { confirmed: { type: 'boolean' }, reason: { type: 'string' } }, required: ['confirmed'] };

const dimensions = args.dimensions;

const results = await pipeline(
  dimensions,
  (dim) => agent(`Review the change set for ${dim} issues. Return findings.`, { phase: 'Review', label: dim, schema: findingSchema }),
  (finding, dim) => agent(`Adversarially verify this ${dim} finding: ${JSON.stringify(finding)}. Confirm only what holds.`, { phase: 'Verify', label: dim, schema: verdictSchema }),
);

const confirmed = results.filter(Boolean).filter((v) => v.confirmed);
return confirmed;
```

### Loop until dry

```js
export const meta = {
  name: 'drain-queue',
  description: 'Keep processing batches until none remain or the budget is exhausted',
  phases: [{ title: 'Process', detail: 'One agent per remaining item' }],
};

let remaining = args.items;
const done = [];

while (remaining.length > 0 && (budget.total === null || budget.remaining() > 0)) {
  const batch = await parallel(
    remaining.map((item) => () => agent(`Process ${item}`, { phase: 'Process', label: String(item) })),
  );
  const processed = batch.filter(Boolean);
  done.push(...processed);
  if (processed.length === 0) {
    log(`Stopping: ${remaining.length} item(s) could not be processed`);
    break;
  }
  remaining = [];
}

return done;
```
