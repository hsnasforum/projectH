---
paths:
  - "README.md"
  - "docs/**/*.md"
  - "AGENTS.md"
  - "CLAUDE.md"
  - "GEMINI.md"
  - "PROJECT_CUSTOM_INSTRUCTIONS.md"
  - ".codex/config.toml"
  - ".agents/skills/**/*.md"
  - ".claude/skills/**/*.md"
  - ".codex/agents/**/*.toml"
  - ".claude/agents/**/*.md"
---

# Doc Sync Rules

- Docs follow implementation truth, not wishful future behavior.
- If behavior is ambiguous, mark it as `TODO` or `OPEN QUESTION` instead of overstating certainty.
- When agent / skill / operator config changes, sync `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `PROJECT_CUSTOM_INSTRUCTIONS.md` in the same task.
- Keep `CLAUDE.md` lean and execution-focused. Put heavy file-family guidance in `.claude/rules/` so Claude does not pay startup context for rules that only matter on a subset of files.
- If mirrored agent or skill files change, keep the Codex and Claude copies aligned.
- If roadmap or staged product framing changes, sync `plandoc/` and the near-term product docs that describe current scope.
