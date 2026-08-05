#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import sys
import tempfile

TRANSCRIPT_NAME = "transcript.jsonl"
EVENTS_NAME = "events.json"
SCENARIO_COPY_NAME = "scenario.json"
RESULT_NAME = "result.json"
RUN_META_NAME = "run-meta.json"
SCHEMA_NAME = "schema.json"
FIXTURES_DIR_NAME = "fixtures"
PLUGINS_DIR_NAME = "plugins"

ALIGNMENT_MODES = ("aligned_first", "acted_directly", "blocked")
MUTATION_STATES = ("changed", "unchanged")
CLEANUP_POLICIES = ("always", "on_pass", "never")
VERDICTS = ("PASS", "FAIL", "SKIP", "ERROR")
DELEGATION_TOOL_NAMES = ("task", "agent")
MUTATING_TOOL_NAMES = ("write", "edit", "multiedit", "notebookedit")
EVIDENCE_KEYS = ("command", "result")

READ_ONLY_COMMANDS = frozenset([
    "awk", "basename", "cat", "cd", "cksum", "column", "comm", "cut", "date",
    "df", "diff", "dirname", "du", "echo", "false", "file", "find", "grep",
    "head", "hostname", "jq", "less", "ls", "md5sum", "more", "nl", "od",
    "printenv", "printf", "pwd", "readlink", "realpath", "rg", "sed",
    "sha1sum", "sha256sum", "shasum", "sort", "stat", "strings", "tail",
    "tr", "tree", "true", "type", "uname", "uniq", "wc", "which", "whoami",
    "xxd",
])

READ_ONLY_GIT_SUBCOMMANDS = frozenset([
    "blame", "cat-file", "check-ignore", "describe", "diff", "grep", "log",
    "ls-files", "ls-remote", "ls-tree", "rev-list", "rev-parse", "shortlog",
    "show", "show-ref", "status", "whatchanged",
])

GIT_TAG_LISTING_FLAGS = (
    "-l", "--list", "-n", "--contains", "--no-contains", "--merged", "--no-merged",
    "--points-at", "--sort", "--format", "--column", "--ignore-case",
)

GIT_TAG_MUTATING_FLAGS = (
    "-d", "--delete", "-a", "--annotate", "-s", "--sign", "-u", "--local-user",
    "-m", "--message", "-F", "--file", "-e", "--edit", "-f", "--force",
    "--create-reflog", "--cleanup",
)

GIT_GLOBAL_OPTIONS_WITH_VALUE = frozenset([
    "-C", "-c", "--config-env", "--exec-path", "--git-dir", "--namespace",
    "--work-tree",
])

MUTATING_FLAG_PREFIXES = {
    "sed": ("-i", "--in-place"),
    "find": ("-delete", "-exec", "-execdir", "-ok", "-fprint"),
    "sort": ("-o", "--output"),
}

BASH_SEPARATORS = ("&&", "||", ";", "|", "&")
BASH_OPERATORS = (">", ">>", ">&", "<", "<<", "(", ")")
REDIRECT_OPERATORS = (">", ">>", "&>", "&>>")

DECISION_REQUEST_PATTERNS = (
    re.compile(r"\b(should|shall|can|may|do|would)\s+(i|we)\b", re.IGNORECASE),
    re.compile(r"\bwant\s+me\s+to\b", re.IGNORECASE),
    re.compile(r"\byou\s+(want|prefer|choose|pick|decide)\b", re.IGNORECASE),
    re.compile(r"\byour\s+(call|choice|preference|decision)\b", re.IGNORECASE),
    re.compile(r"\bwhich\b", re.IGNORECASE),
    re.compile(r"\bor\b", re.IGNORECASE),
)
SECOND_PERSON_PATTERN = re.compile(r"\b(you|your)\b", re.IGNORECASE)
QUESTION_SENTENCE = re.compile(r"[^.!?\n]*\?")
VERDICT_ORNAMENT = r"[\s*_`>#]*"
VERDICT_OPENING = re.compile(r"^{}(DONE|BLOCKED|FAILED)\b".format(VERDICT_ORNAMENT))

SCENARIO_FIELDS = {
    "id": {"type": str, "required": True},
    "description": {"type": str, "required": True},
    "fixture": {"type": str, "required": True},
    "expect_plugins": {"type": list, "required": True, "item_type": str},
    "expect_agents": {"type": list, "required": True, "item_type": str},
    "prompt": {"type": str, "required": True},
    "preceding_turns": {"type": list, "required": False, "item_type": str},
    "expect_alignment_mode": {"type": str, "required": True, "enum": ALIGNMENT_MODES},
    "expect_delegate": {"type": str, "required": False, "nullable": True},
    "forbidden_delegates": {"type": list, "required": False, "item_type": str},
    "forbidden_tools": {"type": list, "required": False, "item_type": str},
    "forbidden_bash_patterns": {"type": list, "required": False, "item_type": str},
    "expect_verdict_prefix": {"type": list, "required": False, "item_type": str},
    "required_response_markers": {"type": list, "required": False, "item_type": str},
    "required_response_markers_any": {"type": list, "required": False, "item_type": str},
    "expect_mutation_state": {"type": str, "required": True, "enum": MUTATION_STATES},
    "expect_verification_evidence": {
        "type": dict,
        "required": False,
        "nullable": True,
        "object_keys": EVIDENCE_KEYS,
    },
    "timeout_seconds": {"type": int, "required": True, "positive": True},
    "cleanup_policy": {"type": str, "required": True, "enum": CLEANUP_POLICIES},
    "agent_under_test": {"type": str, "required": False, "nullable": True},
    "skip_reason": {"type": str, "required": False, "nullable": True},
}

SESSION_INIT_FIELDS = ("agents", "model", "permissionMode", "plugins", "tools")

INTEGRITY = "integrity"
BEHAVIORAL = "behavioral"

ABSOLUTE_PATH = re.compile(r"(?<![\w/:])/[^\s'\";|&()<>]*")
SYSTEM_PATH_PREFIXES = (
    "/usr", "/bin", "/sbin", "/opt", "/etc", "/dev", "/Library", "/System", "/var/db",
)
SCRATCH_PATH_PREFIXES = (
    "/tmp", "/var/folders", "/private/tmp", "/private/var/folders",
)
TOLERATED_PATH_PREFIXES = SYSTEM_PATH_PREFIXES + SCRATCH_PATH_PREFIXES
SUBSTITUTION = re.compile(r"\$\([^()]*\)|`[^`]*`")
SUBSTITUTION_PLACEHOLDER = "$SUBSTITUTION"
TOKEN_SPLIT = re.compile(r"[\s;|&()<>]+")
QUOTE_CHARACTERS = "\"'"

PATTERN_OPERAND_COMMANDS = frozenset([
    "ag", "awk", "egrep", "fgrep", "grep", "rg", "sed",
])

PATTERN_OPERAND_FLAGS = frozenset([
    "-ipath", "-iname", "-iwholename", "-name", "-path", "-wholename",
])

TYPE_NAMES = {
    str: "string",
    list: "array",
    dict: "object",
    int: "integer",
    float: "number",
    bool: "boolean",
    type(None): "null",
}


SCHEMA_TYPE_NAMES = {"string": str, "array": list, "object": dict, "integer": int}


def type_name(kind):
    return TYPE_NAMES.get(kind, getattr(kind, "__name__", str(kind)))


def required_field_names():
    return sorted(key for key, spec in SCENARIO_FIELDS.items() if spec["required"])


def object_key_errors(key, value, allowed_keys):
    errors = []
    for inner in allowed_keys:
        if inner not in value:
            errors.append(
                "Key '{}' has no '{}'. -> add \"{}\": \"<text>\" inside '{}'".format(
                    key, inner, inner, key
                )
            )
        elif not isinstance(value[inner], str):
            errors.append(
                "Key '{}.{}' is {}, expected string. -> quote the value of '{}.{}' as a string".format(
                    key, inner, type_name(type(value[inner])), key, inner
                )
            )
    for inner in sorted(value):
        if inner not in allowed_keys:
            errors.append(
                "Key '{}.{}' is not a known key. -> remove '{}' or rename it to one of {}".format(
                    key, inner, inner, list(allowed_keys)
                )
            )
    return errors


def item_errors(key, values, item_type):
    errors = []
    for position, item in enumerate(values):
        if not isinstance(item, item_type) or isinstance(item, bool):
            errors.append(
                "Key '{}[{}]' is {}, expected {}. -> make every entry of '{}' a {}".format(
                    key,
                    position,
                    type_name(type(item)),
                    type_name(item_type),
                    key,
                    type_name(item_type),
                )
            )
    return errors


def value_errors(key, value, spec):
    expected = spec["type"]
    if expected is int and isinstance(value, bool):
        return [
            "Key '{}' is a boolean. -> set '{}' to a positive integer number of seconds".format(
                key, key
            )
        ]
    if not isinstance(value, expected):
        return [
            "Key '{}' is {}, expected {}. -> change '{}' to {}".format(
                key, type_name(type(value)), type_name(expected), key, type_name(expected)
            )
        ]
    errors = []
    if spec.get("enum") and value not in spec["enum"]:
        errors.append(
            "Key '{}' is '{}', which is not an allowed value. -> set '{}' to one of {}".format(
                key, value, key, list(spec["enum"])
            )
        )
    if spec.get("positive") and value < 1:
        errors.append(
            "Key '{}' is {}, not a positive integer. -> set '{}' to a positive integer number of seconds".format(
                key, value, key
            )
        )
    if spec.get("item_type"):
        errors.extend(item_errors(key, value, spec["item_type"]))
    if spec.get("object_keys"):
        errors.extend(object_key_errors(key, value, spec["object_keys"]))
    return errors


def missing_key_errors(data):
    errors = []
    for key in required_field_names():
        if key not in data:
            errors.append(
                "Required key '{}' is missing. -> add '{}' to the scenario; the required keys are {}".format(
                    key, key, required_field_names()
                )
            )
    return errors


def unknown_key_errors(data):
    errors = []
    for key in sorted(data):
        if key not in SCENARIO_FIELDS:
            errors.append(
                "Key '{}' is not a known scenario key. -> remove '{}' or rename it to one of {}".format(
                    key, key, sorted(SCENARIO_FIELDS)
                )
            )
    return errors


def field_type_errors(data):
    errors = []
    for key in sorted(data):
        spec = SCENARIO_FIELDS.get(key)
        if spec is None:
            continue
        value = data[key]
        if value is None:
            if not spec.get("nullable"):
                errors.append(
                    "Key '{}' is null. -> give '{}' a {} value".format(
                        key, key, type_name(spec["type"])
                    )
                )
            continue
        errors.extend(value_errors(key, value, spec))
    return errors


def id_match_errors(data, stem):
    scenario_id = data.get("id")
    if not isinstance(scenario_id, str) or scenario_id == stem:
        return []
    return [
        "Key 'id' is '{}' but the filename stem is '{}'. -> rename the file to '{}.json' or set \"id\": \"{}\"".format(
            scenario_id, stem, scenario_id, stem
        )
    ]


AGENT_ID_CACHE = []


def repository_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fixtures_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), FIXTURES_DIR_NAME)


def plugins_directory():
    return os.path.join(repository_root(), PLUGINS_DIR_NAME)


def is_inside_directory(path, root):
    resolved = os.path.realpath(path)
    return resolved.startswith(os.path.realpath(root) + os.sep)


def repository_agent_ids():
    if AGENT_ID_CACHE:
        return AGENT_ID_CACHE[0]
    plugins = plugins_directory()
    if not os.path.isdir(plugins):
        return None
    identifiers = []
    for plugin in sorted(os.listdir(plugins)):
        agents = os.path.join(plugins, plugin, "agents")
        if not os.path.isdir(agents):
            continue
        for name in sorted(os.listdir(agents)):
            if name.endswith(".md"):
                identifiers.append("{}:{}".format(plugin, os.path.splitext(name)[0]))
    AGENT_ID_CACHE.append(identifiers)
    return identifiers


def agent_reference_errors(data):
    known = repository_agent_ids()
    if known is None:
        return []
    errors = []
    for key in ("expect_agents", "agent_under_test"):
        value = data.get(key)
        wanted = value if isinstance(value, list) else ([value] if isinstance(value, str) else [])
        for name in wanted:
            if not isinstance(name, str):
                continue
            if any(agent_id_matches(name, offered) for offered in known):
                continue
            errors.append(
                "Key '{}' names agent '{}', which no plugins/*/agents/*.md provides. -> use one of "
                "{} (bare or plugin:agent form)".format(key, name, known)
            )
    return errors


def fixture_errors(data):
    fixture = data.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        return []
    root = fixtures_directory()
    if not os.path.isdir(root):
        return []
    path = os.path.normpath(os.path.join(root, fixture))
    if not is_inside_directory(path, root):
        return [
            "Key 'fixture' is '{}', which resolves outside {}. -> name a directory that sits "
            "directly under evals/fixtures/; a live run copies the fixture into the workspace the "
            "agent under test reads, so a traversing path would stage repository content as if it "
            "were the fixture".format(fixture, root)
        ]
    if not os.path.isdir(path):
        return [
            "Key 'fixture' is '{}' but {} is not a directory. -> create the fixture or correct "
            "'fixture'; a live run would abort on this after paying for every scenario before "
            "it".format(fixture, path)
        ]
    return []


