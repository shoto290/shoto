# Discovery Check

Validates that a new or modified `description` / `when_to_use` fires on the right requests and does not collide with a sibling. Run it only when a `description` or a `when_to_use` is newly written or modified. The rules for writing the description itself live in [Trigger-rich descriptions](../../skill/SKILL.md#trigger-rich-descriptions); the exemplar to imitate is [git-flow](../../../../git/agents/git-flow.md).

## Collision scan

The mechanically verifiable half, and the only half the validation gate checks. Its output — the reported result — is a written list of the overlapping siblings and the boundary clause chosen for each.

1. Grep the `description` field of every sibling artifact in the same target scope — both surfaces:

```bash
grep -h "^description:" <scope>/skills/*/SKILL.md
grep -h "^description:" <scope>/agents/*.md
```

2. List the siblings whose capability wording overlaps the new artifact: same verb, same object, or same domain noun.
3. For each overlap, require an explicit "Not for X — use Y instead" clause in the new `description`, naming the sibling by its invocation name.

## Trigger draft

A drafting aid, not a gate check. From the frontmatter alone — no body, no file path — write:

- Three user phrasings that must trigger the artifact.
- Three near-miss phrasings that must not: an adjacent tool, an adjacent stack, or an adjacent step of the same workflow.

If a near-miss would plausibly trigger, the description is too broad — narrow it before writing the file.
