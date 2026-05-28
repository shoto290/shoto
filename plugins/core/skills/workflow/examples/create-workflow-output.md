# Example: fan-out audit workflow

A small workflow that audits each changed file independently, then verifies the flagged files before reporting. Scoped to the files passed in `args.files` so the run stays bounded.

```js
export const meta = {
  name: 'audit-changed-files',
  description: 'Audit each changed file for risky patterns, then verify the flagged ones',
  whenToUse: 'Quick risk pass over a small set of changed files',
  phases: [
    { title: 'Audit', detail: 'One auditor per changed file' },
    { title: 'Verify', detail: 'Re-check each flagged file adversarially' },
  ],
  model: 'sonnet',
};

const flagSchema = {
  type: 'object',
  properties: { flagged: { type: 'boolean' }, note: { type: 'string' } },
  required: ['flagged'],
};

const files = args.files;

const results = await pipeline(
  files,
  (file) => agent(`Audit ${file} for risky patterns. Return whether it is flagged.`, { phase: 'Audit', label: file, schema: flagSchema }),
  (audit, file) => {
    if (!audit.flagged) return audit;
    return agent(`Adversarially verify the concern in ${file}: ${audit.note}. Confirm only what holds.`, { phase: 'Verify', label: file, schema: flagSchema });
  },
);

const confirmed = results.filter(Boolean).filter((r) => r.flagged);
log(`Confirmed ${confirmed.length} of ${files.length} file(s)`);
return confirmed;
```

**How it was scoped:** the fan-out unit is `args.files`, so the caller controls the surface and the run stays small. Unflagged files short-circuit past the verify stage, keeping token spend proportional to risk.
