# 2026-04-20 G7 gate decision-class read-path arbitration

## context
- seq 547 (`G7-REASON_CODE-OPERATOR_POLICY-READ-PATH`) 완료.
- `pipeline_runtime/control_writers.py:validate_operator_candidate_status`에 `REASON_CODE` 및 `OPERATOR_POLICY` 리터럴 검증이 추가되었으나, `DECISION_CLASS`는 `autonomy` dict가 carry하지 않는다는 가정 하에 누락됨.
- 하지만 `pipeline_runtime/supervisor.py` 및 `status.json` 확인 결과, `autonomy` 블록은 이미 `decision_class`를 carry하고 있음.

## ambiguity resolution
- **후보**:
  1. `G7-DECISION_CLASS-READ-PATH-EXTEND` (G7 gate 완결)
  2. `AXIS-EMIT-PAYLOAD-ENRICH` (observability 보강)
  3. `AXIS-STALE-REFERENCE-AUDIT` (cleanup)
- **결정**: `G7-DECISION_CLASS-READ-PATH-EXTEND`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, 시작한 G7 gate 리터럴 검증 suite를 완결하여 read-path integrity를 확보하는 것이 가장 coherent합니다. 이는 UI나 thin reader가 `status.json`을 소비하기 전 런타임에서 최후의 canonical-set 검증을 보장합니다.

## recommendation
- **RECOMMEND: implement G7-DECISION_CLASS read-path extension**
- **대상 파일**: `pipeline_runtime/control_writers.py`, `tests/test_pipeline_runtime_control_writers.py`
- **세부**:
  - `pipeline_runtime/control_writers.py`에서 `SUPPORTED_DECISION_CLASSES`를 import합니다.
  - `validate_operator_candidate_status`가 `autonomy` dict에서 `decision_class`를 추출하고, `normalize_decision_class` 결과가 canonical set에 있는지 검증하도록 확장합니다.
  - `tests/test_pipeline_runtime_control_writers.py`에 `unsupported decision_class` 경로를 검증하는 regression test를 append합니다. (Gemini 545의 placement 오류를 반복하지 않도록 주의)
