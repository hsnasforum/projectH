# 2026-05-20 controller Queue handler asset response guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-queue-handler-asset-response-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2047`가 server socket 없이 `ControllerHandler`의 `/controller-assets/js/queue-presentation.js`와 `/controller-assets/js/cozy.js` route/asset response 경로를 고정하라고 지시했다.
- 직전 asset-resolution guard는 `_resolve_controller_asset()`의 실제 파일 경로와 JavaScript MIME 해석을 확인했지만, handler route가 해당 asset response 경로를 사용하는지는 직접 확인하지 않았다.

## 핵심 변경
- `tests/test_controller_server.py`에 `io.BytesIO` 기반 fake handler response helper를 추가했다.
- `ControllerHandler.do_GET()`이 `/controller-assets/js/queue-presentation.js`와 `/controller-assets/js/cozy.js`를 각각 `_serve_controller_asset("js/...")`로 dispatch하는지 확인했다.
- `_serve_controller_asset()`이 실제 Queue helper JS asset에 대해 `HTTPStatus.OK`, JavaScript `Content-Type`, `Cache-Control: no-cache`, 정확한 `Content-Length`, non-empty body를 반환하는지 확인했다.
- 응답 body에 `PipelineQueuePresentation`과 `queuePresentationHelper` marker가 포함되는지 확인했다.
- `controller/server.py` 생산 코드는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 32 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free handler/asset-response unit guard만 추가했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
