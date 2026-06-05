---
name: accessibility-craft
description: Design accessible, inclusive interfaces to WCAG - contrast, focus order, target sizes, forms, and state documentation.
when_to_use: Use when checking or designing for accessibility, contrast, keyboard, or inclusive UX.
---

# Accessibility Craft

Design interfaces that everyone can use, and document them so developers implement them correctly. This skill owns the contrast and keyboard detail that other designer skills defer to. Ground decisions in Stéphanie Walter's "A Designer's Guide to Documenting Accessibility & User Interactions", the W3C WAI "Designing for Web Accessibility" tips, and the WCAG practical guide for UI/UX designers.

## Contrast

WCAG AA thresholds. Measure every text and UI combination against the surface behind it.

| Element | AA minimum | AAA |
| :-- | :-- | :-- |
| Normal text (< 24px, or < 18.66px bold) | 4.5:1 | 7:1 |
| Large text (>= 24px, or >= 18.66px bold) | 3:1 | 4.5:1 |
| UI components, icons, focus indicators, meaningful graphics | 3:1 | — |

Never rely on color alone to convey meaning. Pair every color signal with text, an icon, or shape so it survives color blindness and grayscale.

## Focus & Keyboard

| Rule | Threshold / expectation |
| :-- | :-- |
| Focus order | Logical, matches visual reading order (top-to-bottom, left-to-right per language) |
| Focus indicator | Always visible; contrast >= 3:1 against adjacent colors; not removed by `outline: none` alone |
| Skip links | Provide "skip to main content" before repeated nav |
| Keyboard traps | None — every interactive element is reachable and escapable with keyboard only |

Document the intended tab order directly in the design (numbered overlay) so developers don't guess.

## Target Sizes

| Standard | Minimum target |
| :-- | :-- |
| Comfortable mobile touch | ~44 x 44px |
| WCAG 2.2 (2.5.8 Target Size, minimum) | 24 x 24px with adequate spacing |

Add spacing between adjacent targets so a 24px control still has a comfortable hit area. Prefer larger touch targets for primary mobile actions.

## Accessible Palettes

Build palettes that pass contrast across every role they appear in, not just one pairing.

- Test text-on-surface for each surface tier (background, card, raised).
- Test text and icons on brand/accent colors — brand color is often the weakest pairing.
- Provide non-color status cues: success/warning/error/info each get an icon + text label, never color alone.
- Verify the palette in both light and dark themes; contrast that passes in one can fail in the other.

## Forms

| Element | Requirement |
| :-- | :-- |
| Labels | Always visible above or beside the field — never placeholder-only |
| Required | Marked with text or a clear, documented indicator, not color alone |
| Instructions | Placed before the field, not only on error |
| Input purpose | Set autocomplete/input purpose so assistive tech and autofill work |
| Errors | Specific message tied to its field, programmatically associated, describing how to fix |

## Documenting Accessibility

Annotate the design so developers implement the right semantics:

- Contrast ratios for key text and UI pairings.
- Focus order (numbered) and which elements are focusable.
- Alt text intent for every meaningful image; mark decorative images as such.
- ARIA roles and landmark intent (header, nav, main, complementary, footer).
- All interactive states: default, hover, focus, active, disabled, error, loading.

## Pitfalls

| Pitfall | Fix |
| :-- | :-- |
| Gray-on-gray text below 4.5:1 | Raise contrast to AA threshold |
| Color-only status | Add icon + text |
| Invisible focus | Provide a visible 3:1 focus indicator |
| Tiny targets | Meet 24px (WCAG 2.2) / aim for 44px on mobile |
| Placeholder-as-label | Add a persistent visible label |
| Undocumented states | Annotate every state in the design |
