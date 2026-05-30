# MCP Server Catalog

A signal → server map for the **Recommend flow**. Only suggest a server when the repo shows the matching signal. Each entry: when to recommend + a one-line value statement. Transport noted where it isn't plain `stdio`.

## Documentation & Knowledge

### context7

- **Recommend when**: the repo uses popular libraries/SDKs — React, Vue, Angular, Next.js, Express, FastAPI, Django, Prisma, Drizzle, Stripe, Twilio, AWS SDK, LangChain, the Anthropic/OpenAI SDKs, etc.
- **Value**: Claude codes against live, up-to-date docs instead of training data — fewer hallucinated APIs and outdated patterns.

## Browser & Frontend

### Playwright MCP

- **Recommend when**: a frontend app (React/Vue/Angular) needs browser automation, E2E tests, visual checks, or form-flow validation.
- **Value**: Claude drives the running app — clicks, fills forms, takes screenshots, verifies UI behavior.

### Puppeteer MCP

- **Recommend when**: headless browser automation, web scraping, or HTML-to-PDF generation (often in CI).
- **Value**: programmatic headless browsing for extraction and report generation.

## Databases

### Supabase MCP

- **Recommend when**: `@supabase/supabase-js` in deps, or a Supabase-backed auth/database/realtime app.
- **Value**: Claude queries tables, manages auth, and touches Supabase storage directly.

### Convex MCP

- **Recommend when**: `convex` in deps, a `convex/` directory, or `convex.json` at the repo root; `useQuery`/`useMutation`/`useAction` usage. Run via `npx convex mcp start`.
- **Value**: Claude introspects the live deployment (tables, function specs, env vars, logs) and runs queries/mutations against it.

### PostgreSQL MCP

- **Recommend when**: raw `pg`/`postgres` usage with no ORM, migrations, or data-debugging needs.
- **Value**: direct SQL access for schema management, analysis, and inspecting real data.

### Neon MCP

- **Recommend when**: Neon serverless Postgres in use.
- **Value**: manage Neon branches/databases and query them directly.

### Turso MCP

- **Recommend when**: Turso / libSQL edge database in use.
- **Value**: query and manage edge SQL databases.

## Version Control & Issues

### GitHub MCP

- **Recommend when**: a GitHub remote, issue-driven development, PR workflows, or GitHub Actions.
- **Value**: Claude creates issues, reviews PRs, checks workflow runs, and manages releases.

### GitLab MCP

- **Recommend when**: a GitLab-hosted remote.
- **Value**: GitLab issue/MR/pipeline integration.

### Linear MCP

- **Recommend when**: a Linear workspace, issue refs like `ABC-123`, sprint/backlog work.
- **Value**: Claude reads, creates, and updates Linear issues from code context.

## Cloud Infrastructure

### AWS MCP

- **Recommend when**: `@aws-sdk/*` in deps, IaC (Terraform/CDK/SAM), Lambda, or S3/DynamoDB usage.
- **Value**: inspect and manage AWS resources alongside the code that uses them.

### Cloudflare MCP

- **Recommend when**: Cloudflare Workers, Pages, R2, or D1.
- **Value**: manage edge functions, static hosting, object storage, and edge SQL.

### Vercel MCP

- **Recommend when**: a Vercel-deployed project.
- **Value**: inspect deployments, env config, and project settings.

## Monitoring & Observability

### Sentry MCP

- **Recommend when**: `@sentry/*` in deps, production error tracking.
- **Value**: Claude investigates issues, finds root causes, and correlates errors with releases.

### Datadog MCP

- **Recommend when**: Datadog APM, logs, or metrics in use.
- **Value**: query traces, logs, and metrics during debugging.

## Communication

### Slack MCP

- **Recommend when**: the team uses Slack for notifications, deploy alerts, or incident response.
- **Value**: Claude posts updates and alerts to channels.

### Notion MCP

- **Recommend when**: Notion is the docs/knowledge base.
- **Value**: read, search, and update Notion pages and notes.

## Containers

### Docker MCP

- **Recommend when**: a `Dockerfile` or `docker-compose.yml` is present.
- **Value**: build images, orchestrate containers, inspect logs, exec into containers.

### Kubernetes MCP

- **Recommend when**: K8s manifests or Helm charts are present.
- **Value**: deploy/scale pods, inspect status, and read pod logs.

## Research & Persistence

### Exa MCP

- **Recommend when**: research, competitive analysis, or finding current external info is needed.
- **Value**: web search and retrieval for up-to-date information.

### Memory MCP

- **Recommend when**: long-running projects that benefit from remembered context, preferences, or patterns.
- **Value**: Claude persists context and decisions across conversations.

## Quick Reference: Detection Patterns

| Look for | Suggests |
| :-- | :-- |
| Popular npm/PyPI packages, framework SDKs | context7 |
| React / Vue / Next.js frontend | Playwright MCP |
| `@supabase/supabase-js` | Supabase MCP |
| `convex` in deps, `convex/` dir, or `convex.json` | Convex MCP |
| `pg` / `postgres` (no ORM) | PostgreSQL MCP |
| Neon connection string | Neon MCP |
| Turso / libSQL | Turso MCP |
| GitHub remote | GitHub MCP |
| GitLab remote | GitLab MCP |
| Linear refs (`ABC-123`) | Linear MCP |
| `@aws-sdk/*`, Terraform/CDK/SAM | AWS MCP |
| Cloudflare Workers / `wrangler.toml` | Cloudflare MCP |
| `vercel.json` / Vercel deploy | Vercel MCP |
| `@sentry/*` | Sentry MCP |
| Datadog SDK / config | Datadog MCP |
| `Dockerfile`, `docker-compose.yml` | Docker MCP |
| K8s manifests, Helm charts | Kubernetes MCP |
| Slack webhook URLs | Slack MCP |
| Notion as docs | Notion MCP |
| Research / web-search need | Exa MCP |
| Cross-session memory need | Memory MCP |
