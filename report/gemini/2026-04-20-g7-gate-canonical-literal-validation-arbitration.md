# 2026-04-20 Pipeline Gate Canonical Literals (G7-GATE) Arbitration

## Context
- **Status**: The `FIX_DISPATCHER_REPOINT` family (Vector 1+2) is closed and verified. The supervisor baseline is 100% green (95/95).
- **Remaining Risk**: Protocol drift. Without a hard gate, non-canonical literals (REASON_CODE, etc.) can enter the control slots, complicating triage and breaking automated monitoring.
- **Goal**: Wire strict canonical validation into `scripts/pipeline_runtime_gate.py` via `validate_operator_candidate_status`.

## Decision: RECOMMEND: implement G7-GATE (Canonical Literal Validation)
This axis is the most impactful quality improvement available. Now that the baseline is clean, we can enforce strict adherence to the 3-agent protocol literals without triggering false positives from historical drift.

## Rationale
- **Protocol Integrity**: Priority 2 (user-visible improvement via stability). Hardening the gate ensures that every `operator_request` uses supported literals, reducing ambiguity for agents and operators.
- **Timing**: Ideal. Following the dispatcher stability and baseline cleanup, the environment is ready for a Hard Gate.
- **Foundation**: Re-uses the existing `SUPPORTED_*` sets in `pipeline_runtime/operator_autonomy.py`.

## Execution Strategy
1. **Target**: `pipeline_runtime/control_writers.py:validate_operator_candidate_status`.
2. **Logic**:
    - Extract `reason_code`, `operator_policy`, and `decision_class` from the `autonomy` block of the `status` dictionary.
    - Use `normalize_*` functions from `pipeline_runtime.operator_autonomy` on these fields.
    - Raise `ValueError` if the normalized values are not in `SUPPORTED_REASON_CODES`, `SUPPORTED_OPERATOR_POLICIES`, or `SUPPORTED_DECISION_CLASSES`.
3. **Verification**:
    - Add `test_validate_operator_candidate_status_fails_on_unsupported_literal` to `tests/test_operator_request_schema.py`.
    - Simulated status with `reason_code: "unknown_reason"` must raise `ValueError`.
    - Run `python3 -m unittest tests.test_operator_request_schema` (expect 7 green).
    - Run `scripts/pipeline_runtime_gate.py check-operator-classification` to confirm it passes on the current canonical state.

## Alternatives Considered
- **AXIS-STALE-REFERENCE-AUDIT**: Internal cleanup; less immediate impact than protocol enforcement.
- **G5-DEGRADED-BASELINE**: Minor doc-sync; can be bundled later.
- **G11/G8/G3**: Deferred. Protocol stability (G7) is the priority.

## Risk Assessment
- Low. Only triggers on invalid operator candidates.
- `advisory_only` remains IN the canonical set as per current code.
