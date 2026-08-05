#!/usr/bin/env bash
set -euo pipefail

EVALS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$EVALS_DIR/.." && pwd -P)"
SCENARIOS_DIR="$EVALS_DIR/scenarios"
FIXTURES_DIR="$EVALS_DIR/fixtures"
RESULTS_DIR="$EVALS_DIR/results"
VERIFY="$EVALS_DIR/verify.py"
CONTROL_SUBDIR="controls"
MAX_BUDGET_USD="${EVAL_MAX_BUDGET_USD:-2}"
DEFAULT_AGENT_UNDER_TEST="orchestrator:orchestrator"
WORKSPACE_ROOT="${EVAL_WORKSPACE_ROOT:-${TMPDIR:-/tmp}}"
WORKSPACE_ROOT="${WORKSPACE_ROOT%/}/richmond-evals"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"

fail() {
  printf 'EVAL ERROR: %s\n' "$1" >&2
  exit 1
}

physical_path() {
  local candidate=$1
  local suffix=""
  local parent
  while [ ! -d "$candidate" ]; do
    parent="$(dirname "$candidate")"
    [ "$parent" != "$candidate" ] || break
    suffix="/$(basename "$candidate")$suffix"
    candidate=$parent
  done
  local base
  base="$(cd "$candidate" 2>/dev/null && pwd -P)" || base=$candidate
  printf '%s%s\n' "${base%/}" "$suffix"
}

require_inside() {
  local candidate=$1
  local parent=$2
  case "$candidate" in
    *../* | */.. ) fail "$candidate contains a '..' component -> refusing to touch it; harness paths must be fully resolved" ;;
  esac
  local resolved_candidate resolved_parent
  resolved_candidate="$(physical_path "$candidate")"
  resolved_parent="$(physical_path "$parent")"
  case "$resolved_candidate" in
    "$resolved_parent"/?*) return 0 ;;
  esac
  fail "$candidate resolves to $resolved_candidate, which is not inside $resolved_parent -> refusing to touch it"
}

