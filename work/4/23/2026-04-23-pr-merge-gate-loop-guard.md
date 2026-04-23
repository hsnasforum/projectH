# 2026-04-23 PR merge gate 반복 루프 방지

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_operator_request_schema.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `README.md`
- `.pipeline/README.md`
- `docs/MILESTONES.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 사용 skill
- `security-gate`: runtime control slot / operator stop 판정 변경이 승인 경계와 로그 surface에 닿는지 확인했습니다.
- `doc-sync`: `pr_merge_gate`를 실제 publication boundary로 문서화해야 하는 범위를 골랐습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경, 검증, 남은 리스크를 `/work`에 남겼습니다.
- `finalize-lite`: 구현 종료 전 검증 사실, doc-sync 여부, `/work` closeout 준비 상태를 점검했습니다.

## 변경 이유
- live pipeline에서 `PR #27 merge` operator stop이 `pr_merge_gate + internal_only + merge_gate` 형태로 반복 재작성되며 `RETRIAGE_COUNT`가 746까지 증가했습니다.
- 원인은 `routed_to=operator`인 실제 operator stop도 shared `operator_gate_marker_from_decision()`에서 gate marker로 취급되어 watcher/supervisor가 verify follow-up 루프로 다시 보낼 수 있었기 때문입니다.

## 핵심 변경
- `operator_gate_marker_from_decision()`이 `routed_to == "operator"` 또는 `mode == "needs_operator"`인 decision에는 gate marker를 만들지 않게 했습니다.
- `PR_MERGE_GATE_REASON = "pr_merge_gate"`를 publication boundary reason으로 등록하고, `merge_gate` decision class를 지원 목록에 추가했습니다.
- 현재 사고 모양을 재현하는 테스트를 추가했습니다: schema helper는 gate marker가 없음을 확인하고, watcher는 `OPERATOR_WAIT`에 머물며 verify retriage를 호출하지 않고, supervisor는 `needs_operator + pr_boundary`로 surface하며 `control_operator_gated` event를 남기지 않습니다.
- README, `.pipeline/README.md`, runtime 기술설계/운영 runbook, milestones에 `pr_merge_gate`가 draft PR creation follow-up이 아니라 실제 PR merge publication boundary임을 반영했습니다.
- live `.pipeline/operator_request.md` 기준 새 코드 판정은 `mode=needs_operator`, `reason_code=pr_merge_gate`, `routed_to=operator`, `gate_marker=None`으로 확인했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py` → OK
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_pr_merge_gate_stays_operator_visible_without_gate_marker tests.test_watcher_core.WatcherCoreTest.test_pr_merge_gate_stays_operator_wait_without_verify_retriage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_pr_merge_gate_operator_visible_without_gated_event -v` → watcher class 이름 오기로 1건 loader error, 나머지 2건 OK
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_pr_merge_gate_stays_operator_wait_without_verify_retriage -v` → OK
- `python3 -m unittest tests.test_operator_request_schema tests.test_turn_arbitration -v` → 28/28 OK
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest tests.test_watcher_core.RollingSignalTransitionTest -v` → 42/42 OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_commit_push_bundle_authorization_operator_gate_routes_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_pr_creation_gate_to_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_external_publication_boundary_operator_visible tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_pr_merge_gate_operator_visible_without_gated_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_preserves_operator_gate_first_seen_across_seq_only_bump tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_waiting_next_control_internal_only_to_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_slice_ambiguity_operator_stop_gated_when_based_work_is_verified -v` → 7/7 OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema -v` → 44/44 OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration -v` → 147/147 OK
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py README.md .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md docs/MILESTONES.md` → OK
- live `.pipeline/operator_request.md` 직접 판정 스크립트 → `gate_marker=None`

## 남은 리스크
- 패치 전 실행 중이던 기존 runtime은 source 변경 전 코드로 `CONTROL_SEQ 1721`까지 몇 번 더 반복한 뒤 `runtime_stopped`로 내려갔습니다. 현재 pipeline runtime 프로세스는 없습니다.
- `.pipeline/operator_request.md`에는 기존 PR #27 merge stop이 남아 있으며, 새 코드 기준으로는 operator wait로 판정됩니다. 런타임 재시작 또는 PR merge 여부는 별도 operator 결정입니다.
- 이번 라운드는 runtime/operator gate 회귀 방지에 한정했고, `latest_verify`가 live status에서 `—`로 보이는 별도 artifact 선택 문제는 수정하지 않았습니다.
