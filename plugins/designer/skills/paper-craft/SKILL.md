---
name: paper-craft
description: 'Design on the Paper.design canvas - HTML/CSS artboards, code-to-design and design-to-code - via the Paper MCP.'
when_to_use: 'When designing in Paper.design or moving between live code and the canvas via the Paper MCP.'
---

# Paper Craft

Design in Paper.design — a spatial canvas built on real HTML/CSS/DOM — and drive its MCP server so an agent reads and edits the canvas directly. The core shift: the canvas IS the product, not a picture of it.

## Why Paper Is Different

- **The canvas is the product.** Artboards are real HTML/CSS/DOM, not vector shapes that approximate a UI. What you see is what ships.
- **No abstraction gap.** There is no mockup→code translation step where intent gets lost. The design and the implementation are the same artifact, so there is no mockup→code mismatch to reconcile later.
- **Agents work in the native medium.** Agents are trained on web standards (HTML, CSS, the DOM), so they operate directly in Paper instead of guessing at a proprietary design format.
- **Live data, not static mockups.** Sections render with real data and real components, so the canvas reflects production reality instead of placeholder lorem ipsum.

## Spatial Design

- **Lay multiple futures side by side.** Place design variants next to each other on the canvas and compare them in one view instead of toggling between files.
- **Humans own spatial reasoning.** Comparison, judgment, taste, and the final decision stay with the person — the parts that need a human eye.
- **Agents own execution.** Boilerplate, repetitive refactors across variants, and pulling live data are delegated to the agent so the human stays focused on the decisions.

## Code-to-Design

Pull a live section of an app onto the canvas, iterate, then push the real change back.

1. Pull a live section (React or HTML/CSS) of the running app onto the canvas as an editable artboard.
2. Iterate spatially — adjust layout, styles, and structure, branching into variants as needed.
3. Push the actual change back as production code — not a screenshot or a redline of the change, the change itself.

## Design-to-Code

Start on the canvas and export real implementation.

- Iterate on the canvas with HTML/CSS-native artboards.
- Export real **React / Tailwind / HTML**, not a spec sheet or a handoff document the developer must re-implement.

## Paper MCP

The `paper` server is wired into this plugin at `http://127.0.0.1:29979/mcp` (no secret). It runs from the **Paper desktop app** — opening a design file starts the server. If the MCP is not connected, say so and ask the user to open the Paper desktop app and a design file — do not block on it.

| Group | Tools |
| :-- | :-- |
| Read | `get_basic_info`, `get_selection`, `get_node_info`, `get_children`, `get_tree_summary`, `get_screenshot`, `get_jsx`, `get_computed_styles`, `get_font_family_info`, `export` |
| Write | `create_artboard`, `write_html`, `set_text_content`, `rename_nodes`, `duplicate_nodes`, `move_nodes`, `update_styles`, `delete_nodes` |
| Workflow | `get_guide` (read first for agent guidance), `finish_working_on_nodes` (finalize) |

**Default approach:**

1. **Orient** — call `get_guide` first, then `get_tree_summary` and/or `get_screenshot` to understand the current canvas before touching anything.
2. **Edit** — make changes via `write_html`, `update_styles`, `create_artboard`, and the other write tools.
3. **Finalize** — call `finish_working_on_nodes` when done.

## Pitfalls

- **Treating Paper like a static mockup tool** — it is live HTML/CSS, not a flat picture. Design with real structure and data.
- **Ignoring the live-code round-trip** — code-to-design only pays off when you push the real change back, not a redline.
- **Editing blindly** — never write to the canvas before reading the tree and the guide. Orient with `get_guide` + `get_tree_summary` / `get_screenshot` first.
