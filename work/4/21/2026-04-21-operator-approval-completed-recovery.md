# 2026-04-21 operator approval completed recovery

## 변경 파일
- `watcher_core.py`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/status_labels.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `pipeline-launcher.py`
- `pipeline_gui/home_presenter.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_launcher.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_operator_request_schema.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/21/2026-04-21-operator-approval-completed-recovery.md`

## 사용 skill
- `security-gate`: `approval_required` operator boundary와 read-only git 판정이 자동 commit/push나 destructive action으로 번지지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 검증 사실, doc sync 범위, `/work` closeout 필요성을 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 현재 closeout을 남겼습니다.

## 변경 이유
- `.pipeline/operator_request.md`의 commit/push 승인 stop이 이미 operator-approved commit/push로 충족된 뒤에도 old `needs_operator` 경계가 unresolved loop처럼 보일 수 있었습니다.
- 이번 slice는 commit/push를 실행하지 않고, 이미 완료된 상태를 read-only git evidence로만 인식해 verify/handoff owner가 다음 control을 정리하도록 복구 상태를 드러내는 것입니다.

## 핵심 변경
- watcher에 `operator_approval_completed` recovery marker를 추가했습니다. 조건은 `STATUS: needs_operator`, `REASON_CODE: approval_required`, shared `is_commit_push_approval_stop` predicate가 commit 및 push approval boundary로 판정함, branch upstream 존재, `HEAD`가 upstream tip과 같거나 upstream에 포함됨, rolling `.pipeline` artifact 외 clean worktree입니다.
- git state를 읽지 못하거나 upstream이 없거나 upstream이 `HEAD`를 포함하지 않거나 non-rolling source dirty가 있으면 기존 `needs_operator` behavior를 유지하도록 fail-closed 처리했습니다.
- satisfied marker는 기존 operator recovery path를 통해 `VERIFY_FOLLOWUP`으로 라우팅하며, raw log/runtime event에 `control_seq`, `branch`, `head_sha`, `upstream`, `operator_request.md` 정보를 남깁니다.
- commit/push approval stop 판정은 `pipeline_runtime/operator_autonomy.py`의 metadata/body predicate로 분리했고, operator-facing 한국어 label은 `pipeline_runtime/status_labels.py`에서만 제공합니다. 현재 branch, commit SHA, 특정 operator_request 본문, pane target, 표시 문구를 watcher/launcher/test fixture에 직접 박지 않도록 정리했습니다.
- supervisor/automation health는 `operator_approval_completed`를 recovery + `verify_followup`으로 surface합니다. raw reason은 snapshot detail/debug context에만 남깁니다.
- runtime docs와 `.pipeline/README.md`에 satisfied commit/push operator boundary 계약과 fail-closed 조건을 동기화했습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline-launcher.py pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py pipeline_runtime/status_labels.py pipeline_gui/home_presenter.py` → 통과
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_satisfied_commit_push_operator_request_routes_to_codex_followup tests.test_watcher_core.TurnResolutionTest.test_commit_push_operator_request_without_upstream_stays_operator_turn tests.test_watcher_core.TurnResolutionTest.test_commit_push_operator_request_upstream_behind_stays_operator_turn tests.test_watcher_core.TurnResolutionTest.test_commit_push_operator_request_dirty_source_stays_operator_turn tests.test_watcher_core.TurnResolutionTest.test_commit_push_operator_request_allows_rolling_pipeline_dirty_slots` → 5 tests OK
- `python3 -m unittest tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_build_snapshot_localizes_operator_approval_completed_reason` → 1 test OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_progress_hint_marks_operator_approval_completed tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_operator_approval_completed_turn_suppresses_active_operator_control` → 2 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest` → 11 tests OK
- `python3 -m unittest tests.test_operator_request_schema` → 11 tests OK
- `python3 -m unittest tests.test_pipeline_gui_home_presenter` → 16 tests OK
- `python3 -m unittest tests.test_watcher_core` → 168 tests OK
- `python3 -m unittest tests.test_pipeline_launcher` → 25 tests OK
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_automation_health` → 137 tests OK
- `git diff --check -- watcher_core.py pipeline-launcher.py pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py pipeline_runtime/operator_autonomy.py pipeline_gui/home_presenter.py tests/test_watcher_core.py tests/test_pipeline_launcher.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_operator_request_schema.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` → 통과
- `git diff --check --no-index -- /dev/null pipeline_runtime/status_labels.py` → whitespace warning 출력 없음 (`--no-index` 신규 파일 diff라 rc=1)
- `git diff --check --no-index -- /dev/null work/4/21/2026-04-21-operator-approval-completed-recovery.md` → whitespace warning 출력 없음 (`--no-index` 신규 파일 diff라 rc=1)

## 남은 리스크
- 이번 변경은 read-only local git refs만 확인하며 `git fetch`를 하지 않습니다. local upstream ref 자체가 오래됐는지는 별도 네트워크 동기화 없이 판단하지 않습니다.
- allowed dirty set은 rolling `.pipeline` control/runtime artifact로 제한했습니다. `.pipeline/README.md` 같은 source/document dirty는 의도대로 satisfied marker를 막습니다.
- implement lane boundary를 지켜 commit, push, PR 생성, long soak, 다음 slice 선택은 수행하지 않았습니다.
