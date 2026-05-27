# Curated Technique Catalog

Nine techniques selected from the Asana list of 29 brainstorming methods, kept only when they work in a 1-on-1 Claude exchange. Group-only techniques (Charrette, Brainwriting, eyes-closed image, change of scenery, brain-netting, walking outside, multiple rooms) are excluded — they require co-located humans.

## When to use what

| Idea type | Recommended technique(s) |
|-----------|--------------------------|
| New product / feature exploration | Starbursting, SCAMPER, What-if |
| Problem-solving | 5 Whys, Reverse, Six Hats |
| Root-cause analysis | 5 Whys |
| Decision between options | SWOT, How-Now-Wow, Six Hats |
| Prioritization of a shortlist | How-Now-Wow |
| Rapid divergence on an open question | Crazy 8, What-if |
| Stress-testing an existing idea | Reverse, SWOT, Six Hats |
| Adapting an existing thing to a new context | SCAMPER, What-if |

In Phase 2.a, pick 1 or 2 techniques whose row matches the idea type. In Phase 2.c, use **SWOT** for decision/evaluation flavors and **How-Now-Wow** for prioritization flavors.

---

## 1. Starbursting

- **EN/FR**: Starbursting / Starbursting (no common French translation).
- **One-liner**: Ask Who / What / When / Where / Why / How systematically around the idea.
- **When to use**: deep analysis of a new product or feature; surface unknown unknowns.
- **Prompt template**: "For the question <Q>, generate at least one concrete sub-question and one candidate idea under each of: Who, What, When, Where, Why, How."
- **Output shape**: six-section numbered list, one section per W/H question.

## 2. 5 Whys

- **EN/FR**: 5 Whys / Les 5 pourquoi.
- **One-liner**: Ask "why?" five times in a row to drill from symptom to root cause.
- **When to use**: root-cause analysis; understanding why a problem persists.
- **Prompt template**: "Start with the observed symptom <S>. Ask 'Why?' Generate the answer. Then ask 'Why?' on that answer. Repeat five levels deep."
- **Output shape**: linear tree of 5 levels; one line per level.

## 3. SCAMPER

- **EN/FR**: SCAMPER / SCAMPER.
- **One-liner**: Vary an existing idea via Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse.
- **When to use**: adapting an existing product/feature; generating variants from a baseline.
- **Prompt template**: "For the baseline <B>, generate one concrete variation under each SCAMPER lens: Substitute X, Combine with Y, Adapt from Z, Modify by …, Put to other use as …, Eliminate …, Reverse by …"
- **Output shape**: 7-row numbered list, one row per SCAMPER letter.

## 4. SWOT

- **EN/FR**: SWOT / SWOT (forces, faiblesses, opportunités, menaces).
- **One-liner**: Map Strengths, Weaknesses, Opportunities, Threats for a candidate idea.
- **When to use**: evaluation of one or a few candidates; decision support.
- **Prompt template**: "For candidate <C>, fill a 2×2 matrix: internal Strengths, internal Weaknesses, external Opportunities, external Threats. At least 2 bullets per quadrant."
- **Output shape**: 2×2 Markdown table or four-section bullet list.

## 5. How-Now-Wow matrix

- **EN/FR**: How-Now-Wow / Matrice How-Now-Wow.
- **One-liner**: Plot each idea on two axes — originality (low/high) and feasibility (easy/hard).
- **When to use**: prioritizing a shortlist of 3–5 candidates after divergence.
- **Prompt template**: "Place each shortlisted idea into one of three buckets: NOW (easy + low originality — quick wins), HOW (hard + high originality — future bets), WOW (easy + high originality — sweet spot). Justify each placement in one sentence."
- **Output shape**: Markdown table with columns `Idea | Bucket (Now/How/Wow) | Justification`.

## 6. Reverse brainstorming

- **EN/FR**: Reverse brainstorming / Brainstorming inversé.
- **One-liner**: Invert the question — how would I cause or worsen the problem? — then invert the answers back.
- **When to use**: unblocking a stuck session; finding fresh angles on a well-worn problem.
- **Prompt template**: "Restate the question as its inverse: 'How could I deliberately cause/worsen <problem>?' Generate ≥ 8 ways. Then invert each one back into a solution candidate."
- **Output shape**: two parallel numbered lists (inverse ideas → re-inverted candidates).

## 7. Six Thinking Hats

- **EN/FR**: Six Thinking Hats / Les six chapeaux de Bono.
- **One-liner**: Examine the idea through six successive lenses — facts, emotions, caution, optimism, creativity, process.
- **When to use**: 360° stress-test of an existing idea; surfacing blind spots.
- **Prompt template**: "Walk the idea through each hat in order: White (facts/data only), Red (gut/emotions), Black (caution/risks), Yellow (optimism/benefits), Green (creativity/alternatives), Blue (process/next steps). Claude plays all six hats sequentially in a single pass."
- **Output shape**: 6-section list, one heading per hat.

## 8. What-if

- **EN/FR**: What-if / Et si…
- **One-liner**: Generate a series of "What if …" hypotheticals to shift the problem's context.
- **When to use**: exploring a new product idea; loosening constraints; surfacing assumptions.
- **Prompt template**: "Generate ≥ 8 hypothetical 'What if …' statements that change a key constraint of the question (budget, time, audience, scale, regulation, tech stack). For each, sketch the implication in one line."
- **Output shape**: numbered list `What if … → implication`.

## 9. Crazy 8

- **EN/FR**: Crazy 8s / Crazy 8s.
- **One-liner**: Generate exactly 8 distinct ideas in a single fast pass.
- **When to use**: rapid divergence early in a session; opening up an under-explored question.
- **Prompt template**: "Generate exactly 8 distinct ideas for the question <Q>. No filtering, no ranking, no commentary between them. The original method time-boxes to 8 minutes — Claude generates synchronously, so the time-box is dropped, but the count of 8 is non-negotiable."
- **Output shape**: numbered list, exactly 8 items.

---

## Excluded techniques (and why)

These appear in the Asana list of 29 but are dropped — they require physical co-presence, multiple humans, or non-textual modalities:

- **Charrette** — requires multiple rooms and group rotations.
- **Brainwriting / 6-3-5** — requires multiple human participants writing in parallel.
- **Eyes-closed image** — requires guided physical imagery.
- **Change of scenery / walking outside** — physical environment shift.
- **Brain-netting** — virtual group whiteboard with multiple humans.
- **Round-robin** — requires a turn-based human group.
- **Step-laddering** — requires staggered entry of multiple participants.

A 1-on-1 Claude session cannot fake these, so they are not in the catalog.
