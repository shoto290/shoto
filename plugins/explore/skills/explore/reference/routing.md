# Routing — intent → specialist

A keyword/heuristic table for picking the right specialist when no explicit `profile=` is given.

## Table

| Keywords / phrases (FR or EN) | Specialist |
|---|---|
| pattern, design pattern, paterne, architecture, layering, couche, hexagonal, MVC, repository, factory, observer, structure du repo | `architecture` |
| reuse, réutilis, existing component, already exists, duplicate, déjà, composant existant, can I use, is there a | `component` |
| flow, trace, by where, par où passe, appelle, call chain, lifecycle, request path, étapes | `flow` |
| convention, naming, nommage, idiom, style, how do we, comment on, error handling, logging pattern | `convention` |
| test, coverage, tested, untested, couvert, testé, tests for, is this tested, smoke test | `tests` |
| dependency, depends on, coupling, couplage, dépend de, imports, uses lib, external deps, package coupling | `dependencies` |
| api, public api, surface, public surface, exports, endpoints, interface, contrat, consumers, breaking change | `api-surface` |
| config, configuration, env var, environment variable, feature flag, settings, runtime knob, toggle, .env | `config` |

## Multi-specialist heuristics

When the topic is broad (e.g. "understand the auth module", "explore the payment feature"), dispatch 2–3 specialists in parallel:
- "understand <area>" → `architecture` + `flow`
- "audit <area>" → `architecture` + `convention`
- "before adding <capability>" → `component` + `convention`
- "audit <area> for ship readiness" → `tests` + `dependencies`
- "refactor <area>" → `architecture` + `dependencies`
- "before breaking <module>" → `api-surface` + `flow`
- "onboard onto <area>" → `config` + `architecture`

## Fallback rules

- If 0 keywords match → general mode (default `profile=deep-dive`).
- If the topic looks like a specific symbol or file path (e.g. `requireAuth`, `src/auth/middleware.ts`) → general mode `profile=targeted`.
- If the topic is the name of a folder or module (≤2 words) and no specialty keywords match → general mode `profile=survey`.
