# Parallel PR review

**Use when** a single PR needs review across multiple independent lenses (security, performance, test coverage) and a sequential review tends to fixate on one type of issue at the expense of others.

## Spawn prompt

```text
Create an agent team to review PR #<NUMBER>. Spawn three reviewers:
- security: focused on security implications (auth, input validation, secrets, dependency risk)
- perf: focused on performance impact (hot paths, allocations, queries, big-O)
- tests: focused on test coverage (missing cases, brittle assertions, untested branches)
Use Sonnet for each teammate. Have them each review independently and report findings.
Then synthesise into a single review comment with severity ratings.
```

## Why this works

- Three **disjoint lenses** — reviewers don't overlap, so each is thorough on its own axis
- Explicit **names** — you can later say "ask `security` to re-check after I push the fix"
- **Same PR**, different filters — no file-ownership conflicts because the work is read-only review

## Variations

- **Pair with `subagent` definitions**: if you already have a `security-reviewer` and `perf-reviewer` defined under `.claude/agents/`, spawn the teammates from those definitions to inherit their `tools` allowlist and system prompts:
  ```text
  Spawn three reviewers using the security-reviewer, perf-reviewer, and test-reviewer
  agent types to review PR #142.
  ```
- **Require plan approval** before any "fix it" follow-up commits:
  ```text
  ... Once findings are synthesised, ask the reviewers to propose fixes but require
  plan approval before they make any changes.
  ```

## After the review

- Each reviewer reports back via the mailbox; the lead synthesises
- Ask the lead: "Clean up the team" once you've captured the synthesis