def plugin_reference_errors(data):
    root = plugins_directory()
    if not os.path.isdir(root):
        return []
    errors = []
    for name in data.get("expect_plugins") or []:
        if not isinstance(name, str) or not name:
            continue
        path = os.path.normpath(os.path.join(root, name))
        if not is_inside_directory(path, root):
            errors.append(
                "Key 'expect_plugins' names '{}', which resolves outside {}. -> name a plugin "
                "directory directly under plugins/; every entry is handed to --plugin-dir".format(
                    name, root
                )
            )
        elif not os.path.isdir(path):
            errors.append(
                "Key 'expect_plugins' names '{}' but {} is not a directory. -> add the plugin or "
                "correct the scenario; a live run would abort on this after paying for every "
                "scenario before it".format(name, path)
            )
    return errors


def resource_errors(data):
    if not isinstance(data, dict):
        return []
    return fixture_errors(data) + plugin_reference_errors(data)


def regex_errors(data):
    errors = []
    patterns = data.get("forbidden_bash_patterns")
    if not isinstance(patterns, list):
        return errors
    for position, pattern in enumerate(patterns):
        if not isinstance(pattern, str):
            continue
        try:
            re.compile(pattern)
        except re.error as error:
            errors.append(
                "Key 'forbidden_bash_patterns[{}]' is not a valid regex ({}). -> fix the pattern '{}'".format(
                    position, error, pattern
                )
            )
    return errors


def scenario_errors(data, stem):
    if not isinstance(data, dict):
        return [
            "Top level value is {}, expected object. -> wrap the scenario in a JSON object with the keys {}".format(
                type_name(type(data)), required_field_names()
            )
        ]
    errors = []
    errors.extend(unknown_key_errors(data))
    errors.extend(missing_key_errors(data))
    errors.extend(field_type_errors(data))
    errors.extend(id_match_errors(data, stem))
    errors.extend(regex_errors(data))
    errors.extend(agent_reference_errors(data))
    return errors


def report_scenario_errors(path, errors):
    sys.stderr.write("SCENARIO ERROR: {}\n".format(path))
    for error in errors:
        sys.stderr.write("{}\n".format(error))


