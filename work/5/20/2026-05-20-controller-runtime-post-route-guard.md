# 2026-05-20 controller runtime POST route guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-runtime-post-route-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2052`가 server socket 없이 `ControllerHandler.do_POST()`의 runtime action routes가 helper payload/status와 JSON parsing contract를 보존하는지 unit guard로 고정하라고 지시했다.
- 기존 helper-level `pipeline_start()` / `runtime_send_input()` 테스트와 endpoint 문자열 검사는 있었지만, `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart`, `/api/runtime/send-input` handler dispatch가 `_json()` 응답까지 유지되는지는 직접 확인하지 않았다.

## 핵심 변경
- `ControllerAssetResolutionTests`에 socket-free POST JSON route 호출 helper를 추가해 fake `ControllerHandler`, `io.BytesIO` rfile/wfile, captured `send_response` / `send_header`, minimal `headers`로 `do_POST()`를 호출하게 했다.
- `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart` route가 각각 `pipeline_start()`, `pipeline_stop()`, `pipeline_restart()` mock payload를 `HTTPStatus.OK` JSON body로 반환하는지 확인하는 테스트를 추가했다.
- `/api/runtime/send-input` route가 JSON body `{"lane": "Codex", "text": "hello"}`를 `runtime_send_input(lane="Codex", text="hello")`로 전달하고 helper payload/status를 보존하는지 확인하는 테스트를 추가했다.
- malformed `/api/runtime/send-input` body가 `HTTPStatus.BAD_REQUEST` JSON `{"ok": False, "error": "invalid json"}`로 거절되고 `runtime_send_input()`을 호출하지 않는지 확인하는 테스트를 추가했다.
- `controller/server.py` 생산 코드는 수정하지 않았고 실제 runtime start/stop/restart/send-input 동작도 실행하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 44 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free POST route handler unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
