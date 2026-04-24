STATUS: verified
CONTROL_SEQ: 113
BASED_ON_WORK: work/4/24/2026-04-24-pre-existing-settings-web-gui-gate.md
HANDOFF_SHA: 46e4533 (last committed; this bundle in dirty worktree — uncommitted)
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m26-axes1-2-e2e-isolation.md CONTROL_SEQ 111
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 113 (pending_work_closeout — fake_lane + watcher_core changes)

---

## Pre-existing Settings / Web / GUI / Gate Bundle + test_web_app fix

**Work**: `work/4/24/2026-04-24-pre-existing-settings-web-gui-gate.md`

### Summary

Nine pre-existing dirty files verified plus one targeted test fix:
- `config/settings.py`: `DEFAULT_*` module-level constants extracted
- `app/web.py`: `_effective_service_settings()` + `_has_manual_file_store_override()` + JSON companion isolation
- `scripts/pipeline_runtime_gate.py`: `_control_surface_matches_active_slot()`
- `scripts/promote_assets.py`: `_ensure_promoted()` — lifecycle guard before promoting
- `pipeline_gui/setup_controller.py`: `disk_cached_state_context_exists` fix
- `pipeline_gui/setup_executor.py`: `_active_threads` tracking + `wait_for_idle()`
- `tests/test_pipeline_runtime_gate.py`, `tests/test_pipeline_gui_app.py`: coverage
- `tests/test_web_app.py`: 4 external_fact tests given `sqlite_db_path=str(tmp_path / "test.db")` at lines 8106, 8205, 8254, 8303 — prevents `_effective_service_settings()` JSON-switch hang

### Checks Run

- `python3 -m py_compile [all 9 files]` → **OK**
- `python3 -m unittest tests.test_pipeline_gui_app` → **Ran 52 tests, OK**
- `python3 -m unittest tests.test_pipeline_runtime_gate tests.test_pipeline_gui_app tests.test_web_app` (background, full suite) → **exit 0** ✓
- `sqlite_db_path=str(tmp_path / "test.db")` confirmed present at 4 locations in `tests/test_web_app.py` (lines 8106, 8205, 8254, 8303)
- Work file claims 4 external_fact tests: **Ran 4 tests in 14.543s, OK** (sqlite fix provides ~6x speedup vs 98.9s without fix)
- `git diff --check -- [all 9 files]` → **OK**

### Checks Not Run

- `make e2e-test` — no browser contract change
- `tests.test_web_app` socket tests (10 tests using `LocalOnlyHTTPServer`) — pre-existing socket permission issue in this environment; not in scope of this slice

### Verdict

**PASS.** All 9 pre-existing dirty files + test_web_app regression fix verified. 52+ tests pass. Full background suite (test_pipeline_runtime_gate + test_pipeline_gui_app + test_web_app) exits 0.

---

## Current Shipped Truth

| Item | SHA / Status |
|---|---|
| M22–M26 | b0a14f2 (closed) |
| Runtime-launcher preflight | 06687c4 |
| M27 Axes 1–2 | 422c6ec, d284a77 |
| **Settings/web/GUI/gate + test fix** | **Dirty worktree — PASS, uncommitted** |
| PR #32 | OPEN — operator merge pending |
| Last release gate | M26 Axis 2: 143 passed (6.5m) |

## Risks / Open Questions

1. **Remaining dirty changes (no work file)**:
   - `scripts/pipeline_runtime_fake_lane.py` (+8 net)
   - `tests/test_pipeline_runtime_fake_lane.py` (+1 net)
   - `watcher_core.py` (+13 net)
   - `tests/test_watcher_core.py` (+40 net)
   - Soak report artifacts (untracked, not code)
   Next control (seq 113) handles these.
2. **Socket tests**: 10 `test_web_app` tests using `LocalOnlyHTTPServer` hit `PermissionError` in this environment; not in scope.
3. **PR #32 merge**: operator backlog, unchanged.