def load_scenario(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except IOError:
        sys.stderr.write("SCENARIO ERROR: {}\n".format(path))
        sys.stderr.write(
            "The scenario file cannot be read. -> create it or correct the path passed to --scenario\n"
        )
        return None
    except ValueError as error:
        sys.stderr.write("JSON ERROR: {}\n".format(path))
        sys.stderr.write("Invalid JSON ({}). -> fix the JSON syntax at that position\n".format(error))
        return None
    errors = scenario_errors(data, stem)
    if errors:
        report_scenario_errors(path, errors)
        return None
    return data


def scenario_files(directory):
    if not os.path.isdir(directory):
        return None
    paths = []
    for current, directories, files in os.walk(directory):
        directories[:] = sorted(directories)
        for name in sorted(files):
            if name.endswith(".json") and name != SCHEMA_NAME:
                paths.append(os.path.join(current, name))
    return sorted(paths)


def index_by_stem(paths):
    index = {}
    for path in paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        index.setdefault(stem, []).append(path)
    return index


def scenario_index(directory):
    return index_by_stem(scenario_files(directory) or [])


def duplicate_id_errors(index):
    errors = []
    for stem in sorted(index):
        if len(index[stem]) > 1:
            errors.append(
                "Scenario id '{}' is claimed by {} files: {}. -> scenario ids must be unique across "
                "the whole tree; rename all but one so each id resolves to exactly one file".format(
                    stem, len(index[stem]), index[stem]
                )
            )
    return errors


def available_scenario_ids(directory):
    return sorted(scenario_index(directory))


def available_suites(directory):
    root = os.path.abspath(directory)
    if not os.path.isdir(root):
        return []
    suites = []
    for current, directories, files in os.walk(root):
        directories[:] = sorted(directories)
        for name in directories:
            path = os.path.join(current, name)
            if scenario_files(path):
                suites.append(os.path.relpath(path, root))
    return sorted(suites)


def suite_scenario_ids(directory, name):
    root = os.path.abspath(directory)
    path = os.path.abspath(os.path.join(root, name))
    if path == root or not path.startswith(root + os.sep):
        return []
    return sorted(
        os.path.splitext(os.path.basename(found))[0] for found in scenario_files(path) or []
    )


def ambiguous_scenario_error(scenario_id, paths):
    return (
        "Scenario id '{}' is ambiguous — it resolves to {} files: {}. -> rename all but one so the "
        "id is unique across the whole tree".format(scenario_id, len(paths), paths)
    )


def unknown_target_error(directory, name):
    return (
        "No scenario id or suite directory named '{}' anywhere under {}. -> available scenario ids "
        "are {}; available suite directories are {}".format(
            name,
            directory,
            available_scenario_ids(directory) or "none",
            available_suites(directory) or "none",
        )
    )


def resolve_target(directory, name):
    paths = scenario_index(directory).get(name) or []
    if len(paths) > 1:
        return "", [], ambiguous_scenario_error(name, paths)
    if len(paths) == 1:
        return "scenario", [name], ""
    ids = suite_scenario_ids(directory, name)
    if ids:
        return "suite", ids, ""
    return "", [], unknown_target_error(directory, name)


def resolve_scenario(directory, scenario_id):
    paths = scenario_index(directory).get(scenario_id) or []
    if len(paths) == 1:
        return paths[0], ""
    if not paths:
        return "", (
            "No scenario with id '{}' anywhere under {}. -> available ids are {}".format(
                scenario_id, directory, available_scenario_ids(directory) or "none"
            )
        )
    return "", ambiguous_scenario_error(scenario_id, paths)


def validate_scenarios(directory):
    paths = scenario_files(directory)
    if paths is None:
        sys.stderr.write("SCENARIO ERROR: {}\n".format(directory))
        sys.stderr.write(
            "The scenario directory does not exist. -> create it or pass an existing directory\n"
        )
        return 1
    if not paths:
        sys.stderr.write("SCENARIO ERROR: {}\n".format(directory))
        sys.stderr.write(
            "No scenario files found anywhere under this directory ({} is not a scenario). -> add at "
            "least one scenario, e.g. {}/smoke/<id>.json; reporting success after validating nothing "
            "is a silent pass\n".format(SCHEMA_NAME, directory)
        )
        return 1
    failures = 0
    for path in paths:
        data = load_scenario(path)
        if data is None:
            failures += 1
            continue
        errors = resource_errors(data)
        if errors:
            report_scenario_errors(path, errors)
            failures += 1
    duplicates = duplicate_id_errors(index_by_stem(paths))
    if duplicates:
        sys.stderr.write("SCENARIO ERROR: {}\n".format(directory))
        for error in duplicates:
            sys.stderr.write("{}\n".format(error))
    if failures or duplicates:
        return 1
    sys.stdout.write("OK: {} scenario file(s) validated under {}\n".format(len(paths), directory))
    return 0


def merged(base, extra):
    event = dict(base)
    event.update(extra)
    return event


def content_blocks(record):
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [block for block in content if isinstance(block, dict)]
    return []


def selected_subagent(tool_input):
    for key in ("subagent_type", "agent_type", "agent"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def tool_use_fields(block):
    tool_input = block.get("input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command")
    return {
        "kind": "tool_use",
        "tool_name": block.get("name") or "",
        "tool_use_id": block.get("id") or "",
        "subagent_type": selected_subagent(tool_input),
        "bash_command": command if isinstance(command, str) else "",
        "tool_input": tool_input,
    }


def tool_result_text(block):
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part.get("text") or "" for part in content if isinstance(part, dict)
        )
    return ""


def assistant_events(base, record):
    events = []
    for block in content_blocks(record):
        if block.get("type") == "text":
            events.append(merged(base, {"kind": "assistant_text", "text": block.get("text") or ""}))
        elif block.get("type") == "tool_use":
            events.append(merged(base, tool_use_fields(block)))
    return events


def user_events(base, record):
    events = []
    for block in content_blocks(record):
        if block.get("type") == "tool_result":
            events.append(
                merged(
                    base,
                    {
                        "kind": "tool_result",
                        "tool_use_id": block.get("tool_use_id") or "",
                        "text": tool_result_text(block),
                    },
                )
            )
    return events


def system_event_fields(record):
    fields = {"kind": "system", "subtype": record.get("subtype") or ""}
    if record.get("subtype") == "init":
        fields["session"] = dict(
            (key, record.get(key)) for key in SESSION_INIT_FIELDS if key in record
        )
    return fields


def events_from_record(index, record):
    parent = record.get("parent_tool_use_id")
    base = {
        "index": index,
        "raw_type": record.get("type") or "",
        "parent_tool_use_id": parent,
        "top_level": parent is None,
    }
    kind = record.get("type")
    if kind == "assistant":
        return assistant_events(base, record)
    if kind == "user":
        return user_events(base, record)
    if kind == "result":
        return [
            merged(
                base,
                {
                    "kind": "result",
                    "subtype": record.get("subtype") or "",
                    "text": record.get("result") or "",
                    "is_error": bool(record.get("is_error")),
                },
            )
        ]
    return [merged(base, system_event_fields(record))]


def normalize_events(records):
    events = []
    for index, record in enumerate(records):
        if isinstance(record, dict):
            events.extend(events_from_record(index, record))
    return events


def top_level_events(events):
    return [event for event in events if event.get("top_level")]


def is_delegation(event):
    if event.get("kind") != "tool_use":
        return False
    name = (event.get("tool_name") or "").lower()
    return name in DELEGATION_TOOL_NAMES or "subagent" in name


def delegation_events(events):
    return [event for event in events if is_delegation(event)]


def invoked_subagents(events):
    return [event.get("subagent_type") or "<unnamed>" for event in delegation_events(events)]


def tool_matches(expected, observed):
    return expected.lower() == observed.lower()


def agent_id_matches(expected, observed, over_match=False):
    if expected == observed:
        return True
    if over_match:
        return expected.rsplit(":", 1)[-1] == observed.rsplit(":", 1)[-1]
    return ":" not in expected and observed.rsplit(":", 1)[-1] == expected


def matching_delegates(expected, subagents):
    return [name for name in subagents if agent_id_matches(expected, name)]


def banned_delegates_invoked(banned, subagents):
    return [name for name in subagents if agent_id_matches(banned, name, over_match=True)]


def writes_to_a_file(command):
    try:
        segments = bash_segments(command)
    except ValueError:
        return True
    return any(
        token in REDIRECT_OPERATORS and tokens[position + 1:position + 2] != ["/dev/null"]
        for tokens in segments
        for position, token in enumerate(tokens)
    )


def bash_segments(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segments = [[]]
    for token in list(lexer):
        if token in BASH_SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def bundles_short_option(argument, prefix):
    if len(prefix) != 2 or not argument.startswith("-") or argument.startswith("--"):
        return False
    return prefix[1] in argument[1:]


def matches_flag(argument, prefix):
    return argument.startswith(prefix) or bundles_short_option(argument, prefix)


def has_any_flag(arguments, prefixes):
    return any(
        matches_flag(argument, prefix) for argument in arguments for prefix in prefixes
    )


def has_mutating_flag(command, arguments):
    return has_any_flag(arguments, MUTATING_FLAG_PREFIXES.get(command, ()))


def is_read_only_git_tag(arguments):
    if has_any_flag(arguments, GIT_TAG_MUTATING_FLAGS):
        return False
    return not arguments or has_any_flag(arguments, GIT_TAG_LISTING_FLAGS)


def is_read_only_git(arguments):
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if not argument.startswith("-"):
            if argument == "tag":
                return is_read_only_git_tag(arguments[index + 1:])
            return argument in READ_ONLY_GIT_SUBCOMMANDS
        index += 2 if argument in GIT_GLOBAL_OPTIONS_WITH_VALUE else 1
    return True


def is_read_only_segment(tokens):
    words = [token for token in tokens if token not in BASH_OPERATORS]
    if not words:
        return True
    command = os.path.basename(words[0])
    arguments = words[1:]
    if command == "git":
        return is_read_only_git(arguments)
    if command not in READ_ONLY_COMMANDS:
        return False
    return not has_mutating_flag(command, arguments)


def is_mutating_bash(command):
    text = (command or "").strip()
    if not text:
        return False
    if writes_to_a_file(text):
        return True
    try:
        segments = bash_segments(text)
    except ValueError:
        return True
    return any(not is_read_only_segment(segment) for segment in segments)


def is_orchestrator_action(event):
    if not event.get("top_level") or event.get("kind") != "tool_use":
        return False
    if is_delegation(event):
        return True
    name = (event.get("tool_name") or "").lower()
    if name == "bash":
        return is_mutating_bash(event.get("bash_command"))
    return name in MUTATING_TOOL_NAMES


def requests_a_decision(sentence):
    return any(pattern.search(sentence) for pattern in DECISION_REQUEST_PATTERNS)


def addresses_the_user(sentence):
    return bool(SECOND_PERSON_PATTERN.search(sentence))


def question_sentences(text):
    return [match.strip() for match in QUESTION_SENTENCE.findall(text or "") if match.strip()]


def is_top_level_text(event):
    return bool(event.get("top_level")) and event.get("kind") == "assistant_text"


def asks_the_user_to_decide(event):
    if not is_top_level_text(event):
        return False
    return any(
        requests_a_decision(sentence) for sentence in question_sentences(event.get("text"))
    )


def is_clarifying_question(event):
    if not is_top_level_text(event):
        return False
    return any(
        requests_a_decision(sentence) or addresses_the_user(sentence)
        for sentence in question_sentences(event.get("text"))
    )


def opens_with_verdict_token(text, token):
    pattern = r"^{}{}\b".format(VERDICT_ORNAMENT, re.escape(token))
    return bool(re.match(pattern, text or ""))


def opens_with_verdict(event):
    if not is_top_level_text(event):
        return False
    return bool(VERDICT_OPENING.match(event.get("text") or ""))


def is_meaningful_event(event):
    kind = event.get("kind")
    if kind in ("tool_use", "tool_result"):
        return True
    if kind in ("assistant_text", "result"):
        return bool((event.get("text") or "").strip())
    return False


def meaningful_events(events):
    return [event for event in events if is_meaningful_event(event)]


def last_turn_events(events):
    starts = [
        index
        for index, event in enumerate(events)
        if event.get("kind") == "system" and event.get("subtype") == "init"
    ]
    return events[starts[-1]:] if starts else events


def observed_alignment_mode(events):
    turn = last_turn_events(events)
    verdict_reached = False
    for event in top_level_events(turn):
        if is_orchestrator_action(event):
            return "acted_directly"
        if opens_with_verdict(event):
            verdict_reached = True
        paused_to_align = (
            asks_the_user_to_decide(event)
            if verdict_reached
            else is_clarifying_question(event)
        )
        if paused_to_align:
            return "aligned_first"
    if not meaningful_events(turn):
        return "no_activity"
    return "blocked"


def final_assistant_text(events):
    texts = [
        event.get("text") or ""
        for event in top_level_events(events)
        if event.get("kind") == "assistant_text" and (event.get("text") or "").strip()
    ]
    if texts:
        return texts[-1]
    results = [
        event.get("text") or ""
        for event in events
        if event.get("kind") == "result" and (event.get("text") or "").strip()
    ]
    return results[-1] if results else ""


def bash_commands(events, top_level_only):
    pool = top_level_events(events) if top_level_only else events
    return [
        event.get("bash_command") or ""
        for event in pool
        if event.get("kind") == "tool_use" and (event.get("bash_command") or "")
    ]


def tool_result_texts(events):
    return [event.get("text") or "" for event in events if event.get("kind") == "tool_result"]


def assertion(name, passed, expected, observed, message, kind=BEHAVIORAL):
    return {
        "name": name,
        "kind": kind,
        "passed": bool(passed),
        "expected": expected,
        "observed": observed,
        "message": message,
    }


def integrity(name, passed, expected, observed, message):
    return assertion(name, passed, expected, observed, message, INTEGRITY)


def failed(checks, kind):
    return [check for check in checks if check["kind"] == kind and not check["passed"]]


def of_kind(checks, kind):
    return [check for check in checks if check["kind"] == kind]


def expected_delegate_assertion(expected, events):
    subagents = invoked_subagents(events)
    matched = matching_delegates(expected, subagents)
    passed = bool(matched)
    if passed:
        message = "Subagent '{}' was invoked (as {}).".format(expected, matched)
    else:
        message = (
            "Expected subagent_type '{}' to be selected, but the orchestrator invoked {}. "
            "-> fix the routing rules for this prompt or update 'expect_delegate'.".format(
                expected, subagents or "no subagent at all"
            )
        )
    return assertion("expected_delegate", passed, expected, subagents, message)


def forbidden_delegates_assertion(forbidden, events):
    subagents = invoked_subagents(events)
    violations = [name for name in forbidden if banned_delegates_invoked(name, subagents)]
    passed = not violations
    if passed:
        message = "None of the forbidden delegates {} were invoked (saw {}).".format(
            list(forbidden), subagents
        )
    else:
        message = (
            "Forbidden subagent(s) {} were invoked; the full delegation list was {}. "
            "-> the orchestrator routed to a delegate this scenario bans.".format(
                violations, subagents
            )
        )
    return assertion("forbidden_delegates", passed, "none of {}".format(list(forbidden)), subagents, message)


def forbidden_tools_assertion(forbidden, events):
    orchestrator_uses = [
        event for event in top_level_events(events) if event.get("kind") == "tool_use"
    ]
    violations = []
    for name in forbidden:
        hits = [event for event in orchestrator_uses if tool_matches(name, event.get("tool_name") or "")]
        if hits:
            violations.append(
                "{} used {} time(s), first at transcript record {}".format(
                    name, len(hits), hits[0].get("index")
                )
            )
    passed = not violations
    observed = sorted(set(event.get("tool_name") or "" for event in orchestrator_uses))
    if passed:
        message = "The orchestrator itself used {} and none of the forbidden tools {}.".format(
            observed, list(forbidden)
        )
    else:
        message = (
            "The orchestrator itself invoked forbidden tool(s): {}. Nested subagent usage is allowed "
            "and was ignored. -> the orchestrator must delegate this work instead of doing it.".format(
                "; ".join(violations)
            )
        )
    return assertion(
        "forbidden_tools", passed, "orchestrator never uses {}".format(list(forbidden)), observed, message
    )


def forbidden_bash_patterns_assertion(patterns, events):
    commands = bash_commands(events, True)
    violations = []
    for pattern in patterns:
        expression = re.compile(pattern)
        for command in commands:
            if expression.search(command):
                violations.append("pattern '{}' matched command '{}'".format(pattern, command))
    passed = not violations
    if passed:
        message = "No forbidden pattern in {} matched the {} orchestrator Bash command(s) {}.".format(
            list(patterns), len(commands), commands
        )
    else:
        message = (
            "Forbidden Bash pattern(s) matched an orchestrator command: {}. Nested subagent commands "
            "were ignored. -> the orchestrator ran a command this scenario bans.".format(
                "; ".join(violations)
            )
        )
    return assertion(
        "forbidden_bash_patterns",
        passed,
        "no orchestrator Bash command matches {}".format(list(patterns)),
        commands,
        message,
    )


def response_verdict_prefix_assertion(allowed, events):
    text = final_assistant_text(events).lstrip()
    opening = text[:80]
    passed = any(opens_with_verdict_token(text, token) for token in allowed)
    if passed:
        message = "The final assistant text opens with an allowed verdict token."
    else:
        message = (
            "Expected the final assistant text to start with one of {}, but it starts with '{}'. "
            "-> the answer contract requires a verdict line first.".format(list(allowed), opening)
        )
    return assertion("response_verdict_prefix", passed, list(allowed), opening, message)


def required_response_markers_assertion(markers, events):
    text = final_assistant_text(events)
    missing = [marker for marker in markers if marker not in text]
    passed = not missing
    if passed:
        message = "All required markers {} appear in the final assistant text.".format(list(markers))
    else:
        message = (
            "The final assistant text is missing required marker(s) {}. The text was: '{}'. "
            "-> the response omitted content this scenario requires.".format(
                missing, text[:200]
            )
        )
    return assertion("required_response_markers", passed, list(markers), text[:200], message)


def required_response_markers_any_assertion(markers, events):
    text = final_assistant_text(events)
    present = [marker for marker in markers if marker in text]
    passed = bool(present)
    if passed:
        message = "The final assistant text contains {} of the accepted marker(s) {}.".format(
            present, list(markers)
        )
    else:
        message = (
            "The final assistant text contains none of the accepted marker(s) {}; at least one of "
            "them must appear. The text was: '{}'. -> the response never named what this scenario "
            "requires it to name, in any accepted wording.".format(list(markers), text[:200])
        )
    return assertion(
        "required_response_markers_any", passed, list(markers), text[:200], message
    )


def verification_evidence_assertion(evidence, events):
    expected_command = evidence.get("command") or ""
    expected_result = evidence.get("result") or ""
    commands = bash_commands(events, False)
    texts = tool_result_texts(events)
    command_seen = any(expected_command in command for command in commands)
    result_seen = any(expected_result in text for text in texts)
    passed = command_seen and result_seen
    observed = {"commands": commands, "result_seen": result_seen}
    if passed:
        message = "Verification command '{}' ran and its result '{}' was observed.".format(
            expected_command, expected_result
        )
    else:
        missing = []
        if not command_seen:
            missing.append(
                "no Bash command contained '{}' (commands run: {})".format(expected_command, commands)
            )
        if not result_seen:
            missing.append(
                "no tool result contained '{}' (the model's own prose does not count as "
                "evidence)".format(expected_result)
            )
        message = (
            "Verification evidence incomplete: {}. -> the run claimed or skipped verification instead "
            "of running it and reporting the observed output.".format("; ".join(missing))
        )
    return assertion(
        "verification_evidence",
        passed,
        {"command": expected_command, "result": expected_result},
        observed,
        message,
    )


def mutation_state_assertion(expected, meta):
    before = meta.get("tree_hash_before")
    after = meta.get("tree_hash_after")
    if not before or not after:
        message = (
            "Cannot compare the fixture workspace: run-meta.json has tree_hash_before={} and "
            "tree_hash_after={}. -> run.sh must record both hashes around the CLI call.".format(
                before, after
            )
        )
        return integrity("workspace_hashes_recorded", False, expected, "unknown", message)
    observed = "unchanged" if before == after else "changed"
    passed = observed == expected
    if passed:
        message = "The fixture workspace was {} as expected.".format(observed)
    else:
        message = (
            "Expected the fixture workspace to be '{}' but it was '{}' (hash before {}, after {}). "
            "-> the run mutated the workspace when it should not have, or failed to.".format(
                expected, observed, before[:12], after[:12]
            )
        )
    return assertion("mutation_state", passed, expected, observed, message)


def alignment_mode_assertion(expected, events):
    observed = observed_alignment_mode(events)
    passed = observed == expected
    if passed:
        message = "Alignment mode '{}' observed as expected.".format(observed)
    else:
        message = (
            "Expected alignment mode '{}' but observed '{}'. aligned_first needs a clarifying question "
            "before any orchestrator mutation or delegation, and once the text has opened with a "
            "DONE/BLOCKED/FAILED verdict only an explicit decision request still counts as aligning; "
            "acted_directly means a mutation or delegation came first; blocked means neither "
            "happened. -> check the first top-level events in events.json.".format(expected, observed)
        )
    return assertion("alignment_mode", passed, expected, observed, message)


def completed_before_timeout_assertion(scenario, meta):
    budget = scenario.get("timeout_seconds")
    duration = meta.get("duration_seconds")
    timed_out = bool(meta.get("timed_out"))
    passed = not timed_out
    if passed:
        message = "The run finished in {}s within the {}s budget.".format(duration, budget)
    else:
        message = (
            "The run exceeded its {}s budget and was killed after {}s. -> raise 'timeout_seconds' or "
            "fix the prompt so the turn completes.".format(budget, duration)
        )
    return integrity(
        "completed_before_timeout",
        passed,
        "finish within {}s".format(budget),
        {"duration_seconds": duration, "timed_out": timed_out},
        message,
    )


def build_assertions(scenario, events, meta):
    checks = []
    expected_delegate = scenario.get("expect_delegate")
    if expected_delegate:
        checks.append(expected_delegate_assertion(expected_delegate, events))
    if scenario.get("forbidden_delegates"):
        checks.append(forbidden_delegates_assertion(scenario["forbidden_delegates"], events))
    if scenario.get("forbidden_tools"):
        checks.append(forbidden_tools_assertion(scenario["forbidden_tools"], events))
    if scenario.get("forbidden_bash_patterns"):
        checks.append(
            forbidden_bash_patterns_assertion(scenario["forbidden_bash_patterns"], events)
        )
    if scenario.get("expect_verdict_prefix"):
        checks.append(response_verdict_prefix_assertion(scenario["expect_verdict_prefix"], events))
    if scenario.get("required_response_markers"):
        checks.append(
            required_response_markers_assertion(scenario["required_response_markers"], events)
        )
    if scenario.get("required_response_markers_any"):
        checks.append(
            required_response_markers_any_assertion(
                scenario["required_response_markers_any"], events
            )
        )
    if scenario.get("expect_verification_evidence"):
        checks.append(
            verification_evidence_assertion(scenario["expect_verification_evidence"], events)
        )
    if scenario.get("expect_mutation_state"):
        checks.append(mutation_state_assertion(scenario["expect_mutation_state"], meta))
    if scenario.get("expect_alignment_mode"):
        checks.append(alignment_mode_assertion(scenario["expect_alignment_mode"], events))
    return checks


def read_meta(result_dir):
    path = os.path.join(result_dir, RUN_META_NAME)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (IOError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_transcript(result_dir):
    path = os.path.join(result_dir, TRANSCRIPT_NAME)
    if not os.path.isfile(path):
        return [], (
            "The transcript {} does not exist. -> the run produced no output; check that run.sh "
            "redirected the stream-json output to {} and that the CLI could start.".format(
                path, TRANSCRIPT_NAME
            )
        )
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except ValueError as error:
                return [], (
                    "Line {} of {} is not valid JSON ({}). -> rerun with "
                    "--output-format stream-json --verbose and keep the stream unfiltered.".format(
                        number, path, error
                    )
                )
    if not records:
        return [], (
            "The transcript {} is empty. -> the CLI exited before emitting any event; check "
            "credentials, the prompt, and stderr.log.".format(path)
        )
    return records, ""


def aborted_result_event(events):
    for event in events:
        if event.get("kind") == "result" and event.get("is_error"):
            return event
    return None


def run_metadata_assertion(meta):
    passed = bool(meta)
    return integrity(
        "run_metadata_recorded",
        passed,
        "a readable {}".format(RUN_META_NAME),
        "present" if passed else "missing",
        "The run metadata was recorded."
        if passed
        else "No readable {} in the result directory. -> run.sh must record cli_exit_code, "
        "duration_seconds, timed_out, the two workspace tree hashes and workspace_path.".format(
            RUN_META_NAME
        ),
    )


def transcript_readable_assertion(transcript_error, events):
    if transcript_error:
        return integrity("transcript_readable", False, "a parseable transcript", "unreadable", transcript_error)
    passed = bool(meaningful_events(events))
    return integrity(
        "transcript_readable",
        passed,
        "at least one assistant, tool or result event",
        "{} event(s), {} meaningful".format(len(events), len(meaningful_events(events))),
        "The transcript carries usable events."
        if passed
        else "The transcript parsed but produced no assistant text, tool call, or result content "
        "({} raw event(s), none meaningful). -> the session died right after start-up; a "
        "transcript with nothing in it cannot evidence any assertion.".format(len(events)),
    )


def cli_exit_assertion(meta):
    exit_code = meta.get("cli_exit_code")
    passed = exit_code == 0
    return integrity(
        "cli_exit_code",
        passed,
        0,
        exit_code,
        "The CLI exited cleanly."
        if passed
        else "The claude CLI exited with code {}. -> read stderr.log in the result directory; a "
        "non-zero exit is never a PASS.".format(exit_code),
    )


def cli_result_assertion(events):
    aborted = aborted_result_event(events)
    passed = aborted is None
    subtype = "" if passed else (aborted.get("subtype") or "unknown")
    return integrity(
        "cli_result_not_aborted",
        passed,
        "is_error false on the result event",
        subtype or "clean",
        "The CLI reported a clean result event."
        if passed
        else "The CLI reported is_error on its result event (subtype '{}'), so the turn was aborted "
        "and the transcript is truncated even though the process exited 0. -> subtype "
        "'error_max_budget_usd' means the --max-budget-usd rail cut the turn: raise "
        "EVAL_MAX_BUDGET_USD. A truncated turn is never a PASS.".format(subtype),
    )


def session_payload(events):
    for event in events:
        if event.get("kind") == "system" and event.get("subtype") == "init":
            return event.get("session") or {}
    return {}


def session_agents_assertion(expected, events):
    available = session_payload(events).get("agents")
    if not available:
        return None
    missing = [
        name for name in expected
        if not any(agent_id_matches(name, offered) for offered in available)
    ]
    passed = not missing
    return integrity(
        "session_agents_available",
        passed,
        list(expected),
        available,
        "Every expected agent was registered in the session."
        if passed
        else "The session never registered agent(s) {}; it offered {}. -> the routing verdict for "
        "this scenario would be meaningless, because the delegate it expects was not loadable. "
        "Check 'expect_plugins' covers the plugin that provides them.".format(missing, available),
    )


def session_plugins_assertion(expected, events):
    loaded = session_payload(events).get("plugins")
    if not loaded:
        return None
    names = [entry.get("name") for entry in loaded if isinstance(entry, dict)]
    missing = [name for name in expected if name not in names]
    passed = not missing
    return integrity(
        "session_plugins_loaded",
        passed,
        list(expected),
        names,
        "Every expected plugin was loaded into the session."
        if passed
        else "The session never loaded plugin(s) {}; it loaded {}. -> every assertion in this "
        "scenario is conditional on a load that did not happen.".format(missing, names),
    )


def workspace_prefixes(workspace):
    normalized = os.path.normpath(workspace)
    return (normalized, os.path.normpath(os.path.join("/private", normalized.lstrip("/"))))


def without_flag_patterns(words):
    kept = []
    operand_of_a_flag = False
    for token in words:
        if operand_of_a_flag:
            operand_of_a_flag = False
        elif token in PATTERN_OPERAND_FLAGS:
            operand_of_a_flag = True
        else:
            kept.append(token)
    return kept


def path_operands(tokens):
    words = without_flag_patterns(
        [token for token in tokens if token not in BASH_OPERATORS]
    )
    if not words or os.path.basename(words[0]) not in PATTERN_OPERAND_COMMANDS:
        return words
    arguments = words[1:]
    for position, token in enumerate(arguments):
        if not token.startswith("-"):
            return arguments[:position] + arguments[position + 1:]
    return arguments


def scanned_arguments(command):
    try:
        segments = bash_segments(command)
    except ValueError:
        return [token.strip(QUOTE_CHARACTERS) for token in TOKEN_SPLIT.split(command) if token]
    return [token for segment in segments for token in path_operands(segment)]


def prefix_matcher(prefixes):
    return prefixes, tuple(prefix + "/" for prefix in prefixes)


def under_prefix(path, matcher):
    prefixes, nested = matcher
    return path in prefixes or path.startswith(nested)


def path_candidates(token):
    candidates = [] if token.startswith("-") else [token]
    if "=" in token:
        assigned = token.partition("=")[2]
        if assigned:
            candidates.append(assigned)
    return candidates


def resolved_path(candidate, workspace):
    if "$" in candidate or "`" in candidate:
        return None
    if candidate.startswith("~"):
        expanded = os.path.expanduser(candidate)
        return os.path.normpath(expanded) if expanded != candidate else None
    if candidate.startswith("/"):
        return os.path.normpath(candidate)
    return os.path.normpath(os.path.join(workspace, candidate))


def home_prefixes():
    home = os.path.expanduser("~")
    return workspace_prefixes(home) if home.startswith("/") else ()


def sibling_workspace_prefixes(workspace):
    root = os.path.dirname(os.path.normpath(workspace))
    if root in ("", "/") or root in SCRATCH_PATH_PREFIXES:
        return ()
    return workspace_prefixes(root)


def without_substitutions(command):
    if "$(" not in command and "`" not in command:
        return command
    text, replaced = SUBSTITUTION.subn(SUBSTITUTION_PLACEHOLDER, command)
    while replaced:
        text, replaced = SUBSTITUTION.subn(SUBSTITUTION_PLACEHOLDER, text)
    return text


def escaping_paths(command, workspace):
    contained = prefix_matcher(workspace_prefixes(workspace))
    sibling_paths = sibling_workspace_prefixes(workspace)
    siblings = prefix_matcher(sibling_paths)
    tolerated = prefix_matcher(TOLERATED_PATH_PREFIXES)
    outside = prefix_matcher(sibling_paths + home_prefixes())
    escapes = []
    for token in scanned_arguments(without_substitutions(command)):
        for candidate in path_candidates(token):
            resolved = resolved_path(candidate, workspace)
            if resolved is None or under_prefix(resolved, contained):
                continue
            if under_prefix(resolved, siblings) or not under_prefix(resolved, tolerated):
                escapes.append(resolved)
    for raw in ABSOLUTE_PATH.findall(command):
        embedded = os.path.normpath(raw)
        if under_prefix(embedded, contained):
            continue
        if under_prefix(embedded, outside):
            escapes.append(embedded)
    return list(dict.fromkeys(escapes))


def workspace_containment_assertion(events, meta):
    workspace = meta.get("workspace_path") or ""
    if not workspace:
        return None
    violations = []
    for event in events:
        command = event.get("bash_command") or ""
        for escape in escaping_paths(command, workspace):
            violations.append("{} (in: {})".format(escape, command[:70]))
    passed = not violations
    return integrity(
        "workspace_containment",
        passed,
        "every Bash path under {}".format(workspace),
        violations or "all contained",
        "No Bash command reached outside the fixture workspace."
        if passed
        else "Bash command(s) referenced path(s) outside the fixture workspace: {}. -> the session "
        "escaped its sandbox, so any verdict from this run describes the wrong filesystem.".format(
            "; ".join(violations)
        ),
    )


def integrity_assertions(scenario, events, meta, transcript_error):
    checks = [
        run_metadata_assertion(meta),
        transcript_readable_assertion(transcript_error, events),
        cli_exit_assertion(meta),
        cli_result_assertion(events),
        completed_before_timeout_assertion(scenario, meta),
    ]
    optional = [
        workspace_containment_assertion(events, meta),
        session_agents_assertion(scenario.get("expect_agents") or [], events),
        session_plugins_assertion(scenario.get("expect_plugins") or [], events),
    ]
    return checks + [check for check in optional if check is not None]


def decide_verdict(scenario, checks):
    if scenario.get("skip_reason"):
        return "SKIP"
    if failed(checks, INTEGRITY):
        return "ERROR"
    if not of_kind(checks, BEHAVIORAL):
        return "ERROR"
    return "PASS" if not failed(checks, BEHAVIORAL) else "FAIL"


def artifact_paths(result_dir):
    return {
        "transcript": os.path.join(result_dir, TRANSCRIPT_NAME),
        "events": os.path.join(result_dir, EVENTS_NAME),
        "scenario": os.path.join(result_dir, SCENARIO_COPY_NAME),
        "result": os.path.join(result_dir, RESULT_NAME),
        "run_meta": os.path.join(result_dir, RUN_META_NAME),
    }


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def failure_reason(scenario, checks, verdict):
    if verdict == "SKIP":
        return scenario.get("skip_reason") or ""
    if verdict == "PASS":
        return ""
    broken = failed(checks, INTEGRITY) or failed(checks, BEHAVIORAL)
    if broken:
        return "; ".join(check["message"] for check in broken)
    return (
        "The scenario declares no behavioral expectation, so nothing about the model's conduct was "
        "checked. -> add at least one behavioral field; a run that asserts nothing is not a pass."
    )


def verify_run(scenario, result_dir):
    return verify_run_with_events(scenario, result_dir)[0]


def verify_run_with_events(scenario, result_dir):
    meta = read_meta(result_dir)
    records, transcript_error = read_transcript(result_dir)
    events = normalize_events(records)
    checks = integrity_assertions(scenario, events, meta, transcript_error)
    if not failed(checks, INTEGRITY):
        checks = checks + build_assertions(scenario, events, meta)
    verdict = decide_verdict(scenario, checks)
    failure = failure_reason(scenario, checks, verdict)
    assertions = checks
    result = {
        "scenario_id": scenario.get("id") or "",
        "verdict": verdict,
        "failure_reason": failure,
        "duration_seconds": meta.get("duration_seconds"),
        "cli_exit_code": meta.get("cli_exit_code"),
        "cli_version": meta.get("cli_version") or "",
        "run_id": meta.get("run_id") or "",
        "assertions": assertions,
        "artifacts": artifact_paths(result_dir),
    }
    return result, events


def tree_hash(root):
    digest = hashlib.sha256()
    for current, directories, files in os.walk(root):
        directories[:] = sorted(name for name in directories if name != ".git")
        for name in sorted(files):
            path = os.path.join(current, name)
            if not os.path.isfile(path) or os.path.islink(path):
                continue
            relative = os.path.relpath(path, root).encode("utf-8")
            with open(path, "rb") as handle:
                content = handle.read()
            digest.update(relative)
            digest.update(b"\0")
            digest.update(str(len(content)).encode("ascii"))
            digest.update(b"\0")
            digest.update(content)
    return digest.hexdigest()


def collect_results(run_dir):
    results = []
    for name in sorted(os.listdir(run_dir)):
        path = os.path.join(run_dir, name, RESULT_NAME)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                results.append(json.load(handle))
    return results


def build_summary(run_dir, results):
    counts = dict((verdict, 0) for verdict in VERDICTS)
    for result in results:
        verdict = result.get("verdict", "ERROR")
        counts[verdict] = counts.get(verdict, 0) + 1
    return {
        "run_id": os.path.basename(run_dir.rstrip("/")),
        "counts": counts,
        "scenarios": [
            {
                "scenario_id": result.get("scenario_id"),
                "verdict": result.get("verdict"),
                "duration_seconds": result.get("duration_seconds"),
                "cli_exit_code": result.get("cli_exit_code"),
                "cli_version": result.get("cli_version"),
                "failure_reason": result.get("failure_reason"),
                "failed_assertions": [
                    check["name"] for check in result.get("assertions", []) if not check["passed"]
                ],
            }
            for result in results
        ],
    }


def render_summary(summary):
    counts = summary["counts"]
    lines = ["# Eval Run {}".format(summary["run_id"]), ""]
    lines.append("| Scenario | Verdict | Duration | Failed assertions |")
    lines.append("| --- | --- | --- | --- |")
    for entry in summary["scenarios"]:
        lines.append(
            "| {} | {} | {}s | {} |".format(
                entry["scenario_id"],
                entry["verdict"],
                entry["duration_seconds"],
                ", ".join(entry["failed_assertions"]) or "-",
            )
        )
    lines.append("")
    lines.append(" · ".join("{} {}".format(verdict, counts[verdict]) for verdict in VERDICTS))
    lines.append("")
    for entry in summary["scenarios"]:
        if entry["verdict"] in ("FAIL", "ERROR") and entry["failure_reason"]:
            lines.append("- **{}** — {}".format(entry["scenario_id"], entry["failure_reason"]))
    return "\n".join(lines)


def summarize_run(run_dir):
    summary = build_summary(run_dir, collect_results(run_dir))
    write_json(os.path.join(run_dir, "summary.json"), summary)
    body = render_summary(summary)
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as handle:
        handle.write(body + "\n")
    return summary, body


def summarize_command(run_dir):
    if not os.path.isdir(run_dir):
        sys.stderr.write("RESULT ERROR: {}\n".format(run_dir))
        sys.stderr.write("The run directory does not exist. -> pass the directory run.sh created\n")
        return 1
    summary, body = summarize_run(run_dir)
    sys.stdout.write("\n".join(body.split("\n")[2:]) + "\n")
    counts = summary["counts"]
    return 1 if counts["FAIL"] or counts["ERROR"] else 0


def reverification_result_name():
    return "result.reverified-{}.json".format(
        datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    )


def persist_run(scenario, result_dir, result, events):
    result_path = os.path.join(result_dir, RESULT_NAME)
    if os.path.exists(result_path):
        archived = os.path.join(result_dir, reverification_result_name())
        write_json(archived, result)
        return archived
    write_json(os.path.join(result_dir, EVENTS_NAME), events)
    write_json(os.path.join(result_dir, SCENARIO_COPY_NAME), scenario)
    write_json(result_path, result)
    return result_path


def print_result(result):
    sys.stdout.write("{}: {}\n".format(result["verdict"], result["scenario_id"]))
    for check in result["assertions"]:
        if not check["passed"]:
            sys.stdout.write("  FAILED {} — {}\n".format(check["name"], check["message"]))
    if result["verdict"] in ("ERROR", "SKIP") and result["failure_reason"]:
        sys.stdout.write("  {}\n".format(result["failure_reason"]))


def verify_scenario(scenario_path, result_dir):
    scenario = load_scenario(scenario_path)
    if scenario is None:
        return 1
    if not os.path.isdir(result_dir):
        sys.stderr.write("RESULT ERROR: {}\n".format(result_dir))
        sys.stderr.write(
            "The result directory does not exist. -> run the scenario first so run.sh creates it\n"
        )
        return 1
    result, events = verify_run_with_events(scenario, result_dir)
    written = persist_run(scenario, result_dir, result, events)
    print_result(result)
    if os.path.basename(written) != RESULT_NAME:
        sys.stdout.write(
            "  re-verification: existing evidence left untouched, verdict written to {}\n".format(
                written
            )
        )
    return 0 if result["verdict"] in ("PASS", "SKIP") else 1


def assistant_text_record(text, parent=None):
    return {
        "type": "assistant",
        "parent_tool_use_id": parent,
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def tool_use_record(name, tool_input, tool_use_id, parent=None):
    return {
        "type": "assistant",
        "parent_tool_use_id": parent,
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": tool_use_id, "name": name, "input": tool_input}
            ],
        },
    }


def tool_result_record(tool_use_id, text, parent=None):
    return {
        "type": "user",
        "parent_tool_use_id": parent,
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}
            ],
        },
    }


