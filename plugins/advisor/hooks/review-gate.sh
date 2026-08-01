#!/usr/bin/env bash
set -euo pipefail
trap 'exit 0' ERR

INPUT="$(cat || true)"

stop_active="$(printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print("true" if data.get("stop_hook_active") else "false")
except Exception:
    print("false")
' 2>/dev/null || printf 'false')"

root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$root" ]; then
  exit 0
fi

slug="$(printf '%s\n' "$root" | shasum | cut -c1-12)"
state="${HOME:-}/.claude/advisor/state/$slug"

if [ ! -d "$state" ]; then
  exit 0
fi

cd "$root" || exit 0

stale_list="$state/checkpoint-untracked"
if [ -s "$stale_list" ]; then
  git reset -q --pathspec-from-file="$stale_list" --pathspec-file-nul >/dev/null 2>&1 || true
  rm -f "$stale_list"
fi

if [ "$stop_active" = "true" ]; then
  exit 0
fi

untracked_list="$(mktemp)"
git ls-files -z --others --exclude-standard > "$untracked_list" 2>/dev/null || true
untracked_count="$(tr -cd '\0' < "$untracked_list" | wc -c | tr -d ' ')"

if [ "$untracked_count" -gt 200 ]; then
  rm -f "$untracked_list"
  printf '%s\n' '{"decision":"block","reason":"Advisor gate: '"$untracked_count"' new untracked files exceed the 200-file review cap (value shared with executant/SKILL.md and review/SKILL.md) - gitignore generated/scaffold output or reduce the untracked count, then this will clear on its own."}'
  exit 0
fi

if [ "$untracked_count" -gt 0 ]; then
  git add -N --pathspec-from-file="$untracked_list" --pathspec-file-nul >/dev/null 2>&1 || true
  trap 'git reset -q --pathspec-from-file="$untracked_list" --pathspec-file-nul >/dev/null 2>&1 || true; rm -f "$untracked_list"' EXIT
else
  rm -f "$untracked_list"
fi

diff_output="$(git diff HEAD 2>/dev/null || true)"
if [ -z "$diff_output" ]; then
  exit 0
fi

cur="$(printf '%s\n' "$diff_output" | shasum | cut -c1-12)"
passed="$(cat "$state/passed" 2>/dev/null || true)"

if [ "$cur" = "$passed" ]; then
  exit 0
fi

printf '%s\n' '{"decision":"block","reason":"Advisor gate: the current changes have not passed adversarial review. Run /advisor:review (spawns the specialist reviewers in parallel) and resolve any high/critical findings before finishing."}'
exit 0
