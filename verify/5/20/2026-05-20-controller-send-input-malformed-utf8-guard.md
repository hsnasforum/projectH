# 2026-05-20 controller send-input malformed utf8 guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-malformed-utf8-guard.md`
- `tests/test_controller_server.py`의 `test_do_post_send_input_rejects_malformed_utf8_body`

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
  - 통과. `Ran 57 tests in 0.052s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "empty|Content-Length.*0|body = b\"\"|lane is required|text is required|test_do_post_send_input" tests/test_controller_server.py controller/server.py`
  - 현재 `/api/runtime/send-input` route-level 테스트는 valid dict JSON, backend failure, missing `lane`, blank `text`, malformed JSON syntax, malformed UTF-8 body, invalid/negative `Content-Length`, non-object JSON, unknown POST route를 고정한다.
  - empty body 또는 `Content-Length: 0` 분기에서 backend send가 발생하지 않는다는 route-level 테스트는 아직 없다.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_post_send_input_rejects_malformed_utf8_body`는 malformed UTF-8 body `b"\xff\xfe"`가 `HTTPStatus.BAD_REQUEST`, `{"ok": False, "error": "invalid json"}`로 닫히고 `runtime_send_input`을 호출하지 않는 점을 고정한다.
- 전체 `tests.test_controller_server` 실행에서 기존 valid dict JSON, missing `lane`, blank `text`, backend failure, malformed JSON body, invalid/negative `Content-Length`, non-object JSON, unknown POST route 테스트도 함께 통과했다.
- `ControllerHandler.do_POST`의 `/api/runtime/send-input` parsing은 `content_length > 0`일 때만 body를 읽고, 0이면 `b"{}"`를 payload로 사용한다. 이 경로는 wrapper validation을 거쳐 `lane is required`로 닫히지만 현재 route-level 테스트로 직접 고정되어 있지 않다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller POST request-body failure-path test에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_empty_body_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2066`
- `EVIDENCE: controller/server.py`의 `/api/runtime/send-input` parsing은 `Content-Length: 0` 또는 empty body를 `b"{}"`로 처리해 wrapper validation으로 보내지만, 현재 tests에는 empty body가 JSON 400 `lane is required`로 닫히고 backend send를 호출하지 않는다는 route-level 테스트가 없다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: Playwright/full-smoke` - local socket guard 환경 제약을 해소하지 않았고 release-ready를 주장하지 않는다.
- 다음 safe local slice는 `/api/runtime/send-input`의 empty body 또는 `Content-Length: 0` 요청이 JSON 400 `lane is required`로 닫히고 `backend_runtime_send_input`을 호출하지 않는 계약을 socket-free 테스트로 고정하는 것이다.
