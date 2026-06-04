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
| [`core`](./plugins/core) | Foundation plugin for the shoto marketplace: artifact authors (skill/subagent/hook/mcp/plugin/workflow smiths), the alignment + base skills, the orchestrator agent, and shared infrastructure. |
| [`git`](./plugins/git) | Git and pull-request workflows: commit changes, create PRs, and rebase branches onto the default branch with safety backups. |
| [`backend-engineer`](./plugins/backend-engineer) | Ships the backend-engineer subagent: a server-side specialist for designing APIs, modeling data, and building secure, observable, resilient services, with seven bundled skills. |
| [`design-engineer`](./plugins/design-engineer) | Ships the design-engineer subagent: a front-end specialist (React + TypeScript) for building, using, and refactoring design systems, with seven bundled skills. |
| [`designer`](./plugins/designer) | Ships the designer subagent: a product/UI design specialist for design systems, Figma and Paper.design canvases, typography, accessibility, and design-to-dev handoff. |
| [`engineering`](./plugins/engineering) | Bundles eight focused senior-developer craft skills that dev subagents preload by default to write and review code with senior judgment. |
| [`explore`](./plugins/explore) | Codebase-grounded external research: precise library docs (context7), conventions/best-practices, and focused web search tied to how this repo actually uses things. |
| [`inventory`](./plugins/inventory) | General-purpose codebase-inventory toolkit: nine read-only lenses that each return one unified anchored contract. |
| [`review`](./plugins/review) | Code review automation: review the workspace diff against bug criteria, triage PR comments into verdicts, and apply confirmed fixes with verification. |
| [`workflow`](./plugins/workflow) | Dynamic multi-agent workflows: fan out subagents at scale and return only the final result. Ships /evolve, /deep-review, and /onboard. |

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
