STATUS: verified
CONTROL_SEQ: 109
BASED_ON_WORK: work/4/24/2026-04-24-m27-axis1-correction-adoption.md
HANDOFF_SHA: 422c6ec (M27 Axis 1 committed); 06687c4 (runtime-launcher committed)
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m26-axes1-2-e2e-isolation.md CONTROL_SEQ 108
NEXT_CONTROL: .pipeline/operator_request.md CONTROL_SEQ 109 (M27 Axis 2 scope + pr_merge_gate)
PUSH_RESULT: pending (see commit note below)

---

## M27 Axis 1 Claim: find_adopted_corrections() + audit_traces adoption count

**Work**: `work/4/24/2026-04-24-m27-axis1-correction-adoption.md`
**Commit**: 422c6ec

### Summary

`find_adopted_corrections()` added to both `CorrectionStore` (JSON, `storage/correction_store.py`) and `SQLiteCorrectionStore` (`storage/sqlite_store.py`). Both filter `status == CorrectionStatus.ACTIVE` and sort ascending by `activated_at` (Python-side, since `activated_at` is in the JSON data blob). `scripts/audit_traces.py` calls the method and prints `Adopted corrections (ACTIVE): N`. Two new test classes cover active-only filter and `activated_at` sort order for both stores.

`docs/MILESTONES.md`: M27 definition, guardrails, and Axis 1 shipped entry added.

### Checks Run

- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py tests/test_correction_store.py` → **OK**
- `python3 -m unittest -v tests/test_correction_store.py` → **Ran 25 tests, OK** (new tests confirmed: `test_find_adopted_corrections_returns_only_active_records`, `test_find_adopted_corrections_sorts_by_activated_at` for both JSON CorrectionStoreTest and SQLiteCorrectionStoreAdoptionTest)
- `python3 scripts/audit_traces.py | grep Adopted` → **`Adopted corrections (ACTIVE): 0`** ✓
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py docs/MILESTONES.md tests/test_correction_store.py` → **OK**

### Checks Not Run

- `python3 -m unittest discover -s tests -p 'test_*.py'` — targeted M27 Axis 1 tests sufficient; full suite deferred to next release gate
- `make e2e-test` — no browser contract change; not in scope

### Verdict

**PASS.** M27 Axis 1 verified. 25 correction store tests pass. `find_adopted_corrections()` contract (active-only, activated_at sorted) confirmed in both JSON and SQLite stores. Audit output confirmed.

---

## Runtime-Launcher Completed-Handoff Preflight (Seq 108, re-confirmed)

**Commit**: 06687c4

354 targeted tests passed at seq 108. Committed in this round. No regressions observed.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M22 Axes 1–3 | ed77ff2, acacb28 |
| M23–M24 | 3a16884, 0e9f46e |
| M25 Axes 1–2 | 0a49752 |
| M26 Axes 1–2 E2E isolation + release gate | b0a14f2 |
| **Milestone 26** | **Closed** |
| **Runtime-launcher completed-handoff preflight** | **06687c4** |
| **M27 Axis 1 correction adoption tracking** | **422c6ec** |
| PR #32 (M20 Axis 2 – M26, now includes runtime-launcher + M27 Axis 1) | OPEN — operator merge pending |
| Last release gate | M26 Axis 2: 143 passed (6.5m, 2026-04-24) |

## Risks / Open Questions

1. **M27 Axis 2 direction**: no advisory (4+ timeouts); operator_request seq 109 open.
2. **PR #32 scope growth**: runtime-launcher + M27 Axis 1 commits now on `feat/watcher-turn-state` grow PR #32 beyond original M20–M26 scope. Operator should decide merge or new branch strategy.
3. **Push pending**: commits 06687c4 and 422c6ec are local; push to origin should happen in this round or operator can instruct.
4. **Full discover suite not run**: targeted tests cover all changed modules. Broader suite check deferred to next release gate.
