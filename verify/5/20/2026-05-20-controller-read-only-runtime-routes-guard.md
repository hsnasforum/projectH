# 2026-05-20 controller read-only runtime routes guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-read-only-runtime-routes-guard.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests._json_route_response`
- `tests/test_controller_server.py`의 `test_do_get_monitor_snapshot_route_returns_json_payload`
- `tests/test_controller_server.py`의 `test_do_get_agent_inspector_route_returns_json_payload`
- `tests/test_controller_server.py`의 `test_do_get_capture_tail_route_returns_json_payload`
- `controller/server.py`의 `ControllerHandler.do_GET()` read-only runtime GET route 경로

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 39 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `ControllerAssetResolutionTests._json_route_response`는 fake `ControllerHandler`, `io.BytesIO` wfile, captured `send_response` / `send_header`를 사용해 server socket 없이 `ControllerHandler.do_GET()`을 호출한다.
- `/api/runtime/monitor-snapshot` test는 `runtime_monitor_snapshot()`를 mock하고, route가 `HTTPStatus.OK`, `Content-Type: application/json`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`, preserved body payload를 반환하는지 확인한다.
- `/api/runtime/agent-inspector?agent=Codex&lines=77` test는 `runtime_agent_inspector(agent="Codex", lines=77)` 호출과 helper payload/status 보존을 확인한다.
- `/api/runtime/capture-tail?lane=Codex&lines=40` test는 `runtime_capture_tail(lane="Codex", lines=40)` 호출과 helper payload/status 보존을 확인한다.
- `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2051`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: same_family_controller_post_route_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2052`
- `EVIDENCE: work/5/20/2026-05-20-controller-read-only-runtime-routes-guard.md`, `verify/5/20/2026-05-20-controller-read-only-runtime-routes-guard.md`, `controller/server.py`, `controller/js/cozy.js`, `tests/test_controller_server.py`
- `REJECTED: operator_request` - 실제 runtime start/stop 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 test-only local guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 코드/검증 증거만으로 같은 family의 다음 안전 slice를 좁힐 수 있다.
- 다음 안전한 local slice는 server socket 없이 `ControllerHandler.do_POST()`의 controller runtime action routes(`/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart`, `/api/runtime/send-input`)가 helper payload/status와 JSON parsing contract를 보존하는지 고정하는 bounded POST route guard bundle이다. 이 slice는 실제 runtime start/stop을 실행하지 않고 helper mock과 fake handler만 사용해야 한다.
