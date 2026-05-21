# 2026-05-20 controller handler fixture result object

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-handler-fixture-result-object.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2058`가 `ControllerAssetResolutionTests`의 `_response_handler()`를 positional tuple과 `list[int]` end counter에서 작은 local result object로 바꾸라고 지시했다.
- 기존 helper 통합은 완료되어 있었지만 caller가 `handler, _, _, _`와 `ended[0]` 형태에 의존해 future route/header/body test drift 위험이 남아 있었다.

## 핵심 변경
- `tests/test_controller_server.py`에 `_HandlerFixture`를 추가해 fake `ControllerHandler`, collected responses, header pairs, end-header count, body access를 이름 있는 필드와 property로 보관하게 했다.
- `_response_handler()`가 raw 4-tuple 대신 `_HandlerFixture`를 반환하도록 바꿨고, fake handler의 `send_response`, `send_header`, `end_headers`는 fixture method에 연결했다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`는 fixture의 named fields/properties를 사용하되 기존 public helper return shape인 `(responses, headers_dict, body_bytes, ended_int)`를 유지했다.
- dispatch-only tests는 tuple unpacking 대신 `fixture.handler`를 사용해 `_serve_controller_asset`와 `_serve_html` delegate-call assertions를 그대로 검증한다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free test fixture reliability refactor만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