def result_record(text):
    return {"type": "result", "subtype": "success", "is_error": False, "result": text}


def self_test_scenario(**overrides):
    scenario = {
        "id": "synthetic",
        "description": "synthetic self-test scenario",
        "fixture": "minimal-repo",
        "expect_plugins": ["orchestrator"],
        "expect_agents": ["generalist"],
        "prompt": "add a health endpoint and verify it",
        "expect_alignment_mode": "acted_directly",
        "expect_delegate": "backend-engineer",
        "forbidden_delegates": ["frontend-engineer"],
        "forbidden_tools": ["Write"],
        "forbidden_bash_patterns": ["rm\\s+-rf"],
        "expect_verdict_prefix": ["DONE", "BLOCKED", "FAILED"],
        "required_response_markers": ["health endpoint"],
        "expect_mutation_state": "changed",
        "expect_verification_evidence": {"command": "pytest -q", "result": "3 passed"},
        "timeout_seconds": 120,
        "cleanup_policy": "never",
    }
    scenario.update(overrides)
    return scenario


def self_test_meta(**overrides):
    meta = {
        "cli_version": "self-test",
        "cli_exit_code": 0,
        "duration_seconds": 1.0,
        "timed_out": False,
        "timeout_seconds": 120,
        "tree_hash_before": "hash-before",
        "tree_hash_after": "hash-after",
        "run_id": "self-test",
    }
    meta.update(overrides)
    return meta


