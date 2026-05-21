#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0

matched=0
case "$FILE" in
  */plugins/*/skills/*/*|plugins/*/skills/*/*) matched=1 ;;
  */plugins/*/agents/*.md|plugins/*/agents/*.md) matched=1 ;;
  */plugins/*/.claude-plugin/plugin.json|plugins/*/.claude-plugin/plugin.json) matched=1 ;;
  */.claude-plugin/marketplace.json|.claude-plugin/marketplace.json) matched=1 ;;
esac

[ "$matched" -eq 0 ] && exit 0

jq -n --arg f "$FILE" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("Plugin artifact changed: " + $f + ". Run /docs:sync before ending the task so docs/ stays in sync with plugins/.")
  }
}'
