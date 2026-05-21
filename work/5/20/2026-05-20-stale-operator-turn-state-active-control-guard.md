# 2026-05-20 stale operator turn-state active control guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-stale-operator-turn-state-active-control-guard.md`

## 사용 skill

- `work-log-closeout`: handoff 완료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- 이전 라운드는 control slot이 전혀 없을 때 stale `OPERATOR_WAIT` mirror가 operator boundary처럼 보이는 문제를 막았습니다.
- 남은 위험은 실제 active non-operator control slot이 있는데도 오래된 `turn_state.json`이 `operator_request.md#2031`을 가리켜 `operator_boundary` progress를 만드는 경우였습니다.
- implement, advisory request, advisory advice control이 실제 active일 때는 parsed active control을 유지하고 stale operator turn-state만 status surface에서 비워야 합니다.

## 핵심 변경

- `_surface_turn_state_for_missing_control()`에서 active control slot이 `needs_operator`가 아니고 turn-state가 `operator_request.md`를 가리키는 경우 status용 turn state를 `IDLE`로 정규화하도록 확장했습니다.
- active slot이 실제 `operator_request.md` / `needs_operator`인 경우에는 기존 `OPERATOR_WAIT` 표면을 유지하도록 분기했습니다.
- `implement_handoff.md`, `advisory_request.md`, `advisory_advice.md` 각각이 active일 때 stale operator turn-state가 `operator_boundary` progress를 만들지 않는 회귀 테스트를 추가했습니다.
- 기존 no-control-slot stale operator mirror 테스트와 같은 helper 안에서 처리해 status surface 정규화 경로를 흩뜨리지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_ignores_stale_operator_turn_state_when_non_operator_control_is_active`
  - 최초 결과: FAIL. 기존 helper가 active/stale control slot 존재 시 조기 반환해 stale `OPERATOR_WAIT`를 그대로 유지하는 것을 확인했습니다.
  - 최종 결과: PASS. 3개 active non-operator control slot 케이스가 모두 통과했습니다.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_codex_task_hint_during_operator_wait`
  - 결과: PASS. 실제 active `operator_request.md`의 operator-wait 표면은 유지됨을 확인했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.

## 남은 리스크

- handoff 지시에 따라 Playwright, e2e, 전체 unittest, long soak, commit, push, PR, merge, release, socket-bound smoke는 실행하지 않았습니다.
- `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`에는 이번 라운드 이전부터 있던 다른 runtime/local-socket/task-hint 관련 dirty 변경이 함께 남아 있습니다. 이번 라운드는 stale operator turn-state와 active non-operator control mismatch만 좁게 수정했습니다.
- 이번 변경은 status surface 정규화입니다. 실제 control dispatch, publication, operator stop release 정책은 변경하지 않았습니다.