def session_init_record(agents=None, plugins=None):
    return {
        "type": "system",
        "subtype": "init",
        "model": "claude-opus-5",
        "tools": ["Bash", "Read", "Task"],
        "agents": ["orchestrator:orchestrator", "orchestrator:generalist"] if agents is None else agents,
        "plugins": [{"name": "orchestrator"}] if plugins is None else plugins,
        "permissionMode": "bypassPermissions",
    }


def passing_records(delegate="backend-engineer"):
    return [
        session_init_record(),
        assistant_text_record("Routing this to the backend specialist."),
        tool_use_record("Task", {"subagent_type": delegate, "prompt": "add it"}, "toolu_task"),
        tool_result_record("toolu_task", "endpoint added"),
        tool_use_record("Bash", {"command": "pytest -q"}, "toolu_bash"),
        tool_result_record("toolu_bash", "3 passed in 0.42s"),
        assistant_text_record("DONE — added the health endpoint and pytest -q reports 3 passed."),
        result_record("DONE — added the health endpoint and pytest -q reports 3 passed."),
    ]


def staged_result_dir(records, meta, write_transcript=True, raw_lines=None):
    directory = tempfile.mkdtemp(prefix="eval-self-test-")
    if raw_lines is not None:
        with open(os.path.join(directory, TRANSCRIPT_NAME), "w", encoding="utf-8") as handle:
            handle.write("\n".join(raw_lines) + "\n")
    elif write_transcript:
        with open(os.path.join(directory, TRANSCRIPT_NAME), "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record) + "\n")
    write_json(os.path.join(directory, RUN_META_NAME), meta)
    return directory


def named_assertion(result, name):
    for check in result["assertions"]:
        if check["name"] == name:
            return check
    raise AssertionError("no assertion named '{}' in {}".format(name, [c["name"] for c in result["assertions"]]))


def expect_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError("{}: expected {!r}, got {!r}".format(label, expected, actual))


def expect_contains(haystack, needle, label):
    if needle not in haystack:
        raise AssertionError("{}: {!r} not found in {!r}".format(label, needle, haystack))


def test_passing_scenario(stage):
    result = stage(self_test_scenario(), passing_records(), self_test_meta())
    expect_equal(result["verdict"], "PASS", "passing scenario verdict")
    expect_equal(result["failure_reason"], "", "passing scenario failure reason")


def test_wrong_delegate_fails(stage):
    result = stage(self_test_scenario(), passing_records("frontend-engineer"), self_test_meta())
    expect_equal(result["verdict"], "FAIL", "wrong delegate verdict")
    check = named_assertion(result, "expected_delegate")
    expect_equal(check["passed"], False, "expected_delegate passed flag")
    expect_contains(check["message"], "backend-engineer", "expected_delegate message names expectation")
    expect_contains(check["message"], "frontend-engineer", "expected_delegate message names observation")


def test_orchestrator_wrote_directly_fails(stage):
    records = passing_records()
    records.insert(2, tool_use_record("Write", {"file_path": "app/health.py"}, "toolu_write"))
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "FAIL", "orchestrator write verdict")
    check = named_assertion(result, "forbidden_tools")
    expect_equal(check["passed"], False, "forbidden_tools passed flag")
    expect_contains(check["message"], "Write used 1 time(s)", "forbidden_tools message names the tool")


def test_subagent_wrote_is_allowed(stage):
    records = passing_records()
    records.insert(
        3, tool_use_record("Write", {"file_path": "app/health.py"}, "toolu_write", "toolu_task")
    )
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "PASS", "subagent write verdict")
    check = named_assertion(result, "forbidden_tools")
    expect_equal(check["passed"], True, "forbidden_tools passed flag for nested write")


def test_missing_transcript_is_error(stage):
    result = stage(self_test_scenario(), [], self_test_meta(), write_transcript=False)
    expect_equal(result["verdict"], "ERROR", "missing transcript verdict")
    expect_contains(result["failure_reason"], "does not exist", "missing transcript reason")


def test_empty_transcript_is_error(stage):
    result = stage(self_test_scenario(), [], self_test_meta())
    expect_equal(result["verdict"], "ERROR", "empty transcript verdict")
    expect_contains(result["failure_reason"], "is empty", "empty transcript reason")


def test_unparseable_transcript_is_error(stage):
    result = stage(self_test_scenario(), [], self_test_meta(), raw_lines=["{not json"])
    expect_equal(result["verdict"], "ERROR", "unparseable transcript verdict")
    expect_contains(result["failure_reason"], "not valid JSON", "unparseable transcript reason")


def test_timeout_is_error(stage):
    result = stage(
        self_test_scenario(), passing_records(), self_test_meta(timed_out=True, duration_seconds=120.0)
    )
    expect_equal(result["verdict"], "ERROR", "timeout verdict")
    expect_contains(result["failure_reason"], "exceeded its 120s budget", "timeout reason")
    check = named_assertion(result, "completed_before_timeout")
    expect_equal(check["passed"], False, "completed_before_timeout passed flag")


def test_non_zero_exit_is_error(stage):
    result = stage(self_test_scenario(), passing_records(), self_test_meta(cli_exit_code=1))
    expect_equal(result["verdict"], "ERROR", "non-zero exit verdict")
    expect_contains(result["failure_reason"], "exited with code 1", "non-zero exit reason")


def test_zero_behavioral_assertions_is_error(stage):
    clean = [integrity("ok", True, "x", "x", "fine")]
    expect_equal(decide_verdict({"id": "empty"}, clean), "ERROR", "integrity-only verdict is ERROR")
    expect_equal(
        decide_verdict({"id": "empty"}, clean + [assertion("b", True, "x", "x", "ok")]),
        "PASS",
        "one passing behavioral assertion verdict",
    )
    expect_equal(
        decide_verdict({"id": "empty"}, [integrity("bad", False, "x", "y", "broken")]),
        "ERROR",
        "a failed integrity assertion is ERROR, never FAIL",
    )
    expect_equal(
        decide_verdict({"id": "empty"}, clean + [assertion("b", False, "x", "y", "miss")]),
        "FAIL",
        "a failed behavioral assertion is FAIL",
    )
    result = stage(
        {"id": "asserts-nothing", "timeout_seconds": 120},
        passing_records(),
        self_test_meta(),
    )
    expect_equal(result["verdict"], "ERROR", "a scenario asserting nothing must never PASS")
    expect_contains(
        result["failure_reason"], "no behavioral expectation", "zero-behavioral failure reason"
    )


def test_forbidden_bash_pattern_fails(stage):
    records = passing_records()
    records.insert(2, tool_use_record("Bash", {"command": "rm -rf build"}, "toolu_rm"))
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "FAIL", "forbidden bash verdict")
    check = named_assertion(result, "forbidden_bash_patterns")
    expect_contains(check["message"], "rm -rf build", "forbidden bash message names the command")


def test_aligned_first_detected(stage):
    records = [
        assistant_text_record("Do you want the endpoint under /health or /healthz?"),
        result_record("Do you want the endpoint under /health or /healthz?"),
    ]
    scenario = self_test_scenario(
        expect_alignment_mode="aligned_first",
        expect_delegate=None,
        forbidden_delegates=[],
        expect_verdict_prefix=[],
        required_response_markers=[],
        expect_verification_evidence=None,
        expect_mutation_state="unchanged",
    )
    meta = self_test_meta(tree_hash_after="hash-before")
    result = stage(scenario, records, meta)
    expect_equal(result["verdict"], "PASS", "aligned_first verdict")


def test_mutation_state_mismatch_fails(stage):
    meta = self_test_meta(tree_hash_after="hash-before")
    result = stage(self_test_scenario(), passing_records(), meta)
    expect_equal(result["verdict"], "FAIL", "mutation mismatch verdict")
    check = named_assertion(result, "mutation_state")
    expect_contains(check["message"], "'changed'", "mutation message names the expectation")
    expect_contains(check["message"], "'unchanged'", "mutation message names the observation")


def test_skip_lifecycle(stage):
    scenario = self_test_scenario(skip_reason="interactive lifecycle is not supported by -p")
    result = stage(scenario, [], self_test_meta(), write_transcript=False)
    expect_equal(result["verdict"], "SKIP", "skip verdict")


def validate_quietly(directory):
    original_out, original_err = sys.stdout, sys.stderr
    sys.stdout = open(os.devnull, "w")
    sys.stderr = sys.stdout
    try:
        return validate_scenarios(directory)
    finally:
        sys.stdout.close()
        sys.stdout, sys.stderr = original_out, original_err


def scenario_tree(entries):
    root = tempfile.mkdtemp(prefix="eval-self-test-tree-")
    for relative, payload in entries:
        path = os.path.join(root, relative)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        write_json(path, payload)
    return root


def marker_scenario(**overrides):
    scenario = self_test_scenario(
        expect_delegate=None,
        forbidden_delegates=[],
        forbidden_tools=[],
        forbidden_bash_patterns=[],
        expect_verdict_prefix=[],
        required_response_markers=[],
        expect_verification_evidence=None,
        expect_mutation_state="unchanged",
        expect_alignment_mode="blocked",
    )
    scenario.update(overrides)
    return scenario


def marker_verdict(stage, scenario, text):
    return stage(
        scenario,
        [assistant_text_record(text)],
        self_test_meta(tree_hash_after="hash-before"),
    )


