---
name: round-handoff
description: Use when a Codex round is finished and you need to reread the latest `/work` closeout, rerun honest verification, reconcile docs/code truth, leave a `/verify` note, and prepare the next-round operator prompt or handoff summary without overstating progress.
---

# Round Handoff Skill

Use this skill when a round has effectively ended and the next task is a verification-backed handoff.

## When To Use
- the user says a Codex round is finished and asks for verification plus next instructions
- you need to re-check the latest `/work` note against current code and docs
- you need to leave or update a `/verify` note with the rerun results
- you need to write a ready / not-ready summary before suggesting the next slice
- you need to draft an operator-ready fenced `md` prompt for the next Codex round

## Expected Input
- the newest `/work` closeout path or today's `work/<month>/<day>/` folder
- the newest `verify/<month>/<day>/` note if one already exists
- the round theme or changed area
- the verification commands that should be rerun
- the current docs or code files that define the next slice

## Expected Output
1. ready / not ready
2. checks rerun and outcomes
3. what was checked
4. what was not checked
5. current shipped truth
6. remaining risks
7. one smallest next slice
8. next-round prompt if requested

## Required Workflow
1. Read today's newest `work/<month>/<day>/` note first, or the newest prior-day note if today has none.
2. If today's `verify/<month>/<day>/` folder already has a note, read the newest one after the `/work` note so you do not silently overwrite a later verification truth.
3. Re-check the latest `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, and the most relevant `plandoc/` or implementation files instead of trusting the closeout alone.
4. Re-run only the verification that is actually needed for the round. If meaningful implementation changed, prefer:
   - `python3 -m py_compile ...`
   - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
   - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<scenario>" --reporter=line` for Playwright-only smoke tightening, selector drift, or single-scenario fixture updates
   - `make e2e-test` only when the browser-visible contract widened, shared browser helpers changed, a current browser family looks broadly broken, or the round is making a ready / release claim
   - `git diff --check`
5. Distinguish automated verification from manual checks not run.
6. Leave or update a verification note under `verify/<month>/<day>/YYYY-MM-DD-<slug>.md` when the handoff itself is meaningful.
7. Summarize current shipped truth, what is still absent or unresolved, and whether the work is still foundation-only or user-visible.
8. Recommend one next slice only. Do not bundle adjacent helpers, later UI openings, or later status widening into the same prompt.
9. Before choosing the next slice, scan today's recent `/work` and `/verify` history for repeated docs-only truth-sync loops. If the same day already has 3 or more same-family docs-only rounds in a row, do not recommend yet another smaller docs-only micro-slice. Instead recommend one bounded docs-only bundle that can close the remaining family drift in one round, or escalate through Gemini/operator if no truthful bundle is obvious.
10. When drafting the next prompt, include:
   - dirty-worktree warning when relevant
   - must-read files
   - exact scope limits
   - required verification
   - `/work` closeout requirement
   - Korean-honorific response requirement when the operator requested it

## Repo-Specific Guardrails
- Keep current shipped contract separate from next phase and long-term north star.
- Do not reinterpret support traces or draft contracts as implemented learning or durable memory.
- Keep blocked or disabled UI states blocked until the latest closeout, docs, and code all justify widening them.
- For current memory-foundation work, preserve absence or unresolved semantics unless the implementation really opened that layer.

## Output Rules
- never claim a test or manual check ran if it did not
- do not write the next prompt until docs, code, and latest closeout are reconciled or the mismatch is called out explicitly
- keep the next prompt narrow, reversible, and implementation-truthful
