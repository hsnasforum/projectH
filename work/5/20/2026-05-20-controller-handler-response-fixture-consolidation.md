# 2026-05-20 controller handler response fixture consolidation

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-handler-response-fixture-consolidation.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2056`가 `ControllerAssetResolutionTests`의 fake `ControllerHandler` response-capture setup 중복을 하나의 로컬 helper로 모으라고 지시했다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`가 각각 `send_response`, `send_header`, `end_headers`, `wfile` 설정을 반복하고 있어 route/header/body assertion test가 서로 다르게 drift할 수 있었다.

## 핵심 변경
- `ControllerAssetResolutionTests._response_handler()`를 추가해 fake `ControllerHandler` 생성, `wfile`, `send_response`, `send_header`, `end_headers`, 선택적 `path`/request body setup을 한 곳으로 모았다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`가 공유 helper를 재사용하도록 바꿨다.
- 기존 helper의 반환 형태인 `responses`, `headers`, `body`, `ended`는 유지했다.
- asset, HTML, GET JSON, POST JSON route tests의 header/body/status/delegate-call/end-header assertions는 삭제하지 않았다.
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
