# 2026-05-21 dirty bundle publication hold alias guard

## 변경 파일

- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `README.md`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/operator_request.md` (gitignored local control slot)
- `work/5/21/2026-05-21-dirty-bundle-publication-hold-alias-guard.md`

## 사용 skill

- `next-slice-triage`: 공개 승인으로 읽지 않고 현재 요청을 `HOLD_PUBLICATION` / 다음 local follow-up으로 좁히기 위해 사용했다.
- `security-gate`: publication, commit, push, PR, merge, release 경계가 계속 held인지 점검하기 위해 사용했다.
- `doc-sync`: runtime 정규화 동작 변경을 README와 pipeline runtime 문서에 맞추기 위해 사용했다.
- `work-log-closeout`: 변경 파일, 검증, 남은 리스크를 한국어 closeout으로 남기기 위해 사용했다.

## 변경 이유

- live `.pipeline/operator_request.md#2072`가 `dirty_bundle_publication_or_hold_decision` / `operator_only_publication_boundary` / `publication_or_hold`를 사용했지만, shared resolver가 이 조합을 알 수 없는 metadata로 보고 `immediate_publish + needs_operator`로 fail-closed했다.
- 사용자는 publication 실행을 승인한 것이 아니라 해당 화면 문제 해결을 먼저 요청했다. 따라서 현재 decision은 local-only hold로 처리하고, commit/push/branch/PR/merge/release 작업은 계속 금지해야 한다.
- 같은 publish-or-hold compatibility header가 다시 들어와도 controller/launcher가 "공개 작업 승인 필요" active stop으로 고정되지 않도록 회귀를 추가했다.

## 핵심 변경

- `normalize_reason_code()`가 `dirty_bundle_publication_or_hold_decision`을 `commit_push_bundle_authorization`으로 정규화한다.
- `normalize_operator_policy()`가 `operator_only_publication_boundary`를 `internal_only`로 정규화한다.
- `normalize_decision_class()`가 `publication_or_hold`를 `release_gate`로 정규화한다.
- operator schema test와 supervisor status test에 live header family 회귀를 추가했다.
- `.pipeline/operator_request.md#2072` live header를 canonical `commit_push_bundle_authorization + internal_only + release_gate`로 바꾸고 `PUBLISH_HELD: true` 및 source metadata를 남겼다.
- README와 pipeline runtime 문서에 publish-or-hold alias가 release-gate follow-up으로 정규화된다는 내용을 동기화했다.

## 검증

- `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_dirty_bundle_publication_or_hold_reuses_commit_push_followup tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_live_operator_request_header_canonical tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dirty_bundle_publication_or_hold_operator_gate_routes_to_triage`
  - 통과. 3 tests OK.
- `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_accumulated_dirty_tree_publish_boundary_reuses_commit_push_followup tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_unknown_release_gate_metadata_still_fails_closed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_accumulated_dirty_tree_publish_boundary_operator_gate_routes_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_commit_push_bundle_authorization_operator_gate_routes_to_triage`
  - 통과. 4 tests OK.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py`
  - 통과.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py README.md .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 통과.
- `python3 -m unittest -v tests.test_operator_request_schema tests.test_pipeline_runtime_supervisor`
  - 통과. 244 tests OK.
- live `.pipeline/operator_request.md` classification 확인
  - `mode=triage`, `reason_code=commit_push_bundle_authorization`, `operator_policy=internal_only`, `decision_class=release_gate`, `classification_source=operator_policy`, `operator_eligible=False`, `publish_immediately=False`로 확인했다.
- `python3 -m pipeline_runtime.cli status . --json`
  - 확인. `automation_health=attention`, `automation_reason_code=commit_push_bundle_authorization`, `automation_next_action=verify_followup`, `control.active_control_status=none`, `autonomy.mode=triage`, `autonomy.operator_eligible=False`로 내려갔다.

## 남은 리스크

- 이번 라운드는 publication을 실행하지 않았다. commit, push, branch/PR publication, merge, release는 계속 held다.
- full Playwright, controller smoke, broad e2e, long soak, socket-bound HTTP 검사는 실행하지 않았다. 변경 범위가 shared metadata 정규화와 runtime status unit path에 한정되어 unittest와 status 확인으로 검증했다.
- `tests/test_pipeline_runtime_supervisor.py`에는 이번 라운드 이전의 stale-handoff 관련 dirty hunk가 이미 섞여 있었다. 이번 closeout은 publish-or-hold alias test 추가와 그 검증만 새로 귀속한다.
