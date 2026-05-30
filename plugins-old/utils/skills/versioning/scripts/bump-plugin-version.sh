#!/usr/bin/env bash
# Usage: bump-plugin-version.sh <plugin-name> [--base <ref>] [--apply]
set -euo pipefail

plugin=""
base=""
apply=0
while [ $# -gt 0 ]; do
  case "$1" in
    --base) base="$2"; shift 2 ;;
    --apply) apply=1; shift ;;
    -*) echo "unknown flag: $1" >&2; exit 2 ;;
    *) if [ -z "$plugin" ]; then plugin="$1"; shift; else echo "unexpected arg: $1" >&2; exit 2; fi ;;
  esac
done

[ -n "$plugin" ] || { echo "usage: bump-plugin-version.sh <plugin-name> [--base <ref>] [--apply]" >&2; exit 2; }

manifest="plugins/${plugin}/.claude-plugin/plugin.json"
[ -f "$manifest" ] || { echo "manifest not found: $manifest" >&2; exit 1; }

if [ -z "$base" ]; then
  if tag=$(git describe --tags --abbrev=0 --match "${plugin}-v*" 2>/dev/null); then
    base="$tag"
  else
    base=$(git rev-list --max-parents=0 HEAD | tail -n1)
  fi
fi

bump="none"
while IFS= read -r sha; do
  [ -n "$sha" ] || continue
  subject=$(git log -1 --format=%s "$sha")
  body=$(git log -1 --format=%b "$sha")
  if printf '%s\n%s' "$subject" "$body" | grep -Eq '(^|[^[:alnum:]])BREAKING CHANGE:' \
     || printf '%s' "$subject" | grep -Eq '^[a-z]+(\([^)]+\))?!:'; then
    bump="major"; break
  fi
  if printf '%s' "$subject" | grep -Eq '^feat(\(|:)'; then
    [ "$bump" = "major" ] || bump="minor"
  elif printf '%s' "$subject" | grep -Eq '^(fix|perf)(\(|:)'; then
    [ "$bump" = "none" ] && bump="patch"
  fi
done < <(git log "$base..HEAD" --format=%H -- "plugins/${plugin}/")

current=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)".*/\1/p' "$manifest" | head -n1)
[ -n "$current" ] || { echo "could not read version from $manifest" >&2; exit 1; }
IFS=. read -r major minor patch <<EOF
$current
EOF

case "$bump" in
  major) new="$((major + 1)).0.0" ;;
  minor) new="${major}.$((minor + 1)).0" ;;
  patch) new="${major}.${minor}.$((patch + 1))" ;;
  none)  new="$current" ;;
esac

echo "plugin=${plugin} current=${current} bump=${bump} new=${new}"

if [ "$apply" -eq 1 ] && [ "$bump" != "none" ]; then
  tmp=$(mktemp)
  sed "s/\"version\"[[:space:]]*:[[:space:]]*\"${current}\"/\"version\": \"${new}\"/" "$manifest" > "$tmp"
  mv "$tmp" "$manifest"
fi
