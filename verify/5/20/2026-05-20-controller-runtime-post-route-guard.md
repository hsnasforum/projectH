# 2026-05-20 controller runtime POST route guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-runtime-post-route-guard.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests._json_post_response`
- `tests/test_controller_server.py`의 `test_do_post_runtime_start_route_returns_json_payload`
- `tests/test_controller_server.py`의 `test_do_post_runtime_stop_route_returns_json_payload`
- `tests/test_controller_server.py`의 `test_do_post_runtime_restart_route_returns_json_payload`
- `tests/test_controller_server.py`의 `test_do_post_send_input_route_parses_json_payload`
- `tests/test_controller_server.py`의 `test_do_post_send_input_rejects_invalid_json`
- `controller/server.py`의 `ControllerHandler.do_POST()` runtime action route 경로

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 44 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `ControllerAssetResolutionTests._json_post_response`는 fake `ControllerHandler`, `io.BytesIO` rfile/wfile, captured `send_response` / `send_header`, minimal `headers`를 사용해 server socket 없이 `ControllerHandler.do_POST()`를 호출한다.
- `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart` test는 각각 `pipeline_start()`, `pipeline_stop()`, `pipeline_restart()`를 mock하고, route가 `HTTPStatus.OK`, `Content-Type: application/json`, 정확한 `Content-Length`, `Access-Control-Allow-Origin: *`, preserved body payload를 반환하는지 확인한다.
- `/api/runtime/send-input` test는 JSON body `{"lane": "Codex", "text": "hello"}`가 `runtime_send_input(lane="Codex", text="hello")`로 전달되고 helper payload/status가 보존되는지 확인한다.
- malformed `/api/runtime/send-input` body test는 `HTTPStatus.BAD_REQUEST` JSON `{"ok": False, "error": "invalid json"}` 응답과 `runtime_send_input()` 미호출을 확인한다.
- `controller/server.py` 생산 코드는 이번 구현 라운드에서 수정되지 않았고, 실제 runtime start/stop/restart/send-input 동작도 실행되지 않았다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2052`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: same_family_controller_action_client_contract_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2053`
- `EVIDENCE: work/5/20/2026-05-20-controller-runtime-post-route-guard.md`, `verify/5/20/2026-05-20-controller-runtime-post-route-guard.md`, `tests/test_controller_server.py`, `controller/js/cozy.js`, `controller/js/panel.js`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 socket-free source/test guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 코드/검증 증거만으로 같은 family의 다음 안전 slice를 좁힐 수 있다.
- `REJECTED: more handler route micro-guards` - unknown route나 non-object JSON 같은 추가 branch만 고정하는 것은 현재 shipped UI contract 보호보다 내부 completeness 성격이 강하다.
- 다음 안전한 local slice는 server-side POST route guard와 맞물려, controller UI clients가 runtime action routes를 올바른 POST/JSON request shape로 호출하는지 source-level unit guard로 고정하는 것이다. 특히 `controller/js/cozy.js`의 `apiPost()` start/stop/restart POST method, `sendModalInput()`의 `/api/runtime/send-input` JSON body, `controller/js/panel.js`의 `sendInput()` JSON body를 기존 source-string test 스타일로 확인한다.
