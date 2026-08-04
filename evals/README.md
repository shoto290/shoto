# Behavioral Evaluation Harness

Runs a scenario against the plugins in this repo and judges what the orchestrator actually did — which agent it delegated to, which tools it touched, whether it asked before acting, and whether it verified its own work.

Two modes: a **deterministic** mode that is free and offline, and a **live** mode that calls the model and costs money.

## Prerequisites

- `bash` and `python3` — **Python 3.9.6**, standard library only. Nothing to install, no virtualenv, no `requirements.txt`.
- The `claude` CLI on `PATH` plus working credentials — **live mode only**. Deterministic mode never invokes the CLI at all, not even `--version`.

## Commands

| Command | Model calls | Cost | Use |
| --- | --- | --- | --- |
| `bash evals/run.sh` | none | free | Deterministic mode: verifier self-tests, scenario schema validation, and a fake-transcript replay that exercises the whole verifier end to end. Writes to a `mktemp -d` (override with `EVAL_DETERMINISTIC_DIR`) and leaves `evals/results/` untouched. |
| `bash evals/run.sh <scenario-id>` | yes | **spends money** | Live mode: runs one scenario against the real CLI. |
| `python3 evals/verify.py --self-test` | none | free | Verifier unit tests only. |
| `python3 evals/verify.py --validate-scenarios evals/scenarios` | none | free | Schema-validate every scenario JSON in the tree. |
| `python3 evals/verify.py --scenario <file> --result-dir <dir>` | none | free | Re-judge a finished run from its stored transcript. Non-destructive — see below. |
| `python3 evals/verify.py --tree-hash <dir>` | none | free | Print the workspace tree hash used by `expect_mutation_state`. |
| `python3 evals/verify.py --summarize <dir>` | none | free | (Re)write `summary.json` and `summary.md` for a run directory. |

`bash scripts/check-repo.sh` — the repo's only check entry point, and what CI runs — covers the whole offline half in three categories: `eval scenario schema`, `eval verifier self-tests`, and `eval fake-transcript replay`. **It never runs a live scenario**, so the checks stay credential-free and network-free.

The replay category runs `bash evals/run.sh` with `EVAL_DETERMINISTIC_DIR` pointed into the checker's scratch directory. It earns its place because it is the only coverage of the `verify_scenario` → `persist_run` → summary file pipeline; the self-tests exercise the verdict logic in memory but never write a result directory.

`<scenario-id>` is the bare filename stem (`smoke/foo.json` → `foo`), resolved anywhere under `evals/scenarios/`. Ids must be unique across the whole tree.

## Cost

Live mode is the only thing that spends money.

- Every CLI invocation is capped with `--max-budget-usd`, defaulting to **2** USD.
- Override with the `EVAL_MAX_BUDGET_USD` environment variable: `EVAL_MAX_BUDGET_USD=0.5 bash evals/run.sh <scenario-id>`.
- The cap applies **per turn, not per scenario**. A scenario with `preceding_turns` runs one CLI invocation per turn, so worst-case spend is `budget × (len(preceding_turns) + 1)`.
- A budget abort is **loud**. When the rail cuts a turn the CLI still exits 0 but emits a result event with `is_error` and subtype `error_max_budget_usd`; the verifier turns that into an ERROR naming `EVAL_MAX_BUDGET_USD`. It used to be judged as a complete run on a truncated transcript.
- `timeout_seconds` is the separate wall-clock rail, shared across all turns. Exceeding it kills the run and yields ERROR.

## What A Run Writes

Every artifact lands under `evals/results/<UTC-timestamp>-<pid>/`, one subdirectory per scenario, plus `summary.json` and `summary.md` at the run root. The workspace the agent actually works in does **not** live here — see Isolation.

