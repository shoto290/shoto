---
name: tools
description: Reference for Claude Code's built-in tools (Read, Edit, Write, Bash, Glob, Grep, WebFetch, WebSearch, Agent, Skill, Monitor, NotebookEdit, TodoWrite, Task*, Cron*, RemoteTrigger, SendMessage, PushNotification, EnterPlanMode, ExitPlanMode, EnterWorktree, ExitWorktree, AskUserQuestion, PowerShell, LSP, ListMcpResourcesTool, ReadMcpResourceTool, WaitForMcpServers, ToolSearch, ShareOnboardingGuide, TeamCreate, TeamDelete). Load BEFORE the first tool call in a session, or when deciding between similar tools (Read vs Bash cat, Edit vs Write, Glob vs Grep, WebFetch vs curl, WebFetch vs WebSearch, Agent vs Skill, Monitor vs background Bash), debugging a tool failure (Edit failed, read-before-edit, exact-match, uniqueness, file not read), reasoning about permission rules (Tool(specifier) format, allow/deny patterns, Bash command matcher, Read/Edit path matcher, WebFetch domain matcher), or hitting limits (Glob 100-file cap, Bash 2-min timeout, Read large-file partial view, PDF page param, WebFetch 15-min cache, ripgrep regex escaping). Authoritative source: https://docs.claude.com/en/docs/claude-code/tools.
---

# tools

Reference for Claude Code's built-in tools. Use this skill to pick the right tool, avoid common failures, and write correct permission rules.

## When to use which tool

| Task | Preferred | Avoid / fallback | Why |
| :-- | :-- | :-- | :-- |
| Read a file's content | `Read` | `Bash cat/head/tail/sed` | `Read` returns line-numbered, cached output and registers the file for `Edit`. Shell readers only count as a read-before-edit in narrow cases (see [reference/file-tools.md](./reference/file-tools.md)). |
| Modify part of an existing file | `Edit` | `Write` | `Edit` sends only the diff; `Write` rewrites the entire file. Both require a prior `Read`. |
| Create a new file or full rewrite | `Write` | `Edit` | `Edit` cannot create files; new files have no prior content to match. |
| Find files by name / glob | `Glob` | `Bash find` | `Glob` is faster and sorted by mtime; `find` scans the whole tree. `Glob` does NOT respect `.gitignore` by default. |
| Search file contents | `Grep` | `Bash grep/rg` | `Grep` uses ripgrep, respects `.gitignore`, and supports structured `output_mode`. |
| Fetch a known URL | `WebFetch` | `Bash curl` | `WebFetch` runs the page through a small extractor model — lossy. Use `curl` for raw bytes or to bypass extraction. |
| Discover unknown URLs / current info | `WebSearch` | `WebFetch` | `WebSearch` returns ranked titles + URLs only; follow up with `WebFetch` to read a hit. |
| Spin off an isolated investigation | `Agent` | `Skill` | `Agent` opens a fresh context window and returns a single report. `Skill` runs inline in the current context. |
| Apply a reusable workflow inline | `Skill` | `Agent` | `Skill` loads `SKILL.md` into the current turn. No extra context cost. |
| Stream a long-running process | `Monitor` | `Bash run_in_background` | `Monitor` notifies on each stdout line. Background `Bash` requires manual polling. |
| Wait for a one-shot job | `Bash run_in_background` | `Monitor` | `run_in_background` notifies once on completion. |
| Run a Jupyter notebook cell edit | `NotebookEdit` | `Edit` | `Edit` does not understand `.ipynb` cell structure. |
| Schedule recurring work | `CronCreate` | `Bash` cron | Managed by Claude Code; survives sessions. |
| Persist async work across sessions | `TaskCreate` | inline reasoning | Tasks have their own lifecycle (`TaskGet`, `TaskList`, `TaskOutput`, `TaskStop`, `TaskUpdate`). |
| Trigger a remote runtime | `RemoteTrigger` | `Bash ssh`/`curl` | First-class API for remote execution; pairs with `PushNotification`. |
| Ask the user a structured question | `AskUserQuestion` | free-text prompt | Multi-choice prompts with options + recommendation are clearer than open-ended questions. |
| Send a chat message between sessions | `SendMessage` | n/a | Cross-session messaging primitive. |
| Plan-mode boundary | `EnterPlanMode` / `ExitPlanMode` | n/a | Mark planning vs execution segments. |
| Work in an isolated worktree | `EnterWorktree` / `ExitWorktree` | `Bash git worktree` | Managed lifecycle; auto-cleanup. |

Drill into the dedicated references for behavior nuances:

- [reference/file-tools.md](./reference/file-tools.md) — Read, Edit, Write, Glob, Grep, NotebookEdit
- [reference/shell-tools.md](./reference/shell-tools.md) — Bash, Monitor, PowerShell
- [reference/web-tools.md](./reference/web-tools.md) — WebFetch, WebSearch
- [reference/agent-tools.md](./reference/agent-tools.md) — Agent, Skill, SendMessage, AskUserQuestion, ShareOnboardingGuide
- [reference/task-cron.md](./reference/task-cron.md) — TaskCreate/Get/List/Output/Stop/Update, CronCreate/Delete/List, RemoteTrigger, PushNotification, TodoWrite, EnterPlanMode, ExitPlanMode, EnterWorktree, ExitWorktree, TeamCreate, TeamDelete, ToolSearch, WaitForMcpServers, ListMcpResourcesTool, ReadMcpResourceTool, LSP
- [reference/permissions.md](./reference/permissions.md) — `Tool(specifier)` rule syntax, allow/deny patterns, hook matchers

