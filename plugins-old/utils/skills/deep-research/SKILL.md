---
name: deep-research
description: Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report. Use when the user wants a deep, multi-source, fact-checked research report on any topic — "research X", "deep dive on", "investigate", "give me a thorough report on", "compare the options for", "what does the evidence say about". Before invoking, if the question is underspecified, ask 2-3 clarifying questions to narrow scope, then pass the refined question to the workflow.
---

# deep-research

Thin wrapper that reproduces Claude Code's built-in bundled `deep-research` workflow. When it fires, run the bundled script at [scripts/research.workflow.js](./scripts/research.workflow.js) via the **Workflow** tool, passing the user's research question as `args`. This skill firing is itself the opt-in to the Workflow tool — do not refuse for lack of a "workflow" keyword.

## When invoked

1. **Check scope.** If the question is specific enough to research directly, skip to step 2. If underspecified (e.g. "what car to buy" with no budget, use-case, or region), ask 2-3 clarifying questions, then weave the answers into a single refined question.
2. **Run the workflow.** Resolve the absolute path to the bundled script inside THIS skill's own directory — the canonical path is `${CLAUDE_PLUGIN_ROOT}/skills/deep-research/scripts/research.workflow.js` — and invoke:
   ```
   Workflow({
     scriptPath: "<absolute path to plugins/utils/skills/deep-research/scripts/research.workflow.js>",
     args: "<refined question>"
   })
   ```
   The script's `meta.name` is `deep-research`; passing the refined question as `args` is the only input it needs.
3. **Present the report.** The workflow returns a structured result object. Render it as a clean cited report — do not dump raw JSON:
   - **Executive summary** — the answer in 2-4 sentences.
   - **Findings** — each with its confidence level and cited sources.
   - **Caveats** — limitations, conflicting evidence, low-confidence claims.
   - **Open questions** — what remains unresolved or needs follow-up.

## What the workflow does

Five phases, all internal to the script: Scope (decompose into search angles) → Search (parallel WebSearch per angle) → Fetch (URL-dedup, fetch top sources, extract falsifiable claims) → Verify (adversarial multi-vote per claim) → Synthesize (merge dupes, rank by confidence, cite sources).

## Reference

- [scripts/research.workflow.js](./scripts/research.workflow.js) — the bundled workflow invoked via the Workflow tool. Do not inline or edit it from here.
