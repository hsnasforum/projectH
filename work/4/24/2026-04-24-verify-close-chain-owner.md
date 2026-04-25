# 2026-04-24 verify close chain owner 정리

## 변경 파일
- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_verify_fsm.py`
- `tests/test_watcher_core.py`
- `work/4/24/2026-04-24-verify-close-chain-owner.md`

## 사용 skill
- `finalize-lite`: 구현 범위, 검증 사실, doc-sync 필요 여부, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M28 Axis 1 handoff는 `TASK_ACCEPTED -> TASK_DONE -> receipt close -> next handoff dispatch` 전이 체인을 `verify_fsm.py` 단일 owner로 고정하라고 지시했습니다.
- 기존에는 watcher polling이 `VERIFY_RUNNING` job을 일반 `step()`으로 다시 해석할 수 있어, advisory pending 상태와 verify close chain 경계가 섞일 재발 위험이 있었습니다.
- handoff의 acceptance에는 `pipeline_runtime/verify_fsm.py`, `pipeline_runtime/watcher_core.py`가 적혀 있었지만 현재 repo에는 해당 파일이 없고 실제 runtime owner는 루트 `verify_fsm.py`, `watcher_core.py`입니다.

## 핵심 변경
- `StateMachine.step_verify_close_chain()`을 추가해 `VERIFY_RUNNING` close chain 전이를 FSM 전용 진입점으로 분리했습니다.
- verify close 결과는 current dispatch가 `TASK_ACCEPTED`와 `TASK_DONE`을 모두 통과한 뒤에만 `VERIFY_DONE`으로 닫히도록 `close_chain_done` 조건을 명확히 했습니다.
- `WatcherCore._poll()`은 current-run `VERIFY_RUNNING` job을 처리할 때 `self.sm.step()` 대신 `self.sm.step_verify_close_chain()`만 호출하도록 위임했습니다.
- watcher의 새 라운드 reset 직접 state write를 `StateMachine.reset_job_for_new_round()` 위임으로 옮겼습니다.
- `tests/test_verify_fsm.py`에 `TASK_ACCEPTED -> TASK_DONE -> receipt close` replay와 close outputs 선행 발생 시 미종료 검증을 추가했습니다.
- `tests/test_watcher_core.py`의 current-run verify-running 우선순위 테스트는 generic `step()` 미호출까지 확인해 watcher가 close chain을 재해석하지 않도록 고정했습니다.

## 검증
- `python3 -m py_compile verify_fsm.py watcher_core.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_verify_fsm`
  - 통과: `Ran 7 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 통과: `Ran 201 tests`, `OK`
- `python3 -m unittest tests.test_verify_fsm tests.test_watcher_core`
  - 통과: `Ran 208 tests in 9.130s`, `OK`
- `git diff --check`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_pipeline_gui_app.PipelineGuiAppTest.test_setup_refresh_downgrades_cached_applied_state_when_active_profile_is_missing`
  - 통과: `Ran 1 test`, `OK`
- `python3 -m unittest discover -s tests`
  - 실패: `Ran 1756 tests in 42.960s`, `FAILED (failures=1, errors=36, skipped=1)`
  - 36개 error는 sandbox에서 `127.0.0.1` socket 생성이 `PermissionError: [Errno 1] Operation not permitted`로 막힌 HTTP/Ollama/Web handler 테스트였습니다.
  - 1개 failure는 `test_pipeline_gui_app.PipelineGuiAppTest.test_setup_refresh_downgrades_cached_applied_state_when_active_profile_is_missing`였고, 같은 테스트는 단독 재실행에서 통과했습니다.

## 남은 리스크
- 전체 unittest suite는 현재 sandbox socket 제한과 order-dependent로 보이는 GUI setup 단일 실패 때문에 green으로 닫히지 않았습니다. 이번 handoff 대상 모듈과 직접 관련된 `tests.test_verify_fsm`, `tests.test_watcher_core`는 통과했습니다.
- 작업트리에는 이번 handoff 범위 밖의 기존 dirty files가 남아 있습니다: `pipeline_runtime/cli.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/turn_arbitration.py`, `scripts/pipeline_runtime_gate.py`, 관련 테스트 및 report/verify/work 파일들입니다. 이번 implement round에서는 해당 파일들을 수정하거나 되돌리지 않았습니다.
- handoff의 py_compile 경로 `pipeline_runtime/verify_fsm.py`, `pipeline_runtime/watcher_core.py`는 repo에 존재하지 않아 그대로 실행하지 않았고, 실제 runtime 파일인 루트 `verify_fsm.py`, `watcher_core.py`를 기준으로 검증했습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, commit/push/PR은 건드리지 않았습니다.
