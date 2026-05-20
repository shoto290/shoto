# `plugin.json` Manifest Schema

The manifest lives at `<plugin-root>/.claude-plugin/plugin.json`. It declares the plugin's identity and metadata.

## Fields

| Field | Type | Required | Purpose |
| :-- | :-- | :-- | :-- |
| `name` | string (kebab-case) | Yes | Unique identifier. Becomes the skill namespace (`/<name>:skill`). |
| `description` | string | Yes | Shown in the plugin manager when browsing or installing. |
| `version` | string (semver) | Optional | If set, users only receive updates when this field is bumped. If omitted and the plugin is distributed via git, the commit SHA is used and every commit counts as a new version. |
| `author` | object `{ name, email?, url? }` | Optional | Attribution. |
| `homepage` | string (URL) | Optional | Project homepage. |
| `repository` | string (URL) | Optional | Source repository. |
| `license` | string (SPDX id) | Optional | License identifier (e.g. `MIT`, `Apache-2.0`). |
| `settings` | object | Optional | Default settings to apply when the plugin is enabled. Overridden by a sibling `settings.json` at the plugin root. |

## Minimal example

```json
{
  "name": "my-first-plugin",
  "description": "A greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

## Full example

```json
{
  "name": "security-toolkit",
  "description": "Security review skills, agents, and hooks",
  "version": "2.3.0",
  "author": {
    "name": "Acme Security",
    "email": "security@acme.example",
    "url": "https://acme.example"
  },
  "homepage": "https://acme.example/security-toolkit",
  "repository": "https://github.com/acme/security-toolkit",
  "license": "Apache-2.0"
}
```

## Notes

- `name` is the **only** identifier — it determines the slash-command namespace. Renaming changes every `/<name>:skill` command.
- Pin `version` explicitly if you want users to upgrade deliberately. Omit it for trunk-style continuous delivery (every commit is a version).
- `settings` here is overridden by a top-level `settings.json` if both exist.
