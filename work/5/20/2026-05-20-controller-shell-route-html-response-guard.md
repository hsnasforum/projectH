# 2026-05-20 controller shell route HTML response guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-shell-route-html-response-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2049`가 server socket 없이 `/`, `/controller`, `/controller/` shell route가 `_serve_html()`로 dispatch되고, 실제 controller HTML shell이 Queue script tags를 포함하는지 unit guard로 고정하라고 지시했다.
- 기존 정적 HTML 테스트와 Queue JS asset handler guard는 있었지만, shell route handler와 `_serve_html()` 응답 자체가 HTML entrypoint를 제공하는지는 직접 확인하지 않았다.

## 핵심 변경
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests`에 `_html_response()` fake handler helper를 추가했다.
- `ControllerHandler.do_GET()`이 `/`, `/controller`, `/controller/` 요청을 각각 `_serve_html()`로 dispatch하는지 확인했다.
- `_serve_html()`이 실제 `controller/index.html`을 `HTTPStatus.OK`, `Content-Type: text/html; charset=utf-8`, 정확한 `Content-Length`, non-empty body로 반환하는지 확인했다.
- HTML body에 `src="/controller-assets/js/queue-presentation.js"`와 `src="/controller-assets/js/cozy.js"`가 모두 있고, `queue-presentation.js`가 `cozy.js`보다 먼저 로드되는지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 35 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free shell route/HTML response unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
