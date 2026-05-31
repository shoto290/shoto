# Workflow Constraints and Meta-Facts

## Hard constraints

Every workflow script MUST respect these. `workflow-smith` enforces them; this skill states them to the user.

- **No mid-run user input.** ALL `AskUserQuestion` — clarification and approval gates — lives in the **wrapper skill**, never in the `.workflow.js`. A background run cannot block on the user. For sign-off between stages, split the work into separate workflows the user runs in sequence.
- **No direct filesystem or shell access from the script.** The script only coordinates. Only **spawned agents** touch files or run shell commands. The orchestration code must not read, write, or exec.
- **Concurrency cap: ≤16 concurrent agents.** A `parallel()` or `pipeline()` fan-out wider than 16 is throttled by the runtime; design within the cap.
- **Run cap: 1000 agents maximum per run.** A workflow that would spawn more must bound its fan-out (e.g. slice the work items).
- **JavaScript only — not TypeScript.** No type annotations, no `.ts` features.
- **`meta` is a pure object literal.** No variables, calls, or spreads inside it.
- **No nondeterminism in the script.** No `Date.now()`, no `Math.random()`, no `new Date()`. Nondeterministic values must come from agents if needed.
- **Spawned subagents run in `acceptEdits` mode**, inherit the tool allowlist, and use the session model unless a stage routes to another via `agent(..., { model })`.
- **Prefer `pipeline()` over a `parallel()` barrier** unless a stage genuinely needs all prior results at once.
- **`workflow()` sub-workflows nest one level deep only.**

## Meta-facts (availability and control)

Synced with code.claude.com/docs/en/workflows.

- **Research preview.** Requires Claude Code **v2.1.154+**.
- **Available on:** paid plans, the Claude API, Amazon Bedrock, Google Vertex, and Microsoft Foundry.
- **Disable** via any of:
  - the `/config` menu → "Dynamic workflows",
  - `"disableWorkflows": true` in settings,
  - the `CLAUDE_CODE_DISABLE_WORKFLOWS=1` environment variable.
- **Triggering:** the `workflow` keyword in a prompt, or ultracode (`/effort ultracode`). A wrapper skill firing is itself the opt-in — it does not need the keyword.
- **Saving a run's script:** from the `/workflows` view, press `s` to save the script that a run used.
