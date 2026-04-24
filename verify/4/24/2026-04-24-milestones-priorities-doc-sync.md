STATUS: verified
CONTROL_SEQ: 101
BASED_ON_WORK: work/4/24/2026-04-24-milestones-priorities-doc-sync.md
HANDOFF_SHA: c5c9b07
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m23-axis1-json-correction-guard.md CONTROL_SEQ 99
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 101
ADVISORY_RECOVERY: advisory_request seq 100 timed out (901s); council convergence → Option C (list_incomplete_corrections)
PUSH_RESULT: feat/watcher-turn-state daebfab..c5c9b07 pushed to origin (2026-04-24)

---

## Docs-Only Round: MILESTONES.md Stale Priorities Cleanup

**Work**: `work/4/24/2026-04-24-milestones-priorities-doc-sync.md`
**Commit**: c5c9b07

### Summary

Removed 3 stale `## Next 3 Implementation Priorities` bullets that referenced `reviewed_memory_boundary_draft`, `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility` — none present in the M13–M23 shipped codebase. Replaced with 3 accurate current items: (1) global candidate E2E test isolation, (2) PR #32 merge pending, (3) next milestone via advisory.

No code, test, or runtime files changed.

### Checks Run

- `git diff --check -- docs/MILESTONES.md` → **OK**
- Diff confirms: exactly 3 stale bullets removed, 3 accurate bullets added. No other section touched.

### Checks Not Run

- Unit tests / Playwright — docs-only change; no code modified; prior release gate (M22 Axis 3, 143 passed) remains current

### Verdict

**PASS.** `docs/MILESTONES.md` now accurately reflects current shipped state and known open risks.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M20–M21 bundle | 1b460d1–9538dd5 |
| M22 Axes 1–3 | ed77ff2, acacb28, (143 passed) |
| M23 Axis 1 JSON guard | 3a16884 |
| MILESTONES.md priorities refresh | c5c9b07 |
| PR #32 (M20 Axis 2–M22) | OPEN — operator merge pending |
| Release gate | M22 Axis 3: 143 passed (10.1m, 2026-04-24) |

## Risks / Open Questions

1. **Global candidate test isolation**: still open; temp-DB-per-run not implemented.
2. **PR #32 merge**: operator backlog.
3. **M24 direction**: advisory_request CONTROL_SEQ 100 open.
