# `plugin.json` Manifest Schema

The manifest lives at `<plugin-root>/.claude-plugin/plugin.json`. It declares the plugin's identity, metadata, and where to find every component.

## Complete schema example

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "security-toolkit",
  "displayName": "Security Toolkit",
  "version": "2.3.0",
  "description": "Security review skills, agents, and hooks",
  "author": {
    "name": "Acme Security",
    "email": "security@acme.example",
    "url": "https://acme.example"
  },
  "homepage": "https://acme.example/security-toolkit",
  "repository": "https://github.com/acme/security-toolkit",
  "license": "Apache-2.0",
  "keywords": ["security", "review", "sast"],
  "skills": ["./skills/"],
  "commands": ["./commands/"],
  "agents": ["./agents/"],
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json",
  "outputStyles": ["./output-styles/"],
  "lspServers": "./.lsp.json",
  "experimental": {
    "themes": ["./themes/"],
    "monitors": "./monitors/monitors.json"
  },
  "userConfig": {
    "api_token": {
      "type": "string",
      "title": "API token",
      "description": "Authentication token",
      "sensitive": true
    }
  },
  "channels": [],
  "dependencies": ["helper-lib"]
}
```

## Required fields

Only `name` is required.

| Field | Rule |
| :-- | :-- |
| `name` | Kebab-case identifier, no spaces. Used for namespacing as `<plugin-name>:<component-name>`. |

## Metadata fields

| Field | Type | Purpose |
| :-- | :-- | :-- |
| `$schema` | string | URL for editor autocomplete. Ignored at load time. Example: `https://json.schemastore.org/claude-code-plugin-manifest.json`. |
| `displayName` | string (v2.1.143+) | Human-readable name. May contain spaces and any casing. Falls back to `name`. NOT used for lookup. |
| `version` | string (semver) | Pins the plugin to that version string. If omitted, falls back to the git commit SHA. `plugin.json` value wins over a `version` set in the marketplace entry. |
| `description` | string | Shown in the plugin manager when browsing or installing. |
| `author` | object `{ name, email?, url? }` | Attribution. |
| `homepage` | string (URL) | Project homepage. |
| `repository` | string (URL) | Source repository. |
| `license` | string (SPDX id) | e.g. `MIT`, `Apache-2.0`. |
| `keywords` | array of strings | Discovery tags surfaced in marketplaces. |

## Component path fields

Every component field points at either a file or a directory under the plugin root. See [reference/structure.md](./structure.md) for how custom paths interact with default locations.

| Field | Type | Description | Example |
| :-- | :-- | :-- | :-- |
| `skills` | string \| array | Skill directories. Custom paths ADD to the default `skills/`. | `["./skills/", "./extras/"]` |
| `commands` | string \| array | Command directories. REPLACES default `commands/` when set. | `"./commands/"` |
| `agents` | string \| array | Agent directories. REPLACES default `agents/`. | `"./agents/"` |
| `hooks` | string \| object | Path to `hooks.json` or inline hooks object. | `"./hooks/hooks.json"` |
| `mcpServers` | string \| object | Path to `.mcp.json` or inline MCP config. | `"./.mcp.json"` |
| `outputStyles` | string \| array | Output-style directories. REPLACES default `output-styles/`. | `["./output-styles/"]` |
| `lspServers` | string \| object | Path to `.lsp.json` or inline LSP config. | `"./.lsp.json"` |
| `experimental.themes` | string \| array | Theme directories. REPLACES default `themes/`. See [reference/themes.md](./themes.md). | `["./themes/"]` |
| `experimental.monitors` | string \| object | Path to monitors config. Inline object also accepted. See [reference/structure.md](./structure.md). | `"./monitors/monitors.json"` |
| `userConfig` | object | Prompted values exposed as `${user_config.KEY}`. See [reference/user-config.md](./user-config.md). | see [reference/user-config.md](./user-config.md) |
| `channels` | array | Messaging channels backed by an MCP server. See [reference/channels.md](./channels.md). | see [reference/channels.md](./channels.md) |
| `dependencies` | array | Other plugins this one requires. See [reference/dependencies.md](./dependencies.md). | `["helper-lib"]` |

## Unrecognized fields

Claude Code IGNORES top-level fields it does not recognize. This keeps `plugin.json` compatible with VS Code/Cursor/`npm` `package.json` manifests.

- `claude plugin validate` reports unrecognized fields as WARNINGS, not errors.
- One-or-two-character typos trigger suggestions ("did you mean `keywords`?").
- Wrong types still fail. Example: `keywords` declared as a string instead of an array is a LOAD error, not a warning.
- Pass `--strict` to escalate warnings to errors:

```bash
claude plugin validate ./my-plugin --strict
```

## Experimental components

`experimental.themes` and `experimental.monitors` are stabilizing — their manifest schema may change between releases.

- Top-level `themes` and `monitors` still work for backwards compatibility, but `claude plugin validate` warns about them.
- A future release will require the `experimental.*` prefix.

## Minimal example

```json
{
  "name": "my-first-plugin",
  "description": "A greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

## Notes

- `name` is the only identifier — it determines the slash-command namespace. Renaming changes every `/<name>:component` command.
- Pin `version` explicitly if you want users to upgrade deliberately. Omit it for trunk-style continuous delivery (every commit is a version).
- Inline objects for `hooks`, `mcpServers`, `lspServers`, `experimental.monitors` are equivalent to pointing at the corresponding JSON file. Prefer files for larger configs.
