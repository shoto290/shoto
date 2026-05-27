# Mode calibration

`ultraplan` exposes an intensity dial via `--mode quick|standard|deep`. The mode controls (i) how many `Skill({ skill: "explore:explore", args: "..." })` calls run during Phase 2, (ii) which fields each step must carry in Phase 3, and (iii) whether the Phase 4 mirroring gate is soft or hard.

Default mode when `--mode` is absent: `standard`.

## Calibration table

| Mode | Explorer calls | Step shape | Mirroring gate | Example `args` |
| :-- | :-- | :-- | :-- | :-- |
| quick | 1 | `action` + `verify` + `mirrors` | soft | `profile=component <topic>` |
| standard *(default)* | 2 parallel | `action` + `verify` + `mirrors` | hard | `profile=component <topic>` AND `profile=convention <area>` |
| deep | 4 parallel | `action` + `verify` + `mirrors` + `risk` + `rollback` | hard | `profile=architecture <area>`, `profile=component <topic>`, `profile=convention <area>`, `profile=flow <entry>` |

## Per-mode explorer argument templates

Dispatch the calls listed for the active mode. For `standard` and `deep`, send them in parallel (multiple `Skill` invocations in a single message). For `quick`, send the single call alone.

### quick

```
Skill({ skill: "explore:explore", args: "profile=component <topic>" })
```

### standard

```
Skill({ skill: "explore:explore", args: "profile=component <topic>" })
Skill({ skill: "explore:explore", args: "profile=convention <area>" })
```

### deep

```
Skill({ skill: "explore:explore", args: "profile=architecture <area>" })
Skill({ skill: "explore:explore", args: "profile=component <topic>" })
Skill({ skill: "explore:explore", args: "profile=convention <area>" })
Skill({ skill: "explore:explore", args: "profile=flow <entry>" })
```

## Deriving `<topic>`, `<area>`, `<entry>` from the user goal

- **`<topic>`** — the noun phrase naming the component/utility/module the goal touches. From "add a date-picker component to the settings page" → `date-picker component`.
- **`<area>`** — the broader subsystem the change lives in. From the same goal → `settings page` or `frontend forms`.
- **`<entry>`** — the runtime entry point or user flow the change is part of. From "migrate the auth middleware from custom JWT to OAuth2" → `request authentication flow`.

When the goal does not yield a clean value for one of these, pick the closest noun phrase that gives the explorer a concrete starting point. Avoid generic placeholders like "the app" or "the code".

## Mirroring gate

Phase 4 (coherence check) enforces the mirroring contract per the table above.

- **soft (quick)** — any step without a real `mirrors:` anchor OR the escape hatch produces a warning in the inline output, but the plan is still written.
- **hard (standard, deep)** — any step without a real `mirrors:` anchor OR the escape hatch is rejected; the skill re-drafts the offending step before writing the file. In `deep`, missing `risk` or `rollback` is also a hard rejection.

## Escape hatch literal

When a step genuinely has no local precedent (true greenfield), use the literal:

```
mirrors: no precedent — creating new pattern
```

The exact string is what the hard gate recognizes. Any paraphrase ("no example found", "n/a", "first of its kind") fails the gate.

## Deferred modes

`ultra` mode (all 8 explore specialists in parallel, alternatives per step) is deferred to a future release. For v0, `--mode ultra` is not accepted; users who request it are routed to `deep`.

## Mode inference rubric

Used by Phase 1 step 2 of [`../SKILL.md`](../SKILL.md) to pick the **Recommended** mode when the user does not pass `--mode`. The user can always override via the AskUserQuestion prompt or by passing `--mode` explicitly.

| Signal in the restated goal | Recommended mode | Example goals |
| :-- | :-- | :-- |
| Small, isolated change — clearly under ~5 files, no architectural impact (typo, rename, single-component addition, one-liner) | **quick** | "fix typo in README", "rename a utility function", "add a CTA button to the landing page" |
| Standard feature work — bounded module, no migration, no global refactor | **standard** | "add a date-picker component to the settings page", "wire a new API endpoint", "expose a config flag in the UI" |
| Refactor, migration, or cross-package change — non-trivial risk, rollback matters | **deep** | "migrate the auth middleware from JWT to OAuth2", "refactor the data layer to use repositories", "split the auth module into its own package" |
| Vague or unscoped goal | **standard** + ask the user to refine the goal | "improve performance", "clean up the code", "make it better" |

Ties go to `standard`. When the goal mentions both a small change *and* a refactor (e.g. "add a button and refactor the layout"), recommend `standard` and let the user upgrade to `deep` if they want.