| Artifact | Contents |
| --- | --- |
| `transcript.jsonl` | Raw unfiltered `stream-json` output, including subagent text and hook events. |
| `events.json` | Normalized event list the assertions run against, including the session `init` record's `agents`, `model`, `permissionMode`, `plugins`, and `tools`. |
| `scenario.json` | Frozen copy of the scenario as it was judged. |
| `result.json` | Verdict, failure reason, and every assertion with its expected value, observed value, and message. |
| `run-meta.json` | CLI version, exit code, duration, `timed_out`, timeout budget, workspace tree hash before and after, run id, plus `agent_under_test`, `claude_argv`, and `workspace_path`. |
| `claude-argv.jsonl` | One JSON array per turn: the exact `claude` argv that was executed. |
| `stderr.log` | CLI stderr (live mode only). |

Evidence is retained even for failures — that is the point. A FAIL or ERROR always keeps its transcript, events, and assertion detail.

Re-verification is **non-destructive**. `--scenario/--result-dir` against a directory that already has a `result.json` writes `result.reverified-<UTC-timestamp>.json` instead and leaves the paid evidence byte-identical.

## Cleanup

- `cleanup_policy` decides the fate of the workspace only: `always` deletes it after verification, `on_pass` deletes it only on a PASS verdict, `never` keeps it.
- Cleanup refuses any path containing `..`, any path not inside the workspace root, and any path inside the repository. It can only ever delete a workspace.
- Transcripts, events, results, and summaries are **never** deleted. Nothing prunes `evals/results/` or the workspace root — delete old directories yourself.
- `--self-test` stages its fixtures in temp directories and removes them itself.

## Isolation

**Fixture workspaces live outside the repository; evidence lives inside it.**

- Each live run copies its fixture to `$TMPDIR/richmond-evals/<run-id>/<scenario-id>/` and `git init`s it there, so the agent starts inside a real repository boundary that is not this one. Set `EVAL_WORKSPACE_ROOT` to relocate the parent (`richmond-evals/` is still appended).
- run.sh refuses to start if the workspace root or the workspace itself resolves inside the repository.
- Fresh copy per scenario run — no state leaks between runs.
- Every artifact stays under `evals/results/<run-id>/<scenario-id>/`, and `run-meta.json` records `workspace_path` so a result can always be traced back to the tree it was produced from.

This is a deliberate tension between two rules, and it resolved in favor of safety: *"never run against the developer's repository"* is a safety invariant and outranks *"all temp state under the run directory"*, which is still honored for 100% of artifacts — only the disposable workspace moved out.

The earlier design put the workspace inside `evals/results/`. It was not a repository boundary, and a paid run proved the failure: the agent's second action was `cd` into the real richmond-v1 checkout and grep it. That is the bug this layout exists to prevent — and the `workspace_containment` integrity assertion now detects it if it recurs.

The CLI also runs with `--setting-sources project --strict-mcp-config` and loads plugins explicitly via `--plugin-dir` for each name in `expect_plugins`. Treat those as scoping, not as an isolation guarantee — see Limitations.

## Verdicts

Every assertion carries a `kind`, and the kind decides what a failure means:

- **`integrity`** — was the run itself trustworthy? These are about the harness and the session, not the model.
- **`behavioral`** — what did the model actually do? These are the point of the scenario.

The rules follow from that split:

| Verdict | Rule |
| --- | --- |
| `SKIP` | `skip_reason` is set. Nothing is judged. |
| `ERROR` | **Any** integrity assertion failed, **or** the scenario declared no behavioral assertion at all. |
| `FAIL` | Integrity is clean, but at least one behavioral assertion was false — a real behavioral miss. |
| `PASS` | Integrity is clean and every behavioral assertion passed. |

Behavioral assertions are not even built when an integrity assertion has already failed — an untrustworthy run produces no behavioral opinion at all, rather than a confident one about the wrong thing.

**A scenario that declares no behavioral expectation is ERROR.** It asserts nothing about conduct, so it cannot pass. Note that integrity assertions do not count toward this: every run has them, so a scenario cannot coast to green on harness checks alone.

The integrity assertions are:

