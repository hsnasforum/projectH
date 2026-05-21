# 2026-05-20 controller send-input invalid content length guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-invalid-content-length-guard.md`
- `controller/server.py`의 `/api/runtime/send-input` `Content-Length` parsing
- `tests/test_controller_server.py`의 `test_do_post_send_input_rejects_invalid_content_length`
- `ControllerAssetResolutionTests._response_handler`
- `ControllerAssetResolutionTests._json_post_response`

## 변경 파일
- 없음. 이 기록은 검증 노트 추가만 수행했다.

## 사용 skill
- `round-handoff`: 최신 `/work`의 주장과 현재 코드/검증 결과를 대조하고 `/verify` 기록을 남기기 위해 사용했다.
- `next-slice-triage`: advisory 비활성 조건에서 검증 이후 하나의 안전한 다음 implement slice로 수렴하기 위해 사용했다.

## 실행한 확인
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 51 tests 통과.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `controller/server.py`는 `/api/runtime/send-input`에서 `Content-Length` 정수 변환을 request body JSON parsing `try` block 안에서 수행한다.
- 같은 `except`가 `ValueError`를 포함하므로 non-integer `Content-Length`는 기존 bad request JSON shape인 `{"ok": False, "error": "invalid json"}`와 `HTTPStatus.BAD_REQUEST`로 닫힌다.
- `test_do_post_send_input_rejects_invalid_content_length`는 invalid `Content-Length`가 JSON 400을 반환하고 `runtime_send_input`을 호출하지 않는지 검증한다.
- `_response_handler`와 `_json_post_response`는 named fixture pattern과 기존 public helper return shape를 유지하면서 header override만 지원한다.
- 기존 valid JSON, malformed JSON body, unknown POST, route, asset, header, body, dispatch assertions는 유지되어 있다.
- 이번 verify 지시의 `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state=RUNNING`, `automation_health=recovering`, `automation_next_action=retrying`, active control `.pipeline/implement_handoff.md#2060`, `turn_state=IDLE`, `active_round=VERIFY_PENDING`로 주어졌다. 따라서 lane-local `status --json`, `doctor --json`, `tmux` 명령은 런타임 생존성 판단에 사용하지 않았다.

## 남은 확인
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 이번 work 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 `local_socket_guard_auto_held` 상태가 남아 있다. 이번 검증은 controller-smoke pass, full-smoke pass, release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 verify에서는 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_non_object_json_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2061`
- `EVIDENCE: work/5/20/2026-05-20-controller-send-input-invalid-content-length-guard.md`, `verify/5/20/2026-05-20-controller-send-input-invalid-content-length-guard.md`, `tests/test_controller_server.py`, `controller/server.py`
- `REJECTED: operator_request` - 실제 runtime action 실행, release, publication, auth/credential, destructive action, approval/truth-sync repair가 아니며 local controller POST payload-shape guard라 operator-only boundary가 아니다.
- `REJECTED: advisory_request` - advisory가 비활성화되어 있고, 현재 `/work`, `/verify`, `controller/server.py`, `tests/test_controller_server.py` 증거만으로 다음 안전한 local slice를 결정할 수 있다.
- `REJECTED: Playwright/full-smoke rerun` - 같은 family의 local socket guard가 보류 상태이고 이번 검증은 release readiness를 주장하지 않으므로 동일한 full-smoke handoff를 재발행하지 않는다.
- 다음 안전한 local slice는 `/api/runtime/send-input` POST에서 syntactically valid JSON이지만 object가 아닌 payload, 예를 들어 JSON array, 를 받았을 때 `runtime_send_input`을 호출하지 않고 기존 invalid JSON 계약과 같은 JSON 400으로 닫히는 동작을 socket-free test로 고정하는 것이다. 현재 `controller/server.py`에는 `if not isinstance(payload, dict)` branch가 있지만 해당 branch는 `ControllerAssetResolutionTests`에서 직접 고정되어 있지 않다.
