# 2026-04-23 operator publish follow-up normalization

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `watcher_prompt_assembly.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/23/2026-04-23-operator-publish-followup-normalization.md`

## 사용 skill
- `finalize-lite`: 변경 범위에 맞는 좁은 검증만 다시 실행하고, docs/verify 범위로 불필요하게 넓히지 않았습니다.
- `work-log-closeout`: operator stop 회귀 원인, 실제 수정, 실행한 검증, 런타임 회복 상태를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 재시작 후에도 `.pipeline/operator_request.md`의 `REASON_CODE: m21_complete_push_and_pr_bundle`가 canonical publish follow-up reason으로 분류되지 않아 `needs_operator` 또는 `hibernate`로 남을 수 있었습니다.
- 기존 정책은 `commit_push_bundle_authorization`, `pr_creation_gate`, `pr_merge_gate` 같은 structured reason만 verify/handoff follow-up으로 자동 라우팅하도록 되어 있어, ad hoc publish reason이 그 경로를 비켜갔습니다.
- 같은 유형의 raw operator stop 재발을 줄이기 위해 operator retriage prompt에도 canonical reason 사용 가드를 보강할 필요가 있었습니다.

## 핵심 변경
- `normalize_reason_code()`에 `m21_complete_push_and_pr_bundle -> commit_push_bundle_authorization` alias를 추가해 기존 live stop도 canonical internal publish follow-up으로 정규화되도록 했습니다.
- operator retriage prompt에 `.pipeline/operator_request.md` 작성 시 ad hoc publish/merge reason 대신 `commit_push_bundle_authorization`, `pr_creation_gate`, `pr_merge_gate` 같은 shared-helper canonical metadata를 쓰도록 명시했습니다.
- schema/unit 테스트에 alias normalization과 classify 결과가 `triage -> verify_followup`로 가는지 회귀 테스트를 추가했습니다.
- supervisor 상태 테스트에 live `operator_request.md`가 ad hoc reason을 들고 있어도 status surface가 canonical publish follow-up으로 정규화되는 케이스를 추가했습니다.
- 추가 스캔으로 `.pipeline/operator_request.md`의 현재 ad hoc reason이 canonical alias로 회복되는지 확인했고, implement/advisory/harness 쪽의 다른 `REASON_CODE`들은 operator stop schema 대상이 아닌 별도 control 문맥임을 분리해서 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_prompt_assembly.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_seq617_raw_operator_headers_normalize_to_canonical_metadata tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_m21_publish_bundle_alias_routes_to_internal_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_commit_push_bundle_authorization_operator_gate_routes_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_normalizes_m21_publish_bundle_stop_to_verify_followup -v`
  - 통과: `Ran 4 tests`, `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py watcher_prompt_assembly.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 통과: 출력 없음
- `python3 -m pipeline_runtime.cli status /home/xpdlqj/code/projectH --json`
  - 확인: `runtime_state=RUNNING`, `turn_state=VERIFY_FOLLOWUP`, `automation_health=ok`, `automation_next_action=continue`
- `python3 - <<'PY' ... REASON_CODE scan ... PY`
  - 확인: live `.pipeline/operator_request.md`의 `m21_complete_push_and_pr_bundle`는 alias로 `commit_push_bundle_authorization`에 매핑됨

## 남은 리스크
- 현재 실행 중인 supervisor/watcher 프로세스는 이미 `VERIFY_FOLLOWUP`로 들어가 있어 추가 재시작은 하지 않았습니다. 따라서 새 alias/프롬프트 규칙은 다음 supervisor code load부터 확실하게 반영됩니다.
- live `.pipeline/operator_request.md` 자체는 그대로 두었습니다. 지금 verify owner가 follow-up round를 진행 중이라 control 파일을 중간에 덮어써 흐름을 흔들지 않기 위해서입니다.
- `m21_complete_push_and_pr_bundle`를 쓰는 tracked producer는 찾지 못했습니다. 현재 문자열은 raw/manual control write 계열 흔적에 가까우므로, 같은 계열이 다시 보이면 producer를 찾아 `write_operator_request()` 경로로 고정하는 후속 정리가 필요합니다.
