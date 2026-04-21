# 2026-04-20 Autonomy payload stability lock arbitration

## context
- seq 567 (`AXIS-EMIT-KEY-STABILITY-LOCK`) 완료. `dispatch_selection` 이벤트 페이로드의 6-key 형계가 테스트 레이어에서 고정됨.
- G7-autonomy-producer 축 역시 4개reachable 모드에 대한 기본값 부여가 완료되어 포화 상태임.
- 이제 `classify_operator_candidate`가 반환하는 16-key 형계와 `decision_class`의 "canonical OR empty" 불변성(invariant)을 테스트 레이어에서 명시적으로 잠글 시점임.

## ambiguity resolution
- **후보**:
  1. `AXIS-AUTONOMY-KEY-STABILITY-LOCK` (분류기 반환 키셋 및 불변성 고정)
  2. `AXIS-DISPATCHER-TRACE-BACKFILL` (실제 trace 확인 예약)
  3. `AXIS-G5-DEGRADED-BASELINE` (문서 동기화)
- **결정**: `AXIS-AUTONOMY-KEY-STABILITY-LOCK`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, 오늘 대규모로 변경된 두 주요 인터페이스(emit payload, autonomy producer)의 안정성을 대칭적으로 보호합니다. `classify_operator_candidate`가 항상 16개의 특정 키를 반환하고, `decision_class`가 항상 유효한 어휘이거나 빈 문자열임을 보장하는 tripwire를 추가하여 향후의 의도치 않은 회귀를 방지합니다.

## recommendation
- **RECOMMEND: implement AXIS-AUTONOMY-KEY-STABILITY-LOCK**
- **대상 파일**: `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `tests/test_pipeline_runtime_supervisor.py`에 `test_classify_operator_candidate_payload_stability` 메서드를 추가합니다. (위치: `test_classify_operator_candidate_defaults_decision_class_per_visible_mode` 직후)
  - 이 테스트는 다음 두 가지 불변성을 검증합니다:
    1. **Cardinality & Order**: 반환된 dict의 키가 정확히 16개이며, `mode`, `suppressed_mode`, ..., `fingerprint` 순서로 정렬되어 있는지 확인.
    2. **Decision Class Invariant**: `normal` 모드(non-candidate)를 포함한 시나리오에서 `decision_class`가 항상 `SUPPORTED_DECISION_CLASSES` 멤버이거나 `""`임을 확인.
  - 기존 100개 테스트의 green baseline을 유지하며 총 101개 테스트를 목표로 합니다.