def test_any_of_markers_need_only_one(stage):
    scenario = marker_scenario(
        required_response_markers_any=["capability", "no installed agent", "profiling"]
    )
    none_present = marker_verdict(
        stage, scenario, "BLOCKED - nothing here matches the request."
    )
    expect_equal(none_present["verdict"], "FAIL", "no accepted marker present must FAIL")
    check = named_assertion(none_present, "required_response_markers_any")
    for candidate in ("capability", "no installed agent", "profiling"):
        expect_contains(check["message"], candidate, "failure message lists every candidate")
    expect_contains(check["message"], "none of the accepted marker(s)", "failure message is explicit")

    one_present = marker_verdict(
        stage, scenario, "BLOCKED - no installed agent can do live production work."
    )
    expect_equal(one_present["verdict"], "PASS", "exactly one accepted marker must PASS")

    all_present = marker_verdict(
        stage,
        scenario,
        "BLOCKED - no installed agent has the capability for live production profiling.",
    )
    expect_equal(all_present["verdict"], "PASS", "all accepted markers present must PASS")


def test_all_of_and_any_of_are_independent(stage):
    scenario = marker_scenario(
        required_response_markers=["BLOCKED"],
        required_response_markers_any=["capability", "profiling"],
    )
    both = marker_verdict(stage, scenario, "BLOCKED - no agent has the profiling capability.")
    expect_equal(both["verdict"], "PASS", "both marker fields satisfied must PASS")

    any_only = marker_verdict(stage, scenario, "DONE - nobody covers profiling here.")
    expect_equal(any_only["verdict"], "FAIL", "any-of alone must not satisfy the all-of field")
    expect_equal(
        named_assertion(any_only, "required_response_markers")["passed"], False, "all-of failed"
    )
    expect_equal(
        named_assertion(any_only, "required_response_markers_any")["passed"], True, "any-of passed"
    )

    all_only = marker_verdict(stage, scenario, "BLOCKED - nothing here matches the request.")
    expect_equal(all_only["verdict"], "FAIL", "all-of alone must not satisfy the any-of field")
    expect_equal(
        named_assertion(all_only, "required_response_markers")["passed"], True, "all-of passed"
    )
    expect_equal(
        named_assertion(all_only, "required_response_markers_any")["passed"], False, "any-of failed"
    )


def test_reverification_preserves_evidence(stage):
    directory = staged_result_dir(passing_records(), self_test_meta())
    try:
        scenario = self_test_scenario()
        first, first_events = verify_run_with_events(scenario, directory)
        persist_run(scenario, directory, first, first_events)
        original = open(os.path.join(directory, RESULT_NAME), encoding="utf-8").read()
        tampered = self_test_scenario(expect_delegate="frontend-engineer")
        second, second_events = verify_run_with_events(tampered, directory)
        written = persist_run(tampered, directory, second, second_events)
        expect_equal(second["verdict"], "FAIL", "re-verification still judges honestly")
        if os.path.basename(written) == RESULT_NAME:
            raise AssertionError("re-verification must not overwrite the archived result")
        preserved = open(os.path.join(directory, RESULT_NAME), encoding="utf-8").read()
        expect_equal(preserved, original, "the original paid verdict must survive re-verification")
        expect_equal(
            json.load(open(os.path.join(directory, SCENARIO_COPY_NAME)))["expect_delegate"],
            "backend-engineer",
            "the frozen scenario copy must survive re-verification",
        )
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_unknown_agent_fails_validation(stage):
    root = scenario_tree(
        [(os.path.join("smoke", "ghost.json"), self_test_scenario(id="ghost", expect_agents=["no-such-agent"]))]
    )
    try:
        expect_equal(validate_quietly(root), 1, "a scenario naming a nonexistent agent must fail CI")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    accepted = scenario_tree(
        [(os.path.join("smoke", "ok.json"), self_test_scenario(id="ok", expect_agents=["orchestrator:generalist", "generalist"]))]
    )
    try:
        expect_equal(validate_quietly(accepted), 0, "bare and namespaced agent names are accepted")
    finally:
        shutil.rmtree(accepted, ignore_errors=True)


def test_eventless_transcript_is_error(stage):
    result = stage(self_test_scenario(), [], self_test_meta(), raw_lines=["[]", '"str"', "123", "null"])
    expect_equal(result["verdict"], "ERROR", "junk-but-parseable transcript must be ERROR")
    expect_contains(result["failure_reason"], "none meaningful", "eventless failure reason")
    expect_equal(
        of_kind(result["assertions"], BEHAVIORAL), [], "an eventless run judges no behavior"
    )
    expect_equal(
        [c["name"] for c in failed(result["assertions"], INTEGRITY)],
        ["transcript_readable"],
        "an eventless run names the integrity check that caught it",
    )


def test_init_only_transcript_is_error(stage):
    records = [{"type": "system", "subtype": "init", "tools": ["Bash"]}]
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "ERROR", "init-only transcript must be ERROR")
    expect_contains(result["failure_reason"], "no assistant text", "init-only failure reason")


def test_silence_is_not_blocked(stage):
    expect_equal(observed_alignment_mode([]), "no_activity", "an empty event list is not 'blocked'")
    init_only = normalize_events([{"type": "system", "subtype": "init"}])
    expect_equal(observed_alignment_mode(init_only), "no_activity", "init-only is not 'blocked'")
    refused = normalize_events([assistant_text_record("BLOCKED - no specialist owns this.")])
    expect_equal(observed_alignment_mode(refused), "blocked", "a real refusal is still 'blocked'")


def test_result_is_error_is_error(stage):
    records = passing_records()
    records.append({"type": "result", "subtype": "error_max_budget_usd", "is_error": True, "result": ""})
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "ERROR", "is_error on the result event must be ERROR")
    expect_contains(result["failure_reason"], "error_max_budget_usd", "budget abort names its subtype")
    expect_contains(result["failure_reason"], "EVAL_MAX_BUDGET_USD", "budget abort is self-diagnosing")


def test_model_prose_is_not_verification_evidence(stage):
    records = [
        tool_use_record("Task", {"subagent_type": "backend-engineer"}, "toolu_task"),
        tool_use_record("Bash", {"command": "pytest -q"}, "toolu_bash"),
        tool_result_record("toolu_bash", "collected 3 items"),
        assistant_text_record("DONE - the health endpoint works, 3 passed, all green."),
    ]
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "FAIL", "prose must not satisfy verification evidence")
    check = named_assertion(result, "verification_evidence")
    expect_contains(check["message"], "prose does not count", "evidence message rejects prose")


def test_namespaced_ban_over_matches(stage):
    if not agent_id_matches("core:skill-smith", "skill-smith", over_match=True):
        raise AssertionError("a namespaced ban must catch a bare invocation")
    if not agent_id_matches("skill-smith", "core:skill-smith", over_match=True):
        raise AssertionError("a bare ban must catch a namespaced invocation")
    if agent_id_matches("skill-smith", "orchestrator:generalist", over_match=True):
        raise AssertionError("a ban must not catch an unrelated agent")
    scenario = self_test_scenario(
        expect_delegate="skill-smith", forbidden_delegates=["core:skill-smith"]
    )
    result = stage(scenario, passing_records("skill-smith"), self_test_meta())
    expect_equal(result["verdict"], "FAIL", "namespaced ban must trip on a bare invocation")


def test_tool_bans_are_case_insensitive(stage):
    events = normalize_events([tool_use_record("Write", {"file_path": "a"}, "t1")])
    for ban in ("Write", "write", "WRITE"):
        check = forbidden_tools_assertion([ban], events)
        if check["passed"]:
            raise AssertionError("ban {!r} must catch the Write tool".format(ban))
        expect_contains(check["message"], "forbidden tool", "ban message names the violation")
    if not forbidden_tools_assertion(["Edit"], events)["passed"]:
        raise AssertionError("a ban on an unused tool must not fire")
    nested = normalize_events([tool_use_record("Write", {"file_path": "a"}, "t1", "parent")])
    if not forbidden_tools_assertion(["write"], nested)["passed"]:
        raise AssertionError("a delegated subagent's Write must still not trip the orchestrator ban")


def test_unregistered_agent_is_integrity_error(stage):
    records = passing_records()
    records[0] = session_init_record(agents=["orchestrator:orchestrator"])
    scenario = self_test_scenario(expect_agents=["generalist", "skill-smith"])
    result = stage(scenario, records, self_test_meta())
    expect_equal(result["verdict"], "ERROR", "an unregistered agent is a harness fault, not a FAIL")
    check = named_assertion(result, "session_agents_available")
    expect_equal(check["kind"], INTEGRITY, "roster check is integrity-kind")
    expect_contains(check["message"], "skill-smith", "roster message names the missing agent")
    expect_contains(check["message"], "generalist", "roster message names every missing agent")
    ok = stage(self_test_scenario(expect_agents=["orchestrator:generalist"]), passing_records(), self_test_meta())
    expect_equal(ok["verdict"], "PASS", "a registered agent passes in namespaced form")


def test_unloaded_plugin_is_integrity_error(stage):
    records = passing_records()
    records[0] = session_init_record(plugins=[{"name": "core"}])
    result = stage(self_test_scenario(expect_plugins=["orchestrator"]), records, self_test_meta())
    expect_equal(result["verdict"], "ERROR", "an unloaded plugin is a harness fault")
    check = named_assertion(result, "session_plugins_loaded")
    expect_equal(check["kind"], INTEGRITY, "plugin check is integrity-kind")
    expect_contains(check["message"], "orchestrator", "plugin message names the missing plugin")


def test_workspace_escape_is_integrity_error(stage):
    records = passing_records()
    records.insert(
        2, tool_use_record("Bash", {"command": "cd /Users/dev/real-repo && grep -rn x ."}, "t9")
    )
    meta = self_test_meta(workspace_path="/tmp/richmond-evals/run/scen")
    result = stage(self_test_scenario(), records, meta)
    expect_equal(result["verdict"], "ERROR", "escaping the workspace is a harness fault")
    check = named_assertion(result, "workspace_containment")
    expect_contains(check["message"], "/Users/dev/real-repo", "escape message names the path")
    contained = stage(
        self_test_scenario(),
        passing_records(),
        self_test_meta(workspace_path="/tmp/richmond-evals/run/scen"),
    )
    expect_equal(contained["verdict"], "PASS", "a contained run is unaffected")
    for command in ("ls /usr/bin", "cat /dev/null", "grep -rn x ."):
        if escaping_paths(command, "/tmp/ws"):
            raise AssertionError("system and relative paths must not be flagged: {!r}".format(command))
    for command in ("curl https://example.com/x", 'grep -rn "/health" src'):
        if escaping_paths(command, "/tmp/ws"):
            raise AssertionError("a URL scheme and a search pattern are not paths: {!r}".format(command))
    if escaping_paths("ls /tmp/richmond-evals/run/scen/file", "/tmp//richmond-evals/run/scen"):
        raise AssertionError("a doubled slash in the workspace path must not read as an escape")
    nested = normalize_events(
        [tool_use_record("Bash", {"command": "rm /etc/../Users/dev/x"}, "t1", "parent")]
    )
    if workspace_containment_assertion(nested, {"workspace_path": "/tmp/ws"})["passed"]:
        raise AssertionError("a nested subagent escape must also be caught")


def test_workspace_containment_resolves_paths(stage):
    workspace = "/tmp/richmond-evals/run/scen"
    home = os.path.expanduser("~")
    for command in (
        './check.sh 2>&1; echo "EXIT: $?"',
        "cd /tmp/richmond-evals/run/scen && ./check.sh",
        "R=/tmp/ws; python3 $R/src/cli.py",
        "npx -y pkg < /dev/null > /tmp/out.txt",
        'T=$(mktemp -d)/stubrepo; ls "$T"',
        'echo "MATCH abs /private/var form"',
        "python3 -c \"import json;json.load(open('$R/.claude/settings.json'))\"",
    ):
        found = escaping_paths(command, workspace)
        if found:
            raise AssertionError(
                "a path resolving inside the workspace or into scratch must not be flagged: "
                "{!r} -> {}".format(command, found)
            )
    for command in (
        "find . -not -path '*/node_modules/*' -not -path './.git/*'",
        "find . -path ./.git -prune -o -print",
        "find . -iname '/etc/passwd' -o -name '*/secrets/*'",
    ):
        if escaping_paths(command, workspace):
            raise AssertionError("a pattern passed to a flag is not a path: {!r}".format(command))
    for command in (
        "ls /tmp/richmond-evals/run/other-scenario",
        "ls /tmp/richmond-evals/run",
        "cd ..",
        "cat ~/.npmrc",
        "cat {}/.env".format(home),
        'echo "unterminated && cat {}/.env'.format(home),
        "find /Users/dev/real-repo -name '*.py'",
        "cd /Users/dev/real-repo && grep -rn x .",
    ):
        if not escaping_paths(command, workspace):
            raise AssertionError("a real escape must still be caught: {!r}".format(command))
    expect_equal(
        escaping_paths("ls ~/.claude/agents", workspace),
        [os.path.join(home, ".claude/agents")],
        "a tilde escape is reported as the path it resolves to",
    )
    expect_equal(
        escaping_paths("ls ~/.claude ~/.claude", workspace),
        [os.path.join(home, ".claude")],
        "the same escape is reported once per command",
    )
    expect_equal(
        escaping_paths("ls $(cat pointer)/agents", workspace),
        [],
        "a path built by command substitution stays unresolvable",
    )


