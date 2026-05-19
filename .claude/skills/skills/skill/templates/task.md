# Template: task

Action skill — runs a procedure on demand. Usually manual-only (no auto-load) and pre-approves the tools it needs.

```yaml
---
description: <what action this performs + when to invoke>
disable-model-invocation: true
argument-hint: '[expected-arg]'
allowed-tools: <space-separated tool patterns, e.g. Bash(git add *) Bash(git commit *)>
---

<task description, with $ARGUMENTS or $0 / $1 / ... if accepting input>

1. <step one>
2. <step two>
3. <step three>
```

Customize:
- Drop `disable-model-invocation` if Claude should also be able to auto-invoke
- Drop `argument-hint` if no arguments
- Drop `allowed-tools` to keep approval prompts (safer for unfamiliar repos)

Use when:
- The skill has **side effects** (write, deploy, commit, message)
- You want to **control timing** (don't deploy on Claude's judgement)
- You want a smooth flow without per-tool approval prompts
