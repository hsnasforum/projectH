---
name: doc-sync
description: Use when implementation, tests, skills, or agent rules changed and repo documentation must be synchronized to current behavior without widening scope.
---

# Doc Sync Skill

Use this skill when the main task is aligning docs with implementation.

## When To Use
- UI behavior changed
- approval payload or session schema changed
- new test coverage changed the supported contract
- skills/subagents/agent rules changed
- `.codex/config.toml` or helper-agent registry changed
- README and product docs drifted apart

## Expected Input
- changed behavior summary
- touched files
- current implementation facts

## Expected Output
1. files that must be updated
2. short role for each doc
3. mismatches removed
4. remaining TODO / OPEN QUESTION items

## Required Sync Targets
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml`
- `work/README.md` when operator closeout policy changed
- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## Output Rules
- prefer implementation truth over older docs
- if implementation is ambiguous, mark it as `TODO` or `OPEN QUESTION`
- do not invent future behavior as if already shipped
