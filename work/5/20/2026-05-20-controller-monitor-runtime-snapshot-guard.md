# 2026-05-20 controller monitor runtime_snapshot guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-monitor-runtime-snapshot-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2044`가 `runtime_monitor_snapshot()`이 `get_runtime_status()`에서 받은 reducer-owned `runtime_snapshot`을 monitor/HUD payload 구성 중 드롭하지 않는지 socket-free 단위 테스트로 고정하라고 지시했다.
- 기존 `test_runtime_monitor_snapshot_fans_in_token_hud`는 token HUD fan-in과 lane state만 확인했고, `snapshot["runtime"]["runtime_snapshot"]` 보존 여부는 확인하지 않았다.

## 핵심 변경
- `test_runtime_monitor_snapshot_fans_in_token_hud`의 mock runtime payload에 active implement control과 `runtime_snapshot`을 포함했다.
- `runtime_monitor_snapshot()` 반환값의 `snapshot["runtime"]["runtime_snapshot"]`에서 `contract_version`을 확인하도록 했다.
- 같은 snapshot의 Queue 표면이 `implement #2044`, class `neutral`로 유지되는지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 29 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller server unit guard만 추가했다. Playwright, full controller smoke, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
