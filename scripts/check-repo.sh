#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

FRONTMATTER_VALIDATOR="plugins/core/skills/base/scripts/validate-frontmatter.py"
MANIFEST_VALIDATOR="scripts/check-manifests.py"

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

total=0
status=0

collect_paths() {
  local line
  paths=()
  while IFS= read -r line; do
    paths+=("$line")
  done
}

check_frontmatter() {
  collect_paths < <(git ls-files | grep -E '(^|/)SKILL\.md$|(^|/)agents/.+\.md$')
  if [ "${#paths[@]}" -eq 0 ]; then
    printf 'FRONTMATTER ERROR: the repository has no tracked SKILL.md or agents/*.md -> commit the artifacts before running the checks\n' >&2
    return 1
  fi
  python3 "$FRONTMATTER_VALIDATOR" "${paths[@]}" >/dev/null
}

check_json() {
  collect_paths < <(git ls-files '*.json')
  if [ "${#paths[@]}" -eq 0 ]; then
    return 0
  fi
  python3 - "${paths[@]}" <<'PYTHON'
import json
import sys

failures = 0
for path in sys.argv[1:]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            json.load(handle)
    except json.JSONDecodeError as error:
        failures += 1
        sys.stderr.write("JSON ERROR: {}\n".format(path))
        sys.stderr.write(
            "Invalid JSON at line {}, column {}. -> fix the JSON syntax at that position\n".format(
                error.lineno, error.colno
            )
        )
sys.exit(1 if failures else 0)
PYTHON
}

check_workflows() {
  collect_paths < <(git ls-files '*.workflow.js')
  if [ "${#paths[@]}" -eq 0 ]; then
    return 0
  fi
  local wrapped="$SCRATCH/workflow-check.cjs"
  local status=0
  local path
  for path in "${paths[@]}"; do
    { printf 'void (async () => {'; sed 's/^export //' "$path"; printf '})()\n'; } > "$wrapped"
    if ! node --check "$wrapped"; then
      printf 'WORKFLOW ERROR: %s fails node --check -> fix the JavaScript syntax error reported above, whose line numbers match %s\n' "$path" "$path" >&2
      status=1
    fi
  done
  return "$status"
}

check_shell() {
  collect_paths < <(git ls-files '*.sh')
  if [ "${#paths[@]}" -eq 0 ]; then
    return 0
  fi
  local status=0
  local path
  for path in "${paths[@]}"; do
    if ! bash -n "$path"; then
      printf 'SHELL ERROR: %s fails bash -n -> fix the shell syntax error reported above\n' "$path" >&2
      status=1
    fi
  done
  return "$status"
}

run_category() {
  local label=$1
  shift
  total=$((total + 1))
  if "$@"; then
    printf 'OK: %s\n' "$label"
    return 0
  fi
  printf 'FAILED: %s\n' "$label"
  status=1
}

run_category "frontmatter and internal links" check_frontmatter
run_category "json syntax" check_json
run_category "workflow scripts" check_workflows
run_category "shell scripts" check_shell
run_category "manifest consistency" python3 "$MANIFEST_VALIDATOR"

if [ "$status" -eq 0 ]; then
  printf '\nAll %d repository checks passed.\n' "$total"
fi
exit "$status"
