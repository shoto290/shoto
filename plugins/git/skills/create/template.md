# PR body template

Fill in this skeleton, then hand the result to `gh pr create --body`.

````
## Summary

- <imperative sentence describing a user-visible change>
- <imperative sentence describing another user-visible change>

## Changes

```mermaid
flowchart LR
  subgraph API["api/"]
    PAY["+ payments/"]
    ORD["~ orders/service.ts"]
  end
  subgraph WEB["web/"]
    CO["+ app/checkout/page.tsx"]
  end
  CO --> PAY
  PAY --> ORD
```
````

`## Summary` is 1 to 4 bullets for non-developers. `## Changes` is a mermaid canvas for reviewers — include it only when the change moves structure. For the wording rules, the canvas rules, sample outputs, the opt-in `## Test plan` section, and what to avoid, see [reference/pr-body-rules.md](./reference/pr-body-rules.md).
