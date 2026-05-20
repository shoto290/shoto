# Skill content lifecycle

When a skill is invoked (by user or Claude), the rendered `SKILL.md` content enters the conversation as a single message and stays for the rest of the session. Claude Code does **not** re-read the skill file on later turns.

Implications:
- Write guidance as **standing instructions**, not one-time steps
- Every line in the body is a recurring token cost
- Updates to `SKILL.md` mid-session do **not** retroactively change an already-invoked skill — re-invoke to pick up changes

## Auto-compaction

When the conversation hits the context limit and is summarized:
- The most recent invocation of each skill is **re-attached after the summary**
- Each re-attached skill keeps its first **5,000 tokens**
- Combined budget for re-attached skills: **25,000 tokens**
- Fills starting from most-recently-invoked, so older skills may be dropped entirely after compaction if many were invoked

If a skill seems to stop influencing behavior:
1. The content is usually still present — model is choosing other tools / approaches
2. Strengthen the `description` + instructions so the model keeps preferring it
3. Use hooks to enforce behavior deterministically
4. If large or many newer skills came after, **re-invoke** to restore full content

## Description listing budget

All skill names are always in context. Descriptions share a character budget scaling at **1% of the model's context window** (configurable via `skillListingBudgetFraction` setting or `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var).

When the budget overflows, descriptions for the least-invoked skills are **dropped first** — frequently-used skills keep their full text.

Each entry's combined `description` + `when_to_use` is capped at **1,536 chars** regardless of budget (configurable via `maxSkillDescriptionChars`).

Use `/doctor` to check whether the budget is overflowing.

To free budget:
- Mark low-priority skills `"name-only"` in `skillOverrides`
- Trim `description` and `when_to_use` text
- Put the key use case **first** in the description (it survives truncation)
