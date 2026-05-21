# 2026-05-20 파이프라인 런타임 상태 계약 리듀서 재검증

## 검증 대상
- `RuntimeSnapshot` / `runtime_snapshot` reducer 계약
- supervisor/CLI status export와 stop 보정 경로
- watcher stale advisory recovery dispatch
- wrapper `READY` / `TASK_DONE` 의미 분리
- controller Queue presentation 공유 helper와 shared JSON fixture

## 변경 파일
- 검증 기록 파일 자체 외에는 구현 파일 변경 없음.

## 실행한 확인
- `python3 -m py_compile pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py pipeline_runtime/cli.py controller/server.py watcher_prompt_assembly.py tests/test_controller_queue_presentation.py`
  - 통과.
- `node --check e2e/tests/controller-smoke.spec.mjs`
  - 통과.
- `git diff --check -- .pipeline/README.md README.md controller/index.html controller/js/cozy.js controller/js/state.js controller/server.py docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_prompt_assembly.py tests/test_pipeline_runtime_cli.py tests/test_controller_queue_presentation.py tests/fixtures/controller_queue_presentation_cases.json e2e/tests/controller-smoke.spec.mjs work/5/20/ verify/5/20/`
  - 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_state_contract tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli tests.test_watcher_core tests.test_turn_arbitration tests.test_pipeline_runtime_automation_health tests.test_controller_queue_presentation`
  - 528 tests 통과.
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs -g "controller renders Queue presentation from runtime payloads" --reporter=line`
  - 1 test 통과.

## 판단
- 활성 control/round가 있는데 Queue가 `No queued pipeline task`로 내려가는 핵심 회귀는 reducer unit test와 controller Queue presentation test로 방지되어 있다.
- `prompt_visible`만으로 task 완료를 확정하던 경로는 wrapper unit test로 방지되어 있다.
- stale advisory recovery가 request를 supersede한 뒤 자기 active-control 조건 때문에 verify prompt를 드롭하던 회귀는 watcher core test로 방지되어 있다.
- CLI `stop`이 살아 있는 supervisor가 없을 때 status 보정을 건너뛰던 경로는 unit test 묶음에서 다시 통과했다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=ok`, `automation_next_action=continue`, active control `.pipeline/implement_handoff.md#2042`, `turn_state=VERIFY_ACTIVE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 생존성 판단에 사용하지 않았다.
- 기존 verify note에 남아 있던 `python3 -m pipeline_runtime.cli stop .` 기반 `STOPPED` 판단은 이전 local stop 확인으로만 남기고, 현재 런타임 생존성 truth로는 dispatch 표면을 따른다.
- controller Queue 단일 Playwright 시나리오는 이번 환경에서 socket permission denial 없이 통과했으므로 `local_socket_guard_auto_held`는 이번 재검증 결과가 아니다.

## 남은 확인
- 전체 Playwright smoke와 장시간 soak는 실행하지 않았다. 이번 재검증은 런타임 상태 계약과 controller Queue 단일 시나리오 중심의 좁은 확인이다.
- worktree에는 이번 라운드 이전부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- `controller/server.py`가 legacy runtime status 또는 placeholder에 `runtime_snapshot`을 합성하는 경로는 현재 구현되어 있지만, `tests/test_controller_server.py`의 직접 단위 회귀가 아직 충분하지 않다. 다음 안전 slice는 이 socket-free server contract guard를 추가하는 것이다.
