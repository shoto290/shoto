# Pattern: deploy

**Pattern**: Task action + manual-only + pre-approved tools + arguments

Deploys to a target. Only the user can trigger it — you don't want Claude deploying because the code "looks ready". Bash commands are pre-approved so the deploy flow doesn't get interrupted by approval prompts.

## SKILL.md

```yaml
---
description: Deploy the application to a target environment
disable-model-invocation: true
argument-hint: '[environment]'
allowed-tools: Bash(npm test) Bash(npm run build) Bash(./deploy.sh *)
---

Deploy $ARGUMENTS following these steps:

1. Run the test suite
2. Build the application
3. Push to the deployment target
4. Verify the deployment succeeded
```

## Key choices

- **`disable-model-invocation: true`** — only the user invokes via `/deploy production`
- **`argument-hint`** — autocomplete shows `[environment]` after `/deploy`
- **`allowed-tools`** — specific commands only, not a blanket `Bash *`
- **`$ARGUMENTS`** — whatever follows `/deploy` becomes the environment name

## Invocation

```text
/deploy production
```

Claude receives: "Deploy production following these steps..."
