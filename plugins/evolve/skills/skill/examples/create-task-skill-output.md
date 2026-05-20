---
description: Run the pre-deploy verification checklist
disable-model-invocation: true
argument-hint: '[environment]'
allowed-tools: Bash(npm test) Bash(npm run build)
---

# Deploy Check

Run the pre-deploy checks for `$ARGUMENTS`.

1. Run `npm test`.
2. Run `npm run build`.
3. Summarize failures with the command that failed and the first actionable error.
4. If all checks pass, say the target environment is ready for deployment.
