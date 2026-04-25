STATUS: verified
CONTROL_SEQ: 114
BASED_ON_WORK: work/4/24/2026-04-24-watcher-dispatch-fake-lane-work-ref.md
HANDOFF_SHA: 2bb4748 (last committed; watcher/fake_lane in dirty worktree — uncommitted)
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m26-axes1-2-e2e-isolation.md CONTROL_SEQ 113
NEXT_CONTROL: .pipeline/operator_request.md CONTROL_SEQ 114 (m28_direction + pr_merge_gate)

---

## Watcher Dispatch + Fake Lane Work-Ref Claim

**Work**: `work/4/24/2026-04-24-watcher-dispatch-fake-lane-work-ref.md`

### Summary

`watcher_core._dispatch_claude()` now captures a pane snapshot immediately after paste, then checks whether Enter causes snapshot change toward a busy marker or idle state before marking dispatch successful — reusing `busy_markers_for_lane("Claude")` and `text_matches_markers()` from `pipeline_runtime.lane_surface` rather than adding new heuristics. `scripts/pipeline_runtime_fake_lane._render_verify_note()` now accepts `work_ref` and includes the prompt's `WORK` field in the synthetic verify note.

### Checks Run

- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py scripts/pipeline_runtime_fake_lane.py tests/test_pipeline_runtime_fake_lane.py` → **OK**
- `python3 -m unittest tests.test_watcher_core tests.test_pipeline_runtime_fake_lane` → **Ran 204 tests in 13.003s, OK** (work claimed 11.011s / same count)
- `git diff --check -- [all 4 files]` → **OK**

### Checks Not Run

- `make e2e-test` — no browser contract change; not in scope
- Broader watcher soak — pre-existing soak report artifacts are untracked and not code; not committed

### Verdict

**PASS.** Watcher dispatch + fake lane work-ref bundle verified. 204 tests pass.

---

## Current Shipped Truth (all commits on feat/watcher-turn-state)

| Commits | Content |
|---|---|
| b0a14f2 | M26 Axes 1–2 (closed) |
| 06687c4 | Runtime-launcher completed-handoff preflight |
| 422c6ec | M27 Axis 1 — find_adopted_corrections() |
| d284a77 | M27 Axis 2 — adoption count web UI |
| 3711156 | Settings DEFAULT_* / web isolation / runtime gate / setup GUI / test fix |
| **Watcher dispatch + fake lane work-ref** | **Dirty worktree — PASS, uncommitted** |
| PR #32 | OPEN — operator merge pending |
| Last release gate | M26 Axis 2: 143 passed (6.5m) |

## Risks / Open Questions

1. **PR #32 scope**: branch now includes M20–M27 + runtime-launcher + settings/web/gui/gate + watcher dispatch. Operator should decide merge or branch strategy before M28 work accumulates further.
2. **M28 direction**: M27 complete; advisory unavailable (4+ timeouts); no local slice identifiable without direction. operator_request seq 114 open.
3. **Soak report artifacts**: untracked `report/pipeline_runtime/verification/2026-04-24-*.json/md` — not code, not committed.
