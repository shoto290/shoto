import os
import re
import sys

FRONTMATTER_DELIMITER = "---"
FIELD_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INJUNCTIONS = tuple(
    (word, re.compile(r"\b" + word + r"\b", flags))
    for word, flags in (
        ("proactively", re.IGNORECASE),
        ("use immediately", re.IGNORECASE),
        ("MUST", 0),
        ("ALWAYS", 0),
        ("IMPORTANT", 0),
    )
)
EXTERNAL_LINK_PREFIXES = ("http://", "https://", "mailto:")
BLOCK_SCALAR_PREFIXES = ("|", ">")
MAX_NAME_CHARS = 64
MAX_COMBINED_DESCRIPTION_CHARS = 1536
MAX_SKILL_LINES = 500


def ok(check):
    sys.stdout.write("PASS: {}\n".format(check))


def fail(failures, code, problem, fix):
    failures.append("{} ERROR: {} -> {}".format(code, problem, fix))


def read_lines(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def find_frontmatter_end(lines):
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            return index
    return None


def describe_frontmatter_problem(path, lines):
    if not lines:
        return "{} is empty".format(path)
    if lines[0].strip() != FRONTMATTER_DELIMITER:
        return "{} does not open with --- on line 1 (found {!r})".format(path, lines[0][:60])
    return "{} opens a frontmatter block that is never closed".format(path)


def is_quoted(value):
    return len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"


def unquote(value):
    if is_quoted(value):
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner
    return value


def describe_value_problem(key, value):
    if value.startswith(BLOCK_SCALAR_PREFIXES):
        return (
            "declares {} as a block scalar, which this validator does not read".format(key),
            "put the whole value on a single quoted line",
        )
    if not is_quoted(value) and ": " in value:
        return (
            "declares {} as an unquoted value containing ': '".format(key),
            "wrap the value in double quotes so it parses as YAML",
        )
    return None


def check_frontmatter_values(failures, path, block):
    parsable = True
    for line in block:
        match = FIELD_PATTERN.match(line)
        if not match:
            continue
        detail = describe_value_problem(match.group(1), match.group(2).strip())
        if detail is None:
            continue
        problem, fix = detail
        parsable = False
        fail(failures, "YAML", "{} {}".format(path, problem), fix)
    if parsable:
        ok("frontmatter values")
    return parsable


def parse_fields(block):
    fields = {}
    for line in block:
        match = FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = unquote(match.group(2).strip())
    return fields


def artifact_kind(path):
    if os.path.basename(path) == "SKILL.md":
        return "skill"
    if "agents" in os.path.normpath(os.path.abspath(path)).split(os.sep):
        return "subagent"
    return None


def expected_name(path, kind):
    absolute = os.path.abspath(path)
    if kind == "skill":
        return os.path.basename(os.path.dirname(absolute))
    return os.path.splitext(os.path.basename(absolute))[0]


def declares(fields, key, value):
    return fields.get(key, "").strip().lower() == value


def is_exempt_from_when_to_use(fields):
    return declares(fields, "user-invocable", "false") or declares(
        fields, "disable-model-invocation", "true"
    )


def check_name(failures, path, kind, fields):
    name = fields.get("name", "").strip()
    target = expected_name(path, kind)
    if not name:
        fail(
            failures,
            "NAME",
            "{} declares no name field".format(path),
            'add "name: {}" to the frontmatter'.format(target),
        )
        return
    failed = False
    if not NAME_PATTERN.match(name):
        failed = True
        fail(
            failures,
            "NAME",
            "{} declares name {!r} which is not kebab-case".format(path, name),
            'set "name: {}" to match the path'.format(target),
        )
    if len(name) > MAX_NAME_CHARS:
        failed = True
        fail(
            failures,
            "NAME",
            "{} declares name {!r} at {} characters".format(path, name, len(name)),
            "shorten the name to at most {} characters".format(MAX_NAME_CHARS),
        )
    if not failed:
        ok("name format")


def check_name_matches_path(failures, path, kind, fields):
    name = fields.get("name", "").strip()
    target = expected_name(path, kind)
    if not name:
        return
    if name == target:
        ok("name matches path")
        return
    if kind != "skill":
        return
    fail(
        failures,
        "PATH",
        "{} declares name {!r} but its parent directory is {!r}".format(path, name, target),
        'set "name: {}" or move the file to {}/SKILL.md'.format(target, name),
    )


def check_required_fields(failures, path, kind, fields):
    failed = False
    if not fields.get("description", "").strip():
        failed = True
        fail(
            failures,
            "FIELD",
            "{} has no non-empty description".format(path),
            'add "description: <capability first, then the concrete situations that trigger it>"',
        )
    if kind == "skill" and not fields.get("when_to_use", "").strip():
        if not is_exempt_from_when_to_use(fields):
            failed = True
            fail(
                failures,
                "FIELD",
                "{} is a model-invocable skill with no when_to_use".format(path),
                'add "when_to_use: <trigger phrases or example requests>", or declare '
                '"user-invocable: false" / "disable-model-invocation: true" if the skill is preload-only',
            )
    if not failed:
        ok("required fields")


def check_combined_length(failures, path, fields):
    total = len(fields.get("description", "")) + len(fields.get("when_to_use", ""))
    if total > MAX_COMBINED_DESCRIPTION_CHARS:
        fail(
            failures,
            "LENGTH",
            "{} has description + when_to_use at {} characters".format(path, total),
            "trim {} characters to fit the {} cap".format(
                total - MAX_COMBINED_DESCRIPTION_CHARS, MAX_COMBINED_DESCRIPTION_CHARS
            ),
        )
        return
    ok("description length")


def find_injunctions(text):
    return [word for word, pattern in INJUNCTIONS if pattern.search(text)]


def check_injunctions(failures, path, fields):
    failed = False
    for key in ("description", "when_to_use"):
        found = find_injunctions(fields.get(key, ""))
        if found:
            failed = True
            fail(
                failures,
                "KEYWORD",
                "{} uses injunction keyword(s) {} in {}".format(path, ", ".join(found), key),
                "delete them and name the concrete situations and words a user would type instead",
            )
    if not failed:
        ok("injunction keywords")


def check_size(failures, path, lines):
    if len(lines) > MAX_SKILL_LINES:
        fail(
            failures,
            "SIZE",
            "{} is {} lines".format(path, len(lines)),
            "move detail into reference/ or examples/ until SKILL.md is at most {} lines".format(
                MAX_SKILL_LINES
            ),
        )
        return
    ok("file size")


def body_link_targets(body):
    targets = []
    inside_fence = False
    for line in body:
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        targets.extend(LINK_PATTERN.findall(line))
    return targets


def is_internal_link(target):
    if not target or target.startswith("#"):
        return False
    return not target.startswith(EXTERNAL_LINK_PREFIXES)


def resolve_link(base, target):
    cleaned = target.strip().split()[0].strip("<>").split("#")[0]
    if not cleaned:
        return None
    return os.path.normpath(os.path.join(base, cleaned))


def check_links(failures, path, body):
    base = os.path.dirname(os.path.abspath(path))
    seen = set()
    broken = False
    for target in body_link_targets(body):
        if not is_internal_link(target.strip()):
            continue
        resolved = resolve_link(base, target)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        if os.path.exists(resolved):
            continue
        broken = True
        fail(
            failures,
            "LINK",
            "{} links to {!r} which resolves to {} and does not exist".format(
                path, target.strip(), resolved
            ),
            "fix the relative path or create the missing file",
        )
    if not broken:
        ok("internal links")


def validate_artifact(path, failures):
    if not os.path.isfile(path):
        fail(
            failures,
            "PATH",
            "{} does not exist".format(path),
            "pass the path to a SKILL.md or an agents/<name>.md file",
        )
        return
    kind = artifact_kind(path)
    if kind is None:
        fail(
            failures,
            "PATH",
            "{} is neither a SKILL.md nor a file under an agents/ directory".format(path),
            "move it to <skill-name>/SKILL.md or <plugin>/agents/<name>.md",
        )
        return
    lines = read_lines(path)
    end = find_frontmatter_end(lines)
    if end is None:
        fail(
            failures,
            "FIELD",
            describe_frontmatter_problem(path, lines),
            "open the file with --- on line 1, declare name and description, and close with ---",
        )
        body = lines
    else:
        ok("frontmatter block")
        body = lines[end + 1 :]
        if check_frontmatter_values(failures, path, lines[1:end]):
            fields = parse_fields(lines[1:end])
            check_name(failures, path, kind, fields)
            check_name_matches_path(failures, path, kind, fields)
            check_required_fields(failures, path, kind, fields)
            check_combined_length(failures, path, fields)
            check_injunctions(failures, path, fields)
    if kind == "skill":
        check_size(failures, path, lines)
    check_links(failures, path, body)


def main(argv):
    if not argv:
        sys.stderr.write("usage: python3 validate-frontmatter.py <artifact> [artifact ...]\n")
        return 2
    failures = []
    for path in argv:
        validate_artifact(path, failures)
    for line in failures:
        sys.stderr.write("{}\n".format(line))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
