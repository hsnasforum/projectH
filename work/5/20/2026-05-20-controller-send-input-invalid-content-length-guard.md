# 2026-05-20 controller send-input invalid content length guard

## 변경 파일
- `controller/server.py`
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-send-input-invalid-content-length-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2060`가 `/api/runtime/send-input` POST에서 invalid non-integer `Content-Length` header가 들어와도 `ValueError`가 handler 밖으로 새지 않고 기존 invalid JSON 계약과 같은 JSON 400으로 fail closed 되게 하라고 지시했다.
- 기존 코드는 `int(self.headers.get("Content-Length") or "0")`를 invalid-JSON `try` block 밖에서 실행해, header parsing 실패가 `_json({"ok": False, "error": "invalid json"}, HTTPStatus.BAD_REQUEST)` 경로로 닫히지 않았다.

## 핵심 변경
- `controller/server.py`에서 `/api/runtime/send-input`의 `Content-Length` 정수 변환을 request body JSON parsing `try` block 안으로 옮겼다.
- 같은 `except`에 `ValueError`를 포함해 invalid or unparsable `Content-Length`도 기존 bad request JSON shape로 응답하게 했다.
- `tests/test_controller_server.py`의 `_response_handler`와 `_json_post_response`에 header override를 최소 추가해 socket-free handler test가 invalid request header를 만들 수 있게 했다.
- `test_do_post_send_input_rejects_invalid_content_length`를 추가해 invalid `Content-Length`가 `HTTPStatus.BAD_REQUEST`와 `{"ok": False, "error": "invalid json"}`을 반환하고 `runtime_send_input`을 호출하지 않는지 확인했다.
- 기존 valid JSON, malformed JSON body, unknown POST, route, asset, header, body, dispatch assertions는 유지했다.

## 검증
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 51 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller POST parsing guard만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `controller/server.py`, `tests/test_controller_server.py`, 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
