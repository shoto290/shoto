---
name: figma-craft
description: Working in Figma and driving the Figma MCP.
---

# Figma Craft

Build Figma files that humans, Figma AI, and the MCP server can all understand. The discipline below — auto layout, variants, variables, and semantic naming — is what makes a design legible to a code generator and frictionless at developer handoff.

## File & Page Organization

Structure the file so intent is obvious before anything is opened:

- **Pages by purpose** — separate `Cover`, `Components`, `WIP`, and `Archive`. Production-ready work lives apart from exploration.
- **Consistent naming** — use the same casing and ordering on every page and section; emoji prefixes are fine if applied uniformly.
- **Sections and covers** — group related frames into sections; give the file a cover frame so its purpose reads from the thumbnail.
- **Branching for big changes** — for a major reorganization or redesign, work on a branch and merge, rather than mutating the main file in place.

## Auto Layout

Auto layout encodes intent: it tells a reader (and a code generator) how a frame is meant to respond, not just how it looks at one size.

| Sizing | Meaning | Use for |
| :-- | :-- | :-- |
| **Fill** | Grow/shrink to the parent's available space | Flexible columns, stretched buttons, responsive content |
| **Hug** | Shrink to fit children | Labels, chips, icon buttons, anything sized by content |
| **Fixed** | Locked width/height | Avatars, icons, fixed-width sidebars |

- Set **direction** (horizontal/vertical), **padding**, and **gap** explicitly — they map directly to flex/grid and spacing tokens in code.
- Set **alignment** (start/center/end, space-between) on the container instead of nudging children.
- Use **min/max width** to keep fluid frames readable across breakpoints.
- Build frames so they resize correctly when content or viewport changes — never hand-place children that should be laid out automatically.

## Variants & Properties

- Organize variants in a clean **matrix** — one property per axis (e.g. rows = size, columns = state) so every combination is reachable and named consistently.
- Use **component properties** to expose API rather than multiplying components:
  - **Boolean** — toggle a layer (show/hide icon, badge).
  - **Variant** — pick a discrete option (size, tone, state).
  - **Instance swap** — substitute a nested instance (leading icon).
  - **Text** — expose editable label content.
- **Avoid combinatorial explosion** — prefer a boolean or instance-swap property over adding another variant axis whenever the change is a toggle or a swap, not a distinct design.

## Variables & Tokens

- Use **modes** for theming — define `light` / `dark` (and density or brand) modes inside a collection so one variable resolves per context.
- **Semantic naming** — name by role, not by raw value: `color/bg/surface`, `color/text/muted`, `space/md`. Semantic names survive a value change; literal ones (`blue-500`) do not.
- **Collections and aliases** — keep a primitive collection (raw scales) and alias semantic variables to it, so a palette change propagates everywhere.
- **Scoping** — restrict where a variable applies (color-only, corner-radius-only) so the right options surface in the right fields.
- **Map to design tokens** — mirror the variable structure to the codebase's token names so MCP-generated code references the same scale developers use.

## Naming Conventions

Semantic names are what let Figma AI, the MCP, and developers reason about the design.

- **Slash-separated component names** — `Button/Primary/Large`, `Input/Text/Error`. Slashes build the assets-panel hierarchy and read as a path.
- **Descriptive layer names** — `icon-leading`, `label`, `badge-count`; never leave `Frame 427` or `Rectangle 12`.
- **Assets-panel hygiene** — publish only intentional components; keep the panel a curated library, not a dumping ground.
- Apply the same naming to variables and styles so every surface tells the same story.

## Figma MCP

Two MCP servers are wired in this plugin:

| Server | Endpoint | Requires |
| :-- | :-- | :-- |
| **figma-desktop** | `http://127.0.0.1:3845/mcp` | Figma desktop app open with **Dev Mode MCP** enabled |
| **figma-remote** | `https://mcp.figma.com/mcp` | OAuth on first use; **Figma Professional+** plan |

Key tools to use when present:

| Tool | Purpose |
| :-- | :-- |
| `get_design_context` | Structured React + Tailwind for the current selection |
| `get_variable_defs` | Color, spacing, and type variables in scope |
| `get_metadata` | Node structure of the selection |
| `get_screenshot` | Visual reference image of the selection |
| `get_code_connect_map` | Existing Figma-node → code-component mappings |
| `get_code_connect_suggestions` | Proposed mappings to review |
| `add_code_connect_map` | Persist a node → component mapping |
| `search_design_system` / `get_libraries` | Find existing components and tokens before creating |
| `create_new_file` / `generate_figma_design` / `upload_assets` | Write operations — **remote-only** |

**Read before you generate.** Pull `get_design_context` + `get_variable_defs` + `get_screenshot` before producing any code, and **respect existing components and variables** — search the design system and reuse over reinventing.

**Detect, then degrade gracefully.** If neither MCP server is connected, say so plainly and proceed from the shared file links or screenshots the user provides — do not block on the MCP.

**Setup is out of scope.** Installing or configuring the MCP servers is deferred — route the user to the `core:mcp` skill (`Skill({ skill: "core:mcp" })`). This skill documents how to USE the servers once they exist.

## Handoff Hooks

Keep names, variables, and Code Connect mappings clean so the design hands off without translation:

- Stable slash-separated component names and semantic variables let developers map Figma to code 1:1.
- Maintain Code Connect mappings so generated code points at real components.
- Clean output feeds the `design-handoff` skill and the `design-engineer` pickup with no rework.

## Pitfalls

| Pitfall | Do instead |
| :-- | :-- |
| Absolute positioning | Use auto layout so intent and responsiveness are explicit |
| Ungrouped / unnamed layers (`Frame 427`) | Name every layer descriptively |
| Raw hex (`#3B82F6`) | Bind to a semantic variable |
| Variant explosion | Use boolean / instance-swap properties for toggles and swaps |
| Detached instances | Keep instances linked to the master component |
