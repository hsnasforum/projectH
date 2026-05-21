# 2026-05-20 controller send-input negative content length guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-negative-content-length-guard.md`
- `controller/server.py`의 `/api/runtime/send-input` `Content-Length` parsing
- `tests/test_controller_server.py`의 `test_do_post_send_input_rejects_negative_content_length`

## 변경 파일
- 없음
- 이 검증 단계는 코드와 테스트를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` 주장을 코드와 좁은 검증으로 대조하고 다음 control 전 `/verify`를 남기는 절차에 사용했다.
- `next-slice-triage`: 현재 검증 truth에서 operator/advisory 없이 이어갈 수 있는 한 가지 다음 slice를 고르는 데 사용했다.

## 실행한 확인
- `python3 -m py_compile controller/server.py tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 53 tests in 0.063s`, `OK`.
- `git diff --check -- controller/server.py tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "test_do_post_send_input|lane is required|text is required|backend_runtime_send_input|negative_content_length|non_object_json" tests/test_controller_server.py controller/server.py`
  - `runtime_send_input`의 missing lane/text 검증과 route-level valid/invalid JSON, non-integer `Content-Length`, negative `Content-Length`, non-object JSON 테스트를 확인했다.
  - route-level dict payload에서 missing `lane` 또는 blank `text`를 고정하는 테스트는 아직 별도로 없다.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `controller/server.py`는 `/api/runtime/send-input`에서 `Content-Length`를 정수로 파싱한 뒤 `content_length < 0`이면 `ValueError`를 발생시켜 기존 invalid JSON JSON 400 경로로 보낸다.
- `test_do_post_send_input_rejects_negative_content_length`는 negative `Content-Length` 요청이 `HTTPStatus.BAD_REQUEST`, payload `{"ok": False, "error": "invalid json"}`를 반환하고 `runtime_send_input`을 호출하지 않는다는 점을 socket-free 방식으로 고정한다.
- 기존 valid dict JSON, malformed JSON body, non-integer `Content-Length`, non-object JSON, unknown POST route 테스트도 같은 단위 테스트 실행에서 유지됐다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 controller POST header parsing과 socket-free unit coverage에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_route_validation_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2063`
- `EVIDENCE: runtime_send_input`는 missing lane/text를 backend 호출 전에 검증하지만, `/api/runtime/send-input` route-level dict payload에서 missing `lane` 또는 blank `text`가 같은 JSON 400 계약으로 닫히고 `backend_runtime_send_input`을 호출하지 않는다는 테스트가 아직 없다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- 다음 safe local slice는 `/api/runtime/send-input`의 route-level missing `lane` 및 blank `text` 검증을 한 묶음으로 고정하는 것이다.
