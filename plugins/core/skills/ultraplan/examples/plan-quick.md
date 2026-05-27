<!-- Schema is stable; any planning skill can parse this format. -->

---
name: add-a-date-picker-to-settings
mode: quick
patterns:
  - anchor: src/components/DatePicker.tsx:12-40
    description: existing date-picker primitive with controlled value + onChange contract
  - anchor: src/app/settings/profile/page.tsx:24-58
    description: settings page form layout and field grouping convention
created: 2026-05-27
---

# Plan: Add a date-picker field to the settings page for the user's birthday

## Context

The settings page currently lets users edit display name and avatar but not their birthday. Product wants the birthday captured to drive birthday-aware notifications. The change is local to the settings form and reuses an existing `DatePicker` primitive already used in the booking flow. Mode is `quick` because the scope is one field added to one existing page with a clear precedent.

## Reuse-first

- `DatePicker` primitive — `src/components/DatePicker.tsx:12-40` — controlled `value` + `onChange` contract, already styled to the design system.
- Settings form field group — `src/app/settings/profile/page.tsx:24-58` — convention for label + control + helper text in the settings page.
- `updateProfile` server action — `src/app/settings/profile/actions.ts:8-32` — existing mutation entry point for profile fields.

## Steps

### Step 1 — Add `birthday` to the profile schema

- **action**: extend the Zod profile schema with an optional `birthday: z.date().optional()` field.
- **verify**: `pnpm typecheck` passes; `pnpm test src/schemas/profile.test.ts` covers the new field.
- **mirrors**: `src/schemas/profile.ts:14-22`

### Step 2 — Render a `DatePicker` row in the settings form

- **action**: insert a new field group in `profile/page.tsx` using the existing label/control/helper convention, wired to `DatePicker`.
- **verify**: navigate to `/settings/profile`, see the birthday row aligned with the existing rows; selecting a date updates local state.
- **mirrors**: `src/app/settings/profile/page.tsx:24-58`

### Step 3 — Persist `birthday` through `updateProfile`

- **action**: forward the `birthday` value from the form submit handler to the `updateProfile` server action; add the column write in the action.
- **verify**: submit the form with a date, reload the page, see the value preserved; database row has the expected timestamp.
- **mirrors**: `src/app/settings/profile/actions.ts:8-32`

<!-- Soft-gate note: all three steps cite a real precedent, so no warning was emitted. If Step 1 had been the very first Zod field added to the codebase, the escape hatch `mirrors: no precedent — creating new pattern` would have been used and a warning surfaced in the inline output (not in this file). -->

## Verification

- [ ] Birthday row appears on `/settings/profile` and matches the visual rhythm of the existing rows.
- [ ] Saving and reloading preserves the selected date.
- [ ] `pnpm typecheck` and `pnpm test` pass.
