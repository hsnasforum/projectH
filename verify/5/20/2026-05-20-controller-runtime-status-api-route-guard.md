# 2026-05-20 controller runtime status API route guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-runtime-status-api-route-guard.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests.test_do_get_runtime_status_route_returns_json_snapshot`
- `controller/server.py`의 `ControllerHandler.do_GET()` `/api/runtime/status` JSON route 경로

## 변경 파일
- 이 검증 기록 파일 자체 외에는 없음.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 36 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_get_runtime_status_route_returns_json_snapshot`는 fake `ControllerHandler`와 `io.BytesIO` wfile을 사용해 socket bind 없이 `/api/runtime/status` GET route를 호출한다.
- 해당 test는 `controller_server.get_runtime_status()`를 mock하고, `HTTPStatus.OK`, `Content-Type: application/json`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`, `runtime_state`, `automation_health`, nested `runtime_snapshot` 보존을 확인한다.
- `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2050`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.
- 다음 안전한 local slice는 route별 micro-slice를 더 늘리지 않고, server socket 없이 `ControllerHandler.do_GET()`의 read-only runtime GET routes(`/api/runtime/monitor-snapshot`, `/api/runtime/agent-inspector`, `/api/runtime/capture-tail`)가 각 helper payload를 JSON response로 전달하는지 한 번에 고정하는 bounded route guard bundle이다.
