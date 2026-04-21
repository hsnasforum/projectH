# 2026-04-20 Dispatcher Repoint Observability (AXIS-OBSERVE) Arbitration

## Context
- **Status**: Vector 1 (singleton-fallback) and Vector 2 (reverse-walk) are both closed at the schema layer (seq 527 and seq 530).
- **Ambiguity**: The schema-layer fixes are validated by unit tests, but the runtime supervisor has not yet "proven" it behaves correctly in a live loop.
- **Candidates**: AXIS-OBSERVE, AXIS-SUPERVISOR-BASELINE, AXIS-G4, AXIS-G7-GATE, AXIS-G5-DEGRADED.

## Decision: RECOMMEND: implement AXIS-OBSERVE (Runtime Dispatcher Trace)
This axis is the most direct follow-up to the `FIX_DISPATCHER_REPOINT` family. It provides the empirical closure needed to confirm that the logic changes actually eliminated the backwards-walk pattern in the real environment.

## Rationale
- **Family Closure**: Priority 1 (same-family current-risk reduction). Validating the fix in runtime is the final step of closing the risk.
- **Empirical Truth**: Without a trace, we only have unit test truth. A runtime trace allows the next `/verify` round to confirm that the dispatcher is indeed moving forward.
- **Low Risk**: Purely additive observability code.

## Alternatives Considered
- **AXIS-SUPERVISOR-BASELINE**: High value (internal cleanup), but it's better to close the "active" family (dispatcher repoint) with empirical evidence first.
- **AXIS-G7-GATE**: A good next step for quality, but premature until we are certain the underlying dispatcher is stable.
- **AXIS-G5-DEGRADED**: Minor doc-sync/cleanup; can be handled later.

## Implementation Pin
- **Target**: `pipeline_runtime/supervisor.py:_build_artifacts` (`:804-824`).
- **Logic**: Immediately before returning the artifacts dict, call `self._append_event("dispatch_selection", payload)` where payload contains:
  - `latest_work`: `work_rel`
  - `latest_verify`: `verify_rel`
  - `ts`: current UTC timestamp (already handled by `_append_event`).
- **Goal**: Ensure every dispatcher pulse records its selection.
- **Verification**: New test `test_build_artifacts_emits_dispatch_selection_event` in `tests/test_pipeline_runtime_supervisor.py` that mocks `latest_round_markdown` and asserts the event is appended to the event sequence.
