// Skeleton for a new dynamic workflow. Replace the placeholders and delete
// what you do not use. JavaScript only. The script only coordinates agents —
// it must not touch the filesystem or shell, and must not ask the user anything
// (all AskUserQuestion lives in the wrapper skill).

// meta MUST be a pure object literal: no variables, calls, or spreads.
// Each phases title MUST match a phase() call below, and vice versa.
export const meta = {
  name: 'NAME',                              // kebab-case, matches the filename
  description: 'WHAT THIS WORKFLOW DOES',
  whenToUse: 'WHEN TO INVOKE IT',           // optional
  phases: [
    { title: 'Plan', detail: 'Decompose the input into work items' },
    { title: 'Work', detail: 'One agent per item' },
    { title: 'Synthesize', detail: 'Merge results into the final return' },
  ],
  // model: 'sonnet',                        // optional default model for the run
}

// ─── Schemas (JSON Schema) for structured stages ───
const PLAN_SCHEMA = {
  type: 'object', required: ['items'],
  properties: {
    items: {
      type: 'array', minItems: 1, items: {
        type: 'object', required: ['id', 'instruction'],
        properties: { id: { type: 'string' }, instruction: { type: 'string' } },
      },
    },
  },
}

const WORK_SCHEMA = {
  type: 'object', required: ['id', 'result'],
  properties: { id: { type: 'string' }, result: { type: 'string' } },
}

const FINAL_SCHEMA = {
  type: 'object', required: ['summary'],
  properties: {
    summary: { type: 'string' },
    items: { type: 'array', items: { type: 'object' } },
  },
}

// ─── Plan: one agent decomposes the input (from args) into work items ───
phase('Plan')
const INPUT = (typeof args === 'string' && args.trim()) || ''
if (!INPUT) return { error: 'No input provided. Pass it as args.' }

const plan = await agent(
  '## Planner\n\nInput:\n' + INPUT + '\n\nDecompose into discrete work items.\nStructured output only.',
  { label: 'plan', phase: 'Plan', schema: PLAN_SCHEMA }
)
if (!plan) return { error: 'plan agent returned nothing' }
log('Planned ' + plan.items.length + ' items')

// ─── Work: fan out one agent per item ───
// Prefer pipeline() (no barrier) when each item can flow independently.
// Use parallel() only when the next stage needs ALL results at once.
const worked = await pipeline(
  plan.items,
  item => agent(
    '## Worker: ' + item.id + '\n\n' + item.instruction + '\n\nStructured output only.',
    { label: 'work:' + item.id, phase: 'Work', schema: WORK_SCHEMA }
  ),
)
const results = worked.filter(Boolean)
log('Completed ' + results.length + '/' + plan.items.length + ' items')

// Barrier alternative when synthesis needs everything assembled first:
// const results = (await parallel(
//   plan.items.map(item => () => agent(/* ... */, { schema: WORK_SCHEMA }))
// )).filter(Boolean)

// ─── Synthesize: one agent merges results into the final return ───
phase('Synthesize')
const final = await agent(
  '## Synthesizer\n\nMerge these results into a final answer.\n\n' +
  JSON.stringify(results) + '\n\nStructured output only.',
  { label: 'synthesize', phase: 'Synthesize', schema: FINAL_SCHEMA }
)
if (!final) return { input: INPUT, summary: 'Synthesis skipped.', items: results }

// The return is the ONLY thing that reaches Claude's context.
return { input: INPUT, ...final }
