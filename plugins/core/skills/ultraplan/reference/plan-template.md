<!-- Schema is stable; any planning skill can parse this format. -->

---
name: <slug>
mode: <quick|standard|deep>
patterns:
  - anchor: <path:line-range>
    description: <one-line role of the cited precedent>
  - anchor: <path:line-range>
    description: <one-line role of the cited precedent>
created: <YYYY-MM-DD>
---

# Plan: <one-sentence goal>

## Context

<3–5 sentence framing of why this plan exists: what triggered it, what is at stake, what the user is trying to ship. No implementation details — stay at the intent level.>

## Reuse-first

- <existing component/utility discovered via `explore:explore` — `path:line` — one-line role>
- <existing component/utility discovered via `explore:explore` — `path:line` — one-line role>
- <add more as discovered; omit the section header only if Phase 2 returned zero reusable artifacts>

## Steps

### Step 1 — <imperative verb + object>

- **action**: <what to do, concrete>
- **verify**: <how to check it worked end-to-end>
- **mirrors**: `<path:line-range>` OR `no precedent — creating new pattern`
- **risk** *(deep only)*: `<low|medium|high>` — <one-line justification>
- **rollback** *(deep only)*: <how to undo this step>

### Step 2 — <imperative verb + object>

- **action**: <what to do, concrete>
- **verify**: <how to check it worked end-to-end>
- **mirrors**: `<path:line-range>` OR `no precedent — creating new pattern`
- **risk** *(deep only)*: `<low|medium|high>` — <one-line justification>
- **rollback** *(deep only)*: <how to undo this step>

<Add more `### Step N — <verb + object>` blocks as needed. One block per action.>

## Verification

- [ ] <invariant or end-to-end check 1>
- [ ] <invariant or end-to-end check 2>
- [ ] <invariant or end-to-end check 3>