## Critical gotchas

### Read

- Large files return a **partial view** with offset/limit guidance — re-call `Read` with `offset` and `limit` to fetch the next slice.
- PDFs with more than 10 pages **require** the `pages` parameter (`pages: "1-5"`). Calls without it fail.
- Reading a file that doesn't exist returns an error, not empty contents.
- Empty files return a system reminder warning in place of content.
- Use absolute paths only.

### Edit

- **Read-before-edit** is mandatory. The harness tracks which files were read and rejects edits to unread files. A shell read (`cat`/`head`/`tail`/`sed -n`) satisfies this only when it covered the full file and the file is small.
- `old_string` must be an **exact** match including indentation and whitespace (after the line-number prefix from `Read` output).
- `old_string` must be **unique** in the file. If it isn't, expand the context or pass `replace_all: true`.
- Do NOT include the line-number prefix from `Read` output in `old_string`.

### Write

- Overwrites silently. Read the file first if it exists.
- Never use to create documentation (`*.md` / README) unless explicitly asked.

### Glob

- Caps at **100 files**, sorted by mtime (newest first). For more, narrow the pattern or search a subtree.
- Does **not** respect `.gitignore` by default. Pass `respect_gitignore: true` if you want to skip ignored paths.
- Glob `**` matches across directories; single `*` does not cross `/`.

### Grep

- Uses **ripgrep regex** (Rust regex syntax), not POSIX or PCRE. No lookbehind by default.
- Patterns containing `{}` must be escaped (`\{` `\}`) — ripgrep treats them as repetition counts.
- Respects `.gitignore` by default. Pass `-uu` (via `-u`) to include ignored files.
- `output_mode: "content"` returns matching lines; `"files_with_matches"` returns filenames only; `"count"` returns match counts per file.

### Bash

- Default timeout **120 000 ms** (2 min); max **600 000 ms** (10 min). Set `timeout` explicitly for slow commands.
- Working directory persists between calls within the project root. **Environment variables do not persist** — re-export each call.
- Avoid `cat`/`head`/`tail`/`sed`/`awk`/`echo` when a dedicated tool exists (`Read`, `Edit`, `Write`).
- Quote paths containing spaces. Use absolute paths unless you have intentionally `cd`'d.
- `run_in_background: true` returns immediately; you'll be notified on completion.
- Never chain `sleep` to poll — use `Monitor` for streaming output or `run_in_background` for one-shot completion.

### WebFetch

- HTTP URLs are auto-upgraded to HTTPS.
- Cross-host redirects are **not** followed automatically — `WebFetch` returns a redirect notice and you must issue a second call with the new host.
- Responses are **cached for 15 minutes**.
- The page is summarised by a small extraction model using your `prompt` — the raw HTML is lost. For raw bytes, use `Bash curl`.

### WebSearch

- Returns ranked titles + URLs + short snippets. Follow up with `WebFetch` to read a hit.
- US-only by default.

### Agent

- Opens a fresh context window. Sees only the prompt you pass — no access to the calling conversation.
- Returns a single final message. Stream-of-thought is not exposed.
- Cannot itself spawn `Agent` (no recursion).

### NotebookEdit

- Targets a single cell by `cell_id`. Use `edit_mode: "insert"` to add a new cell, `"delete"` to remove, default replaces in place.
- Cell type (`code` vs `markdown`) is preserved unless overridden.

### Monitor

- Each stdout line from the watched process is delivered as a notification. Use for tailing logs or long builds.
- Pair with `until <check>; do sleep N; done` patterns when polling for a state change.

## Permission rule cheatsheet

Permission rules use `Tool(specifier)` in `~/.claude/settings.json` (and project / enterprise overrides). Empty `()` matches every invocation of the tool.

| Tool family | Specifier format | Example allow rule | Example deny rule |
| :-- | :-- | :-- | :-- |
| `Bash` | command prefix (glob-ish, anchored at start) | `Bash(git status:*)` | `Bash(rm -rf:*)` |
| `Read` / `Edit` / `Write` / `Glob` / `Grep` / `NotebookEdit` | absolute or workspace-relative path glob | `Read(/Users/me/src/**)` | `Edit(**/.env)` |
| `WebFetch` | domain (no scheme, no path) | `WebFetch(domain:docs.claude.com)` | `WebFetch(domain:*)` |
| `WebSearch` | no specifier needed | `WebSearch` | `WebSearch` |
| `Agent` | subagent name | `Agent(Explore)` | `Agent(*)` |
| `Skill` | skill name | `Skill(tools)` | `Skill(deploy)` |
| `Task*` / `Cron*` / `RemoteTrigger` / `SendMessage` / `PushNotification` | bare tool name (no specifier) | `TaskCreate` | `CronDelete` |
| MCP tools (`ListMcpResourcesTool`, `ReadMcpResourceTool`, etc.) | bare tool name | `ListMcpResourcesTool` | `ReadMcpResourceTool` |
| Hook matchers | regex against tool name or pattern against tool input | `"matcher": "Bash"` | `"matcher": "Write|Edit"` |

Full grammar, precedence between `allow` / `deny` / `ask`, hook-matcher details, and pre-approval via skill `allowed-tools` are in [reference/permissions.md](./reference/permissions.md).

## Source

Authoritative documentation lives at:

- https://docs.claude.com/en/docs/claude-code/tools
- https://code.claude.com/docs/llms.txt

When in doubt, prefer the live docs over this skill — Claude Code's tool surface evolves.
