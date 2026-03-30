---
name: work-log-closeout
description: Create or update a projectH `/work` closeout note after a meaningful round. Trigger when implementation, operator-rule, or verification work is done and you need a Korean handoff note with changed files, used skills, executed checks, residual risks, and next-step context.
---

# Work Log Closeout

Use this skill to write a repository-consistent `work/<month>/<day>/YYYY-MM-DD-<slug>.md` note after a round of changes.

## Inputs

- Actual changed files
- Actual commands that were run
- Real pass/fail or blocked outcomes
- Remaining risks, gaps, and next steps
- Skill names that were actually used in the round, if any

## Required workflow

1. Gather only executed facts.
   - today's folder path: `work/<month>/<day>/`
   - create the folder first if it does not exist
   - read the newest note in today's folder before writing
   - if there is no note for today, read the newest note from the previous day
   - changed files
   - commands actually run
   - outcomes actually observed
2. Keep the note in Korean unless an external convention requires English.
3. Use a short slug tied to the work theme.
4. If operator rules, helper-agent roles, Codex config, or `/work` policy changed, mention related docs updated or still pending.
5. Never claim an unrun test or verification step was completed.
6. Always keep a short `사용 skill` section. If skills were used, list each name and why it mattered; otherwise write `- 없음`.
7. Normalize new notes to the standard title and section order even if nearby notes drifted.

## Recommended structure

- 제목: `# YYYY-MM-DD <작업명>`
- `## 변경 파일`
- `## 사용 skill`
- `## 변경 이유`
- `## 핵심 변경`
- `## 검증`
- `## 남은 리스크`

Use these section names exactly unless the user explicitly asks for a different format.

## Writing rules

- Prefer concrete facts over long narrative
- Keep `핵심 변경` to about 3 to 6 flat bullets
- Include exact commands in `검증`
- Include only skills that were actually used, not merely available in the session
- Keep the `## 사용 skill` section even when no skill was used, and write `- 없음`
- Keep the title date prefix and do not omit `YYYY-MM-DD`
- If something is blocked, mark it clearly and say why
- If `.codex/config.toml` changed locally but is gitignored, note that explicitly when relevant

## Output format

- completed note content only when the user asks for the file body
- otherwise: filename suggestion under `work/<month>/<day>/`, summary bullets, and missing facts still needed
