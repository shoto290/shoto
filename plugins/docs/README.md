# docs

A Claude Code plugin for **documentation creation workflows** powered by [Mintlify](https://www.mintlify.com/). Scaffold a docs site, author MDX pages, and validate before pushing. Requires the `mint` CLI (`npm i -g mint`) and a GitHub remote for auto-deploy.

## Install

```bash
# inside Claude Code
/plugin marketplace add shoto290/shoto
/plugin install docs@shoto
```

After install, run `/help` to see the `docs:` skills and `/agents` to confirm the `docs-architect` sub-agent is registered.

## What's inside

### Skills (`/docs:<name>`)

| Skill | Purpose |
| :--- | :--- |
| `/docs:mintlify-init` | Scaffold a new Mintlify docs site in the current repo via `mint new`, then patch `docs.json` with site name, primary color, and GitHub repo URL. |
| `/docs:mintlify-page` | Author a new MDX page (optionally from existing source code via `explore:explore`), delegate to the `docs-architect` sub-agent which drafts the page and wires it into `docs.json` navigation. |
| `/docs:mintlify-validate` | Run `mint validate` and `mint build` against the docs site and report broken links, invalid frontmatter, and missing navigation entries. Read-only. |

### Sub-agents

| Agent | When it fires |
| :--- | :--- |
| `docs-architect` | Owns the full lifecycle of Mintlify docs artifacts: **CREATE** new MDX pages (with house style + Mintlify components), **READ** / audit the site to surface orphans, dangling refs, and style violations, **UPDATE** existing pages or `docs.json` navigation surgically. Auto-delegated by `docs:mintlify-page`; invocable directly for audits and refactors. |

## Typical flow

1. `/docs:mintlify-init demo-docs` — scaffold a new docs site.
2. `/docs:mintlify-page "Rate limits" Concepts` — author a new page (or `--from-code <path>` to document existing code).
3. `/docs:mintlify-validate` — verify the build is clean.
4. Commit and `/git:create` — Mintlify auto-deploys on push.

## Repo

[github.com/shoto290/shoto](https://github.com/shoto290/shoto)