require_outside_repository() {
  local candidate
  candidate="$(physical_path "$1")"
  case "$candidate" in
    "$REPO_ROOT"/* | "$REPO_ROOT")
      fail "$1 resolves to $candidate, inside $REPO_ROOT -> refusing to run; the fixture workspace must never live inside the repository under test, and a symlink pointing back into it counts as inside"
      ;;
  esac
}

resolve_scenario_file() {
  python3 - "$EVALS_DIR" "$SCENARIOS_DIR" "$1" <<'PYTHON'
import sys

sys.path.insert(0, sys.argv[1])
import verify

path, error = verify.resolve_scenario(sys.argv[2], sys.argv[3])
if error:
    sys.stdout.write(error)
    sys.exit(1)
sys.stdout.write(path)
PYTHON
}

resolve_target() {
  python3 - "$EVALS_DIR" "$SCENARIOS_DIR" "$1" <<'PYTHON'
import sys

sys.path.insert(0, sys.argv[1])
import verify

kind, ids, error = verify.resolve_target(sys.argv[2], sys.argv[3])
if error:
    sys.stdout.write(error)
    sys.exit(1)
sys.stdout.write("\n".join([kind] + ids))
PYTHON
}

result_verdict() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["verdict"])' \
    "$1/result.json" 2>/dev/null || printf 'ERROR\n'
}

scenario_string() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get(sys.argv[2]) or "")' "$1" "$2"
}

scenario_list() {
  python3 -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1], encoding="utf-8")).get(sys.argv[2]) or []))' "$1" "$2"
}

scenario_turns() {
  python3 - "$1" <<'PYTHON'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    scenario = json.load(handle)
turns = list(scenario.get("preceding_turns") or [])
turns.append(scenario["prompt"])
sys.stdout.write("\0".join(turns))
sys.stdout.write("\0")
PYTHON
}

available_agent_ids() {
  python3 - "$EVALS_DIR" <<'PYTHON'
import sys

sys.path.insert(0, sys.argv[1])
import verify

sys.stdout.write("\n".join(verify.repository_agent_ids() or []) + "\n")
PYTHON
}

resolve_agent_under_test() {
  local requested=$1
  local candidate
  while IFS= read -r candidate; do
    if [ "$candidate" = "$requested" ] || [ "${candidate#*:}" = "$requested" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(available_agent_ids)
  return 1
}

record_argv() {
  local target=$1
  shift
  python3 - "$target" "$@" <<'PYTHON'
import json
import sys

with open(sys.argv[1], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[2:]) + "\n")
PYTHON
}

tree_hash() {
  python3 "$VERIFY" --tree-hash "$1"
}

write_run_meta() {
  python3 - "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10:-}" "${11:-}" "${12:-}" <<'PYTHON'
import json
import os
import sys

(path, version, exit_code, duration, timed_out, budget, before, after, run_id, agent,
 argv_log, workspace) = sys.argv[1:13]
invocations = []
if argv_log and os.path.isfile(argv_log):
    with open(argv_log, encoding="utf-8") as handle:
        invocations = [json.loads(line) for line in handle if line.strip()]
meta = {
    "cli_version": version,
    "cli_exit_code": int(exit_code),
    "duration_seconds": float(duration),
    "timed_out": timed_out == "true",
    "timeout_seconds": int(budget),
    "tree_hash_before": before,
    "tree_hash_after": after,
    "run_id": run_id,
    "agent_under_test": agent,
    "claude_argv": invocations,
    "workspace_path": workspace,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(meta, handle, indent=2, sort_keys=True)
    handle.write("\n")
PYTHON
}

write_summary() {
  python3 "$VERIFY" --summarize "$1"
}

detect_cli_version() {
  if command -v claude >/dev/null 2>&1; then
    claude --version 2>/dev/null | head -1
  else
    printf 'not-installed\n'
  fi
}

run_turn() {
  local workspace=$1
  local budget=$2
  local stdout_file=$3
  local stderr_file=$4
  shift 4
  local code=0
  ( cd "$workspace" && exec claude "$@" ) >>"$stdout_file" 2>>"$stderr_file" &
  local pid=$!
  local waited=0
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$waited" -ge "$budget" ]; then
      kill -TERM "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 124
    fi
    sleep 1
    waited=$((waited + 1))
  done
  wait "$pid" || code=$?
  return "$code"
}

replay_declared_verdict() {
  local path="$1/expected-verdict"
  if [ -f "$path" ]; then
    tr -d '[:space:]' <"$path"
  else
    printf 'PASS'
  fi
}

replay_scenario_file() {
  local candidate
  local found=""
  for candidate in "$1"/*.json; do
    [ -f "$candidate" ] || continue
    [ -z "$found" ] || return 1
    found="$candidate"
  done
  [ -n "$found" ] || return 1
  printf '%s\n' "$found"
}

replay_one_fixture() {
  local run_dir=$1
  local source_dir=$2
  local declared=$3
  local scenario_file=$4
  local name
  name="$(basename "$source_dir")"
  local target="$run_dir/$name"
  if [ "$declared" = "FAIL" ]; then
    target="$run_dir/$CONTROL_SUBDIR/$name"
  fi
  mkdir -p "$target"
  cp "$scenario_file" "$target/"
  cp "$source_dir/transcript.jsonl" "$target/"
  write_run_meta "$target/run-meta.json" "replay" 0 0 false 120 "tree-before" "tree-after" \
    "$RUN_ID" "orchestrator:orchestrator" "" "$target/workspace"
  printf -- '-- %s (expected-verdict: %s) --\n' "$name" "$declared"
  python3 "$VERIFY" --scenario "$target/$(basename "$scenario_file")" --result-dir "$target" || true
  local verdict
  verdict="$(result_verdict "$target")"
  if [ "$verdict" = "$declared" ]; then
    printf '  matched: the verifier returned the declared %s\n' "$declared"
    return 0
  fi
  printf '  MISMATCH: the verifier returned %s but %s/expected-verdict declares %s -> a replay fixture must produce exactly the verdict it declares; a fixture that declares FAIL and passes means the assertions it guards stopped detecting anything, so no green suite is meaningful until this matches again\n' \
    "$verdict" "$source_dir" "$declared"
  return 1
}

replay_fixtures() {
  local run_dir=$1
  local status=0
  local total=0
  local controls=0
  local source_dir name declared scenario_file
  for source_dir in "$FIXTURES_DIR"/replay*/; do
    source_dir="${source_dir%/}"
    [ -d "$source_dir" ] || continue
    total=$((total + 1))
    name="$(basename "$source_dir")"
    declared="$(replay_declared_verdict "$source_dir")"
    case "$declared" in
      PASS | FAIL) ;;
      *)
        printf -- '-- %s --\n  ERROR: expected-verdict reads %s -> write exactly PASS or FAIL, or delete the file to declare PASS\n' \
          "$name" "$declared"
        status=1
        continue
        ;;
    esac
    [ "$declared" != "FAIL" ] || controls=$((controls + 1))
    if ! scenario_file="$(replay_scenario_file "$source_dir")"; then
      printf -- '-- %s --\n  ERROR: the fixture must hold exactly one scenario JSON next to transcript.jsonl\n' "$name"
      status=1
      continue
    fi
    if [ ! -f "$source_dir/transcript.jsonl" ]; then
      printf -- '-- %s --\n  ERROR: transcript.jsonl is missing -> a replay fixture is its recorded transcript\n' "$name"
      status=1
      continue
    fi
    replay_one_fixture "$run_dir" "$source_dir" "$declared" "$scenario_file" || status=1
  done
  if [ "$total" -eq 0 ]; then
    printf 'ERROR: no replay fixture directory matches %s/replay* -> restore at least one; replaying nothing is a silent pass\n' "$FIXTURES_DIR"
    return 1
  fi
  if [ "$controls" -eq 0 ]; then
    printf 'ERROR: %d replay fixture(s) were replayed but none declares FAIL in its expected-verdict -> the negative control is gone. Without a fixture that must fail, every assertion in the verifier could stop detecting anything and this suite would still report green. Restore %s/replay-control-direct-write, or add another fixture whose expected-verdict file reads FAIL\n' \
      "$total" "$FIXTURES_DIR"
    return 1
  fi
  printf '%d replay fixture(s) replayed, %d of them declared FAIL controls, every one judged against its declared expected-verdict\n' \
    "$total" "$controls"
  return "$status"
}

