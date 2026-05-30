# Transports & Scopes

How an MCP server connects, where it's configured, and how to debug it. Used by the **Add** and **Debug** flows.

## Transports

| Transport | Shape | Use when |
| :-- | :-- | :-- |
| **stdio** | Local `command` + `args`; Claude spawns the process and talks over stdin/stdout | The server runs locally as a binary or npm/PyPI package (the common case) |
| **SSE** | Remote URL, server-sent-events stream | The vendor exposes a streaming SSE endpoint |
| **HTTP** | Remote URL, request/response | The vendor exposes a plain HTTP endpoint |

stdio config carries `command`/`args`/`env`; SSE and HTTP carry a `url` (and optional `headers`). Picking the wrong transport for a server is the most common "won't connect" failure.

## Scopes

| Scope | Where it lives | Shared? |
| :-- | :-- | :-- |
| **Project** | `.mcp.json` at the repo root | Yes — checked into git, everyone on the team gets it |
| **Local** | Stored per-project, not committed (`claude mcp add --scope local`) | No — only your machine, this repo |
| **User** | `~/.claude.json` (`claude mcp add --scope user`) | No — only you, across all your projects |

**Team tip:** check `.mcp.json` into git so the whole team gets the same MCP servers automatically. Reserve local/user scope for personal or machine-specific servers.

## Two ways to register

### Edit `.mcp.json` directly (project scope)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp",
      "headers": { "Authorization": "Bearer ${SENTRY_TOKEN}" }
    }
  }
}
```

If `mcpServers` already exists, add the new server as a **sibling key** — don't replace the whole object.

### `claude mcp add` (CLI)

```bash
# stdio, project scope (writes to .mcp.json)
claude mcp add github --scope project -- npx -y @modelcontextprotocol/server-github

# HTTP, user scope
claude mcp add --scope user --transport http sentry https://mcp.sentry.dev/mcp
```

## Secrets via Environment Variables

Never inline a token. Reference an env var the user exports in their shell:

```json
{ "env": { "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}" } }
```

For HTTP/SSE, put it in a header: `"Authorization": "Bearer ${API_TOKEN}"`. Tell the user which variable to export — do not ask them to paste the value.

## Debugging

- **`claude --mcp-debug`** — launches with verbose MCP logging; shows the connection handshake and the server's stdout/stderr.
- **`/mcp`** (in-session) — lists connected servers and their status; confirms what actually loaded.
- **Common failures:**
  - Wrong transport (stdio config for a remote endpoint, or HTTP for a local command).
  - Missing env var — server starts but auth fails because `${VAR}` resolved empty.
  - Bad binary / package path — `command` not on `PATH`, or wrong package name.
  - Process exits immediately — run the `command` + `args` by hand in a terminal to read the real error.
