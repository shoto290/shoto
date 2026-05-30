# Input & Navigation

The fastest UI is the one nobody has to point at. Optimize the path from intent to action; let the keyboard outpace the mouse.

## Keyboard shortcut hierarchy

**What** — Single-letter shortcuts for frequent operations, two-letter combos for navigation.

**Why** — A keystroke is ~100ms; a mouse traversal plus click is 500-1500ms. Single letters cover the daily verbs; two-letter combos give room for hundreds of actions without modifier-key gymnastics.

**When to apply** — Power-user apps (editors, trackers, dashboards) where the same actions repeat thousands of times per week.

**Anti-pattern** — Modifier-heavy shortcuts (`⌘⌥⇧X`). High cognitive load, slow to type, hostile to muscle memory.

## Global command palette

**What** — `⌘K` searches the local store, not the server — instant and works offline.

**Why** — Centralizes navigation, creation, and modification in one searchable surface. Searching the local store eliminates network latency on every keystroke.

**When to apply** — Apps with more than ~20 distinct destinations or commands. Anywhere a menu would otherwise grow unmanageable.

**Anti-pattern** — Deeply nested menus plus a server-backed search dialog. The user must remember where things live and wait for results on every query.

## Contextual scoping

**What** — The same palette adapts its actions to the current context (issue, project, settings), teaching shortcuts organically.

**Why** — One primitive serves every flow, so users learn one tool instead of many. Contextual actions surface when relevant and expose keyboard shortcuts as the user discovers commands.

**When to apply** — Apps with multiple object types and many per-object actions.

**Anti-pattern** — A static command list ignoring context, or a different palette per surface. Either floods the user with irrelevant actions or fragments muscle memory.
