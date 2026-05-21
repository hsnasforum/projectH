# 2026-05-20 controller read-only runtime routes guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-read-only-runtime-routes-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2051`가 server socket 없이 `ControllerHandler.do_GET()`의 read-only runtime GET route 세 개가 helper payload와 query parameter를 JSON 응답 경로로 보존하는지 unit guard로 고정하라고 지시했다.
- 기존 helper-level 테스트와 `/api/runtime/status` handler route guard는 있었지만, `/api/runtime/monitor-snapshot`, `/api/runtime/agent-inspector`, `/api/runtime/capture-tail` handler dispatch가 `_json()` 응답까지 유지되는지는 직접 확인하지 않았다.

## 핵심 변경
- `ControllerAssetResolutionTests`에 socket-free GET JSON route 호출 helper를 추가해 fake `ControllerHandler`, `io.BytesIO` wfile, captured `send_response` / `send_header`로 `do_GET()`을 호출하게 했다.
- JSON 응답 공통 assertion helper를 추가해 status, `Content-Type: application/json`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`, body payload 보존, `end_headers()` 1회 호출을 확인하게 했다.
- 기존 `/api/runtime/status` route guard를 새 helper 기반으로 정리했다.
- `/api/runtime/monitor-snapshot` route가 `runtime_monitor_snapshot()` payload를 `HTTPStatus.OK` JSON body로 반환하는지 확인하는 테스트를 추가했다.
- `/api/runtime/agent-inspector?agent=Codex&lines=77` route가 `runtime_agent_inspector(agent="Codex", lines=77)`로 dispatch하고 helper payload/status를 보존하는지 확인하는 테스트를 추가했다.
- `/api/runtime/capture-tail?lane=Codex&lines=40` route가 `runtime_capture_tail(lane="Codex", lines=40)`로 dispatch하고 helper payload/status를 보존하는지 확인하는 테스트를 추가했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 39 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free read-only runtime GET route unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
