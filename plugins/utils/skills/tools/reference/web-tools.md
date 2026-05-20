# Web tools

Covers: `WebFetch`, `WebSearch`.

## WebFetch

**Summary.** Fetches a URL and runs the body through a small extraction model using your `prompt`. Returns the model's extraction, not the raw page.

**Permission rule.** `WebFetch(domain:<host>)` — host only, no scheme, no path.

Examples:

- `WebFetch(domain:docs.claude.com)` — allow that host.
- `WebFetch(domain:*)` — typically used in a `deny` rule.

**Parameters.**

- `url` (required).
- `prompt` (required) — what to extract.

**Behaviour.**

- HTTP URLs are auto-upgraded to HTTPS.
- Cross-host redirects are **not** followed transparently. The response notes the redirect target; you must issue a fresh `WebFetch` for the new host.
- Responses are **cached for 15 minutes** — quick to call twice, but stale data is a real risk.
- Output is **lossy**. The page is summarised, not returned verbatim.

**Pitfalls.**

- Using `WebFetch` when you need raw HTML / JSON — use `Bash curl` instead.
- Relying on `WebFetch` to chase a 30x redirect chain across domains — it stops at the first cross-host hop.
- Stale cached answers after a doc page changed — the cache wins for 15 minutes.

**Worked example.**

```text
WebFetch(
  url="https://docs.claude.com/en/docs/claude-code/tools",
  prompt="List every tool name and one-line summary."
)
```

For raw bytes:

```text
Bash(command="curl -fsSL https://example.com/api.json")
```

## WebSearch

**Summary.** Performs a web search and returns ranked results (title, URL, short snippet).

**Permission rule.** `WebSearch` (bare). No specifier needed.

**Parameters.**

- `query` (required).
- `allowed_domains` / `blocked_domains` — optional host filters.

**Behaviour.**

- US-only by default.
- Returns titles + URLs + snippets — NOT the page body. Follow up with `WebFetch` to read a specific hit.
- Use for "what's the current X" or to discover an unknown URL.

**Pitfalls.**

- Expecting page content from `WebSearch` directly — chain with `WebFetch`.
- Using `WebSearch` when you already know the URL — go straight to `WebFetch`.
- Searching for version-specific facts without the version in the query — generic hits dominate.
