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
| [`core`](./plugins/core) | Foundation plugin for the shoto marketplace: the artifact authors (skill/subagent/hook/mcp/plugin/workflow smiths) and the base skill they build on. |
| [`git`](./plugins/git) | Git and pull-request workflows: commit changes, create PRs, and rebase branches onto the default branch with safety backups. |
| [`inventory`](./plugins/inventory) | General-purpose codebase-inventory toolkit: nine read-only lenses that each return one unified anchored contract. |
| [`review`](./plugins/review) | Code review automation: review the workspace diff against bug criteria, triage PR comments into verdicts, and apply confirmed fixes with verification. |
| [`workflow`](./plugins/workflow) | Dynamic multi-agent workflows: fan out subagents at scale and return only the final result. Ships /evolve and /deep-review. |

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
