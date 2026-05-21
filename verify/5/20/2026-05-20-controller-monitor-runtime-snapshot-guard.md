# 2026-05-20 controller monitor runtime_snapshot guard 검증

## 검증 대상
- `tests/test_controller_server.py`의 `runtime_monitor_snapshot()` socket-free guard
- monitor/HUD payload 구성 중 `runtime.runtime_snapshot` 보존 확인
- controller server status/placeholder/role metadata 기존 guard 유지 확인

## 변경 파일
- 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_runtime_monitor_snapshot_fans_in_token_hud`는 mock runtime payload에 `runtime_snapshot`을 포함하고, `runtime_monitor_snapshot()` 결과의 `snapshot["runtime"]["runtime_snapshot"]`에서 `contract_version`, Queue `implement #2044`, class `neutral`을 확인한다.
- `RuntimeMonitorStateManager.snapshot()`은 `runtime_status`를 `runtime` 필드에 그대로 전달하므로, monitor/HUD payload 구성 중 reducer-owned snapshot이 드롭되지 않는 계약이 단위 테스트로 고정되었다.
- `controller/server.py` 생산 코드는 이번 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2044`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 같은 계열의 안전한 local slice는 controller HTML이 `queue-presentation.js`를 `cozy.js`보다 먼저 로드한다는 정적 server/HTML guard를 추가해, `globalThis.PipelineQueuePresentation` 의존 순서가 깨지지 않게 하는 것이다.
