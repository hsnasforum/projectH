---
name: next-slice-triage
description: Use after current verification truth is already reconciled to choose one exact next slice or the correct Gemini/operator escalation without rerunning `/verify` or widening into whole-project audit.
---

# Next Slice Triage

Use this skill as a narrow turbo-lite wrapper when the remaining task is exact next-slice selection.

## When To Use
- after the latest `/work` and `/verify` already reflect current truth
- when verification reruns are done and the only open question is the next exact slice
- when you need to decide between `implement`, `gemini_request`, and `needs_operator`
- when you need one implementation-truthful tie-break instead of a broad audit

## Expected Input
- newest relevant `/work`
- newest relevant `/verify`
- current docs or implementation files that define the candidate area
- current risks, user-visible gaps, and known ambiguity

## Expected Output
1. one exact next slice, or
2. `gemini_request` recommendation, or
3. `needs_operator` recommendation
4. short reason tied to repo slice-selection guardrails

## Required Workflow
1. Read the newest relevant `/work` note first, then the newest relevant `/verify` note.
2. Confirm current truth is already reconciled. If verification still needs rerun or `/verify` is stale, stop and use `round-handoff` instead.
3. Evaluate candidates in this order:
   - same-family current-risk reduction
   - same-family user-visible improvement
   - new quality axis
   - internal cleanup
4. Reject candidates that only close internal completeness, route-by-route drift, or helper-level neatness without protecting a shipped contract or user-visible value.
5. Prefer one smallest coherent slice. Do not split into a micro-slice when one slightly larger bounded slice closes the same unit more truthfully.
6. If the same day already contains 3 or more same-family docs-only truth-sync rounds, do not choose another narrower docs-only micro-slice. Pick one bounded docs-only bundle or escalate.
7. If the only blocker is next-slice ambiguity, overlapping candidates, or a low-confidence tie-break, recommend `gemini_request` before `needs_operator`.
8. Recommend `needs_operator` only for a real operator-only decision, approval/truth-sync blocker, immediate safety stop, or a still-unresolved tie after Gemini.
9. Stop at slice selection. Do not rerun verification, do not write `/verify`, and do not implement the slice from this wrapper.

## Repo-Specific Guardrails
- This wrapper reuses existing AGENTS slice-selection rules; it does not invent a new prioritization policy.
- Use this after `round-handoff` truth work, not instead of it.
- Keep current shipped contract, next phase, and long-term north star separate while choosing the slice.
- Do not push slice selection back onto the implement owner.
- Keep outputs narrow, reversible, and implementation-truthful.

## Not In Scope
- verification reruns
- `/verify` note creation or update
- commit / push / PR
- whole-project audit
- `.pipeline` control-slot writes
- implementation edits

## Related Skills
- `round-handoff` for verification-backed truth reconciliation
- `finalize-lite` for implementation-side wrap-up
