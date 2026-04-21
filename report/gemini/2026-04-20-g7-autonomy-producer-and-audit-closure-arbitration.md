# 2026-04-20 G7 autonomy-producer and audit-closure arbitration

## context
- seq 559 (`GEMINI_REPROPOSE`) 요청.
- seq 557에서 권고한 `AXIS-STALE-REFERENCE-AUDIT`에 대한 상세 분류(Category A/B/C) 결과, Category-A(수정 필요) 대상이 0건으로 확인됨. 3건은 의도적인 bare fixture(Category-B), 13건은 로직과 무관한 no-op(Category-C)임.
- 따라서 `AXIS-STALE-REFERENCE-AUDIT`은 "수정 없음(audit-closed)"으로 종결하는 것이 진실한(truthful) 결과임.
- G7-gate family는 제어기(control-writers) 경계에서 포화(saturated)되었으나, `decision_class`가 `autonomy` 블록에서 여전히 빈 값으로 전달되는 경우가 많아 "방어 전용(defensive-only)" 상태에 머물러 있음.

## ambiguity resolution
- **후보**:
  1. `AXIS-G7-AUTONOMY-PRODUCER` (G7-family 완결, end-to-end load-bearing)
  2. `AXIS-DISPATCHER-TRACE-BACKFILL` (관측 가능성 보강)
  3. `AXIS-G5-DEGRADED-BASELINE` (문서 동기화)
- **결정**: `AXIS-G7-AUTONOMY-PRODUCER`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, G7 어휘집(vocabulary)의 일관성을 확보하는 작업을 마무리합니다. `autonomy` 블록을 생성하는 producer(분류기) 단에서 `decision_class`에 canonical default를 부여함으로써, 런타임 상태 파일(`status.json`)이 항상 유효한 어휘를 carry하도록 보장합니다. 이는 `STALE-REFERENCE-AUDIT`의 실패를 뒤로하고 다시 견고한 아키텍처적 진전을 만드는 가장 적절한 선택입니다.

## recommendation
- **RECOMMEND: implement AXIS-G7-AUTONOMY-PRODUCER**
- **대상 파일**: `pipeline_runtime/operator_autonomy.py`, `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `pipeline_runtime/operator_autonomy.py:classify_operator_candidate`에서 `decision_class`가 비어 있을 경우, `visible_mode` 또는 `mode`에 따라 적절한 canonical default를 부여합니다.
    - 예: `hibernate` -> `internal_only` 또는 `advisory_only`
    - 예: `triage` -> `next_slice_selection`
    - 예: `needs_operator` -> `operator_only`
  - `tests/test_pipeline_runtime_supervisor.py`에서 supervisor가 생성하는 `status["autonomy"]` 블록의 `decision_class`가 항상 `SUPPORTED_DECISION_CLASSES` 세트 내에 있는지 검증하는 어서션을 보강합니다.
  - `AXIS-STALE-REFERENCE-AUDIT`은 0-target 확인에 따라 "audit-closed"로 종결하며 추가 수정을 진행하지 않습니다.
