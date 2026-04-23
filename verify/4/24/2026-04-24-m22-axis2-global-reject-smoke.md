STATUS: verified
CONTROL_SEQ: 96
BASED_ON_WORK:
  - work/4/24/2026-04-24-m22-axis1-correction-lifecycle-guard.md
  - work/4/24/2026-04-24-m22-axis2-global-reject-smoke.md
HANDOFF_SHA: acacb28
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m22-axis1-correction-lifecycle-guard.md CONTROL_SEQ 95
NEXT_CONTROL: .pipeline/operator_request.md CONTROL_SEQ 96
PUSH_RESULT: pending — operator_request CONTROL_SEQ 96 written for push+PR

---

## M22 Axis 2 Claim: Global Reject Permanence Smoke

**Work**: `work/4/24/2026-04-24-m22-axis2-global-reject-smoke.md`
**Commit**: acacb28

### Summary

New Playwright scenario `"global reject permanently silences candidate in subsequent sessions"` added to `e2e/tests/web-smoke.spec.mjs`. Flow: 2 sessions create cross-session recurrence → 3rd session verifies global candidate appears → API POST `/api/candidate-review` with `review_action: "reject"` and `message_id: "global"` → 4th session verifies the rejected `candidate_id` is absent from `review_queue_items`. Soft-skip guard preserved for cases where global candidate hasn't materialized.

`docs/MILESTONES.md` updated with M22 Axis 2 shipped entry.

### Checks Run

- `git diff --check -- e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md` → **OK**
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "global reject permanently" --reporter=line` → **1 passed (11.9s)** ← isolated rerun (verify lane)

### Checks Not Run

- Full suite at this stage — deferred to M22 Axis 3 release gate (run in same verify round below)

### Verdict

PASS.

---

## M22 Axis 3 Claim: Release Gate

**Commit**: acacb28 (same, M22 Axis 3 doc entry included)

### Checks Run

- `make e2e-test` (full suite) → **143 passed (10.1m)** ← M22 Axis 3 release gate PASS
  - New scenario test #141 (`global reject permanently silences candidate in subsequent sessions`) confirmed passing
  - Total count: 142 → 143 (one new scenario added in Axis 2)
  - No regressions in existing 142 scenarios

### Verdict

PASS. **Milestone 22 closed** (Axes 1–3): SQLite correction lifecycle state-order guard, global reject permanence browser coverage, and release gate complete.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M22 Axis 1 state-order guard | ed77ff2 |
| M22 Axis 2 global reject permanence smoke | acacb28 |
| M22 Axis 3 release gate (143 passed, 10.1m) | acacb28 |
| **Milestone 22** | **All 3 axes complete** |
| PR #32 (M20 Axis 2–M21 bundle) | OPEN — operator merge pending |
| Branch vs origin | ahead (M22 commits unpushed) |

## Risks / Open Questions

1. **JSON CorrectionStore guard absent**: `storage/correction_store.py` `_transition()` still allows invalid transitions. Low risk (SQLite is default), but parity gap remains.
2. **PR #32 merge**: operator backlog (M20 Axis 2–M21 bundle).
3. **M22 commits unpushed**: local only — operator_request CONTROL_SEQ 96 for push+PR.
