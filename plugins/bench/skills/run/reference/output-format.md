# Output format

Exact structure for the markdown file written to `runs/<safe-artifact>/<timestamp>.md` after a bench run. Substitute the placeholders verbatim.

## Filename

```
runs/<safe-artifact>/<YYYY-MM-DDTHH-MM-SS>.md
```

- `safe-artifact` = `artifact.replace(':', '-')` (e.g. `bench:run` → `bench-run`)
- Timestamp uses hyphens instead of colons so the path is filesystem-safe on every OS.

## Body

````markdown
# Bench run — <artifact> — <ISO-timestamp>

Total: <N> tests, <total-duration> total

## Summary

| Test | Duration | Status |
|------|----------|--------|
| <test-name-1> | <duration-1> | <ok|error> |
| <test-name-2> | <duration-2> | <ok|error> |

## <test-name-1> (<duration-1>)

**Prompt:**

> <prompt verbatim — preserve line breaks; prefix each line with `> ` if multi-line>

**Output:**

<raw output from bench-runner — verbatim, no truncation>

---

## <test-name-2> (<duration-2>)

**Prompt:**

> <prompt verbatim>

**Output:**

<raw output from bench-runner>
````

## Formatting rules

- `<artifact>` keeps the colon form (`bench:run`) inside the file content — only the filesystem path uses `-`.
- `<ISO-timestamp>` in the H1 may keep colons (it is content, not a path).
- `<duration-N>` is human-readable: `<ms>ms` under 1000ms, otherwise `<s.sss>s`.
- `<total-duration>` is the wall-clock max across parallel runs (longest test), not the sum.
- Separate each test section with a `---` horizontal rule.
- Do not truncate sub-agent output. If a test errored, put the error message verbatim in the Output block and mark status `error` in the summary.
