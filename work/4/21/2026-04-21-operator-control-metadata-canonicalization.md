# 2026-04-21 operator-control metadata canonicalization

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/control_writers.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/21/2026-04-21-operator-control-metadata-canonicalization.md`

## 사용 skill
- `security-gate`: operator control metadata와 writer validation 변경이 사용자 문서 쓰기, 외부 네트워크, 삭제/덮어쓰기 동작을 새로 만들지 않는지 점검했습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증, doc-sync 필요 여부, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 표준 Korean closeout 형식으로 정리했습니다.

## 변경 이유
- seq 617 `.pipeline/operator_request.md`의 raw `OPERATOR_POLICY: stop_until_operator_decision`, `REASON_CODE: branch_complete_pending_milestone_transition`, `DECISION_CLASS: branch_closure_and_milestone_transition`가 runtime autonomy payload에서 비정규 metadata로 남아 `classification_source='metadata_fallback'`와 unsupported `decision_class`를 만들었습니다.
- 향후 같은 operator-stop 계열 header가 runtime event와 writer validation을 통과할 때 canonical metadata로 수렴하도록, alias와 검증 경계를 좁게 보강했습니다.

## 핵심 변경
- `normalize_operator_policy(...)`가 `stop_until_operator_decision`을 `immediate_publish`로 정규화하도록 alias를 추가했습니다.
- `normalize_reason_code(...)`가 `branch_complete_pending_milestone_transition`을 operator 승인 성격의 canonical reason인 `approval_required`로 정규화하도록 alias를 추가했습니다.
- `normalize_decision_class(...)`가 `branch_closure_and_milestone_transition`와 `branch_complete_pending_milestone_transition`을 `operator_only`로 정규화하도록 alias를 추가했습니다.
- `validate_operator_request_headers(...)`가 normalized non-empty `decision_class`도 `SUPPORTED_DECISION_CLASSES` 안에 있어야 통과하도록 writer validation을 강화했습니다.
- `tests/test_operator_request_schema.py`에 seq 617 raw header normalization과 random unsupported decision class reject 회귀 테스트를 추가했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 seq 617 raw metadata가 `classification_source='operator_policy'`와 canonical payload로 분류되는 회귀 테스트를 추가했습니다.

## 검증
- `python3 -m unittest tests.test_operator_request_schema`
  - `Ran 8 tests in 0.001s`
  - `OK (skipped=1)`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - `Ran 107 tests in 0.651s`
  - `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/control_writers.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 출력 없음, `rc=0`

## 남은 리스크
- 이번 변경은 future emission/validation 경계를 고치는 것이며, 기존 `.pipeline/runs/20260421T051027Z-p63257/events.jsonl`의 과거 event payload를 backfill하지 않았습니다.
- `.pipeline/operator_request.md` 자체는 handoff 제약에 따라 implement lane에서 수정하지 않았습니다.
- 전체 unittest, pytest, Playwright smoke는 이번 handoff 범위에서 요구되지 않아 실행하지 않았습니다.
- 작업 시작 전부터 `tests/test_pipeline_runtime_supervisor.py`에는 seq 593 origin 주석 관련 dirty change가 있었고, 이번 라운드에서는 이를 되돌리지 않은 채 seq 617 regression test만 추가했습니다.
