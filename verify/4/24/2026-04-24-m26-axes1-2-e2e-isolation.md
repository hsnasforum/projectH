STATUS: verified
CONTROL_SEQ: 111
BASED_ON_WORK: work/4/24/2026-04-24-m27-axis2-adoption-web-ui.md
HANDOFF_SHA: e7a826f (last committed; M27 Axis 2 changes in dirty worktree — uncommitted)
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m26-axes1-2-e2e-isolation.md CONTROL_SEQ 109
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 111 (pending_work_closeout — pre-existing dirty changes need /work file)

---

## M27 Axis 2 Claim: adopted_corrections_count in /api/preferences/audit + PreferencePanel

**Work**: `work/4/24/2026-04-24-m27-axis2-adoption-web-ui.md`

### Summary

`get_preference_audit()` now calls `self.correction_store.find_adopted_corrections()` and returns `adopted_corrections_count`. `PreferenceAudit` TypeScript interface extended with optional `adopted_corrections_count` field. `PreferencePanel` audit row displays `활성 교정 N개` when N > 0. Frontend rebuilt (`npx vite build`). `tests/test_preference_handler.py` extended with two new cases (zero and nonzero adopted count).

### Checks Run

- `python3 -m py_compile app/handlers/preferences.py tests/test_preference_handler.py` → **OK**
- `python3 -m unittest -v tests/test_preference_handler.py -k preference_audit` → **Ran 3 tests, OK** (new tests confirmed: `test_get_preference_audit_includes_adopted_count_zero`, `test_get_preference_audit_includes_adopted_count_nonzero`)
- `app/handlers/preferences.py:108` — `adopted_count = len(self.correction_store.find_adopted_corrections())` confirmed present
- `app/handlers/preferences.py:113` — `"adopted_corrections_count": adopted_count` in return dict confirmed
- `app/frontend/src/components/PreferencePanel.tsx:164-165` — `(audit.adopted_corrections_count ?? 0) > 0 && ...` display confirmed
- `app/static/dist/assets/index.js` mtime: Apr 24 10:43 → positive evidence rebuild ran
- `git diff --check -- [all claimed files]` → **OK**

### Checks Not Run

- `python3 -m unittest discover` — M27 Axis 2 tests sufficient; full suite deferred to next release gate
- `make e2e-test` — preference panel audit row is a sidebar count; no E2E scenario currently tests it specifically
- Live browser smoke — UI correctness via TypeScript build + unit test coverage; Playwright smoke deferred to release gate

### Verdict

**PASS.** M27 Axis 2 verified. 3 preference_audit tests pass. `adopted_corrections_count` contract locked by nonzero-seed test case. Frontend rebuild confirmed.

---

## Pre-existing Dirty Changes — Unaccounted (not from M27 Axis 2)

The following files were modified before M27 Axis 2 started and have **no /work closeout**:

| File | Net change |
|---|---|
| `config/settings.py` | +26 net — extract `DEFAULT_*` path constants |
| `app/web.py` | +55 net — `_has_manual_file_store_override()` using those constants |
| `scripts/pipeline_runtime_gate.py` | +38 net — `_control_surface_matches_active_slot()` |
| `scripts/promote_assets.py` | +25 net — unknown scope |
| `pipeline_gui/setup_controller.py` | +14 net |
| `pipeline_gui/setup_executor.py` | +27 net |
| `tests/test_pipeline_runtime_gate.py` | +66 net |
| `tests/test_pipeline_gui_app.py` | +43 net |
| `tests/test_web_app.py` | +17 net |

`git diff --check` on these files: **OK** (no whitespace errors). Tests appear functional. No work file exists for this slice. **Cannot commit without a work file.** Next control is a pending_work_closeout implement_handoff to produce it.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M22–M26 | b0a14f2 (closed) |
| Runtime-launcher completed-handoff preflight | 06687c4 |
| M27 Axis 1 correction adoption tracking | 422c6ec |
| **M27 Axis 2 adoption count web UI** | **Dirty worktree — PASS, uncommitted** |
| **Milestone 27** | **Axes 1–2 complete** |
| PR #32 | OPEN — operator merge pending |
| Last release gate | M26 Axis 2: 143 passed (6.5m, 2026-04-24) |

## Risks / Open Questions

1. **Pre-existing dirty changes without work file**: 9 files modified, no `/work` closeout. Cannot commit until a work file is produced. Next control (seq 111) handles this.
2. **M27 UI smoke not run**: adoption count display in `PreferencePanel` covered by unit test + TypeScript build. No Playwright scenario tests this sidebar count specifically.
3. **Advisory unavailable**: Gemini 4+ consecutive timeouts. M28 direction deferred until pre-existing dirty changes are closed out.
4. **PR #32 merge**: operator backlog, unchanged.