print_control_results() {
  local controls_dir="$1/$CONTROL_SUBDIR"
  [ -d "$controls_dir" ] || return 0
  local dir
  for dir in "$controls_dir"/*/; do
    dir="${dir%/}"
    [ -d "$dir" ] || continue
    printf 'control replay (kept out of the table above so an expected FAIL cannot redden the run): %s -> %s, declared FAIL, evidence under %s\n' \
      "$(basename "$dir")" "$(result_verdict "$dir")" "$dir"
  done
}

deterministic_mode() {
  local run_dir="${EVAL_DETERMINISTIC_DIR:-$(mktemp -d)}/$RUN_ID"
  mkdir -p "$run_dir"
  printf 'offline run, artifacts under %s\n\n' "$run_dir"
  printf '== verifier self-tests ==\n'
  python3 "$VERIFY" --self-test
  printf '\n== scenario schema validation ==\n'
  python3 "$VERIFY" --validate-scenarios "$SCENARIOS_DIR"
  printf '\n== fake-transcript replay ==\n'
  local replay_status=0
  replay_fixtures "$run_dir" || replay_status=$?
  printf '\n== summary ==\n'
  local summary_status=0
  write_summary "$run_dir" || summary_status=$?
  print_control_results "$run_dir"
  if [ "$replay_status" -ne 0 ] || [ "$summary_status" -ne 0 ]; then
    return 1
  fi
  return 0
}

require_plugins() {
  local scenario_file=$1
  local plugin
  while IFS= read -r plugin; do
    [ -n "$plugin" ] || continue
    if [ ! -d "$REPO_ROOT/plugins/$plugin" ]; then
      fail "$scenario_file -> 'expect_plugins' names '$plugin' but plugins/$plugin does not exist; add the plugin or correct the scenario"
    fi
  done < <(scenario_list "$scenario_file" expect_plugins)
}

plugin_args() {
  local scenario_file=$1
  local plugin
  while IFS= read -r plugin; do
    [ -n "$plugin" ] || continue
    printf '%s\n' "--plugin-dir"
    printf '%s\n' "$REPO_ROOT/plugins/$plugin"
  done < <(scenario_list "$scenario_file" expect_plugins)
}

make_workspace() {
  local fixture_path=$1
  local workspace=$2
  local workspace_root=$3
  require_outside_repository "$workspace_root"
  require_inside "$workspace" "$workspace_root"
  require_outside_repository "$workspace"
  mkdir -p "$(dirname "$workspace")"
  cp -R "$fixture_path" "$workspace"
  [ -d "$workspace" ] || fail "failed to copy $fixture_path into $workspace -> check permissions"
  git -C "$workspace" init -q &&
    git -C "$workspace" add -A &&
    git -C "$workspace" -c user.email=evals@localhost -c user.name=evals commit -qm "fixture baseline" ||
    fail "failed to create the git baseline in $workspace -> check that git can write there"
  printf 'workspace: %s\n' "$workspace"
}

destroy_workspace() {
  local policy=$1
  local workspace=$2
  local workspace_root=$3
  local verdict=$4
  case "$policy" in
    never) return 0 ;;
    on_pass) [ "$verdict" = "PASS" ] || return 0 ;;
  esac
  require_outside_repository "$workspace_root"
  require_inside "$workspace" "$workspace_root"
  require_outside_repository "$workspace"
  rm -rf "$workspace"
}

run_scenario() {
  local scenario_id=$1
  local run_dir=$2
  local cli_version=$3
  local scenario_file
  if ! scenario_file="$(resolve_scenario_file "$scenario_id")"; then
    fail "$scenario_file"
  fi
  printf -- '\n-- %s --\n' "$scenario_id"

  local requested_agent
  requested_agent="$(scenario_string "$scenario_file" agent_under_test)"
  [ -n "$requested_agent" ] || requested_agent="$DEFAULT_AGENT_UNDER_TEST"
  local agent_under_test
  if ! agent_under_test="$(resolve_agent_under_test "$requested_agent")"; then
    fail "$scenario_file -> 'agent_under_test' names '$requested_agent' but no plugins/*/agents/ file provides it; available agents: $(available_agent_ids | tr '\n' ' ')"
  fi

  local skip_reason
  skip_reason="$(scenario_string "$scenario_file" skip_reason)"
  local fixture
  fixture="$(scenario_string "$scenario_file" fixture)"
  local budget
  budget="$(scenario_string "$scenario_file" timeout_seconds)"
  local policy
  policy="$(scenario_string "$scenario_file" cleanup_policy)"

  local scenario_dir="$run_dir/$scenario_id"
  mkdir -p "$scenario_dir"
  scenario_dir="$(cd "$scenario_dir" && pwd)"
  local workspace_root="$WORKSPACE_ROOT"
  local workspace="$workspace_root/$RUN_ID/$scenario_id"
  require_outside_repository "$workspace_root"
  require_inside "$workspace" "$workspace_root"
  require_outside_repository "$workspace"

  if [ -n "$skip_reason" ]; then
    printf '{"type":"system","subtype":"skipped"}\n' >"$scenario_dir/transcript.jsonl"
    write_run_meta "$scenario_dir/run-meta.json" "$cli_version" 0 0 false "$budget" "skipped" "skipped" "$RUN_ID" "$agent_under_test" ""
    python3 "$VERIFY" --scenario "$scenario_file" --result-dir "$scenario_dir" || true
    return 0
  fi

  require_plugins "$scenario_file"

  local fixture_path="$FIXTURES_DIR/$fixture"
  require_inside "$fixture_path" "$FIXTURES_DIR"
  [ -d "$fixture_path" ] || fail "$scenario_file -> fixture '$fixture' has no directory at $fixture_path; create the fixture or correct 'fixture'"
  make_workspace "$fixture_path" "$workspace" "$workspace_root"

  local args=()
  args+=(-p --output-format stream-json --verbose --forward-subagent-text --include-hook-events)
  args+=(--setting-sources project --strict-mcp-config)
  args+=(--permission-mode bypassPermissions --max-budget-usd "$MAX_BUDGET_USD")
  args+=(--agent "$agent_under_test")
  local plugin_arg
  while IFS= read -r plugin_arg; do
    [ -n "$plugin_arg" ] || continue
    args+=("$plugin_arg")
  done < <(plugin_args "$scenario_file")

  local turns=()
  local turn
  while IFS= read -r -d '' turn; do
    turns+=("$turn")
  done < <(scenario_turns "$scenario_file")
  [ "${#turns[@]}" -gt 0 ] || fail "$scenario_file -> no turns to run; 'prompt' must be a non-empty string"

  local session_id=""
  if [ "${#turns[@]}" -gt 1 ]; then
    session_id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
  fi

  local hash_before
  hash_before="$(tree_hash "$workspace")"
  local transcript="$scenario_dir/transcript.jsonl"
  local stderr_log="$scenario_dir/stderr.log"
  local argv_log="$scenario_dir/claude-argv.jsonl"
  : >"$transcript"
  : >"$stderr_log"
  : >"$argv_log"

  local started=$SECONDS
  local remaining=$budget
  local exit_code=0
  local timed_out=false
  local index=0
  for turn in "${turns[@]}"; do
    local turn_args=("${args[@]}")
    if [ -n "$session_id" ]; then
      if [ "$index" -eq 0 ]; then
        turn_args+=(--session-id "$session_id")
      else
        turn_args+=(--resume "$session_id")
      fi
    else
      turn_args+=(--no-session-persistence)
    fi
    if [ "$remaining" -le 0 ]; then
      timed_out=true
      exit_code=124
      break
    fi
    local turn_started=$SECONDS
    local turn_code=0
    record_argv "$argv_log" claude "${turn_args[@]}" "$turn"
    run_turn "$workspace" "$remaining" "$transcript" "$stderr_log" "${turn_args[@]}" "$turn" || turn_code=$?
    remaining=$((remaining - (SECONDS - turn_started)))
    index=$((index + 1))
    if [ "$turn_code" -eq 124 ]; then
      timed_out=true
      exit_code=124
      break
    fi
    if [ "$turn_code" -ne 0 ]; then
      exit_code=$turn_code
      break
    fi
  done
  local duration=$((SECONDS - started))

  local hash_after
  hash_after="$(tree_hash "$workspace")"
  write_run_meta "$scenario_dir/run-meta.json" "$cli_version" "$exit_code" "$duration" "$timed_out" "$budget" "$hash_before" "$hash_after" "$RUN_ID" "$agent_under_test" "$argv_log" "$workspace"

  local verify_status=0
  python3 "$VERIFY" --scenario "$scenario_file" --result-dir "$scenario_dir" || verify_status=$?
  local verdict
  verdict="$(result_verdict "$scenario_dir")"
  destroy_workspace "$policy" "$workspace" "$workspace_root" "$verdict"
  return "$verify_status"
}

