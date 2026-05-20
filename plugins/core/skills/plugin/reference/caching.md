# Plugin Caching and File Resolution

Plugins reach Claude Code through two mechanisms:

- `claude --plugin-dir` / `claude --plugin-url` — session-only.
- Marketplace install — persistent across sessions.

For security and verification, Claude Code COPIES marketplace plugins to the local plugin cache (`~/.claude/plugins/cache`) rather than using them in place.

## Version directories

Each installed version of a plugin is a separate directory in the cache.

- On update or uninstall, the previous version is marked orphaned and removed automatically after 7 days.
- The grace period lets concurrent sessions that already loaded the old version keep running with their original paths.
- `Glob` and `Grep` tools skip orphaned directories.

## Path traversal limitations

Installed plugins CANNOT reference files outside their own directory. Paths like `../shared-utils` do not work post-install because external files are not copied into the cache.

## Share files within a marketplace with symlinks

Symlinks INSIDE the plugin directory are supported, with behavior depending on the target:

| Target | Behavior |
| :-- | :-- |
| Inside the plugin's own directory | Symlink preserved as a relative symlink in the cache; resolves to the copied target. |
| Elsewhere in the SAME marketplace | Symlink is DEREFERENCED. Target content is copied into the cache in place. Lets a meta-plugin's `skills/` link to skills defined by sibling plugins. |
| Outside the marketplace | Symlink is SKIPPED for security. Prevents pulling arbitrary host files into the cache. |

For `--plugin-dir` or local-path installs, only symlinks resolving within the plugin's own directory are preserved. All others are skipped.

## Example

```bash
ln -s ../../shared-plugin/skills/foo ./skills/foo
```

On Windows, use `mklink /D` from an elevated Command Prompt, or run with Developer Mode enabled.
