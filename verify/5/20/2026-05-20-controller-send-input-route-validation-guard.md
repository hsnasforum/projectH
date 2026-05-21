# 2026-05-20 controller send-input route validation guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-route-validation-guard.md`
- `tests/test_controller_server.py`의 `/api/runtime/send-input` missing `lane` 및 blank `text` route-level validation tests

## 변경 파일
- 없음
- 이 검증 단계는 코드와 테스트를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` 주장을 현재 코드와 좁은 검증으로 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 맞는 상태에서 advisory/operator 없이 이어갈 수 있는 한 가지 다음 slice를 고르는 데 사용했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 55 tests in 0.046s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "failed to send input|BAD_GATEWAY|UnicodeDecodeError|utf|decode\(" controller/server.py tests/test_controller_server.py`
  - `runtime_send_input`에는 backend send 실패 시 `HTTPStatus.BAD_GATEWAY`와 `{"ok": False, "error": "failed to send input"}`를 반환하는 경로가 있다.
  - 현재 tests에는 `failed to send input` 또는 `BAD_GATEWAY`를 고정하는 테스트가 없다.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_post_send_input_rejects_missing_lane_payload`는 `{"text": "hello"}` route payload가 `HTTPStatus.BAD_REQUEST`, `{"ok": False, "error": "lane is required"}`로 닫히고 `backend_runtime_send_input`을 호출하지 않는 점을 확인한다.
- `test_do_post_send_input_rejects_blank_text_payload`는 `{"lane": "Codex", "text": "   "}` route payload가 `HTTPStatus.BAD_REQUEST`, `{"ok": False, "error": "text is required"}`로 닫히고 `backend_runtime_send_input`을 호출하지 않는 점을 확인한다.
- 전체 `tests.test_controller_server` 실행에서 기존 valid dict JSON, malformed JSON body, invalid/negative `Content-Length`, non-object JSON, unknown POST route, controller shell/source contract 테스트도 함께 통과했다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller POST route test에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_backend_failure_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2064`
- `EVIDENCE: controller/server.py`에는 `backend_runtime_send_input`이 `False`를 반환할 때 `/api/runtime/send-input` wrapper가 JSON 502 `failed to send input`으로 닫히는 경로가 있지만, 현재 tests에는 이 실패 경로가 명시적으로 고정되어 있지 않다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: malformed UTF-8 route guard` - 같은 endpoint의 fail-closed 후보지만, backend send 실패 전파가 실제 사용자 입력 전송 실패를 더 직접적으로 보호하는 current-risk reduction이다.
- 다음 safe local slice는 valid `/api/runtime/send-input` route payload가 backend send 실패를 JSON 502 `failed to send input`으로 전파하는 계약을 socket-free 테스트로 고정하는 것이다.
