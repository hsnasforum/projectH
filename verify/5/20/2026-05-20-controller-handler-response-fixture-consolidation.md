# 2026-05-20 controller handler response fixture consolidation 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-handler-response-fixture-consolidation.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests._response_handler`
- `ControllerAssetResolutionTests._asset_response`
- `ControllerAssetResolutionTests._html_response`
- `ControllerAssetResolutionTests._json_route_response`
- `ControllerAssetResolutionTests._json_post_response`

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `ControllerAssetResolutionTests._response_handler()`가 fake `ControllerHandler` 생성, `wfile`, `send_response`, `send_header`, `end_headers`, 선택적 `path`, 선택적 request body/`Content-Length` setup을 한 곳으로 모은다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`는 공유 helper를 재사용하고, 기존 반환 형태인 `responses`, `headers`, `body`, `ended`를 유지한다.
- `tests.test_controller_server`의 asset, HTML, GET JSON, POST JSON route tests는 기존 header/body/status/delegate-call/end-header assertions를 유지한 상태로 통과한다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2056`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_handler_dispatch_fixture_consolidation`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2057`
- `EVIDENCE: work/5/20/2026-05-20-controller-handler-response-fixture-consolidation.md`, `verify/5/20/2026-05-20-controller-handler-response-fixture-consolidation.md`, `tests/test_controller_server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free test harness consolidation이라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, 테스트 코드 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 `ControllerAssetResolutionTests`의 dispatch-only fake handler setup도 같은 local helper path로 흡수하는 것이다. 현재 response helper는 통합됐지만, `test_do_get_dispatches_real_controller_queue_js_assets`와 `test_do_get_dispatches_controller_shell_routes_to_html`는 여전히 raw `ControllerHandler` 생성과 `path` 설정을 각 test 안에서 반복한다. 이 중복은 controller shell route dispatch contract를 보호하는 테스트 harness drift risk이므로, 생산 코드는 건드리지 않고 `ControllerAssetResolutionTests` 내부 fake handler setup을 완결한다.
