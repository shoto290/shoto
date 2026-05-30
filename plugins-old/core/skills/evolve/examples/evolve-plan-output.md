## Plan: code-review workflow after every commit

### Reuse (no action needed)
- **Skill: `explore:explore`** — already handles "what changed in this commit" via Glob + Grep

### Update
- **Subagent: `code-reviewer`** (existing) — extend description to mention "post-commit usage" so it auto-triggers from the hook

### Create (in dependency order)
1. **Skill: `review-commit`** — wraps `git show HEAD` + spawns the `code-reviewer` agent on the diff. Why a skill: needs the `!git show HEAD` substitution and a stable `/review-commit` entry point.
2. **Hook: `PostToolUse` on `Bash` matching `git commit*`** — runs `/review-commit` automatically. Why a hook: enforces "every commit" without requiring the user to remember.

### Restart required
- New skill `review-commit`: no restart (`.claude/skills/` is hot-loaded)
- New hook in `settings.json`: restart required so Claude Code re-reads the file

### Test plan
- Manual: `/review-commit` → expect a structured review of HEAD
- End-to-end: make a small commit → expect the hook to fire `/review-commit` automatically
- Reuse check: `/explore:explore` still works unchanged
