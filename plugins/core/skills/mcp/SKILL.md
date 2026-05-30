---
name: mcp
description: 'Understand, recommend, configure, and debug project-level MCP (Model Context Protocol) servers — the external tools and services Claude connects to over stdio, SSE, or HTTP.'
when_to_use: 'Use when the user wants to learn how MCP works, decide which server fits a need, scan a repo and recommend servers, add a server to a project `.mcp.json` or `~/.claude.json`, run `claude mcp add`, pick a transport or scope, handle secrets via env vars, or debug a server that will not connect. Triggers on: mcp, mcp server, .mcp.json, claude mcp add, connect MCP, configure MCP, debug MCP, --mcp-debug, recommend an MCP server, which MCP server, stdio/SSE/HTTP transport, mcpServers, context7, Playwright MCP, Puppeteer MCP, Supabase MCP, Convex MCP, Postgres MCP, Neon MCP, Turso MCP, GitHub MCP, GitLab MCP, Linear MCP, AWS MCP, Cloudflare MCP, Vercel MCP, Sentry MCP, Datadog MCP, Slack MCP, Notion MCP, Docker MCP, Kubernetes MCP, Exa MCP, Memory MCP. This skill covers MCP at the project/repo level (`.mcp.json`, `claude mcp add`, `~/.claude.json`). For MCP bundled and distributed inside a plugin (`.mcp.json` at the plugin root, `mcpServers` in `plugin.json`), route to `core:plugin`.'
argument-hint: '[recommend | add <server> | debug | explain]'
---

# MCP

An **MCP server** is an external process or endpoint that exposes tools, resources, and prompts to Claude over the Model Context Protocol. Claude connects to it over one of three transports (stdio, SSE, HTTP) and gains capabilities the built-in tools don't have: query a live database, drive a browser, read Sentry issues, search the web, persist memory across sessions.

This skill covers MCP at the **project / repo level**:

- Project `.mcp.json` (checked into git, shared with the team)
- `claude mcp add ...` (CLI registration)
- User `~/.claude.json` (your personal servers, all projects)

For MCP **bundled and distributed inside a plugin** (`.mcp.json` at the plugin root, the `mcpServers` field in `plugin.json`), route to [skills/plugin/SKILL.md](../plugin/SKILL.md) (`core:plugin`).

## BLOCKING — Secrets Safety

- **Never read `.env`, `.env.*`, `secrets/`, `*.pem`, `*.key`, or `*.cert`** (inherits the repo AGENTS.md protected-files rule).
- **Never inline an API key or token into `.mcp.json` or any config you write.** Always reference an environment variable instead:

  ```json
  { "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" } }
  ```

  For HTTP/SSE servers, put the secret in a header that resolves from the environment (`"Authorization": "Bearer ${API_TOKEN}"`). If a server genuinely needs a secret, tell the user which env var to export — do not ask them to paste the value to you.

## Detect intent

If invoked as `/mcp <action>`, treat `$ARGUMENTS` as the action: `recommend`, `add <server>`, `debug`, or `explain`.

1. **`recommend` / "which MCP server" / "what would help here"** → **Recommend flow**
2. **`add <server>` / "configure MCP" / "connect …"** → **Add flow**
3. **`debug` / "MCP won't connect" / "server not starting"** → **Debug flow**
4. **`explain` / "how does MCP work" / empty** → **Explain flow** — do not write files

---

## Recommend flow

Map real repo signals to servers — never recommend a server for a service the repo doesn't use.

### 1. Scan the repo for signals

Delegate the repo signal scan to [explore:explore](../../../explore/skills/explore/SKILL.md) (`explore:explore`) rather than reading source files directly from this flow. Ask it to surface: dependency manifests (`package.json`, `pyproject.toml`, `go.mod`, …), framework/ORM usage, database drivers, the git remote host, IaC and container files (`docker-compose.yml`, K8s manifests, Terraform), and monitoring SDKs. To discover canonical mappings for other intents, invoke `core:skills-suggest`.

### 2. Map signals to the catalog

Match the returned signals against [reference/mcp-server-catalog.md](./reference/mcp-server-catalog.md). The "Detection patterns" table there is the fast path (signal → server).

