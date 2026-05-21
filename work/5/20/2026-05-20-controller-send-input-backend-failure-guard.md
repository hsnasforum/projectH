# 2026-05-20 controller send-input backend failure guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-send-input-backend-failure-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2064`가 `/api/runtime/send-input` route에서 backend send 실패가 기존 JSON 502 `failed to send input` 응답으로 전파되는 계약을 socket-free 테스트로 고정하라고 지시했다.
- `runtime_send_input(...)`에는 `backend_runtime_send_input(...)`이 `False`를 반환할 때 `HTTPStatus.BAD_GATEWAY`를 반환하는 경로가 있었지만, route-level POST payload가 실제 wrapper를 거쳐 이 실패 응답을 반환하는 테스트는 없었다.

## 핵심 변경
- `test_do_post_send_input_propagates_backend_failure`를 추가했다.
- valid payload `{"lane": "Codex", "text": "hello"}`로 `/api/runtime/send-input` route를 실행하고, route가 실제 `runtime_send_input(...)` wrapper를 지나도록 했다.
- `backend_runtime_send_input`을 `False` 반환으로 patch해 backend send 실패를 만들었다.
- 응답이 `HTTPStatus.BAD_GATEWAY`와 `{"ok": False, "error": "failed to send input"}`인지 확인했다.
- backend helper가 `PROJECT_ROOT`, `SESSION_NAME`, `"Codex"`, `text="hello"`로 한 번 호출되는지 확인했다.
- production code는 변경하지 않았다. 기존 실패 경로를 route-level 테스트로 고정한 변경이다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 56 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller POST failure-path route 테스트 추가에 한정했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller route family의 앞선 기록에는 local socket guard 환경 제약으로 controller smoke가 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- 작업 트리는 이전 controller/test/work/verify 라운드의 누적 변경을 포함한다. 이번 라운드에서는 handoff 범위인 `tests/test_controller_server.py`와 이 `/work` 기록만 의도적으로 변경했다.