def test_git_tag_is_read_only_only_when_it_lists(stage):
    expect_bash_classification(
        ["git tag", "git tag | tail -5", "git tag --list", "git tag -l 'v*'", "git tag -n5"],
        False,
        "listing tags must not count as a mutation",
    )
    expect_bash_classification(
        [
            "git tag v1.2.3",
            "git tag -a v1.2.3 -m 'release'",
            "git tag -d v1.2.3",
            "git tag --delete v1.2.3",
            "git tag -f v1.2.3 HEAD",
        ],
        True,
        "creating or deleting a tag is a mutation",
    )


def write_tree(entries):
    root = tempfile.mkdtemp(prefix="eval-self-test-tree-hash-")
    for relative, content in entries:
        path = os.path.join(root, relative)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
    return root


def test_tree_hash_defines_mutation(stage):
    trees = []
    try:
        base = write_tree([("a.txt", "one"), ("src/b.py", "two")])
        same = write_tree([("a.txt", "one"), ("src/b.py", "two")])
        trees += [base, same]
        expect_equal(tree_hash(base), tree_hash(same), "identical trees hash identically")

        os.makedirs(os.path.join(base, ".git"))
        with open(os.path.join(base, ".git", "HEAD"), "w", encoding="utf-8") as handle:
            handle.write("ref: refs/heads/main")
        expect_equal(tree_hash(base), tree_hash(same), ".git is excluded from the hash")

        edited = write_tree([("a.txt", "CHANGED"), ("src/b.py", "two")])
        trees.append(edited)
        if tree_hash(edited) == tree_hash(same):
            raise AssertionError("editing file content must change the hash")

        renamed = write_tree([("ab", "c")])
        split = write_tree([("a", "bc")])
        trees += [renamed, split]
        if tree_hash(renamed) == tree_hash(split):
            raise AssertionError(
                "name/content boundary is ambiguous: 'ab'+'c' hashes the same as 'a'+'bc'"
            )
    finally:
        for tree in trees:
            shutil.rmtree(tree, ignore_errors=True)


def test_summary_reports_and_sets_exit_status(stage):
    run_dir = tempfile.mkdtemp(prefix="eval-self-test-summary-")
    try:
        for name, verdict, failed_names in (
            ("a-pass", "PASS", []),
            ("b-fail", "FAIL", ["expected_delegate"]),
            ("c-error", "ERROR", []),
        ):
            os.makedirs(os.path.join(run_dir, name))
            write_json(
                os.path.join(run_dir, name, RESULT_NAME),
                {
                    "scenario_id": name,
                    "verdict": verdict,
                    "duration_seconds": 2.0,
                    "cli_exit_code": 0,
                    "cli_version": "2.1.221",
                    "failure_reason": "" if verdict == "PASS" else "because reasons",
                    "assertions": [
                        {"name": n, "kind": BEHAVIORAL, "passed": False} for n in failed_names
                    ],
                },
            )
        summary, body = summarize_run(run_dir)
        expect_equal(summary["counts"], {"PASS": 1, "FAIL": 1, "SKIP": 0, "ERROR": 1}, "counts")
        expect_equal(len(summary["scenarios"]), 3, "every scenario appears in the summary")
        expect_contains(body, "expected_delegate", "the summary names failed assertions")
        expect_contains(body, "because reasons", "the summary carries the failure reason")
        for name in ("a-pass", "b-fail", "c-error"):
            expect_contains(body, name, "summary lists {}".format(name))
        expect_equal(summarize_command(run_dir), 1, "FAIL or ERROR sets a non-zero exit status")
        for name in ("b-fail", "c-error"):
            shutil.rmtree(os.path.join(run_dir, name))
        expect_equal(summarize_command(run_dir), 0, "an all-PASS run exits zero")
        expect_equal(
            json.load(open(os.path.join(run_dir, "summary.json")))["counts"]["PASS"],
            1,
            "summary.json is rewritten",
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_schema_matches_scenario_fields(stage):
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "evals", "scenarios", SCHEMA_NAME,
    )
    with open(path, encoding="utf-8") as handle:
        schema = json.load(handle)
    expect_equal(
        sorted(schema["properties"]), sorted(SCENARIO_FIELDS), "schema properties match the validator"
    )
    expect_equal(
        sorted(schema["required"]), required_field_names(), "schema required list matches the validator"
    )
    for name, spec in schema["properties"].items():
        declared = spec["type"]
        types = declared if isinstance(declared, list) else [declared]
        nullable = "null" in types
        base = [entry for entry in types if entry != "null"][0]
        field = SCENARIO_FIELDS[name]
        expect_equal(SCHEMA_TYPE_NAMES[base], field["type"], "{} type".format(name))
        expect_equal(nullable, bool(field.get("nullable")), "{} nullability".format(name))
        expect_equal(list(spec.get("enum", [])), list(field.get("enum", [])), "{} enum".format(name))


def test_namespaced_delegate_matching(stage):
    if not agent_id_matches("generalist", "orchestrator:generalist"):
        raise AssertionError("a bare expectation must match the namespaced runtime id")
    if not agent_id_matches("orchestrator:generalist", "orchestrator:generalist"):
        raise AssertionError("an exact namespaced expectation must match")
    if agent_id_matches("core:skill-smith", "other:skill-smith"):
        raise AssertionError("a namespaced expectation must not match a different namespace")
    if agent_id_matches("generalist", "orchestrator:specialist"):
        raise AssertionError("a bare expectation must not match a different agent")
    records = passing_records("orchestrator:backend-engineer")
    result = stage(self_test_scenario(), records, self_test_meta())
    expect_equal(result["verdict"], "PASS", "bare expectation matches namespaced delegate")


def test_namespaced_forbidden_delegate_still_trips(stage):
    records = passing_records("core:skill-smith")
    scenario = self_test_scenario(
        expect_delegate="core:skill-smith", forbidden_delegates=["skill-smith"]
    )
    result = stage(scenario, records, self_test_meta())
    expect_equal(result["verdict"], "FAIL", "namespaced forbidden delegate must still trip")
    check = named_assertion(result, "forbidden_delegates")
    expect_equal(check["passed"], False, "forbidden_delegates passed flag")
    expect_contains(check["message"], "skill-smith", "forbidden message names the delegate")


def test_session_init_evidence_is_retained(stage):
    init = {
        "type": "system",
        "subtype": "init",
        "model": "claude-opus-5",
        "tools": ["Bash", "Read", "Task"],
        "agents": ["orchestrator:orchestrator"],
        "plugins": [{"name": "orchestrator"}],
        "permissionMode": "bypassPermissions",
    }
    event = normalize_events([init])[0]
    expect_equal(event["kind"], "system", "init event kind")
    expect_equal(event["session"]["model"], "claude-opus-5", "init model is retained")
    expect_equal(event["session"]["tools"], ["Bash", "Read", "Task"], "init tools are retained")
    if "Write" in event["session"]["tools"]:
        raise AssertionError("fixture should model an agent session with no Write tool")
    plain = normalize_events([{"type": "system", "subtype": "other"}])[0]
    if "session" in plain:
        raise AssertionError("only the init event should carry a session payload")