### 3. Propose

Propose **1–2 servers per genuine need**, each with a one-line *why* tied to the signal you found. Skip anything speculative. Then offer to wire up the chosen ones via the Add flow.

---

## Add flow

### 1. Pick the scope

Surface this with `AskUserQuestion` before writing anything:

| Scope | Where | Best for |
| :-- | :-- | :-- |
| **Project (recommended)** | `.mcp.json` at repo root, checked into git | Teams — everyone gets the same servers |
| **Local** | `claude mcp add --scope local …` (stored per-project, not shared) | Personal/experimental servers in one repo |
| **User** | `~/.claude.json` (or `claude mcp add --scope user …`) | Your own servers across all projects |

Default to **project** unless the server is personal or holds machine-specific paths. See [reference/transports-and-scopes.md](./reference/transports-and-scopes.md).

### 2. Pick the transport

`stdio` (local command, the common case), `SSE` (remote streaming endpoint), or `HTTP` (remote request/response). The catalog entry tells you which one a given server uses.

### 3. Produce the config

Either a `.mcp.json` entry **or** the equivalent `claude mcp add` command — match the chosen scope. Reference secrets via env vars only (see the Secrets Safety block above).

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest"],
      "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" }
    }
  }
}
```

If `.mcp.json` already has an `mcpServers` block, **add the new server as a sibling key** — don't replace the whole object.

### 4. Tell the user how to load it

New `.mcp.json` servers prompt for trust on next session start. After registering, the user restarts Claude (or runs `/mcp` to inspect connected servers).

---

## Debug flow

1. **Reproduce with diagnostics on**: `claude --mcp-debug` surfaces the server's stdout/stderr and the connection handshake.
2. **Check the usual suspects** (see [reference/transports-and-scopes.md](./reference/transports-and-scopes.md#debugging)):
   - Wrong transport (configured `stdio` for a remote HTTP endpoint, or vice versa).
   - Missing env var — the server starts but auth fails because `${API_TOKEN}` resolved empty.
   - Bad binary / package path — `command` not on `PATH`, or the npm package name is wrong.
   - Server process exits immediately — run the `command` + `args` by hand in a terminal to see the real error.
3. **Inspect connected servers** with `/mcp` inside the session to confirm what actually loaded.

---

## Explain flow

If the user just wants to understand MCP, answer conceptually and **write nothing**:

| Question | Where |
| :-- | :-- |
| What is MCP? What does a server give Claude? | This file's intro + [reference/mcp-server-catalog.md](./reference/mcp-server-catalog.md) |
| stdio vs SSE vs HTTP? Which scope? | [reference/transports-and-scopes.md](./reference/transports-and-scopes.md) |
| Project vs plugin-bundled MCP? | This file's intro — plugin-bundled MCP routes to `core:plugin` |
| How do I debug a server? | [reference/transports-and-scopes.md](./reference/transports-and-scopes.md#debugging) |

---

## Critical principles

- **Recommend from evidence, not vibes.** A server is only worth suggesting if the repo actually uses the matching service. One real signal beats five plausible guesses.
- **Secrets via env, always.** Inlining a token into `.mcp.json` leaks it to git. Reference `${VAR}` and tell the user which var to export.
- **Project `.mcp.json` is a team contract.** Checking it in gives the whole team identical servers — that's the point. Use local/user scope for anything personal or machine-specific.
- **Project ≠ plugin.** Project-level MCP lives in `.mcp.json` / `~/.claude.json`. Plugin-bundled MCP ships inside a plugin and is owned by `core:plugin`.
- **Match the transport to the server.** stdio for local commands, SSE/HTTP for remote endpoints. The wrong transport is the most common "won't connect" cause.

## Reference

- [reference/mcp-server-catalog.md](./reference/mcp-server-catalog.md) — signal → server catalog with one-line value statements and a detection-patterns table
- [reference/transports-and-scopes.md](./reference/transports-and-scopes.md) — stdio/SSE/HTTP transports, the three scopes, team sharing, secrets-via-env, `claude --mcp-debug`
