# 2026-04-20 G7 autonomy-producer extension arbitration

## context
- seq 561 (`AXIS-G7-AUTONOMY-PRODUCER`) 완료. `needs_operator`, `triage`, `hibernate` 모드에 대한 canonical `decision_class` 기본값 부여가 성공적으로 구현됨.
- 하지만 `pending_operator` (24시간 gate 대기 중인 operator candidate) 모드는 여전히 빈 문자열 기본값을 유지하고 있어, G7 일관성 축에서 작은 갭이 남아 있음.

## ambiguity resolution
- **후보**:
  1. `AXIS-G7-AUTONOMY-PRODUCER-EXTEND` (G7-family producer 완결)
  2. `AXIS-EMIT-KEY-STABILITY-LOCK` (6-key 페이로드 안정성 고정)
  3. `AXIS-DISPATCHER-TRACE-BACKFILL` (실제 trace 검증 예약)
- **결정**: `AXIS-G7-AUTONOMY-PRODUCER-EXTEND`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, 직전 라운드에서 시작한 G7-autonomy-producer 축을 완결하는 것이 가장 높은 응집도(coherence)를 갖습니다. `pending_operator`는 `needs_operator`와 본질적으로 같은 operator-only 의사결정 경로를 공유하므로, 이를 `operator_only`로 명시적으로 매핑하여 producer-side 갭을 해소합니다.

## recommendation
- **RECOMMEND: implement AXIS-G7-AUTONOMY-PRODUCER-EXTEND**
- **대상 파일**: `pipeline_runtime/operator_autonomy.py`, `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `pipeline_runtime/operator_autonomy.py:classify_operator_candidate`의 default block에 `elif visible_mode == "pending_operator": decision_class = "operator_only"` 분기를 추가합니다.
  - `tests/test_pipeline_runtime_supervisor.py`의 `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`에 `pending_operator` 시나리오를 추가합니다. (예: `reason_code="safety_stop"`, `now_ts`가 `control_mtime` 직후라 아직 gate 중인 상황 모사)
  - 기존 148개 테스트(99+7+6+36)의 green baseline을 유지합니다.
