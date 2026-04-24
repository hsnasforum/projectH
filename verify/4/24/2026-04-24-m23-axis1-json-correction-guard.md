STATUS: verified
CONTROL_SEQ: 99
BASED_ON_WORK: work/4/24/2026-04-24-m23-axis1-json-correction-guard.md
HANDOFF_SHA: 3a16884
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m22-axis2-global-reject-smoke.md CONTROL_SEQ 98
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 99
PUSH_RESULT: feat/watcher-turn-state 9624433..3a16884 pushed to origin (2026-04-24)

---

## M23 Axis 1 Claim: JSON CorrectionStore State-Order Guard

**Work**: `work/4/24/2026-04-24-m23-axis1-json-correction-guard.md`
**Commit**: 3a16884

### Summary

`storage/correction_store.py` `_transition()` now imports `CORRECTION_STATUS_TRANSITIONS` from `core/contracts.py` and checks whether the current record status permits the target status before writing. Invalid transitions (e.g., RECORDED → ACTIVE, STOPPED → CONFIRMED) return `None` immediately — mirrors the SQLite guard added in M22 Axis 1 (ed77ff2). Guard pattern: `allowed = CORRECTION_STATUS_TRANSITIONS.get(current_status, ()); if status not in allowed: return None`. Four public lifecycle methods unchanged.

`docs/MILESTONES.md`: M23 Axis 1 shipped entry + "Milestone 23 closed" marker added.

### Checks Run

- `python3 -m py_compile storage/correction_store.py` → **OK**
- `python3 -m unittest tests.test_correction_store -v` → **20 tests OK** (18 existing + 2 new guard tests)
  - `test_transition_guard_rejects_out_of_order` — RECORDED → activate: returns None, status stays RECORDED ✓
  - `test_transition_guard_rejects_from_stopped` — STOPPED → confirm: returns None, status stays STOPPED ✓
- `git diff --check -- storage/correction_store.py tests/test_correction_store.py docs/MILESTONES.md` → **OK**

### Checks Not Run

- `storage/sqlite_store.py` — not changed; SQLite guard already in place (M22 Axis 1, ed77ff2)
- Playwright/browser suite — storage-layer only change; no browser-visible contract change; M22 Axis 3 release gate (143 passed) remains current

### Verdict

**PASS.** All 20 tests OK. Whitespace clean. **Milestone 23 closed.**

Both JSON and SQLite `CorrectionStore._transition()` now enforce `CORRECTION_STATUS_TRANSITIONS`.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M22 Axes 1–3 | ed77ff2, acacb28, (143 passed) |
| **M23 Axis 1 JSON guard** | **3a16884** |
| **Milestone 23** | **Closed** |
| PR #32 (M20 Axis 2–M22 Axes 1–3) | OPEN — operator merge pending |

## Risks / Open Questions

1. **`docs/MILESTONES.md` "Next 3 Implementation Priorities" stale**: references `reviewed_memory_boundary_draft`, `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility` — none of which are in the current M13–M23 shipped work. → implement_handoff CONTROL_SEQ 99 for bounded doc-sync cleanup.
2. **Global candidate test isolation**: fingerprint-collision risk managed by fixture uniqueness convention; temp-DB-per-run not implemented.
3. **PR #32 merge**: operator backlog.
