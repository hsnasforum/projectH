# 2026-04-24 operator advisory policy normalization

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `work/4/24/2026-04-24-operator-advisory-policy-normalization.md`

## 사용 skill
- `security-gate`: `needs_operator` runtime control 분류가 실제 operator stop인지, advisory/verify follow-up으로 낮출 수 있는 stop인지 확인했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 `/work` 기록으로 남겼습니다.

## 변경 이유
- 현재 runtime status가 `.pipeline/operator_request.md` `CONTROL_SEQ: 133`, `REASON_CODE: m30_direction_fresh_scoping`, `OPERATOR_POLICY: advisory_before_operator`를 `needs_operator`로 표시했습니다.
- 조사 결과 `advisory_before_operator`가 `SUPPORTED_OPERATOR_POLICIES`의 canonical policy로 정규화되지 않아 `metadata_fallback -> immediate_publish -> needs_operator`로 떨어졌습니다.
- `m30_direction_fresh_scoping` 같은 milestone direction reason도 canonical reason으로 좁혀지지 않아 advisory-first 규칙과 어긋났습니다.

## 핵심 변경
- `normalize_operator_policy()`에 `advisory_before_operator`, `advisory_first`, `advisory_first_before_operator`를 `gate_24h` alias로 추가했습니다.
- `normalize_reason_code()`에 `m<number>_direction...` 계열을 `slice_ambiguity`로 낮추는 정규화를 추가했습니다.
- `pr_merge_gate`, `pr_creation_gate`, `commit_push_bundle_authorization` 같은 publication/merge compound reason이 milestone direction regex보다 우선되도록 기존 compound alias 순서를 유지했습니다.
- 현재 `.pipeline/operator_request.md`를 새 코드로 직접 분류하면 `mode=triage`, `routed_to=verify_followup`, `operator_eligible=false`가 됩니다.

## 검증
- `python3 -m unittest tests.test_operator_request_schema`
  - 1차 실패: `m28_direction + pr_merge_gate` compound reason이 `slice_ambiguity`로 먼저 정규화됨
  - 수정 후 통과: 25 tests, OK (skipped=1)
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor`
  - 통과: 168 tests, OK
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor`
  - 통과: 200 tests, OK (skipped=1)
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
  - 통과: 출력 없음
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py`
  - 통과: 출력 없음
- 현재 `.pipeline/operator_request.md` 직접 분류 스크립트
  - `mode=triage`, `reason_code=slice_ambiguity`, `operator_policy=gate_24h`, `decision_class=next_slice_selection`, `routed_to=verify_followup`, `operator_eligible=false`

## 남은 리스크
- 이미 실행 중인 supervisor 프로세스는 이전 `pipeline_runtime.operator_autonomy` 코드를 import한 상태일 수 있습니다. 새 분류는 supervisor 재시작 또는 runtime start/restart 경계에서 반영됩니다.
- 현재 `.pipeline/operator_request.md` 파일 자체는 아직 남아 있습니다. 새 supervisor 분류에서는 gated operator control로 낮춰 verify follow-up으로 표면화되어야 합니다.
