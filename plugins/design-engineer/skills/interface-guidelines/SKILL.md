---
name: interface-guidelines
description: Checklist for UI/UX polish and accessibility.
---

# Interface Guidelines

A high-signal checklist for shipping accessible, polished UI. Each item is pass/fail — apply when building, and run the Review Pass before shipping.

## Keyboard & Focus

- Every interactive element is operable by keyboard alone (Tab, Enter, Space, arrows, Esc).
- Tab order follows visual/reading order; no positive `tabindex`.
- Focus is always visible via `:focus-visible` — never `outline: none` without a replacement ring.
- Modals/dialogs trap focus while open and restore focus to the trigger on close.
- Provide a skip link to main content as the first focusable element.
- Disabled controls are not focusable; prefer `aria-disabled` when the control must stay discoverable.

## Semantics & ARIA

- Use native elements first: `<button>`, `<a href>`, `<label>`, `<input>`, `<nav>`, `<main>`. Reach for ARIA only when no native element fits.
- Every control has an accessible name (visible text, `aria-label`, or `aria-labelledby`).
- Add `role` only when semantics are missing — never a role that contradicts the element.
- Async updates announce via `aria-live` (`polite` for status, `assertive` for errors).
- Icon-only buttons carry an `aria-label`; decorative images use empty `alt=""`.

## Forms

- Every field has a programmatically associated `<label>` (not placeholder-as-label).
- Errors link to their field with `aria-describedby` and set `aria-invalid` on the input.
- Validate on blur or submit, not on every keystroke; show success/error inline near the field.
- Distinguish disabled (not yet actionable) from error (needs correction) — never use one to mean the other.
- Set `type`, `inputmode`, `autocomplete` correctly (e.g. `email`, `tel`, `one-time-code`).
- Never block paste on any input, including password and OTP fields.

## Touch & Pointer

- Tap targets are at least ~44×44px with adequate spacing between adjacent targets.
- No hover-only affordances — anything revealed on hover is also reachable by focus/tap.
- Set `touch-action` to prevent unwanted scroll/zoom on interactive gestures.
- Avoid the 300ms tap delay (viewport meta `width=device-width`); do not disable zoom.

## Visual

- Text meets WCAG AA contrast (4.5:1 body, 3:1 large text and UI/icon boundaries).
- Never rely on color alone to convey state — pair with icon, text, or shape.
- Body line length ~45–75 characters; line-height ~1.4–1.6 for readable blocks.
- Consistent spacing rhythm from a scale; align to a shared baseline grid.

## Stability & Feedback

- Reserve space for async/media content (set dimensions, `aspect-ratio`) to avoid layout shift (CLS).
- Show skeletons or spinners for loading; prefer optimistic UI for fast mutations.
- Every async surface handles all four states explicitly: loading, empty, error, success.
- Keep the layout stable when content swaps — no jumping when errors or banners appear.

## Motion

- Respect `prefers-reduced-motion`: reduce or remove non-essential animation. For motion design, easing, and transition specifics, see the `/design-engineer:motion` skill.

## Review Pass

Run over a component before shipping:

1. Tab through it — is every action reachable and is focus always visible?
2. Operate it with the keyboard only (open, submit, dismiss, Esc).
3. Inspect names — does each control announce a meaningful label?
4. Trigger each state — loading, empty, error, success — without layout shift.
5. Check contrast and confirm no state is conveyed by color alone.
6. Resize to mobile — tap targets ≥44px, no hover-only paths, no blocked zoom.
7. Toggle `prefers-reduced-motion` — does motion calm down appropriately?
