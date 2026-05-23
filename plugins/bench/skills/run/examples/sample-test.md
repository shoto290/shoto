---
name: sample-test
description: Reference shape of a tests/*.md file consumed by /bench:run.
---

# Sample test file

This document shows the on-disk shape of a benchmark test. A real test would live at, for example:

```
plugins/skill-architect/skills/scaffold/tests/minimal-task-skill.md
```

The file content itself would be:

````markdown
---
name: minimal-task-skill
description: Scaffold the smallest valid task skill from a one-line description.
---

Create a new task skill named `ping-host` in the project scope that takes a single hostname argument and runs `ping -c 1 <host>`. Do not ask follow-up questions. Return the absolute path of the SKILL.md you wrote.
````

The body after the closing `---` is the prompt sent verbatim to the `bench-runner` sub-agent. Add notes or context beneath it as needed — everything is forwarded as-is.
