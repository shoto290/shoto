# Verdict Block Format

Canonical block emitted once per PR comment. Render this verbatim, one block per comment, in input order.

```
---
[#N] [File:line]
Comment: "[verbatim text]"

Verdict: [FIX | FIX-STYLE | INTENTIONAL | OUT-OF-SCOPE | DISCUSS]
Reason: [one sentence]
Action: [what /git:review-fix or the human should do next]
Confidence: [high | medium | low]
---
```

## Verdict glossary

- **FIX** — Real bug, regression, or correctness issue. `/git:review-fix` should patch it.
- **FIX-STYLE** — Cosmetic / lint / naming / formatting nit that improves the diff with no behavior change. Safe for `/git:review-fix`.
- **INTENTIONAL** — The flagged code is correct by design (matches plan, CLAUDE.md, or AGENTS.md). Reply to the reviewer; do not change code.
- **OUT-OF-SCOPE** — Valid point, but unrelated to this PR. Log as a follow-up; do not change code here.
- **DISCUSS** — Ambiguous, needs human judgement, or the verdict subagent failed. Surface to the user before any action.

## Field rules

- `[#N]` — 1-based index matching the order comments appeared in the input.
- `[File:line]` — exactly as cited by the reviewer; if the comment is file-level use `[File]`.
- `Comment` — verbatim text inside double quotes. Do not paraphrase.
- `Reason` — one sentence, ≤ 25 words.
- `Action` — imperative, ≤ 20 words.
- `Confidence` — `low` whenever the cited file/line could not be read or the plan was ambiguous.
