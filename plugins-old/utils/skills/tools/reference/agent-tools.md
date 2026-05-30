# Agent and interaction tools

Covers: `Agent`, `Skill`, `SendMessage`, `AskUserQuestion`, `ShareOnboardingGuide`.

## Agent

**Summary.** Spawns a sub-agent in a fresh context window. The sub-agent runs to completion and returns a single final message.

**Permission rule.** `Agent(<name>)` — the sub-agent's `name:` (e.g. `Agent(Explore)`, `Agent(skill-architect)`).

**Behaviour.**

- The sub-agent sees **only** the prompt you pass — it has no access to the calling conversation.
- Returns the sub-agent's final message verbatim. Intermediate reasoning is hidden.
- Sub-agents cannot themselves call `Agent` (no recursion).
- Use for parallel exploration, isolated investigations, and high-token tasks you don't want polluting the main thread.

**Pitfalls.**

- Assuming the sub-agent inherits context — pass everything it needs in the prompt.
- Expecting streaming output — you get one final message.
- Forgetting that file edits the sub-agent makes persist to disk (they share the filesystem) even though context is isolated.

## Skill

**Summary.** Loads a skill (`SKILL.md` + supporting files) into the current turn. Workflow stays inline; no fresh context.

**Permission rule.** `Skill(<name>)` — e.g. `Skill(tools)`, `Skill(deploy)`.

**Behaviour.**

- Auto-loaded by Claude when a request matches the skill's `description`.
- User-invocable as `/skill-name` unless `user-invocable: false`.
- Body is appended to the current turn — it costs tokens recurringly until compaction.

**When to prefer over `Agent`.**

- Workflow that must operate on the current conversation state.
- Small, focused procedures (commit, deploy, summarise).
- Knowledge / reference material.

**Pitfalls.**

- Overlong `SKILL.md` — keep under ~500 lines; offload detail to `reference/`.
- A `description` without trigger keywords — auto-invocation will miss.

## SendMessage

**Summary.** Sends a chat message between Claude Code sessions.

**Permission rule.** `SendMessage` (bare).

**Behaviour.**

- Targets another session by id. Used for cross-session orchestration (e.g. a long-running task signalling its launcher).
- Pairs with `PushNotification` when the recipient isn't actively running.

**Pitfalls.**

- Treating `SendMessage` as a chat UI — it's a programmatic primitive.

## AskUserQuestion

**Summary.** Prompts the user with a multi-choice question (options + implications + recommendation).

**Permission rule.** `AskUserQuestion` (bare). Almost always allowed.

**Behaviour.**

- Surface a single question with 2-5 options. Each option has a short implication string.
- Mark the recommended option as default.
- Strongly preferred over free-text prompts for decisions with a small option set — clearer for the user and easier to log.

**Pitfalls.**

- Using free-text when a multi-choice would do — slower, more error-prone.
- Asking the same question every turn — cache the answer in the session if it doesn't change.

## ShareOnboardingGuide

**Summary.** Surfaces the Claude Code onboarding guide to the user.

**Permission rule.** `ShareOnboardingGuide` (bare).

**Behaviour.**

- Used to introduce features. Not a programmable surface.
