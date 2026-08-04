import glob
import json
import os
import re
import sys

MARKETPLACE_PATH = os.path.join(".claude-plugin", "marketplace.json")
PLUGIN_MANIFEST_PATH = os.path.join(".claude-plugin", "plugin.json")
HOOKS_PATH = os.path.join("hooks", "hooks.json")
PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"
PLUGIN_ROOT_PATTERN = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?([^\s]*)")


def fail(failures, path, reason, fix):
    failures.append("MANIFEST ERROR: {} {} -> {}".format(path, reason, fix))


def load_json(failures, relative_path, fix):
    try:
        with open(relative_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as error:
        fail(
            failures,
            relative_path,
            "is not valid JSON at line {}, column {}".format(error.lineno, error.colno),
            fix,
        )
    except OSError as error:
        fail(failures, relative_path, "cannot be read ({})".format(error.strerror), fix)
    return None


def marketplace_entries(failures, document):
    plugins = document.get("plugins")
    if not isinstance(plugins, list):
        fail(
            failures,
            MARKETPLACE_PATH,
            "declares no plugins array",
            'add a "plugins": [] array with one entry per plugin directory',
        )
        return []
    entries = []
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            fail(
                failures,
                MARKETPLACE_PATH,
                "entry {} is not an object".format(index),
                "give every plugins[] entry a name and a source path",
            )
            continue
        name = entry.get("name")
        source = entry.get("source")
        if not isinstance(name, str) or not isinstance(source, str):
            fail(
                failures,
                MARKETPLACE_PATH,
                "entry {} declares no string name/source pair".format(index),
                "give every plugins[] entry a name and a source path",
            )
            continue
        entries.append((name, source))
    return entries


def check_manifest_name(failures, manifest_path, manifest, expected_name):
    declared = manifest.get("name")
    if declared == expected_name:
        return
    fail(
        failures,
        manifest_path,
        "declares name {!r} but the marketplace entry is {!r}".format(declared, expected_name),
        'set "name": "{}" so both manifests agree'.format(expected_name),
    )


def check_dependencies(failures, manifest_path, manifest, known_names):
    dependencies = manifest.get("dependencies", [])
    if not isinstance(dependencies, list):
        fail(
            failures,
            manifest_path,
            "declares dependencies that are not an array",
            'set "dependencies" to an array of bare plugin names',
        )
        return
    for dependency in dependencies:
        if dependency in known_names:
            continue
        fail(
            failures,
            manifest_path,
            "depends on {!r} which no marketplace entry provides".format(dependency),
            "add {!r} to .claude-plugin/marketplace.json or drop the dependency".format(dependency),
        )


def hook_commands(document):
    for groups in document["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                yield hook["command"]
                for argument in hook.get("args", []):
                    yield argument


def resolve_plugin_path(directory, relative):
    target = os.path.normpath(os.path.join(directory, relative.lstrip("/")))
    if not target.startswith(directory + os.sep):
        return None
    return target


def check_hook_scripts(failures, directory):
    hooks_path = os.path.join(directory, HOOKS_PATH)
    if not os.path.isfile(hooks_path):
        return
    document = load_json(failures, hooks_path, "fix the JSON syntax so the hook config parses")
    if not isinstance(document, dict):
        return
    try:
        for value in hook_commands(document):
            check_hook_references(failures, hooks_path, directory, value)
    except (AttributeError, KeyError, TypeError) as error:
        fail(
            failures,
            hooks_path,
            "has an unexpected shape ({})".format(error),
            'shape it as {"hooks": {"<Event>": [{"hooks": [{"command": "..."}]}]}}',
        )


def check_hook_references(failures, hooks_path, directory, value):
    unquoted = value.replace('"', "").replace("'", "")
    for match in PLUGIN_ROOT_PATTERN.finditer(unquoted):
        relative = match.group(1)
        if not relative:
            continue
        target = resolve_plugin_path(directory, relative)
        if target is None:
            fail(
                failures,
                hooks_path,
                "references {!r} which escapes the plugin directory".format(match.group(0)),
                "keep every {} path inside {}".format(PLUGIN_ROOT_TOKEN, directory),
            )
            continue
        if os.path.isfile(target):
            continue
        fail(
            failures,
            hooks_path,
            "references {!r} which resolves to {} and does not exist".format(
                match.group(0), target
            ),
            "create {} or fix the hook command path".format(target),
        )


def check_plugin(failures, name, source, known_names):
    directory = os.path.normpath(source)
    if not os.path.isdir(directory):
        fail(
            failures,
            MARKETPLACE_PATH,
            "entry {!r} has source {!r} which is not an existing directory".format(name, source),
            "create {} or point the source at the real plugin directory".format(directory),
        )
        return
    manifest_path = os.path.join(directory, PLUGIN_MANIFEST_PATH)
    if not os.path.isfile(manifest_path):
        fail(
            failures,
            manifest_path,
            "is missing for marketplace entry {!r}".format(name),
            'add the plugin manifest declaring "name": "{}"'.format(name),
        )
        return
    manifest = load_json(failures, manifest_path, "fix the JSON syntax so the manifest parses")
    if not isinstance(manifest, dict):
        return
    check_manifest_name(failures, manifest_path, manifest, name)
    check_dependencies(failures, manifest_path, manifest, known_names)
    check_hook_scripts(failures, directory)


def check_unlisted_plugins(failures, listed_directories):
    pattern = os.path.join("plugins", "*", PLUGIN_MANIFEST_PATH)
    for manifest_path in sorted(glob.glob(pattern)):
        directory = os.path.dirname(os.path.dirname(manifest_path))
        if directory in listed_directories:
            continue
        fail(
            failures,
            directory,
            "is not listed in {}".format(MARKETPLACE_PATH),
            "add a plugins[] entry with source ./{} or delete the directory".format(directory),
        )


def main():
    failures = []
    document = load_json(
        failures, MARKETPLACE_PATH, "fix the JSON syntax so the marketplace manifest parses"
    )
    if isinstance(document, dict):
        entries = marketplace_entries(failures, document)
        known_names = set(name for name, _ in entries)
        for name, source in entries:
            check_plugin(failures, name, source, known_names)
        check_unlisted_plugins(failures, set(os.path.normpath(source) for _, source in entries))
    elif document is not None:
        fail(
            failures,
            MARKETPLACE_PATH,
            "is not a JSON object",
            "make the marketplace manifest an object with name, owner and plugins",
        )
    for line in failures:
        sys.stderr.write("{}\n".format(line))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
