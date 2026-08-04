#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")"

status=0

check_slug() {
  local title=$1
  local expected=$2
  local actual
  actual="$(python3 src/cli.py "$title")"
  if [ "$actual" = "$expected" ]; then
    printf 'ok   slug %s\n' "$expected"
  else
    printf 'CHECK FAILED: slug produced %s, expected %s\n' "$actual" "$expected"
    status=1
  fi
}

check_flags() {
  local flag
  while IFS= read -r flag; do
    [ -n "$flag" ] || continue
    if grep -qxF -- "$flag" flags.lock; then
      printf 'ok   flag %s\n' "$flag"
    else
      printf 'CHECK FAILED: flag %s is not declared in flags.lock\n' "$flag"
      status=1
    fi
  done < <(grep -oE "['\"]--[a-z0-9-]+['\"]" src/cli.py | tr -d "'\"" | sort -u)
}

check_slug "Hello World" "hello-world"
check_slug "  Release 2.0 Notes " "release-2-0-notes"
check_flags

if [ "$status" -ne 0 ]; then
  printf '\nCHECK FAILED: the workspace does not pass its checks\n'
  exit 1
fi

printf '\nCHECK PASSED: 3 checks, 0 failures\n'
