# 2026-05-20 controller send-input backend failure guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-backend-failure-guard.md`
- `tests/test_controller_server.py`의 `test_do_post_send_input_propagates_backend_failure`

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
  - 통과. `Ran 56 tests in 0.044s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "malformed|utf-8|UnicodeDecodeError|failed to send input|BAD_GATEWAY|backend_failure|propagates_backend_failure" tests/test_controller_server.py controller/server.py`
  - backend send 실패 route-level 테스트와 서버의 `BAD_GATEWAY` 경로를 확인했다.
  - `/api/runtime/send-input`의 malformed UTF-8 body를 직접 고정하는 테스트는 아직 없다.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_post_send_input_propagates_backend_failure`는 valid payload `{"lane": "Codex", "text": "hello"}`가 실제 `runtime_send_input(...)` wrapper를 지나도록 하고, `backend_runtime_send_input`이 `False`를 반환할 때 `HTTPStatus.BAD_GATEWAY`와 `{"ok": False, "error": "failed to send input"}`를 반환하는 점을 고정한다.
- 같은 테스트는 backend helper가 `PROJECT_ROOT`, `SESSION_NAME`, `"Codex"`, `text="hello"`로 한 번 호출되는 점도 확인한다.
- 전체 `tests.test_controller_server` 실행에서 기존 valid dict JSON, missing `lane`, blank `text`, malformed JSON body, invalid/negative `Content-Length`, non-object JSON, unknown POST route 테스트도 함께 통과했다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller POST route failure-path test에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_malformed_utf8_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2065`
- `EVIDENCE: controller/server.py`의 `/api/runtime/send-input` parsing은 `raw.decode("utf-8")`에서 발생하는 `UnicodeDecodeError`를 invalid JSON JSON 400 경로로 처리하지만, 현재 tests에는 malformed UTF-8 body가 이 경로로 닫히고 `runtime_send_input`을 호출하지 않는다는 route-level 테스트가 없다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: commit/push/PR` - implement owner prompt가 publication 작업을 금지하고 이번 변경은 local socket-free test coverage에 한정된다.
- 다음 safe local slice는 `/api/runtime/send-input`의 malformed UTF-8 request body가 JSON 400 `invalid json`으로 닫히고 `runtime_send_input`을 호출하지 않는 계약을 socket-free 테스트로 고정하는 것이다.
