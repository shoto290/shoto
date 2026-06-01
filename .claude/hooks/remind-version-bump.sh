#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)

ACTIVE=$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false')
[ "$ACTIVE" = "true" ] && exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$ROOT" ] && exit 0
cd "$ROOT" || exit 0

CHANGED=$(git status --porcelain=v1 2>/dev/null | sed 's/^...//')

normalize_changed() {
  printf '%s\n' "$CHANGED" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [ "${line#* -> }" != "$line" ]; then
      printf '%s\n' "${line##* -> }"
    else
      printf '%s\n' "$line"
    fi
  done
}

PLUGINS=$( (normalize_changed | grep -E '^plugins/[^/]+/' || true) | cut -d/ -f2 | sort -u)

[ -z "$PLUGINS" ] && exit 0

BASE=""
if git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
  BASE="origin/main"
elif git rev-parse --verify --quiet main >/dev/null 2>&1; then
  BASE="main"
fi

version_gt() {
  [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n1)" = "$1" ]
}

KEPT=""
MANIFEST_LIST=""
while IFS= read -r plugin; do
  [ -z "$plugin" ] && continue
  manifest="plugins/$plugin/.claude-plugin/plugin.json"

  work_ver=""
  [ -f "$ROOT/$manifest" ] && work_ver=$(jq -r '.version // empty' "$ROOT/$manifest" 2>/dev/null)

  if [ -z "$work_ver" ]; then
    KEPT="${KEPT}${plugin}"$'\n'
    MANIFEST_LIST="${MANIFEST_LIST}${manifest} (missing — scaffold this manifest)"$'\n'
    continue
  fi

  if [ -n "$BASE" ]; then
    main_ver=$(git show "$BASE:$manifest" 2>/dev/null | jq -r '.version // empty' 2>/dev/null || true)
    if [ -z "$main_ver" ] || version_gt "$work_ver" "$main_ver"; then
      continue
    fi
  fi

  KEPT="${KEPT}${plugin}"$'\n'
  MANIFEST_LIST="${MANIFEST_LIST}${manifest}"$'\n'
done <<< "$PLUGINS"

KEPT="${KEPT%$'\n'}"
MANIFEST_LIST="${MANIFEST_LIST%$'\n'}"

[ -z "$KEPT" ] && exit 0

COMMA_LIST=$(printf '%s' "$KEPT" | paste -sd, - | sed 's/,/, /g')

MESSAGE="Task modified files under these plugin(s): ${COMMA_LIST}. Before finishing, bump each affected plugin's version in its .claude-plugin/plugin.json following semver (https://semver.org): MAJOR for breaking changes, MINOR for backward-compatible additions, PATCH for fixes. Use your judgment to pick the level per plugin — do not bump versions that were not affected. Manifests to review:
${MANIFEST_LIST}"

jq -n --arg msg "$MESSAGE" '{
  decision: "block",
  reason: $msg
}'

exit 0