summarize_aborted_suite() {
  printf '\nEVAL ERROR: the suite aborted before every scenario ran -> summarising the scenarios that did complete, so a partially paid run still leaves a summary behind\n' >&2
  write_summary "$1" || true
}

announce_shadowed_suite() {
  local target=$1
  local kind=$2
  [ "$kind" = "scenario" ] || return 0
  [ -d "$SCENARIOS_DIR/$target" ] || return 0
  printf "note: '%s' is both a scenario id and a directory -> running the single scenario; a scenario id always wins, so rename one of the two to reach the suite\n" \
    "$target"
}

live_mode() {
  local target=$1
  command -v claude >/dev/null 2>&1 || fail "the 'claude' CLI is not on PATH -> install it before running a live scenario"
  python3 "$VERIFY" --validate-scenarios "$SCENARIOS_DIR"

  local resolved
  if ! resolved="$(resolve_target "$target")"; then
    fail "$resolved"
  fi
  announce_shadowed_suite "$target" "$(printf '%s\n' "$resolved" | head -1)"

  local scenario_ids=()
  local scenario_id
  while IFS= read -r scenario_id; do
    [ -n "$scenario_id" ] || continue
    scenario_ids+=("$scenario_id")
  done < <(printf '%s\n' "$resolved" | tail -n +2)
  [ "${#scenario_ids[@]}" -gt 0 ] || fail "'$target' resolved to no runnable scenario -> check evals/scenarios/"

  local run_dir="$RESULTS_DIR/$RUN_ID"
  mkdir -p "$run_dir"
  run_dir="$(cd "$run_dir" && pwd)"

  local cli_version
  cli_version="$(detect_cli_version)"
  printf 'claude CLI: %s\nrun id: %s\nscenarios: %s\n' "$cli_version" "$RUN_ID" "${scenario_ids[*]}"

  local failures=0
  trap "summarize_aborted_suite '$run_dir'" EXIT
  for scenario_id in "${scenario_ids[@]}"; do
    run_scenario "$scenario_id" "$run_dir" "$cli_version" || failures=$((failures + 1))
  done
  trap - EXIT

  printf '\n== summary ==\n'
  local summary_status=0
  write_summary "$run_dir" || summary_status=$?
  if [ "$failures" -ne 0 ] || [ "$summary_status" -ne 0 ]; then
    return 1
  fi
  return 0
}

main() {
  [ -f "$VERIFY" ] || fail "$VERIFY is missing -> restore evals/verify.py"
  if [ "$#" -eq 0 ]; then
    deterministic_mode
    return $?
  fi
  [ "$#" -eq 1 ] || fail "usage: bash evals/run.sh [scenario-id|suite-directory] -> pass no argument for deterministic mode, exactly one scenario id, or exactly one directory under evals/scenarios/ to run every scenario beneath it"
  live_mode "$1"
}

main "$@"