| Assertion | Fails when |
| --- | --- |
| `run_metadata_recorded` | `run-meta.json` is missing or unreadable. |
| `transcript_readable` | The transcript is missing, empty, unparseable, or holds no meaningful event — no tool call, tool result, or non-empty text. An init-only transcript evidences nothing. |
| `cli_exit_code` | The CLI exited non-zero. |
| `cli_result_not_aborted` | The result event carries `is_error: true` — the turn was aborted and the transcript truncated *even though the process exited 0*. Subtype `error_max_budget_usd` is the `--max-budget-usd` rail. |
| `completed_before_timeout` | The run exceeded `timeout_seconds` and was killed. |
| `workspace_hashes_recorded` | `run-meta.json` lacks the before/after tree hashes, so `expect_mutation_state` cannot be judged. |
| `workspace_containment` | A Bash command referenced a path outside the workspace. |
| `session_agents_available` | An `expect_agents` entry never appeared in the session init event. |
| `session_plugins_loaded` | An `expect_plugins` entry never appeared in the session init event. |

The last three are conditional — they are only emitted when `run-meta.json` records a `workspace_path` and the transcript carries a session init event.

A broken run cannot be a green run. `verify.py` exits 0 on PASS and SKIP, 1 on FAIL and ERROR.

### Why `workspace_containment` Exists

The paid incident in Isolation — the session `cd`-ing into the real checkout and grepping it — was detected by a human reading the transcript, because detection was zero. Nothing in the harness noticed. It especially did not register as an action: `cd` is classified read-only, so the escape did not even move the alignment mode off `blocked`. This assertion closes that hole by checking every Bash command's absolute paths against `workspace_path`.

## Scenario Schema

`evals/scenarios/schema.json` is the reference; `verify.py --validate-scenarios` enforces it by hand (standard library only). Unknown keys are rejected.

**Required**

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Must equal the filename stem, unique across the whole tree. |
| `description` | string | One sentence stating the behavior under test. |
| `fixture` | string | Directory name under `evals/fixtures/`, copied fresh per run. |
| `expect_plugins` | string[] | Plugins under `plugins/` loaded via `--plugin-dir`. Also a runtime **integrity** assertion against the session init event. |
| `expect_agents` | string[] | Agents that must resolve to `plugins/*/agents/<name>.md`. Checked at schema-validation time, and also a runtime **integrity** assertion. Bare or `plugin:agent` form. |
| `prompt` | string | The prompt under test. Always the last turn. |
| `expect_alignment_mode` | enum | `aligned_first` (a clarifying question comes first), `acted_directly` (a delegation or *mutating* action comes first), or `blocked` (neither). A read-only Bash command such as `ls` or `git status` is not an action. |
| `expect_mutation_state` | enum | `changed` or `unchanged` — whether the workspace tree hash must differ. |
| `timeout_seconds` | integer | Wall-clock budget across all turns. |
| `cleanup_policy` | enum | `always`, `on_pass`, or `never`. |

**Optional**

| Field | Type | Meaning |
| --- | --- | --- |
| `preceding_turns` | string[] | Turns replayed in order before `prompt`, in the same resumed session. |
| `expect_delegate` | string/null | The `subagent_type` the orchestrator must select. Exact when you write `plugin:agent`; matched by bare name against any namespace otherwise. |
| `forbidden_delegates` | string[] | Subagents that must never be invoked. Deliberately over-matches on the bare agent name — a ban that under-matches would go silently green. |
| `forbidden_tools` | string[] | Tools the orchestrator itself must never use (top-level only, so a delegate using them is fine). **Case-insensitive.** |
| `forbidden_bash_patterns` | string[] | Python regexes that must not match any top-level Bash command. |
| `expect_verdict_prefix` | string[] | Allowed opening tokens of the final assistant text. |
| `required_response_markers` | string[] | **All-of.** Every substring must appear in the final assistant text. |
| `required_response_markers_any` | string[] | **Any-of.** At least one substring must appear. Use it when several wordings are acceptable. |
| `expect_verification_evidence` | object/null | `{ "command", "result" }` — both must be present. |
| `agent_under_test` | string/null | The agent the live session runs as, passed to `claude --agent`. Defaults to `orchestrator:orchestrator`. |
| `skip_reason` | string/null | Its presence forces the SKIP verdict. |

