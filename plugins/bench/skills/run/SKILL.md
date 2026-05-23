---
name: run
description: Benchmarks a skill or sub-agent by executing colocated `tests/*.md` prompt files in parallel sub-agents, capturing wall-clock timing and raw outputs, then writing a markdown report under `runs/<artifact>/<timestamp>.md`. Use when the user types `/bench:run`, says `run benchmarks`, `benchmark a skill`, `benchmark a sub-agent`, `test a skill with prompts`, `compare skill outputs`, or wants to see how long a skill takes. Spawns one `bench-runner` sub-agent per selected test in a SINGLE Agent tool batch (parallel execution), records per-test elapsed milliseconds, and prints a summary table plus the absolute report path inline.
argument-hint: (none — interactive via AskUserQuestion)
allowed-tools: Glob, Read, Write, Bash, AskUserQuestion, Agent
---

# run

Discover prompt-based tests colocated with skills and sub-agents, let the user pick which ones to execute, run them in parallel via `bench-runner`, and persist a timestamped markdown report.

## Prerequisites

- Repo root must contain a `plugins/` tree following the marketplace layout.
- The `bench-runner` sub-agent (`plugins/bench/agents/bench-runner.md`) must be installed — it is the only executor used here.
- `runs/` is gitignored; the skill writes report files there freely.

## Steps

### 1. Discover tests

Glob from the repo root:

```
plugins/**/tests/*.md
```

For each match, derive the parent artifact from the path:

- `plugins/<plugin>/skills/<name>/tests/<test>.md` → artifact `<plugin>:<name>` (kind: skill)
- `plugins/<plugin>/agents/<name>/tests/<test>.md` → artifact `<plugin>:<name>` (kind: subagent)

Group test files by artifact and keep the kind for display.

If zero tests are found, stop with a short message that points the user at [reference/test-format.md](./reference/test-format.md) and shows the canonical test paths. Do not create anything.

### 2. Ask which artifact

Use `AskUserQuestion` with one question. Each option label is the artifact (`<plugin>:<name>`), description is `<kind> — <N> test(s)`.

- If 4 or fewer artifacts have tests, list them all as options.
- If more than 4, list every artifact in the question text, then expose the 4 most-tested artifacts as options plus a final `Other (specify)` option. When the user picks `Other`, re-prompt with the next batch of artifacts as options. Repeat until one is selected.

### 3. Ask which tests

For the chosen artifact, use `AskUserQuestion` with `multiSelect: true`:

- First option: `All tests` — selects every test for the artifact.
- One option per test file. Label = the test's `name:` from frontmatter (fallback: filename without extension). Description = the test's `description:` from frontmatter.

If the user selects `All tests` plus individual entries, treat the selection as all tests (no duplicates).

### 4. Run tests in PARALLEL

This step is REQUIRED to run all selected tests concurrently.

For each selected test:

- Read the test file. Extract the `prompt:` frontmatter field if present; otherwise treat the entire body (everything after the closing `---`) as the prompt. Body content beyond `prompt:` is appended as additional context.
- Record `Date.now()` (mentally) right before dispatch as `start_ms`.

Then, in a SINGLE assistant message, emit one `Agent` tool call per selected test. All calls go in the same message so the runtime executes them in parallel. Each call targets the `bench-runner` sub-agent with this prompt shape:

```
You are executing benchmark test `<test-name>` for artifact `<artifact>`.
Execute the prompt below and return raw output only.

---
<prompt verbatim>
```

When each sub-agent returns, record `end_ms` and compute `elapsed_ms = end_ms - start_ms`. Capture the raw output verbatim and the status (`ok` if the sub-agent returned, `error` if it failed).

See the `core:subagent` skill or the Claude Code Agent tool docs if you need a refresher on batching Agent calls for parallel execution.

### 5. Write the report

Compute `safe_artifact = artifact.replace(':', '-')` and `timestamp = YYYY-MM-DDTHH-MM-SS` (colons replaced with hyphens for filesystem safety).

Ensure the directory exists:

```bash
mkdir -p runs/<safe_artifact>
```

Write the report to `runs/<safe_artifact>/<timestamp>.md` using the structure in [reference/output-format.md](./reference/output-format.md).

### 6. Print the summary inline

Print the Markdown summary table from the report inline in the conversation. End with the absolute path of the report file on its own line so the user can open it directly.

## Test format

Tests live colocated with the artifact they exercise:

- Skill: `plugins/<plugin>/skills/<name>/tests/<test-name>.md`
- Sub-agent: `plugins/<plugin>/agents/<name>/tests/<test-name>.md`

Minimal frontmatter:

```yaml
---
name: <test-name>
description: <one-line — what this test exercises>
---
```

Body: the prompt to run, free-form markdown. May include extra context/notes appended after the prompt.

Full contract and a worked example in [reference/test-format.md](./reference/test-format.md) and [examples/sample-test.md](./examples/sample-test.md).

## Hard rules

- ALWAYS dispatch all selected tests in a SINGLE assistant message with one `Agent` call each — parallel execution is REQUIRED, never serialize.
- Use the `bench-runner` sub-agent as the sole executor. Do not inline-run prompts in the current context.
- Never modify the test files; read-only.
- Never touch `.claude-plugin/marketplace.json` or any plugin manifest from this skill.
- Write reports only under `runs/<safe-artifact>/`. Do not write anywhere else in the repo.
- Replace `:` with `-` in any path segment derived from `<artifact>`.

## Reference

- [reference/test-format.md](./reference/test-format.md) — full test-file contract and discovery rules
- [reference/output-format.md](./reference/output-format.md) — exact markdown structure for the report file
- [examples/sample-test.md](./examples/sample-test.md) — a complete `tests/*.md` example
