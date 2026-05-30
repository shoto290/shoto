# File tools

Covers: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `NotebookEdit`.

## Read

**Summary.** Reads a file from the local filesystem and returns line-numbered content (`cat -n` style). Registers the file with the harness so `Edit` is allowed.

**Permission rule.** `Read(<path-glob>)` — e.g. `Read(/Users/me/src/**)`, `Read(**/*.md)`. Absolute or workspace-relative paths.

**Parameters.**

- `file_path` (required) — absolute path.
- `offset` — 1-indexed line to start at.
- `limit` — number of lines to read.
- `pages` — required for PDFs with more than 10 pages (e.g. `"1-5"`, `"3"`, `"10-20"`); max 20 pages per call.

**Behaviour.**

- Default reads up to 2 000 lines from the top.
- Large files return a **partial view**; the response tells you how to fetch the rest via `offset`/`limit`.
- Empty files return a system reminder warning in place of the body.
- PDFs and Jupyter notebooks are supported. Notebook cells, outputs, and images are merged.
- Images render visually in the model (multimodal).
- A file you just edited via `Edit` / `Write` does NOT need to be re-read — the harness tracks file state for you.

**Pitfalls.**

- Forgetting the `pages` param on a large PDF — the call fails outright.
- Reading the same file repeatedly to verify edits — unnecessary; `Edit` would have errored if it failed.
- Using relative paths — always pass an absolute path.

**Worked example.**

```text
Read(file_path="/Users/me/repo/src/auth/token.ts", offset=40, limit=60)
```

Reads lines 40-99 of `token.ts`. Re-issue with `offset=100` to continue.

## Edit

**Summary.** Performs an exact string replacement in a file. Sends only the diff.

**Permission rule.** `Edit(<path-glob>)` — same syntax as `Read`.

**Parameters.**

- `file_path` (required) — absolute path.
- `old_string` (required) — exact text to find.
- `new_string` (required) — replacement.
- `replace_all` — replace every occurrence (default `false`).

**Behaviour.**

- The harness rejects `Edit` calls against files it has not seen via `Read`. A shell `cat`/`head`/`tail`/`sed -n` read satisfies this only when the call covered the **full file** and the file is small enough to fit in one response.
- `old_string` must match exactly — including indentation, trailing whitespace, and newlines. The line-number prefix from `Read` output (line number + tab) is NOT part of file content; do not include it in `old_string`.
- `old_string` must be **unique** in the file unless `replace_all: true`. If it isn't unique, expand the surrounding context.

**Pitfalls.**

- Pasting `Read` output into `old_string` with the `   42\t` line prefix included → no match.
- Trying to create a new file with `Edit` → use `Write`.
- Editing across multiple lines where indentation differs by a single space → silent no-match.

**Worked example.**

```text
Edit(
  file_path="/Users/me/repo/server.ts",
  old_string="const port = 3000;",
  new_string="const port = Number(process.env.PORT ?? 3000);"
)
```

## Write

**Summary.** Writes (overwrites) a file. Use for new files or complete rewrites.

**Permission rule.** `Write(<path-glob>)`.

**Behaviour.**

- Silently overwrites an existing file. **Read it first** if it exists — the harness enforces this.
- Prefer `Edit` for partial changes — `Write` ships the full file content over the wire.

**Pitfalls.**

- Writing `*.md` / README files unprompted — disallowed unless the user asked.
- Writing secrets (`.env`, credentials) — blocked by repo rules.

## Glob

**Summary.** Filename search by glob pattern. Returns paths sorted by modification time (newest first).

**Permission rule.** `Glob(<path-glob>)` — limits which paths the search may traverse.

**Parameters.**

- `pattern` (required) — e.g. `**/*.ts`, `src/**/test_*.py`.
- `path` — root to search from (default: working directory).
- `respect_gitignore` — default `false`.

**Behaviour.**

- Caps at **100 results**. To get more, narrow the pattern or search a subtree.
- `**` matches across directories; single `*` matches within one segment.
- Brace expansion (`{ts,tsx}`) is supported; put the **longest alternative first** (`'.*\.\(tsx\|ts\)'`) — short-first patterns can silently skip files in some path types.

**Pitfalls.**

- Expecting `.gitignore` to be honoured — it isn't, by default.
- Hitting the 100-result cap on a large repo — narrow with a subtree or a more specific suffix.

**Worked example.**

```text
Glob(pattern="src/**/*.test.ts", respect_gitignore=true)
```

## Grep

**Summary.** Content search across files via ripgrep. Returns matches, files-with-matches, or counts.

**Permission rule.** `Grep(<path-glob>)`.

**Parameters.**

- `pattern` (required) — ripgrep regex.
- `path` — root to search from.
- `glob` — filename filter (e.g. `*.ts`).
- `output_mode` — `"content"` (default), `"files_with_matches"`, `"count"`.
- `-i`, `-n`, `-A`, `-B`, `-C` — passthrough flags.
- `head_limit` — cap on results.

**Behaviour.**

- Regex flavour is **Rust ripgrep** — no lookbehind by default. Use `(?P<name>…)` named groups; `\b` for word boundaries.
- Respects `.gitignore` by default.
- Patterns with `{}` must escape them (`\{`, `\}`) — ripgrep parses unescaped braces as repetition counts.

**Pitfalls.**

- Pasting a PCRE pattern with lookbehind — fails to compile.
- Searching for a literal `{` without escaping.
- Forgetting that the working directory matters — pass `path` explicitly when running from an unexpected cwd.

**Worked example.**

```text
Grep(
  pattern="export\\s+function\\s+\\w+",
  glob="*.ts",
  output_mode="files_with_matches"
)
```

## NotebookEdit

**Summary.** Edits a single cell in a Jupyter notebook.

**Permission rule.** `NotebookEdit(<path-glob>)`.

**Parameters.**

- `notebook_path` (required) — absolute path to `.ipynb`.
- `cell_id` (required for replace/delete) — target cell.
- `new_source` (required for replace/insert) — cell content.
- `cell_type` — `"code"` or `"markdown"`. Defaults to existing type.
- `edit_mode` — `"replace"` (default), `"insert"`, `"delete"`.

**Behaviour.**

- For `insert`, `cell_id` is the cell to insert AFTER (or omit to prepend).
- Output cells are cleared when source changes.

**Pitfalls.**

- Trying to edit notebooks with `Edit` — won't preserve cell structure.
- Forgetting to set `cell_type` when inserting a markdown cell into a code-heavy notebook.
