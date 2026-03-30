---
name: release-check
description: Use before demoing, handing off, or wrapping a meaningful repo change to verify tests, docs, agent rules, and known risks are honestly synchronized.
---

# Release Check Skill

Use this skill near the end of meaningful work.

## When To Use
- before handoff
- before demo
- before pushing a significant documentation or behavior change
- before saying a flow is “done”

## Expected Input
- changed files
- commands run
- behavior changes
- known gaps

## Expected Output
1. ready / not ready
2. what was checked
3. what passed
4. what was not checked
5. doc sync status
6. remaining risks

## Repo-Specific Checklist
- If web UI behavior changed, confirm `README.md`, `docs/PRODUCT_SPEC.md`, and `docs/ACCEPTANCE_CRITERIA.md`.
- If approval flow changed, confirm `docs/ARCHITECTURE.md` and approval-related tests.
- If session/search schema changed, confirm storage docs/spec text and regression coverage.
- If E2E scenarios changed, confirm `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, and `docs/MILESTONES.md`.
- If skills or subagents changed, confirm `AGENTS.md`, `CLAUDE.md`, and `PROJECT_CUSTOM_INSTRUCTIONS.md`.
- If Codex operator config changed, confirm `.codex/config.toml` and mirrored agent/skill files.
- If the round is meaningful implementation or operator work, confirm a `/work` closeout note was added or updated honestly.
- If the round is meaningful verification or handoff work, confirm a `/verify` note was added or updated honestly.

## Output Rules
- never imply tests were run if they were not
- distinguish automated checks from manual verification
- mention remaining risks plainly