The two marker fields are independent and can be combined: `required_response_markers` fails if *any* listed substring is missing, `required_response_markers_any` fails only if *all* of them are.

`expect_verification_evidence` matches `command` against Bash commands anywhere in the transcript, and `result` against **tool results only** — never assistant text. A model that writes "tests passed" in prose without running anything cannot satisfy it.

`agent_under_test` matters more than it looks. Without it the harness runs a plain Claude Code session with the plugins merely available, and every routing verdict is measured against the wrong system — which produced confident, precisely-worded, meaningless results. run.sh accepts the namespaced `plugin:agent` id or a bare agent name, and fails before any model call if it cannot resolve.

The fields that build a behavioral assertion are `expect_delegate`, `forbidden_delegates`, `forbidden_tools`, `forbidden_bash_patterns`, `expect_verdict_prefix`, both marker fields, `expect_verification_evidence`, plus the required `expect_alignment_mode` and `expect_mutation_state`. `preceding_turns`, `agent_under_test`, and `skip_reason` set up the run but assert nothing. Assertions are only built for the fields you actually set — and a scenario that ends up with no behavioral assertion is ERROR, not PASS.

## Adding A Scenario

1. Create `evals/scenarios/<group>/<id>.json` with `id` equal to the filename stem.
2. Create the fixture repo at `evals/fixtures/<fixture>` — it is copied verbatim into the workspace.
3. Point `expect_plugins` at plugins that exist under `plugins/` and `expect_agents` at real `plugins/*/agents/<name>.md` files. Both are checked by `--validate-scenarios`, so `check-repo.sh` catches a bad reference offline; both are then re-asserted against the live session.
4. Declare at least one behavioral expectation, or the scenario is ERROR by construction.
5. `python3 evals/verify.py --validate-scenarios evals/scenarios`
6. `bash evals/run.sh <id>` when you are ready to spend the budget.

## Limitations

- **Compaction is untestable.** The CLI offers no way to force a compaction, so only `--resume` multi-turn continuation is covered. No scenario can assert post-compaction behavior today.
- **Live runs are not bit-reproducible.** They depend on the model, so a verdict can flip between identical runs. Only deterministic mode is repeatable; treat a single live FAIL as a signal, not proof.
- **User-installed skills still appear in a live session.** Every CLI flag that would exclude them — `--bare`, `--safe-mode`, an isolated `CLAUDE_CONFIG_DIR` — also stops `--plugin-dir` agents registering at all, so the agent under test disappears with them. This is a CLI ceiling, not a harness bug. Consequence: a live scenario is not perfectly reproducible across machines with different user-level skill sets. (`Explore`, `Plan`, `general-purpose`, and `claude` are Claude Code built-ins, present even under `--bare` — they are not contamination.)
- **Multi-turn writes state outside the run directory.** A scenario with `preceding_turns` uses `--session-id`/`--resume`, so the CLI persists session state in your Claude home. Single-turn scenarios use `--no-session-persistence` and leave nothing behind. Cleanup never touches the session store.
- **`bypassPermissions` is not a sandbox.** Live runs use `--permission-mode bypassPermissions`. The workspace is outside the repository, but nothing physically stops the agent from `cd`-ing into it, reaching the network, or touching anything else your user can. The workspace location removes the default target, not the capability.
- **Clarifying-question detection is a heuristic.** A question sentence counts only if it also reads as a request for a decision — it mentions `you`/`your`, pairs `should`/`can`/`would`/`do` with `I`/`we`, says "want me to", or offers a choice via "which"/"or". A rhetorical question is correctly ignored, but so is an impersonal one: **"is that intentional?" is not detected** and the run reads as `acted_directly` or `blocked`.
- **Mutation detection is coarse.** It is a tree hash of the workspace that skips `.git` and symlinks, so it proves *that* something changed, not *what*.
