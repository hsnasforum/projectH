# 2026-04-26 operator control resolver

## 변경 파일
- `.pipeline/README.md`
- `README.md`
- `pipeline_runtime/operator_autonomy.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_operator_request_schema.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/26/2026-04-26-operator-control-resolver.md`

## 사용 skill
- `security-gate`: operator-control demotion이 auth/credential, approval/truth-sync, destructive/safety, publication/merge boundary를 숨기지 않는지 확인했다.
- `doc-sync`: README와 `.pipeline/README.md`의 runtime truth를 새 shared resolver 경로에 맞췄다.
- `finalize-lite`: 구현 뒤 실행한 검증과 생략한 live soak/browser smoke 범위를 정리했다.
- `work-log-closeout`: 변경 파일, 실제 검증, dirty tree inventory, 남은 리스크를 한국어 closeout으로 남겼다.

## 변경 이유
- watcher와 supervisor가 `classify_operator_candidate`, `evaluate_stale_operator_control`, `operator_gate_marker_from_decision` 조합을 각자 조립하면 legacy release-gate false-stop demotion과 real-risk 보존 경계가 다시 갈라질 수 있다.
- legacy `operator_request.md` 파일 형태 자체를 읽는 live-file 스타일 회귀가 부족해, 실제 control slot header 조합이 shared truth로 처리되는지 한 번 더 고정할 필요가 있었다.
- 기존 작업트리에 watcher re-export 정리, report/gemini advisory 기록, 선행 `/work` 파일이 섞여 있어 이번 범위와 기존 dirty 범위를 명확히 나눠 기록할 필요가 있었다.

## 핵심 변경
- `pipeline_runtime.operator_autonomy.resolve_operator_control(...)`을 추가해 operator decision, stale recovery marker, gate marker를 한 번에 계산하게 했다.
- `pipeline_runtime/supervisor.py`와 `watcher_core.py`가 새 shared resolver를 사용하도록 바꿔, 두 runtime owner가 operator-control truth를 다시 조립하지 않게 했다.
- `tests/test_operator_request_schema.py`에 실제 `.pipeline/operator_request.md` 파일을 temp workspace에 쓰고 `read_control_meta(...)`와 `resolve_operator_control(...)`로 B1 legacy dirty-tree release gate를 verify follow-up으로 낮추는 회귀를 추가했다.
- README와 `.pipeline/README.md`에 supervisor/watcher가 `resolve_operator_control(...)` 공유 resolver를 쓰는 현재 구현 truth를 반영했다.
- dirty tree 정리는 되돌리기가 아니라 inventory로 처리했다. 이번 라운드에서 의도적으로 다룬 파일은 위 `변경 파일` 목록이고, 기존 dirty로 보존한 항목은 `tests/test_watcher_core.py`, `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, 선행 untracked `/work` 파일들이다. `watcher_core.py`에는 선행 re-export 정리와 이번 resolver 연결이 함께 들어 있다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py` 통과, 출력 없음
- `python3 -m unittest -v tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_live_legacy_release_gate_file_resolves_via_shared_resolver tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_b1_dirty_tree_release_gate_routes_to_internal_followup tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_auth_login_required_stays_operator_visible` 통과
  - `Ran 3 tests in 0.003s`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_b1_dirty_tree_release_gate_operator_request_surfaces_as_triage tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_auth_login_stays_operator_visible` 통과
  - `Ran 2 tests in 0.003s`
- `python3 -m unittest -v tests.test_operator_request_schema` 통과
  - `Ran 31 tests in 0.005s`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_automation_health` 통과
  - `Ran 171 tests in 0.970s`
- `python3 -m unittest -v tests.test_watcher_core` 통과
  - `Ran 204 tests in 7.783s`
- `git diff --check -- pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py README.md .pipeline/README.md tests/test_operator_request_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py` 통과, 출력 없음
- `rg -n "[ \t]+$" work/4/26/2026-04-26-operator-control-resolver.md` 통과, trailing whitespace 없음

## 남은 리스크
- live supervisor/watcher soak, controller browser smoke, 실제 `.pipeline` 런타임 세션 재시작은 실행하지 않았다. 이번 변경은 shared resolver와 단위/파일 기반 회귀에 한정했다.
- 기존 dirty tree 항목은 사용자가 만들었거나 병행 lane 산출물로 보고 되돌리지 않았다.
- commit, push, branch/PR 생성, merge는 수행하지 않았다.
