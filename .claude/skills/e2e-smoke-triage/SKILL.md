---
name: e2e-smoke-triage
description: Use when Playwright smoke fails or browser-contract changes may require selector, flow, or documentation updates.
---

# E2E Smoke Triage Skill

Use this skill when browser smoke is failing or likely to drift.

## When To Use
- Playwright smoke failure
- UI selector changes
- approval/timeline/panel behavior changed
- browser file picker or streaming cancel flow changed

## Expected Input
- failing scenario
- touched UI files
- relevant test files

## Expected Output
1. likely breakpoints
2. affected selectors or flows
3. minimal fix order
4. docs/tests that must be updated
5. what should be manually rechecked

## Verification Order
- start with the isolated failing Playwright scenario first
- expand to nearby scenario reruns only if shared selectors, shared browser helpers, or family-level drift is suspected
- use full `make e2e-test` only when the change widened browser-visible behavior, touched shared browser helpers, or the round is making a ready / release claim

## Repo-Specific Coverage
Current smoke suite covers:
- file summary with evidence and summary-range
- browser file picker
- browser folder picker search
- approval reissue
- approval-backed save
- corrected-save first bridge path
- streaming cancel

## Document Update Range
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
