# 2026-05-20 controller runtime status API route guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-runtime-status-api-route-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2050`가 server socket 없이 `/api/runtime/status` handler route가 `get_runtime_status()` payload를 JSON으로 반환하고 `runtime_snapshot`을 보존하는지 unit guard로 고정하라고 지시했다.
- 기존 helper-level `get_runtime_status()` 테스트와 shell/asset route guard는 있었지만, `ControllerHandler.do_GET()`의 `/api/runtime/status` route가 JSON 응답 경로로 payload를 전달하는지는 직접 확인하지 않았다.

## 핵심 변경
- `tests/test_controller_server.py`에 `json` import를 추가했다.
- `ControllerAssetResolutionTests`에 `test_do_get_runtime_status_route_returns_json_snapshot`를 추가했다.
- fake `ControllerHandler`와 `io.BytesIO` wfile을 사용해 socket bind 없이 `/api/runtime/status` GET route를 호출했다.
- `controller_server.get_runtime_status()`를 mock해 `runtime_state`, `automation_health`, nested `runtime_snapshot` payload를 반환하도록 했다.
- 응답이 `HTTPStatus.OK`, `Content-Type: application/json`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`를 가지며 body가 mock `runtime_snapshot`을 그대로 보존하는지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 36 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free `/api/runtime/status` handler route unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
