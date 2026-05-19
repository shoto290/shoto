# Troubleshooting

## Skill not triggering

1. **Description**: does it include keywords the user would say? Trigger phrases?
2. **Listed?**: ask `What skills are available?` — does it appear?
3. **Rephrase**: try a request more aligned with the `description`
4. **Direct**: invoke with `/skill-name` to confirm the skill itself works

## Skill triggers too often

1. **More specific description**: narrow trigger phrases
2. **Manual only**: set `disable-model-invocation: true`

## Descriptions cut short

Descriptions share a character budget = 1% of context window. When it overflows, least-invoked skills lose their descriptions first.

Diagnostics: `/doctor` shows budget usage + affected skills.

Fixes:
- Raise budget: `skillListingBudgetFraction` setting (e.g. `0.02` = 2%) or `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var
- Free budget: mark low-priority skills `"name-only"` in `skillOverrides`
- Trim: shorten `description` + `when_to_use` (combined cap = 1,536 chars per entry)
- Reorder: put the key use case **first** in `description` so it survives truncation

## Skill stopped influencing behavior

Content is usually still in context — the model is choosing other tools / approaches.

1. Strengthen `description` + instructions
2. Use hooks to enforce behavior deterministically
3. Re-invoke the skill (especially after compaction in long sessions)

## New skill directory not detected

Claude Code watches existing skill directories. Creating a **top-level** skill directory that did not exist at session start → restart Claude Code to register the watch. Adding skills inside an already-watched directory does not need restart.

## `context: fork` returns empty / no output

Forked subagents need an explicit task. If your skill body is only guidelines (`"use these conventions"`), the subagent has no prompt to act on.

Fix: include an explicit task ("Research X", "Generate Y", "Summarize the diff"). Use `$ARGUMENTS` to pass user input as the task target.

## Project skill's `allowed-tools` not pre-approving

Requires workspace trust. Accept the trust dialog for the project folder. Same as permission rules in `.claude/settings.json`.

## Dynamic context (`!command`) not executing

- Check `"disableSkillShellExecution"` is not `true` in settings (managed settings often enforce this)
- Confirm the syntax: backtick + `!` + command + backtick on a single line, or a fenced block opened with `` ```! ``
- Output substitution runs **once** — a command cannot emit a placeholder that gets expanded in a second pass