def test_nested_scenario_discovery(stage):
    root = scenario_tree(
        [
            ("schema.json", {"title": "not a scenario"}),
            ("flat.json", self_test_scenario(id="flat")),
            (os.path.join("smoke", "nested.json"), self_test_scenario(id="nested")),
            (os.path.join("smoke", "schema.json"), {"title": "not a scenario"}),
            (os.path.join("suite", "deep", "buried.json"), self_test_scenario(id="buried")),
        ]
    )
    try:
        found = [os.path.basename(path) for path in scenario_files(root)]
        expect_equal(found, ["flat.json", "nested.json", "buried.json"], "recursive discovery")
        expect_equal(
            available_scenario_ids(root), ["buried", "flat", "nested"], "discovered scenario ids"
        )
        expect_equal(validate_quietly(root), 0, "nested tree validates clean")
        path, error = resolve_scenario(root, "buried")
        expect_equal(error, "", "resolving a nested id reports no error")
        expect_equal(os.path.basename(path), "buried.json", "resolved nested path")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_ambiguous_scenario_id_is_error(stage):
    root = scenario_tree(
        [
            (os.path.join("smoke", "dup.json"), self_test_scenario(id="dup")),
            (os.path.join("regression", "dup.json"), self_test_scenario(id="dup")),
        ]
    )
    try:
        path, error = resolve_scenario(root, "dup")
        expect_equal(path, "", "ambiguous id resolves to no path")
        expect_contains(error, "ambiguous", "ambiguous id error wording")
        expect_contains(error, os.path.join("smoke", "dup.json"), "ambiguous error names first path")
        expect_contains(
            error, os.path.join("regression", "dup.json"), "ambiguous error names second path"
        )
        expect_equal(validate_quietly(root), 1, "duplicate ids fail validation")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_empty_scenario_tree_is_error(stage):
    root = scenario_tree([("schema.json", {"title": "not a scenario"})])
    try:
        expect_equal(scenario_files(root), [], "schema.json is not discovered as a scenario")
        expect_equal(validate_quietly(root), 1, "an empty scenario tree must not report success")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unknown_scenario_id_lists_available(stage):
    root = scenario_tree(
        [(os.path.join("smoke", "trivial-task.json"), self_test_scenario(id="trivial-task"))]
    )
    try:
        path, error = resolve_scenario(root, "typo-task")
        expect_equal(path, "", "unknown id resolves to no path")
        expect_contains(error, "trivial-task", "unknown id error lists the available ids")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_suite_target_resolves_every_nested_scenario(stage):
    root = scenario_tree(
        [
            (os.path.join("smoke", "one.json"), self_test_scenario(id="one")),
            (os.path.join("group", "b.json"), self_test_scenario(id="b")),
            (os.path.join("group", "a.json"), self_test_scenario(id="a")),
            (os.path.join("group", "deep", "c.json"), self_test_scenario(id="c")),
        ]
    )
    try:
        expect_equal(
            available_suites(root),
            ["group", os.path.join("group", "deep"), "smoke"],
            "every directory holding a scenario is a suite",
        )
        expect_equal(
            resolve_target(root, "one"),
            ("scenario", ["one"], ""),
            "a scenario id resolves to itself",
        )
        kind, ids, error = resolve_target(root, "group")
        expect_equal((kind, ids, error), ("suite", ["a", "b", "c"], ""), "a suite runs its whole tree")
        expect_equal(
            resolve_target(root, os.path.join("group", "deep")),
            ("suite", ["c"], ""),
            "a nested suite path resolves",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_scenario_id_wins_over_a_same_named_suite(stage):
    root = scenario_tree(
        [
            (os.path.join("dup", "inner.json"), self_test_scenario(id="inner")),
            (os.path.join("smoke", "dup.json"), self_test_scenario(id="dup")),
        ]
    )
    try:
        expect_equal(
            resolve_target(root, "dup"),
            ("scenario", ["dup"], ""),
            "a scenario id beats a same-named suite directory",
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_unknown_target_lists_scenarios_and_suites(stage):
    root = scenario_tree(
        [(os.path.join("smoke", "trivial-task.json"), self_test_scenario(id="trivial-task"))]
    )
    try:
        kind, ids, error = resolve_target(root, "typo")
        expect_equal((kind, ids), ("", []), "an unknown target resolves to nothing")
        expect_contains(error, "trivial-task", "unknown target lists the available scenario ids")
        expect_contains(error, "smoke", "unknown target lists the available suite directories")
        expect_equal(
            resolve_target(root, os.path.join("..", ".."))[0],
            "",
            "a target escaping the scenario root is never a suite",
        )
        expect_equal(
            resolve_target(root, ".")[0], "", "the scenario root itself is not a suite target"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def expect_bash_classification(commands, mutating, label):
    for command in commands:
        if is_mutating_bash(command) != mutating:
            raise AssertionError(
                "{}: {!r} classified as {}".format(
                    label, command, "mutating" if not mutating else "read-only"
                )
            )


def text_event(text):
    return normalize_events([assistant_text_record(text)])[0]


def test_read_only_bash_is_not_a_mutation(stage):
    expect_bash_classification(
        [
            "ls -la",
            "cat src/cli.py",
            "head -20 README.md",
            "tail -f",
            "grep -rn 'health' src",
            "grep -E 'foo|bar' src",
            "rg --files",
            "find . -name '*.py'",
            "wc -l src/cli.py",
            "git status --porcelain",
            "git diff HEAD~1",
            "git log --oneline -5",
            "git show HEAD",
            "stat README.md",
            "file src/cli.py",
            "which python3",
            "echo scouting the repo",
            "sed -n '1,5p' README.md",
            "cd src && ls",
            "ls >/dev/null 2>&1",
            "/bin/ls -la",
        ],
        False,
        "read-only command must not count as a mutation",
    )
    events = normalize_events(
        [
            tool_use_record("Bash", {"command": "git status --porcelain"}, "t1"),
            tool_use_record("Bash", {"command": "cat src/cli.py"}, "t2"),
            assistant_text_record("BLOCKED - the spec names two sources of truth."),
        ]
    )
    expect_equal(
        observed_alignment_mode(events), "blocked", "read-only scouting must not flip alignment mode"
    )


def test_mutating_bash_is_a_mutation(stage):
    expect_bash_classification(
        [
            "rm -rf build",
            "mkdir -p out",
            "touch marker",
            "mv a b",
            "cp a b",
            "sed -i 's/a/b/' f",
            "sed --in-place 's/a/b/' f",
            "tee out.txt",
            "echo hi > f",
            "cat a >> b",
            "find . -name '*.pyc' -delete",
            "find . -name '*.py' -exec rm {} ;",
            "sort -o f f",
            "git add -A",
            "git commit -m 'x'",
            "git checkout main",
            "git reset --hard",
            "npm install",
            "pip install requests",
        ],
        True,
        "mutating command must count as a mutation",
    )
    events = normalize_events([tool_use_record("Bash", {"command": "rm -rf build"}, "t1")])
    expect_equal(
        observed_alignment_mode(events), "acted_directly", "mutating bash must flip alignment mode"
    )


def test_bundled_short_option_is_still_a_mutating_flag(stage):
    expect_bash_classification(
        [
            "sed -ni '1s/a/b/w out' f",
            "sed -nie 's/a/b/' f",
            "sed -i.bak 's/a/b/' f",
            "sed -E -i '' f",
            "sort -bo out f",
        ],
        True,
        "a bundled short option must not hide an in-place edit",
    )
    expect_bash_classification(
        [
            "sed -n '1,5p' README.md",
            "sed -ne '1,5p' README.md",
            "sed -e 's/a/b/' f",
            "sed --expression='s/a/b/' f",
            "find . -name '*.py'",
            "sort -k2 -n f",
        ],
        False,
        "a legitimate short option must stay read-only",
    )


def test_quoted_angle_bracket_is_not_a_redirection(stage):
    expect_bash_classification(
        ['grep -rn "a -> b" src', "grep -rn 'x > y' .", "echo 'a -> b'"],
        False,
        "an angle bracket inside a quoted argument must not count as a mutation",
    )
    expect_bash_classification(
        ["echo hi > out.txt", "echo hi >> out.txt", "cat a > b", "cat a > b 2>&1"],
        True,
        "a redirection to a file must count as a mutation",
    )


def test_git_global_options_do_not_hide_the_subcommand(stage):
    expect_bash_classification(
        [
            "git -C sub status",
            "git -c k=v log",
            "git --git-dir=/x/.git log",
            "git --work-tree x diff",
            "git --namespace ns show HEAD",
        ],
        False,
        "a git global option value must not be read as the subcommand",
    )
    expect_bash_classification(
        [
            "git -C sub push",
            "git -c k=v commit -m 'x'",
            "git --work-tree x checkout .",
        ],
        True,
        "a git global option must not hide a mutating subcommand",
    )


def test_compound_command_is_mutating_when_any_part_mutates(stage):
    expect_bash_classification(
        [
            "ls && rm -rf x",
            "cat f; rm g",
            "ls | xargs rm",
            "git status && git add -A",
            "grep -q foo f && sed -i 's/a/b/' f",
            "cd src || mkdir src",
            "ls&&rm -rf x",
        ],
        True,
        "compound command with a mutating part must count as a mutation",
    )
    expect_bash_classification(
        ["ls -la && git status", "cat a | grep foo | wc -l", "cd src && cat cli.py"],
        False,
        "compound command that is read-only throughout must not count as a mutation",
    )


def test_unknown_command_defaults_to_mutating(stage):
    expect_bash_classification(
        [
            "frobnicate --all",
            "./scripts/deploy.sh",
            "make build",
            "cargo run",
            "pytest -q",
            "ls && frobnicate",
            'grep "unbalanced',
        ],
        True,
        "an unclassifiable command must default to mutating",
    )


def test_rhetorical_question_is_not_a_clarifying_question(stage):
    for text in [
        "BLOCKED - the lockfile pins a version that no longer exists. Why does this fail? The registry dropped it.",
        "FAILED - the suite errored. What happened? A fixture went missing.",
        "DONE - see https://example.com/docs?page=2 for the details.",
        "BLOCKED - the migration cannot be reversed. What then? Nothing, the data is gone.",
    ]:
        if is_clarifying_question(text_event(text)):
            raise AssertionError("rhetorical question treated as clarifying: {!r}".format(text))
    events = normalize_events(
        [
            assistant_text_record("BLOCKED - two sources of truth. Why? The spec contradicts itself."),
            tool_use_record("Write", {"file_path": "a"}, "t1"),
        ]
    )
    expect_equal(
        observed_alignment_mode(events),
        "acted_directly",
        "a rhetorical question must not flip alignment mode",
    )


def test_genuine_clarifying_question_is_detected(stage):
    for text in [
        "BLOCKED - two sources of truth. Which one should win?",
        "Do you want the endpoint under /health or /healthz?",
        "Should I bump the major version before releasing?",
        "BLOCKED - I need your call: Postgres or MySQL?",
        "Want me to open the PR?",
    ]:
        if not is_clarifying_question(text_event(text)):
            raise AssertionError("clarifying question not detected: {!r}".format(text))
    events = normalize_events(
        [
            assistant_text_record("Which suite should I target?"),
            tool_use_record("Write", {"file_path": "a"}, "t1"),
        ]
    )
    expect_equal(
        observed_alignment_mode(events),
        "aligned_first",
        "a genuine question before a mutation is aligned_first",
    )


def alignment_mode_of(*texts):
    return observed_alignment_mode(
        normalize_events([assistant_text_record(text) for text in texts])
    )


def test_question_after_a_verdict_is_reporting_not_aligning(stage):
    refusal = (
        "BLOCKED - src/normalize.py is gone from git, from the backups and from the manifest, so "
        "there is no way to recover it."
    )
    expect_equal(
        alignment_mode_of(refusal + " Do you have a copy in a CI artifact?"),
        "blocked",
        "a recovery question inside a BLOCKED refusal is not aligned_first",
    )
    expect_equal(
        alignment_mode_of(refusal),
        "blocked",
        "the same refusal without the question scores the same",
    )
    expect_equal(
        alignment_mode_of(refusal, "Do you have a copy in a CI artifact?"),
        "blocked",
        "a verdict in an earlier text block still suppresses the question",
    )
    expect_equal(
        alignment_mode_of(
            "BLOCKED - notarization needs a Developer ID no installed delegate holds. Do you have "
            "that certificate on this machine?"
        ),
        "blocked",
        "an information question after a verdict is not aligned_first",
    )


def test_decision_request_after_a_verdict_is_still_aligned_first(stage):
    for text in [
        "BLOCKED - batch support is underspecified. Should I take the titles from a file or from stdin?",
        "BLOCKED - the slug separator is undecided. Which one do you want?",
        "BLOCKED - I need your call before routing this: Postgres or MySQL?",
        "BLOCKED - the flag name is unsettled. Want me to go with --upper?",
    ]:
        expect_equal(
            alignment_mode_of(text),
            "aligned_first",
            "a decision request after a verdict still aligns: {!r}".format(text),
        )


def test_question_without_a_verdict_keeps_the_wider_bar(stage):
    expect_equal(
        alignment_mode_of("Do you have a copy of the deleted module in a CI artifact?"),
        "aligned_first",
        "the same question with no verdict is a pause to align",
    )
    expect_equal(
        alignment_mode_of("The lockfile is blocked behind review. Do you have the token?"),
        "aligned_first",
        "'blocked' in prose is not a verdict line",
    )


def test_verdict_prefix_accepts_the_markdown_the_classifier_accepts(stage):
    for text in [
        "**DONE** — shipped the rename.",
        "DONE — shipped the rename.",
        "## DONE — shipped the rename.",
        "> BLOCKED — the spec names two sources of truth.",
        "`FAILED` — pytest -q reports 2 failures.",
    ]:
        event = text_event(text)
        check = response_verdict_prefix_assertion(["DONE", "BLOCKED", "FAILED"], [event])
        expect_equal(check["passed"], True, "a decorated verdict opens the answer: {!r}".format(text))
        expect_equal(
            opens_with_verdict(event),
            check["passed"],
            "the assertion and the alignment classifier agree: {!r}".format(text),
        )


def test_verdict_prefix_still_rejects_a_token_buried_in_prose(stage):
    text = "I read src/cli.py and traced the rename, so the variable work is DONE now."
    event = text_event(text)
    check = response_verdict_prefix_assertion(["DONE", "BLOCKED", "FAILED"], [event])
    expect_equal(check["passed"], False, "a mid-sentence verdict token is not a verdict line")
    expect_equal(
        opens_with_verdict(event), False, "the classifier also reads that opening as prose"
    )
    expect_contains(
        check["message"], "I read src/cli.py", "the failure message shows the actual opening"
    )


def test_alignment_mode_judges_the_last_turn(stage):
    events = normalize_events(
        [
            session_init_record(),
            tool_use_record("Task", {"subagent_type": "backend-engineer"}, "t1"),
            tool_use_record("Write", {"file_path": "a"}, "t2"),
            session_init_record(),
            assistant_text_record("Which suite should I target?"),
        ]
    )
    expect_equal(
        observed_alignment_mode(events),
        "aligned_first",
        "a preceding turn's action must not decide the turn under test",
    )
    mirrored = normalize_events(
        [
            session_init_record(),
            assistant_text_record("Which suite should I target?"),
            session_init_record(),
            tool_use_record("Write", {"file_path": "a"}, "t1"),
        ]
    )
    expect_equal(
        observed_alignment_mode(mirrored),
        "acted_directly",
        "a preceding turn's question must not decide the turn under test",
    )


def only_error(errors, label):
    if len(errors) != 1:
        raise AssertionError("{}: expected exactly one error, got {!r}".format(label, errors))
    return errors[0]


def test_declared_fixture_and_plugins_are_accepted(stage):
    errors = resource_errors(
        self_test_scenario(fixture="minimal-repo", expect_plugins=["core", "orchestrator"])
    )
    expect_equal(errors, [], "a real fixture and real plugins raise nothing")


def test_missing_fixture_is_rejected_before_any_model_call(stage):
    errors = resource_errors(self_test_scenario(fixture="no-such-fixture"))
    message = only_error(errors, "missing fixture")
    expect_contains(message, "no-such-fixture", "missing fixture error names the fixture")
    expect_contains(message, "is not a directory", "missing fixture error names the reason")


def test_traversing_fixture_is_rejected(stage):
    for fixture in ["../../plugins/orchestrator/skills/alignment", "..", ".", "/etc"]:
        errors = resource_errors(self_test_scenario(fixture=fixture))
        message = only_error(errors, "traversing fixture {!r}".format(fixture))
        expect_contains(message, "resolves outside", "traversal error names the escape")


def test_missing_plugin_is_rejected_before_any_model_call(stage):
    errors = resource_errors(self_test_scenario(expect_plugins=["core", "no-such-plugin"]))
    message = only_error(errors, "missing plugin")
    expect_contains(message, "no-such-plugin", "missing plugin error names the plugin")
    expect_contains(message, "is not a directory", "missing plugin error names the reason")


def test_traversing_plugin_is_rejected(stage):
    errors = resource_errors(self_test_scenario(expect_plugins=["../evals"]))
    message = only_error(errors, "traversing plugin")
    expect_contains(message, "resolves outside", "plugin traversal error names the escape")


def self_test_cases():
    return [
        (name[5:], function)
        for name, function in list(globals().items())
        if name.startswith("test_") and callable(function)
    ]


def run_self_test():
    created = []

    def stage(scenario, records, meta, write_transcript=True, raw_lines=None):
        directory = staged_result_dir(records, meta, write_transcript, raw_lines)
        created.append(directory)
        return verify_run(scenario, directory)

    passed = 0
    failures = []
    for name, case in self_test_cases():
        try:
            case(stage)
        except AssertionError as error:
            failures.append((name, str(error)))
        else:
            passed += 1
            sys.stdout.write("  ok   {}\n".format(name))
    for name, detail in failures:
        sys.stdout.write("  FAIL {} — {}\n".format(name, detail))
    for directory in created:
        shutil.rmtree(directory, ignore_errors=True)
    total = passed + len(failures)
    sys.stdout.write(
        "\nself-test: {}/{} passed, {} failed\n".format(passed, total, len(failures))
    )
    return 1 if failures else 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="verify.py", description="Behavioral evaluation verifier."
    )
    parser.add_argument("--self-test", action="store_true", help="run the verifier unit tests")
    parser.add_argument(
        "--validate-scenarios", metavar="DIR", help="schema-validate every scenario JSON under DIR"
    )
    parser.add_argument("--scenario", metavar="FILE", help="scenario file for a completed run")
    parser.add_argument(
        "--result-dir", metavar="DIR", help="result directory holding transcript.jsonl"
    )
    parser.add_argument("--tree-hash", metavar="DIR", help="hash a fixture workspace tree")
    parser.add_argument("--summarize", metavar="DIR", help="write summary.json and summary.md")
    return parser


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.validate_scenarios:
        return validate_scenarios(args.validate_scenarios)
    if args.tree_hash:
        sys.stdout.write(tree_hash(args.tree_hash) + "\n")
        return 0
    if args.summarize:
        return summarize_command(args.summarize)
    if args.scenario and args.result_dir:
        return verify_scenario(args.scenario, args.result_dir)
    parser.error(
        "pass --self-test, --validate-scenarios DIR, --tree-hash DIR, --summarize DIR, "
        "or --scenario FILE --result-dir DIR"
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
