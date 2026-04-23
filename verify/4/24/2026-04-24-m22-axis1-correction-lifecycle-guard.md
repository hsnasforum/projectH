STATUS: verified
CONTROL_SEQ: 95
BASED_ON_WORK: work/4/24/2026-04-24-m22-axis1-correction-lifecycle-guard.md
HANDOFF_SHA: ed77ff2
VERIFIED_BY: Claude
SUPERSEDES: verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md CONTROL_SEQ 94
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 95
PUSH_RESULT: feat/watcher-turn-state a8afe59..ed77ff2 pushed to origin (2026-04-24)

---

## M22 Axis 1 Claim: SQLiteCorrectionStore State-Order Guard

**Work**: `work/4/24/2026-04-24-m22-axis1-correction-lifecycle-guard.md`
**Commit**: ed77ff2

### Summary

`SQLiteCorrectionStore._transition()` now imports `CORRECTION_STATUS_TRANSITIONS` from `core/contracts.py` and checks whether the current row status permits the target status before applying any update. Invalid transitions (e.g., RECORDED → ACTIVE, STOPPED → CONFIRMED) return `None` immediately — consistent with the existing missing-id `None` convention. The four public lifecycle methods (`confirm_correction`, `promote_correction`, `activate_correction`, `stop_correction`) are unchanged.

### Checks Run

- `python3 -m py_compile storage/sqlite_store.py` → **OK**
- `python3 -m unittest tests.test_sqlite_store -v` → **29 tests OK** (26 existing + 3 new guard tests)
  - `test_transition_guard_rejects_out_of_order` — RECORDED → activate: returns None, status stays RECORDED ✓
  - `test_transition_guard_rejects_from_stopped` — STOPPED → confirm: returns None, status stays STOPPED ✓
  - `test_transition_guard_allows_valid_chain` — full RECORDED→CONFIRMED→PROMOTED→ACTIVE→STOPPED ✓
- `git diff --check -- storage/sqlite_store.py tests/test_sqlite_store.py docs/MILESTONES.md` → **OK**

### Checks Not Run

- JSON `CorrectionStore._transition()` — not guarded in this axis (SQLite is default backend; JSON parity is a known open risk, not blocking)
- Playwright/browser suite — storage-layer only change; no browser-visible contract change

### Verdict

**PASS.** All 29 tests OK. Whitespace clean. M22 Axis 1 complete.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M20 Axes 1–3 | 346c4a1, 1b460d1, dbe58af |
| M21 Axes 1–3 | bce09ac, 9538dd5, (142 passed) |
| M22 Axis 1 state-order guard | ed77ff2 |
| PR #32 (M20 Axis 2–M21 bundle) | OPEN — operator merge pending |
| Branch vs origin | pushed (a8afe59..ed77ff2) |

## Risks / Open Questions

1. **JSON CorrectionStore no guard**: `storage/correction_store.py` `_transition()` still allows invalid transitions. Low risk (SQLite is default), but parity gap exists.
2. **Global reject browser coverage absent**: `record_reviewed_candidate_preference(status=REJECTED)` path untested in Playwright — M22 Axis 2 target.
3. **Global candidate test isolation**: temp-DB-per-run not implemented; fingerprint collision prevented by test-level uniqueness convention only.
4. **PR #32 merge**: operator backlog.
