# Research and exploration

**Use when** you're at the front of a design problem and want multiple independent perspectives before committing to a direction. The three roles below are independent — no waiting on each other — so they parallelise cleanly.

## Spawn prompt (the CLI-TODO example)

```text
I'm designing <PRODUCT/FEATURE>. Create an agent team to explore this from
different angles:
- ux: focused on user experience (workflows, ergonomics, edge cases users hit)
- arch: focused on technical architecture (data model, dependencies, deploy story)
- devils-advocate: actively tries to disprove the premise, find prior art that
  failed, surface unaddressed risks
Use Sonnet for each teammate. Have them explore independently for one round, then
share findings via the mailbox and challenge each other. Synthesise consensus and
open questions into RESEARCH.md.
```

## Why this works

- **Three independent lenses** — none of them blocks the others
- **Devil's advocate** is the key role — without it, the team tends toward confirmation bias
- **Two-phase structure** (explore → debate) — independent exploration first means each perspective develops fully before being attacked
- **Single deliverable** (`RESEARCH.md`) — converges to one artefact

## Variations

- **Library evaluation**:
  ```text
  Evaluate <LIBRARY> for adoption. Spawn:
  - api: read the docs and assess the API ergonomics
  - perf: benchmark against our current stack
  - migration: write the migration guide for our current code
  Synthesise a go/no-go recommendation.
  ```
- **Prior-art research**:
  ```text
  We want to build <X>. Spawn 3 teammates to find prior art in different
  ecosystems (one each for npm, crates.io, and PyPI). Each reports the top 3 they
  found and what made each succeed or fail.
  ```

## Watch for

- Teammates returning shallow surveys instead of pointed findings — give each one a sharper scope in the spawn prompt
- The lead synthesising before the debate round — say "wait for the debate to converge before writing the synthesis"
- Devil's advocate going off-mission and trying to be constructive — re-anchor: "your only job is to attack the others' findings"

## After

- The lead writes `RESEARCH.md`
- Teammates go idle and notify the lead
- Clean up the team — research teams are usually one-shot
