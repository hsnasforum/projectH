# 2026-05-20 controller send-input route test consolidation 검증

## 검증 대상
- `work/5/20/2026-05-20-controller-send-input-route-test-consolidation.md`
- `tests/test_controller_server.py`의 `ControllerAssetResolutionTests` send-input route test helper 정리

## 변경 파일
- 없음
- 이 검증 단계는 코드와 테스트를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill
- `round-handoff`: 최신 `/work` 주장을 현재 테스트 코드와 좁은 검증으로 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 맞는 상태에서 advisory/operator 없이 이어갈 수 있는 한 가지 다음 slice를 고르는 데 사용했다.

## 실행한 확인
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 58 tests in 0.044s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/ verify/5/20/`
  - 통과.
- `rg -n "_send_input_body|_assert_send_input_bad_request|json.dumps\\(request\\)|expected = \\{\\\"ok\\\": False, \\\"error\\\": \\\"invalid json\\\"\\}|test_do_post_send_input" tests/test_controller_server.py`
  - `_send_input_body(...)`와 `_assert_send_input_bad_request(...)`가 추가되었고, send-input route test 이름과 covered cases가 유지되는 것을 확인했다.

## 판단
- 최신 `/work`의 변경 주장은 현재 테스트 코드와 일치한다.
- `ControllerAssetResolutionTests`에는 `_send_input_body(...)`가 있어 valid dict JSON request body encoding 반복을 줄이고 있다.
- `_assert_send_input_bad_request(...)`는 send-input invalid request의 공통 `HTTPStatus.BAD_REQUEST` 및 `{"ok": False, "error": <error>}` JSON 응답 assertion을 `_assert_json_response(...)` 위로 모은다.
- success, backend failure, empty body, missing `lane`, blank `text`, malformed JSON, malformed UTF-8, invalid/negative `Content-Length`, non-object JSON 테스트 이름은 유지되어 scenario별 실패 지점이 보존된다.
- 각 테스트의 `runtime_send_input` / `backend_runtime_send_input` patch 대상과 call / non-call assertion도 남아 있다.
- 작업 트리에는 이전 controller route family의 `controller/server.py` 누적 변경이 남아 있다. 이번 `/work`가 주장한 최신 라운드의 의도적 변경 범위는 `tests/test_controller_server.py`와 `/work` closeout이며, 이 검증에서는 해당 범위만 대조했다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 이 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 남은 확인과 위험
- Playwright, full controller smoke, broad e2e, runtime start/stop, long soak은 실행하지 않았다. 이번 변경은 socket-free controller unit test helper 정리에 한정되어 좁은 단위 검증이 충분하다고 판단했다.
- 이전 계열에서 기록된 local socket guard 환경 제약은 해소를 주장하지 않는다. release-ready 또는 full-smoke-pass도 주장하지 않는다.
- 전체 작업 트리는 여러 controller/test/work/verify 누적 변경을 포함한다. 이 검증에서는 기존 변경을 되돌리지 않았다.

## 다음 control 판단
- `COUNCIL_DECISION: implement`
- `REASON_CODE: controller_runtime_json_route_test_consolidation`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2068`
- `EVIDENCE: tests/test_controller_server.py`에는 send-input helper 정리 이후에도 `/api/runtime/status`, `/api/runtime/monitor-snapshot`, `/api/runtime/agent-inspector`, `/api/runtime/capture-tail`, `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart` route tests가 비슷한 mock-return, route execution, `_assert_json_response(...)` 패턴을 반복한다.
- `REJECTED: operator_request` - destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 다음 local slice가 명확하다.
- `REJECTED: another send-input micro-case` - send-input route의 주요 request parsing/fail-closed cases는 이미 고정되었고 helper 정리도 검증되었다. 같은 endpoint의 개별 case를 더 쪼개기보다, 인접 runtime JSON route tests의 반복을 한 번에 줄이는 편이 더 coherent하다.
- 다음 safe local slice는 `ControllerAssetResolutionTests`의 non-send-input runtime JSON route tests에 작은 shared helper를 추가하거나 기존 helper를 재사용해 route response assertion 반복을 줄이되, 기존 test names와 covered route behavior를 보존하는 것이다.
