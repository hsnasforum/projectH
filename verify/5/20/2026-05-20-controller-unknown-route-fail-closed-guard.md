# 2026-05-20 controller unknown route fail-closed guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-unknown-route-fail-closed-guard.md`
- `tests/test_controller_server.py`의 `test_do_get_unknown_runtime_route_returns_json_404`
- `tests/test_controller_server.py`의 `test_do_post_unknown_runtime_route_returns_json_404`
- `controller/server.py`의 unknown `do_GET` / `do_POST` JSON 404 fallback

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 사용 skill
- `round-handoff`: 최신 `/work`의 주장과 현재 코드/검증 결과를 대조하고 `/verify` 기록을 남기기 위해 사용했다.
- `next-slice-triage`: advisory 비활성 조건에서 검증 이후 하나의 안전한 다음 implement slice로 수렴하기 위해 사용했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 50 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_get_unknown_runtime_route_returns_json_404`는 `/api/runtime/not-real` GET 요청이 `HTTPStatus.NOT_FOUND`와 `{"error": "not found"}` JSON payload를 반환하는지 검증한다.
- `test_do_post_unknown_runtime_route_returns_json_404`는 같은 unknown POST route의 JSON 404 fail-closed 계약을 검증한다.
- 두 테스트는 `_json_route_response`, `_json_post_response`, `_assert_json_response`를 사용해 JSON headers, `Content-Length`, CORS header, body bytes, end-header count를 기존 named fixture helper 경로로 확인한다.
- `controller/server.py`의 unknown `do_GET` / `do_POST` fallback은 현재 `self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)`로 유지되어 있으며, 이번 구현 라운드에서 생산 코드는 수정되지 않았다.
- 기존 known route, asset, header, body, dispatch assertions는 유지되어 있다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2059`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_invalid_content_length_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2060`
- `EVIDENCE: work/5/20/2026-05-20-controller-unknown-route-fail-closed-guard.md`, `verify/5/20/2026-05-20-controller-unknown-route-fail-closed-guard.md`, `tests/test_controller_server.py`, `controller/server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 local controller POST parsing fail-closed guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, `controller/server.py`, `tests/test_controller_server.py` 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 `/api/runtime/send-input` POST에서 invalid `Content-Length` header가 들어와도 `ValueError`로 handler를 깨지 않고 기존 invalid JSON 계약과 같은 JSON 400 fail-closed 응답으로 닫히게 하는 것이다. 현재 `controller/server.py`는 `int(self.headers.get("Content-Length") or "0")`를 `try` 밖에서 실행하므로 이 입력이 socket-free handler test로 고정되어 있지 않다.
