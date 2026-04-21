# 2026-04-20 G7 saturation and observability enrichment arbitration

## context
- seq 549 (`G7-DECISION-CLASS-READ-PATH`) 완료.
- `pipeline_runtime/control_writers.py:validate_operator_candidate_status`가 이제 3개 canonical frozenset(`REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS`)을 모두 검증하며, G7-family는 control-writers 경계에서 포화(saturated) 상태입니다.
- seq 542 typo incident(date parsing error)의 교훈을 바탕으로, observability payload를 강화할 필요가 있습니다.

## ambiguity resolution
- **후보**:
  1. `AXIS-EMIT-PAYLOAD-ENRICH` (observability 보강, seq 542 재발 방지)
  2. `AXIS-STALE-REFERENCE-AUDIT` (테스트 코드 cleanup)
  3. `AXIS-DISPATCHER-TRACE-BACKFILL` (trace 신뢰도 보강)
- **결정**: `AXIS-EMIT-PAYLOAD-ENRICH`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, 최근 발생한 seq 542 incident(brittle payload parsing)의 근본 원인을 해결하는 것이 가장 가치 있습니다. `dispatch_selection` 이벤트가 `date_key`를 직접 제공하게 함으로써, handoff가 부정확한 문자열 슬라이싱(`[:10]`)에 의존하지 않도록 truth source를 강화합니다.

## recommendation
- **RECOMMEND: implement AXIS-EMIT-PAYLOAD-ENRICH**
- **대상 파일**: `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `pipeline_runtime/supervisor.py:_build_artifacts`에서 `dispatch_selection` 이벤트의 payload에 `date_key` 필드를 추가합니다.
  - `date_key`는 `work_rel`이 존재할 경우 `Path(work_rel).name[:10]` (예: `2026-04-20`) 형식을 갖도록 합니다.
  - `tests/test_pipeline_runtime_supervisor.py`의 `test_build_artifacts_emits_dispatch_selection_event`를 업데이트하여 새 필드에 대한 assertion을 추가합니다.
