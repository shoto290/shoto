# Competing hypotheses (scientific debate)

**Use when** the root cause of a bug is unclear and a single investigator tends to find one plausible explanation and stop looking. The debate structure forces each teammate to challenge the others' theories instead of anchoring on the first plausible one.

## Spawn prompt

```text
Users report <SYMPTOM>. Spawn 5 agent teammates to investigate different hypotheses:
- h1: <hypothesis 1>
- h2: <hypothesis 2>
- h3: <hypothesis 3>
- h4: <hypothesis 4>
- h5: <hypothesis 5>
Have them talk to each other to try to disprove each other's theories, like a
scientific debate — every teammate's job is not only to gather evidence for its
own theory but to actively attack the others'.
Update FINDINGS.md with whatever consensus emerges. Wait for the debate to
converge before synthesising.
```

If you don't have specific hypotheses, ask the lead to brainstorm them first:

```text
Brainstorm 5 distinct root-cause hypotheses for <SYMPTOM>, then spawn one teammate
per hypothesis and have them debate ...
```

## Why this works

- **Adversarial structure** — each teammate is motivated to disprove others, not just defend its own theory
- **Direct teammate messaging** — debate happens via the mailbox without the lead bottlenecking each exchange
- **Single shared deliverable** (`FINDINGS.md`) — the team converges on one document rather than fragmented reports
- **Avoids anchoring** — sequential investigation is biased toward the first theory explored; parallel investigation isn't

## When to override the default count

- 3 teammates if you have 3 obviously distinct hypotheses
- 5 teammates is the doc's example and a good upper bound — more becomes noise

## Watch for

- One teammate "winning" too fast — ask the lead to make sure the others actually attacked the surviving theory before accepting consensus
- File conflicts on `FINDINGS.md` — have only one teammate (or the lead) own writes; others propose edits via the mailbox

## After convergence

- Ask the lead to summarise the surviving theory + the evidence against the eliminated ones
- Clean up the team before starting the fix
