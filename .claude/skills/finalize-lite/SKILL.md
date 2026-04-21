---
name: finalize-lite
description: Use at the end of a meaningful implementation round as a turbo-lite wrapper that combines focused release-check, doc-sync triage, and `/work` closeout readiness without adding commit/PR or `/verify` work.
---

# Finalize Lite

Use this skill as a lightweight turbo-lite end-of-round wrapper for projectH implementation work.

## When To Use
- after meaningful implementation edits
- before saying a round is "done"
- before handing work back for verify/handoff-owner review
- when you need one pass that checks verification honesty, required doc sync, and `/work` closeout readiness together

## Expected Input
- changed files
- commands actually run
- behavior changes
- known gaps and remaining risks

## Expected Output
1. ready / not ready
2. what passed
3. what was not checked
4. required doc sync
5. whether `/work` closeout is required or prepared
6. remaining risks

## Required Workflow
1. Gather only executed facts: changed files, commands, observed pass/fail, and known gaps.
2. Run or confirm the narrowest relevant verification first. Never imply an unrun check passed.
3. Apply `release-check` thinking to decide ready / not ready.
4. If the round touched UI, agent/skill/config surfaces, or other doc-sensitive behavior, apply `doc-sync` thinking to list exactly which docs must be updated in the same round.
5. If this is a meaningful implementation round, apply `work-log-closeout` thinking to prepare or verify a truthful `/work` closeout.
6. Stop at implementation wrap-up. Do not choose the next slice, do not write `/verify`, and do not update `.pipeline` control slots.
7. Do not commit, push, publish a branch, or open a PR from this wrapper.

## Repo-Specific Guardrails
- This wrapper reuses existing repo rules; it does not define a new release process.
- `/work` is the implementation closeout target. `/verify` remains out of scope here.
- Keep implement-lane boundaries: bounded edits plus truthful closeout only.
- If docs or checks are missing, say so plainly instead of widening scope or implying completion.
- Use this before handoff, not instead of `round-handoff`.

## Not In Scope
- commit / push / PR
- next-slice selection
- `/verify` notes
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `.pipeline/operator_request.md` updates
- operator-stop decisions

## Related Skills
- `release-check` for ready / not ready truth
- `doc-sync` for required documentation updates
- `work-log-closeout` for the canonical `/work` note
