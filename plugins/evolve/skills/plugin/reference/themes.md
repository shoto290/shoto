# Color Themes (Experimental)

Plugins can ship color themes that appear in `/theme` alongside the built-in presets and the user's local themes. A theme is a JSON file in `themes/` with a `base` preset and a sparse `overrides` map of color tokens.

Themes are an EXPERIMENTAL component — the manifest schema may change. Declare with `experimental.themes` in `plugin.json`.

## Example

`themes/dracula.json`:

```json
{
  "name": "Dracula",
  "base": "dark",
  "overrides": {
    "claude": "#bd93f9",
    "error": "#ff5555",
    "success": "#50fa7b"
  }
}
```

Manifest:

```json
{
  "experimental": {
    "themes": ["./themes/"]
  }
}
```

## Behavior

- Selecting a plugin theme persists `custom:<plugin-name>:<slug>` in the user's config.
- Plugin themes are READ-ONLY. Pressing `Ctrl+E` on one in `/theme` copies it into `~/.claude/themes/` so the user can edit the copy without modifying the plugin.
