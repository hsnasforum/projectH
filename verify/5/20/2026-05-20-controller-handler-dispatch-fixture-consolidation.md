# 2026-05-20 controller handler dispatch fixture consolidation 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-handler-dispatch-fixture-consolidation.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests._response_handler`
- `test_do_get_dispatches_real_controller_queue_js_assets`
- `test_do_get_dispatches_controller_shell_routes_to_html`

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
- `test_do_get_dispatches_real_controller_queue_js_assets`는 inline `object.__new__(ControllerHandler)`와 `handler.path` 설정을 제거하고 `_response_handler(path=f"/controller-assets/{rel_path}")`를 사용한다.
- `test_do_get_dispatches_controller_shell_routes_to_html`도 inline fake handler setup 대신 `_response_handler(path=path)`를 사용한다.
- `_serve_controller_asset`와 `_serve_html` delegate-call assertions는 유지되어 있다.
- `_asset_response`, `_html_response`, `_json_route_response`, `_json_post_response`의 response/header/body/end-header assertions와 반환 형태는 이번 구현 라운드에서 바뀌지 않았다.
- 생산 코드(`controller/server.py`, `controller/index.html`, `controller/js/*.js`)는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2057`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_handler_fixture_result_object`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2058`
- `EVIDENCE: work/5/20/2026-05-20-controller-handler-dispatch-fixture-consolidation.md`, `verify/5/20/2026-05-20-controller-handler-dispatch-fixture-consolidation.md`, `tests/test_controller_server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free test fixture cleanup이라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, 테스트 코드 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 `ControllerAssetResolutionTests`의 `_response_handler()` 반환값을 위치 기반 4-tuple과 `list[int]` end counter에서 작은 로컬 fixture/result 객체로 바꾸는 것이다. 현재 shared setup은 완성됐지만 helper callers가 `handler, _, _, _` 또는 `ended[0]`에 의존해 fixture state를 위치로 해석한다. 이 cleanup은 controller route/header/body contract tests의 fixture drift risk를 줄이며, 생산 코드는 건드리지 않고 기존 assertions를 유지한다.
