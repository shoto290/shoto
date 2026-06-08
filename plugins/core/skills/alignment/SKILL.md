---
name: alignment
description: Clarify task intent up front via inline questions.
---

# Alignment

This skill is the alignment gate. Its only job is to make the user's intent 100% explicit before any work begins, by asking the maximum set of genuinely useful clarifying questions through `AskUserQuestion`, then returning control. It writes nothing and never starts the task itself.

## When To Run

- Always run first on a new task unless the task is fully unambiguous and trivial (typo, obvious one-liner). This is the `Think Before Coding` guideline from `core:base` applied as a gate.
- If after reading the request everything is already 100% clear, say so in one line and hand back immediately. Do not invent questions for their own sake.

## How To Align

1. Restate the task in one sentence as you currently understand it.
2. Enumerate every dimension that is unstated or ambiguous: goal/outcome, scope (in/out), target files or surfaces, inputs, output format, constraints (perf, style, deps), acceptance criteria, edge cases, and any decision with multiple plausible interpretations.
3. Ask the maximum set of useful clarifying questions via `AskUserQuestion`. Batch related questions into one `AskUserQuestion` call where the tool allows multiple questions; never silently pick when interpretations diverge. Each question carries canonical question text, 2-4 concrete options each with an implication string, and a recommended default pre-selected. Prefer concrete options over open-ended prompts.
4. `Maximum` means maximally complete coverage of real ambiguity, not padding. Drop any question whose answer is already determined by the request or context.

## Hand Back

- After the user answers, produce a tight `Aligned intent` recap: the confirmed one-sentence goal plus a compact bullet list of each resolved decision (e.g. scope: X, output: Y, constraint: Z).
- Then STOP. Do not begin the work. Do not write any file or artifact. Control returns to the caller (the orchestrator or the user) to execute with the now-explicit intent.

## Constraints

- No written artifact — questions and the recap only.
- `AskUserQuestion` is the only tool; never read or modify files.
- English only. House rules apply (no co-author or generated-by lines).
- Honor the `core:base` SIMPLE principles and the destructive-operation safety rules by reference, not by restating them.
