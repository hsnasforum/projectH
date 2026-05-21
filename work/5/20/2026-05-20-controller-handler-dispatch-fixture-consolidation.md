# 2026-05-20 controller handler dispatch fixture consolidation

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-handler-dispatch-fixture-consolidation.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2057`가 `ControllerAssetResolutionTests`의 dispatch-only route tests도 같은 fake handler setup path를 쓰도록 정리하라고 지시했다.
- response-capture helper는 `_response_handler()`로 통합되어 있었지만, `test_do_get_dispatches_real_controller_queue_js_assets`와 `test_do_get_dispatches_controller_shell_routes_to_html`는 여전히 raw `ControllerHandler` 생성과 `path` 설정을 각 test 안에서 반복하고 있었다.

## 핵심 변경
- `test_do_get_dispatches_real_controller_queue_js_assets`가 inline `object.__new__(ControllerHandler)`와 `handler.path` 설정 대신 `_response_handler(path=...)`를 사용하도록 바꿨다.
- `test_do_get_dispatches_controller_shell_routes_to_html`도 같은 `_response_handler(path=...)` 경로를 사용하도록 바꿨다.
- `_serve_controller_asset`와 `_serve_html` delegate-call assertions는 그대로 유지했다.
- 기존 response/header/body/end-header assertions와 helper 반환 형태는 변경하지 않았다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free test harness consolidation만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
