# 2026-05-20 controller unknown route fail-closed guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-unknown-route-fail-closed-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2059`가 unknown controller GET/POST routes가 shell, asset handler, runtime action으로 오인되지 않고 JSON 404로 fail closed 되는 계약을 socket-free test로 고정하라고 지시했다.
- 이전 slice에서 `ControllerAssetResolutionTests`의 named fixture helper가 준비되었고, unknown route JSON 404 경로는 아직 그 helper 경로로 직접 검증되지 않았다.

## 핵심 변경
- `test_do_get_unknown_runtime_route_returns_json_404`를 추가해 `/api/runtime/not-real` GET 요청이 `HTTPStatus.NOT_FOUND`와 `{"error": "not found"}` JSON payload를 반환하는지 확인했다.
- `test_do_post_unknown_runtime_route_returns_json_404`를 추가해 같은 unknown POST route도 JSON 404 fail-closed 계약을 유지하는지 확인했다.
- 두 테스트 모두 `_json_route_response`, `_json_post_response`, `_assert_json_response`를 사용해 JSON headers, `Content-Length`, CORS header, body bytes, end-header count를 기존 helper 경로로 검증한다.
- 기존 known route, asset, header, body, dispatch assertions는 변경하지 않았다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 50 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller route contract test guard만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
