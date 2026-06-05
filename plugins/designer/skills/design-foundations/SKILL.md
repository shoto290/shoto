---
name: design-foundations
description: 'Visual fundamentals of UI design - typographic scale, color and palettes, spacing systems, grids, and visual hierarchy.'
when_to_use: 'When establishing or auditing type, color, spacing, layout, or visual hierarchy on a screen.'
---

# Design Foundations

The visual craft a senior designer reuses on every screen. Five systems — type, color, spacing, grid, hierarchy — that turn a wireframe into something that reads as intentional. The through-line: **decisions come from a small, fixed system, never picked ad hoc per element.** Grounded in Refactoring UI (Wathan & Schoger), the Prototypr wireframe-to-high-fidelity workflow, and Smart Mentors' color/typography/layout guidance.

## Typographic Scale

Pick a ratio, generate a small set of sizes, and never improvise a size in between.

- **Modular scale** — multiply a base (16px) by a fixed ratio. 1.2 (minor third) for dense UI; 1.25 (major third) for marketing or airier screens. Round to clean pixels.
- **Limit the set** — 5 to 7 sizes total covers an entire product. More sizes read as noise, not hierarchy.
- **Line-height by role** — tight for headings (1.1–1.25), roomy for body (~1.5). Line-height shrinks as size grows.
- **Measure** — keep body line length at 45–75 characters. Cap with `max-width` (~65ch), don't let prose run the full container.
- **Weight over size** — separate a label from its value with weight (500 vs 400) or color before reaching for a larger size. Most hierarchy is achievable inside two or three sizes.

| Role | Size (1.25 from 16) | Line-height | Weight |
| :-- | :-- | :-- | :-- |
| Display | 39px | 1.1 | 700 |
| H1 | 31px | 1.15 | 700 |
| H2 | 25px | 1.2 | 600 |
| H3 | 20px | 1.3 | 600 |
| Body | 16px | 1.5 | 400 |
| Small / caption | 13px | 1.45 | 400 |

## Color

Build a palette from a few roles, not a swatch grab-bag.

- **60-30-10** — ~60% dominant (a near-white or near-black surface), ~30% secondary, ~10% accent. The accent is the smallest slice and carries the eye.
- **Neutral ramp + 1–2 accents** — most of a UI is grays. Define a 9–10 step neutral ramp (slightly tinted toward the brand hue, never pure gray) plus one brand accent. Add a second accent only if the product truly needs it.
- **Semantic roles** — map colors to intent, not hue: `surface`, `text`, `text-muted`, `border`, `brand`, `success`, `warning`, `danger`. Components consume roles so a re-theme is one remap.
- **Tints & shades from a base** — derive hover/active/subtle-background variants by adjusting lightness (and nudging saturation) of one base hue, so a color family stays coherent.
- **Never pure black on pure white** — `#000` on `#fff` vibrates. Use a very dark desaturated ink (e.g. `#1a1a1a`) on an off-white surface; reserve true extremes for nothing.
- **Contrast is a hard gate** — text must pass WCAG AA (4.5:1 body, 3:1 large). Treat this as pass/fail, not taste. Detailed contrast checking and remediation defer to `accessibility-craft`.

## Spacing & Rhythm

One unit governs every gap on the screen.

- **Single base unit** — 4px or 8px. Everything is a multiple. 8px is the common default; 4px when a dense UI needs finer steps.
- **Spacing scale** — 4, 8, 12, 16, 24, 32, 48, 64. A fixed ladder kills the "is it 13 or 15px?" guesswork and makes spacing decisions binary.
- **Consistent padding & gap** — the same component gets the same internal padding everywhere; sibling elements share one gap value. Inconsistent gaps are the loudest signal of an unsystematic layout.
- **Vertical rhythm** — relate vertical spacing to the type scale: more space above a heading than below it, so a heading groups with the content it introduces (proximity).
- **Optical alignment** — trust the eye over the math. Icons, punctuation, and round shapes often need a nudge past their geometric box to look aligned.

## Grids & Layout

- **Columns, gutters, margins** — a 12-column grid flexes to 2/3/4/6 splits. Define gutter and outer margin in spacing-scale units.
- **8pt grid** — snap component sizes and positions to 8px (or your base). Removes a class of one-off measurements.
- **Container widths** — cap content (~1200–1280px on desktop) and center it. Full-bleed text is unreadable.
- **Breakpoints** — design a few intentional layouts (mobile / tablet / desktop) rather than fluid mush; let content, not devices, dictate where a layout breaks.
- **Alignment & proximity (Gestalt)** — related items sit close and share an edge; unrelated items get more space. Grouping by spacing beats grouping by borders and boxes.
- **Whitespace is a design element** — generous negative space signals quality and focus. Crowding to "use the space" is the most common amateur tell. Add emptiness deliberately.

## Visual Hierarchy

Rank information so the eye lands in the right order.

- **Levers** — size, weight, color/contrast, and spacing. Combine two or three; relying on size alone forces large, clumsy jumps.
- **Demote, don't only promote** — to make the primary thing stand out, mute the secondary (gray it, shrink it, thin it) rather than enlarging everything.
- **One primary action per view** — a single high-emphasis button. Secondary actions are lower-contrast (outline/ghost); destructive actions read as `danger` but stay visually quiet until needed.
- **Scannability** — clear headings, short groups, aligned starts. A user should grasp the structure before reading a word.

**Worked example — card promoted from wireframe to high fidelity:**

Wireframe state: title, price, and description all 16px/400, equal 16px gaps, a black "Buy" button and a black "Save" button side by side. Everything competes; nothing leads.

Applied foundations:
- **Type** — title to 20px/600, price to 16px/600, description stays 16px/400 `text-muted`. Three levels from two sizes plus weight and color.
- **Color** — surface off-white, ink `#1a1a1a`, one brand accent on the single primary button. "Save" becomes a ghost button in neutral.
- **Spacing** — 8px base: 8px title-to-price, 16px price-to-description, 24px description-to-actions. Rhythm now signals grouping.
- **Hierarchy** — one accent "Buy" (primary), one quiet "Save" (secondary). The eye goes title → price → action.

Result: same content, but it reads top-to-bottom with an obvious next step — the wireframe-to-high-fidelity jump done with system decisions, not decoration.

## Pitfalls

- **Too many type sizes** — five improvised sizes where three from a scale would do. Collapse to the modular scale.
- **Inconsistent spacing** — gaps off the scale (13px here, 18px there). Snap everything to the ladder.
- **Low-contrast gray text** — light gray on white fails AA and tires the eye. Darken until it passes; verify with `accessibility-craft`.
- **Decorative-over-functional color** — color used for prettiness dilutes the accent meant to guide action. Spend color where it directs attention.
- **Crowded layouts** — filling every pixel. Whitespace is the cheapest upgrade to perceived quality; add it on purpose.
