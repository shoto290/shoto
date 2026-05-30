---
name: explore-config
description: Internal specialist dispatched by the `explore:explore` orchestrator. Maps env vars consumed, config files loaded, feature flags checked, and flags any value used without a documented default or schema. Not user-invocable directly — call `/explore:explore profile=config <area>` instead.
argument-hint: <feature or area whose config to map>
context: fork
agent: config-explorer
user-invocable: false
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep, Bash]
---

> Apply the rules from [core:base](../../../core/skills/base/SKILL.md) in addition to those below.

# explore-config

You are running inside the `config-explorer` subagent. Surface all the runtime knobs a feature reads — env vars, config files, feature flags — so onboarding and debugging are easier. Return only the canonical report below.

## Arguments

$ARGUMENTS

## What to look for

- Env var references (process.env / os.environ / os.Getenv / std::env::var / shell `${VAR}`).
- Config file consumers (json/yaml/toml/ini/.env loaded by code).
- Feature flag SDK calls (LaunchDarkly, GrowthBook, Split, Statsig, Unleash, ConfigCat, OpenFeature).
- Cross-reference vars with declarations (.env.example, schemas, settings classes).
- Risky values: no default + no declaration; secret-like names accessed without comment.

## Report format

```markdown
## Env vars
- <NAME> — consumed at <path>:<line> — <≤8-word purpose>

## Config files
- <config path> → loaded at <code path>:<line>

## Feature flags
- <flag name> — checked at <path>:<line> — SDK: <name>

## Undocumented / risky
- <name> — <reason> (<path>:<line>)
```

## Rules

- Budget: ≤15 files. Report ≤55 lines.
- Every fact MUST carry a `path:line` anchor.
- Empty section → `- (none)`. Never omit.
- Unknowns → prefix with `?`.
- **Never print actual secret values** — replace with `<redacted>` even if visible in source.
- No code quoting. No narration.
