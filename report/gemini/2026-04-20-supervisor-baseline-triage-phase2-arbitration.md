# 2026-04-20 Supervisor Baseline Triage Phase 2 (AXIS-SUPERVISOR-BASELINE-2) Arbitration

## Context
- **Status**: Seq 536 fixed 1 of 3 baseline failures (`test_build_artifacts_uses_canonical_round_notes_only`).
- **Remaining Failures**:
    1. `test_write_status_emits_receipt_and_control_block` (`AssertionError: '' is not true`)
    2. `test_slot_verify_manifest_role_is_accepted_for_receipt` (`AssertionError: 'DEGRADED' != 'STOPPED'`)
- **Root Cause**: Both failures are confirmed to be caused by the seq 527 Vector 1 (RESOLVE-B) contract change. The test fixtures use stale verify notes that lack the required explicit work reference, causing `latest_verify_note_for_work` to return `None` and the supervisor to skip receipt generation.

## Decision: RECOMMEND: implement AXIS-SUPERVISOR-BASELINE-2
Complete the supervisor baseline cleanup by fixing the remaining 2 failures. This ensures that the supervisor module is 100% green and that the Vector 1 (referenced-match only) contract is fully reflected in the test suite.

## Rationale
- **Integrity**: Priority 4 (internal cleanup). A clean baseline is mandatory for future quality gates.
- **Contract Alignment**: These tests are currently failing because they don't follow the new production contract. Fixing them is the final step of the Vector 1 implementation cycle.
- **Simplicity**: Targeted fixture updates with no production code changes required.

## Implementation Pin
- **Target**: `tests/test_pipeline_runtime_supervisor.py`.
- **Fix 1**: Update `test_write_status_emits_receipt_and_control_block` (`:353`) to include `Based on \`work/4/11/work-note.md\`` in the verify note content.
- **Fix 2**: Update `test_slot_verify_manifest_role_is_accepted_for_receipt` (`:1120`) to include `Based on \`work/4/11/work-note.md\``.
- **Goal**: `python3 -m unittest tests.test_pipeline_runtime_supervisor` returns `OK` (94/94 green).

## Alternatives Considered
- **AXIS-OBSERVE-EVALUATE**: Deferred until the baseline is green. Empirical validation is more robust when the underlying test suite is stable.
- **G7-GATE**: Deferred. Wiring a gate while the baseline is red is technically premature.

## Risk Assessment
- Low. Test-only fixture updates.
- No impact on production logic.
