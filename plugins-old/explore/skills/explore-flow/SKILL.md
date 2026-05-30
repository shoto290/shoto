---
name: explore-flow
description: Internal specialist dispatched by the `explore:explore` orchestrator. Traces the control and data flow of a feature from entry point through handlers and side effects to success or error exits. Not user-invocable directly — call `/explore:explore profile=flow <feature>` instead.
argument-hint: <feature or entry symbol>
context: fork
agent: flow-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-flow

You are running inside the `flow-explorer` subagent. Trace the control and data flow of one feature, end-to-end. Return only the canonical report below; no preamble, no closing.

## Arguments

$ARGUMENTS

## What to capture

- The single entry point (most public if multiple candidates).
- Each synchronous step, depth-first, max 5 hops deep.
- Branch conditions when they route to different outcomes (note as sub-bullets under the step).
- All async / event / IO side effects.
- Both success and error exit points.

## Report format

```markdown
## Entry
<path>:<line> — `<signature>` — <trigger: HTTP route | CLI cmd | event | cron | public API>

## Steps
1. <path>:<line> — <action> — <input shape → output shape if non-obvious>
2. <path>:<line> — <action>
   - if <condition>: → step 3
   - else: → step 5
3. ...

## Side effects
- <DB write to <table> | external API <url> | event emit `<name>` | log | file write> (<path>:<line>)

## Exit points
- success: <path>:<line> — <response shape or return type>
- error: <path>:<line> — <error class or status code>
```

## Rules

- Budget: ≤20 files opened total. Max 5 hops deep. Report ≤70 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)` on a single line. Never omit a section.
- Unknowns → prefix with `?`. Never invent.
- No code blocks quoting source. No narration like "I traced through…".
