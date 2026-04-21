# 2026-04-20 Supervisor Baseline Triage (AXIS-SUPERVISOR-BASELINE) Arbitration

## Context
- **Status**: AXIS-OBSERVE (dispatch selection trace) is implemented, but empirical results are pending a full dispatcher round.
- **Problem**: Three pre-existing baseline failures in `tests.test_pipeline_runtime_supervisor` persist. Specifically, `test_build_artifacts_uses_canonical_round_notes_only` fails because the verify note does not explicitly reference the work note, causing the new `latest_verify_note_for_work` logic (from seq 527) to return `None`.
- **Goal**: Clean the baseline to ensure that recurring failures do not mask new regressions.

## Decision: RECOMMEND: implement AXIS-SUPERVISOR-BASELINE (Triage Red Tests)
Triage and fix the 3 pre-existing supervisor test failures. This axis is the most logical next step to maintain high technical integrity and clear the path for more advanced axes like G7-GATE.

## Rationale
- **Integrity**: Priority 4 (internal cleanup). A clean baseline is a prerequisite for reliable automated verification.
- **Root Cause Identified**: At least one failure (`test_build_artifacts_uses_canonical_round_notes_only`) is a direct consequence of the Vector 1 (RESOLVE-B) contract change. The test fixture simply needs to be updated to include an explicit work reference.
- **Coherent Slice**: Triage all 3 failures in one slice to achieve a green supervisor module.

## Implementation Pin
- **Target**: `tests/test_pipeline_runtime_supervisor.py`.
- **Fix 1**: Update `test_build_artifacts_uses_canonical_round_notes_only` fixture to add `Based on \`work/4/16/2026-04-16-real-round.md\`` to the verify note content.
- **Fix 2**: Investigate and fix `test_slot_verify_manifest_role_is_accepted_for_receipt` (`DEGRADED != STOPPED`).
- **Fix 3**: Investigate and fix `test_write_status_emits_receipt_and_control_block` (`last_receipt_id` empty).
- **Goal**: `python3 -m unittest tests.test_pipeline_runtime_supervisor` returns `OK` (94/94 green).

## Alternatives Considered
- **G7-GATE**: Declined. It is risky to wire a gate that ignores or blocks on known baseline failures. Clear the failures first.
- **G4/G11/G8**: Deferred. Baseline health takes precedence over new feature/audit adoption.

## Risk Assessment
- Low. These are test-only fixes or minor alignment fixes in the supervisor.
- No impact on production dispatcher logic.
