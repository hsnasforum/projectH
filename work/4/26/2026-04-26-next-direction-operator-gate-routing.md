# 2026-04-26 next-direction operator gate routing

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `.pipeline/operator_request.md` (gitignored live control slot)
- `work/4/26/2026-04-26-next-direction-operator-gate-routing.md`

## 사용 skill
- `security-gate`: operator control routing을 바꾸되 safety/auth/truth-sync/publication boundary는 계속 operator stop으로 남기는지 확인했다.
- `doc-sync`: runtime/operator routing 계약이 문서와 맞도록 `.pipeline/README.md`, runtime 기술설계, runbook을 좁게 갱신했다.
- `work-log-closeout`: 구현 사실, 검증, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- launcher 라운드 완료 뒤 `next_direction_after_launcher_close`가 `metadata_fallback`으로 분류되어 `immediate_publish + needs_operator`가 됐다.
- 이 stop은 "M44 publish, M45 start, runtime hardening 중 다음 우선순위"를 묻는 next-slice 선택 문제라 operator-only boundary가 아니다.
- 같은 유형이 반복되면 생산성이 operator stop에 묶이므로 shared resolver에서 canonical `slice_ambiguity` 흐름으로 낮춰야 했다.

## 핵심 변경
- `next_direction_after_launcher_close`, `next_priority_*`, `milestone_direction*` reason을 `slice_ambiguity`로 정규화했다.
- `direction_selection_after_feature_complete` policy를 `gate_24h`로, `milestone_direction`/`next_direction` decision class를 `next_slice_selection`으로 정규화했다.
- watcher/supervisor/schema 회귀 테스트를 추가해 해당 control이 `control=none`, `autonomy.mode=triage`, `operator_policy=gate_24h`, `automation_next_action=advisory_followup`로 내려가는지 고정했다.
- live `.pipeline/operator_request.md` seq 290을 canonical `slice_ambiguity + gate_24h + next_slice_selection`으로 고쳐 즉시 `OPERATOR_WAIT`를 해제했다.
- docs에는 launcher-close next-direction stop이 생산성 차단 operator wait로 보이면 회귀라는 운영 기준을 추가했다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py` 통과.
- `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_next_direction_after_launcher_close_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_next_direction_after_launcher_close_routes_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close` 통과.
- `python3 -m unittest -v tests.test_operator_request_schema` 통과: 32 tests.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_next_direction_after_launcher_close tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_pr_creation_gate_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_external_publication_boundary_operator_visible` 통과: 4 tests.
- `python3 -m unittest -v tests.test_watcher_core.WatcherPromptAssemblyTest.test_next_direction_after_launcher_close_routes_to_verify_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_pr_creation_gate_routes_to_verify_owner_publish_followup tests.test_watcher_core.WatcherPromptAssemblyTest.test_legacy_milestone_commit_push_doc_sync_operator_request_routes_to_verify_followup` 통과: 3 tests.
- live `.pipeline/operator_request.md` 직접 분류: `mode=triage`, `reason_code=slice_ambiguity`, `operator_policy=gate_24h`, `decision_class=next_slice_selection`, `routed_to=verify_followup`, `operator_eligible=false`.
- `python3 -m pipeline_runtime.cli status . --json` 확인: canonical `control.active_control_status=none`, `turn_state=VERIFY_FOLLOWUP`, `automation_reason_code=slice_ambiguity`, `automation_next_action=advisory_followup`.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md .pipeline/operator_request.md` 통과.

## 남은 리스크
- 전체 supervisor/watcher test suite는 실행하지 않았다. 변경 범위가 operator candidate normalization과 관련 surface에 한정되어 관련 회귀만 실행했다.
- `rg -n "[ \t]$" ...`는 runtime docs의 기존 문서 줄 끝 공백을 보고했지만, `git diff --check` 기준 새 trailing whitespace는 없다.
- M44 publish 자체는 여전히 보류 상태이며 이번 변경은 next-direction stop의 자동 라우팅 문제만 해결했다.
