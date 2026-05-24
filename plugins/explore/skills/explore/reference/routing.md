# Routing — intent → specialist

A keyword/heuristic table for picking the right specialist when no explicit `profile=` is given.

## Table

| Keywords / phrases (FR or EN) | Specialist |
|---|---|
| pattern, design pattern, paterne, architecture, layering, couche, hexagonal, MVC, repository, factory, observer, structure du repo | `architecture` |
| reuse, réutilis, existing component, already exists, duplicate, déjà, composant existant, can I use, is there a | `component` |
| flow, trace, by where, par où passe, appelle, call chain, lifecycle, request path, étapes | `flow` |
| convention, naming, nommage, idiom, style, how do we, comment on, error handling, logging pattern | `convention` |

## Multi-specialist heuristics

When the topic is broad (e.g. "understand the auth module", "explore the payment feature"), dispatch 2–3 specialists in parallel:
- "understand <area>" → `architecture` + `flow`
- "audit <area>" → `architecture` + `convention`
- "before adding <capability>" → `component` + `convention`

## Fallback rules

- If 0 keywords match → general mode (default `profile=deep-dive`).
- If the topic looks like a specific symbol or file path (e.g. `requireAuth`, `src/auth/middleware.ts`) → general mode `profile=targeted`.
- If the topic is the name of a folder or module (≤2 words) and no specialty keywords match → general mode `profile=survey`.
