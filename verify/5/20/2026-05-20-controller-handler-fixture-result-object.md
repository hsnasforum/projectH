# 2026-05-20 controller handler fixture result object 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-handler-fixture-result-object.md`
- `tests/test_controller_server.py`의 `_HandlerFixture`
- `ControllerAssetResolutionTests._response_handler`
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`
- `test_do_get_dispatches_real_controller_queue_js_assets`
- `test_do_get_dispatches_controller_shell_routes_to_html`

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 사용 skill
- `round-handoff`: 최신 `/work`의 주장과 현재 코드/검증 결과를 대조하고 `/verify` 기록을 남기기 위해 사용했다.
- `next-slice-triage`: advisory 비활성 조건에서 검증 이후 하나의 안전한 다음 implement slice로 수렴하기 위해 사용했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 48 tests 통과.
- `rg -n "_HandlerFixture|_response_handler|ended\\[0\\]|handler, _, _, _|tuple\\[controller_server\\.ControllerHandler|list\\[int\\]" tests/test_controller_server.py`
  - `_HandlerFixture`와 named fixture 사용만 확인되며, `ended[0]`, `handler, _, _, _`, raw tuple return annotation, `list[int]` counter hit는 없었다.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `_response_handler()`는 더 이상 raw positional 4-tuple 또는 mutable `list[int]` end counter를 반환하지 않고 `_HandlerFixture`를 반환한다.
- `_HandlerFixture`는 fake `ControllerHandler`, responses, header pairs, end-header count, body access를 이름 있는 field/property로 보관한다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`는 named fixture fields/properties를 사용하지만 기존 public helper return shape인 `(responses, headers_dict, body_bytes, ended_int)`를 유지한다.
- dispatch-only tests는 tuple unpacking 대신 `fixture.handler`를 사용하며 `_serve_controller_asset`와 `_serve_html` delegate-call assertions는 유지되어 있다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2058`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_unknown_route_fail_closed_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2059`
- `EVIDENCE: work/5/20/2026-05-20-controller-handler-fixture-result-object.md`, `verify/5/20/2026-05-20-controller-handler-fixture-result-object.md`, `tests/test_controller_server.py`, `controller/server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free controller route test guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, `controller/server.py`, `tests/test_controller_server.py` 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 unknown GET/POST controller routes가 controller shell, asset handler, runtime action으로 오인되지 않고 JSON 404로 fail closed 되는 동작을 `ControllerAssetResolutionTests`의 named fixture helpers로 고정하는 것이다. 이 slice는 shipped local controller route surface를 보호하며 생산 코드를 건드리지 않고 현재 contract를 테스트로 잠근다.
