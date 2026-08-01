# shoto

A Claude Code marketplace hosting plugins for **building Claude Code itself**.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install <plugin>@shoto
```

## Plugins

| Plugin | Description |
| :--- | :--- |
| [`advisor`](./plugins/advisor) | Coached-executor system: an executant agent that writes every change itself and self-reviews each delta with four parallel adversarial reviewers (correctness, security, scalability, craft), plus `/advisor:onboard` to set up a committed project executant and its out-of-repo ledger, and `/advisor:review` for on-demand review of the current delta. |
| [`core`](./plugins/core) | Foundation plugin for the shoto marketplace: the artifact authors (skill/subagent/hook/mcp/plugin/workflow smiths), the base skill they build on, and `/evolve` — plan and apply coordinated skill/subagent/hook/plugin/MCP changes. |
| [`git`](./plugins/git) | Git and pull-request workflows: commit changes, create PRs, and rebase branches onto the default branch with safety backups. |
| [`orchestrator`](./plugins/orchestrator) | The orchestrator agent and its `generalist` fallback writer, the base/alignment/orchestrator skills they run on, and `/onboard` to set up a committed project orchestrator. |
| [`review`](./plugins/review) | Code review automation: review the workspace diff against bug criteria, triage PR comments into verdicts, apply confirmed fixes with verification, plus `/deep-review` — a multi-lens parallel review of the whole branch. |

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
