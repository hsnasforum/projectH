# 2026-05-20 controller send-input empty body guard 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-empty-body-guard.md`
- `tests/test_controller_server.py`의 `test_do_post_send_input_rejects_empty_body_payload`

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
  - 통과. `Ran 58 tests in 0.052s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "test_do_post_send_input|_json_post_response|runtime_send_input|backend_runtime_send_input" tests/test_controller_server.py controller/server.py`
  - `/api/runtime/send-input` route tests가 valid dict JSON, backend failure, empty body, missing `lane`, blank `text`, malformed JSON syntax, malformed UTF-8 body, invalid/negative `Content-Length`, non-object JSON, unknown POST route를 고정하고 있음을 확인했다.

## 판단
- 최신 `/work`의 변경 주장은 현재 코드와 일치한다.
- `test_do_post_send_input_rejects_empty_body_payload`는 `_json_post_response("/api/runtime/send-input")` 기본 body 경로가 `HTTPStatus.BAD_REQUEST`, `{"ok": False, "error": "lane is required"}`로 닫히고 `backend_runtime_send_input`을 호출하지 않는 점을 고정한다.
- 이 경로는 `ControllerHandler.do_POST`가 `content_length <= 0`일 때 `b"{}"`를 payload로 사용하고, 실제 `runtime_send_input(...)` wrapper validation을 거쳐 `lane is required`를 반환하는 현재 구현과 맞다.
- 전체 `tests.test_controller_server` 실행에서 기존 valid dict JSON, backend failure, missing `lane`, blank `text`, malformed JSON body, malformed UTF-8 body, invalid/negative `Content-Length`, non-object JSON, unknown POST route 테스트도 함께 통과했다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller POST empty-body route test에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_send_input_route_test_consolidation`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2067`
- `EVIDENCE: tests/test_controller_server.py`에는 같은 `/api/runtime/send-input` route 계약을 고정하는 socket-free tests가 누적되어 있고, 여러 invalid request cases가 같은 expected payload, non-call assertion, `_assert_json_response(...)` 패턴을 반복한다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: another send-input micro-case` - 현재 주요 fail-closed route cases는 고정되었고, 같은 endpoint의 개별 case를 더 쪼개는 것보다 테스트 반복을 정리해 향후 계약 drift 위험을 줄이는 편이 더 coherent하다.
- 다음 safe local slice는 `ControllerAssetResolutionTests`의 `/api/runtime/send-input` route tests에 작은 shared helper를 추가해 repeated JSON body encoding, invalid response assertion, backend/runtime non-call assertion을 줄이되, 기존 test names와 covered behavior를 보존하는 것이다.
