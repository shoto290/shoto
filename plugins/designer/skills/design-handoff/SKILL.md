---
name: design-handoff
description: Handing off designs to developers cleanly.
---

# Design Handoff

A handoff is the contract between design and engineering. The work is not done when the happy-path screen looks right — it is done when a developer can build every state, at every breakpoint, without guessing. Most handoff failures are not visual; they are missing intent, missing states, and unnamed primitives.

## Align on Scope

Agree what is in and out before anything is annotated. Misaligned scope is the most expensive handoff defect — it surfaces mid-build.

- **In / out** — list the screens, flows, and components this handoff covers, and explicitly name what it does not.
- **Breakpoints** — name the breakpoints you designed for (e.g. mobile / tablet / desktop) and which is the source of truth.
- **Platforms** — web, iOS, Android, or all; each has different conventions for navigation, gestures, and system states.
- **Shared language** — use the same names design and engineering already use for components and tokens, so a "card" means one thing on both sides.

## Responsive Intent

A fixed frame describes one width. Developers build for a range. Communicate how the layout *behaves*, not just how it looks at one size.

- **Reflow rules** — for each region, state fill vs hug, min/max width, and wrap behavior — not just absolute pixel positions.
- **Per-breakpoint behavior** — specify what changes at each breakpoint: stacking, column counts, hidden/shown elements, type scale shifts.
- **Elastic content** — show how the layout holds when text is short, long, or translated; mark what truncates, wraps, or grows.

## Invisible & Edge States

The happy path is the easy 20%. Design and annotate the states that are easy to forget — they are where builds stall and bugs ship.

- **Empty** — first-run, no data, cleared filters.
- **Loading** — skeletons, spinners, optimistic UI; what shows while data is in flight.
- **Error** — failed request, validation failure, offline; the message, recovery action, and tone.
- **Success** — confirmation, toast, post-submit state.
- **Disabled** — why an action is unavailable and how it reads.
- **Long-content** — long names, long lists, many tags; how the layout absorbs overflow.
- **Zero / overflow** — `0`, `999+`, counts that exceed their container.

## Annotations

Annotations carry the intent a static frame cannot. Attach them where the developer reads them — on the design, not in a separate doc that drifts.

- **Interaction notes** — triggers, transitions, what is tappable, gesture behavior, and motion specs (duration, easing).
- **Accessibility notes** — focus order, alt text, ARIA intent, contrast expectations, and reduced-motion behavior. For the full a11y discipline, defer to `accessibility-craft`.
- **Business rules** — conditional logic, permissions, formatting and validation rules, edge-case handling.
- **Prototype links** — link the interactive prototype for any flow that motion or branching cannot be captured in a still frame.

## Clean File Hygiene

A messy file forces developers to reverse-engineer your decisions. Clean structure is what makes Dev Mode useful instead of confusing.

- **Named, auto-laid-out components** — real components with meaningful names and auto layout, not detached groups or pixel-pushed copies.
- **Named styles & variables** — colors, type, spacing, and effects bound to named styles/variables so they map to code tokens — never raw hex or magic numbers.
- **Organized pages** — a predictable page/section structure; archive exploration and scratch frames away from the handoff surface.
- **Code Connect mappings** — map design components to their code counterparts so developers land on the real implementation.
- **Dev Mode** — hand off via Figma Dev Mode so developers read tokens, measurements, and specs directly from the source instead of from screenshots.

## Handoff Checklist

A concrete pass/fail gate. Every item must be true before the handoff is dev-ready.

- [ ] Scope agreed — in/out, breakpoints, and platforms confirmed with engineering.
- [ ] All states designed — empty, loading, error, success, disabled, long-content, zero/overflow.
- [ ] Responsive behavior specified — reflow and per-breakpoint rules, not just fixed frames.
- [ ] Components & styles named — real components, auto layout, predictable page structure.
- [ ] Tokens/variables applied — colors, type, spacing bound to named styles/variables.
- [ ] Accessibility annotated — focus order, alt text, ARIA intent, contrast, reduced motion.
- [ ] Prototype linked — interactive flows reachable from the handoff.
- [ ] Assets exportable — icons and images set up for export at the right scales/formats.

## Handoff to design-engineer

This skill produces clean *specs*, not application code. Production React/TypeScript implementation is owned by the `design-engineer` agent. The designer's job is to deliver a handoff that passes the checklist above; the design-engineer turns it into shipped components. Do not write app code from this skill — hand off the spec and let the implementation owner build it.
