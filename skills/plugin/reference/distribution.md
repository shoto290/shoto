# Distribution

How to ship a plugin: marketplace schema, version management, community submission.

## `marketplace.json` Schema

A marketplace is a directory containing `.claude-plugin/marketplace.json`. The file lists plugins the marketplace exposes.

```json
{
  "name": "acme-marketplace",
  "owner": { "name": "Acme Inc." },
  "plugins": [
    {
      "name": "security-toolkit",
      "source": "./security-toolkit"
    },
    {
      "name": "release-helpers",
      "source": "github:acme/release-helpers"
    }
  ]
}
```

| Field | Required | Purpose |
| :-- | :-- | :-- |
| `name` | Yes | Marketplace identifier. Used as `@<name>` when installing. |
| `owner.name` | Yes | Display name for the marketplace owner. |
| `plugins[].name` | Yes | Plugin identifier (matches `plugin.json` `name`). |
| `plugins[].source` | Yes | Where to fetch the plugin from. Supports relative paths (`./<dir>`), git refs (`github:owner/repo`), and `https://` URLs to a zip. |

Users add a marketplace with:

```bash
/plugin marketplace add <owner>/<repo>
/plugin install <plugin-name>@<marketplace-name>
```

Private repos work transparently when the user has `gh` / GitHub credentials available locally.

## Version Management

Two strategies:

| Strategy | When to use | Behavior |
| :-- | :-- | :-- |
| Explicit `version` in `plugin.json` | Stable releases, semver discipline | Users only see updates when the field is bumped. |
| Omit `version` | Trunk-style continuous delivery | Commit SHA becomes the version — every commit is a release. |

Recommendation: pin `version` for shared plugins, omit it for personal experiments.

## Community Marketplace Submission

Anthropic runs two public marketplaces:

| Marketplace | How it works |
| :-- | :-- |
| `claude-plugins-official` | Curated by Anthropic. Auto-available in every install. No application form — Anthropic adds plugins at its discretion. |
| `claude-community` | Public catalog at [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community). Users add it with `/plugin marketplace add anthropics/claude-plugins-community` and install as `@claude-community`. |

Submit to `claude-community` via:

- Claude.ai — <https://claude.ai/settings/plugins/submit>
- Console — <https://platform.claude.com/plugins/submit>

Before submitting, run:

```bash
claude plugin validate
```

The review pipeline runs the same validator plus automated safety screening. Approved plugins are pinned to a commit SHA in the catalog, and CI bumps the pin as you push new commits. The catalog syncs nightly, so expect a delay between approval and the plugin appearing in `marketplace.json`.

If Anthropic lists your plugin in `claude-plugins-official`, your CLI can prompt Claude Code users to install it via plugin hints.

## Pre-submission Checklist

1. `claude plugin validate` passes locally.
2. `README.md` present with install + usage instructions.
3. `version` pinned in `plugin.json`.
4. Every component (skills, agents, hooks) tested via `--plugin-dir`.
5. No secrets in the repo (`.env`, keys, tokens).
6. License declared in `plugin.json` and (ideally) a top-level `LICENSE` file.
