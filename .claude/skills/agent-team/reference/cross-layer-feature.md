# Cross-layer feature

**Use when** a feature spans frontend, backend, and tests, and each layer can be built in parallel because the contract between them is already agreed. Teammates own **disjoint files** to avoid overwrite conflicts.

## Spawn prompt

```text
Create an agent team to implement <FEATURE>. Spawn three teammates:
- backend: owns src/api/**, src/db/**. Implements the endpoint + schema changes.
- frontend: owns src/components/**, src/pages/**. Builds the UI against the API contract.
- tests: owns tests/**. Writes integration tests covering the new flow.
Use Sonnet for each teammate. The API contract is: <PASTE THE CONTRACT>.
Each teammate must not edit files outside its scope. Require plan approval from
backend before they make any database schema changes.
Coordinate via the shared task list. Frontend and tests depend on backend
publishing the endpoint shape.
```

## Why this works

- **Disjoint file ownership** — no overwrites because each teammate has a directory it owns
- **Contract first** — the spawn prompt pins the API shape so frontend doesn't have to wait blocked on backend's decisions
- **Task dependencies** encoded in the prompt — the lead creates frontend and tests tasks with backend tasks as deps; they auto-unblock
- **Plan approval gates schema changes** — the lead reviews migrations before they happen

## Sequencing options

If your contract isn't fully nailed down:

```text
... First, have all three teammates discuss the API contract via the mailbox until
they converge. The lead must approve the agreed contract before any teammate
starts implementing.
```

## Watch for

- A teammate touching files outside its scope — the lead should reject and reassign
- Tests teammate finishing first and going idle — give it more work (edge cases, performance regression tests) or shut it down
- Backend teammate's plan getting approved without test coverage requirements — bias the lead up front: "only approve backend plans that ship with a migration rollback script"

## After

- Each teammate sends an idle notification when its work is done
- Lead synthesises a single PR description and shuts down teammates
- Clean up the team
