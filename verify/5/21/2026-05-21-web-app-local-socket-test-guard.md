# 2026-05-21 web app local socket test guard 검증

## 검증 대상

- `work/5/21/2026-05-21-web-app-local-socket-test-guard.md`
- `verify/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
- `.pipeline/implement_handoff.md#2075`

## 변경 파일

- `verify/5/21/2026-05-21-web-app-local-socket-test-guard.md`
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`, `.pipeline/operator_request.md`, `.pipeline/advisory_request.md`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 코드/test truth 및 직전 `/verify`와 대조하고 다음 control 전 `/verify`를 남기는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory 비활성 조건에서 다음 safe local slice를 고르는 데 사용했다.

## 실행한 확인

- `sed -n '1,260p' work/5/21/2026-05-21-web-app-local-socket-test-guard.md`
  - 통과. 최신 `/work`는 `tests/test_web_app.py`의 test-only loopback socket guard와 13개 HTTP handler test decorator 적용을 기록한다.
- `sed -n '1,260p' verify/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
  - 통과. 직전 `/verify`는 `tests/test_web_app.py`의 13개 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 테스트가 no-socket 환경에서 실패하던 문제를 다음 slice로 지정했다.
- `sed -n '1,140p' tests/test_web_app.py`
  - 통과. `socket` import, `_local_loopback_socket_available()`, `_requires_local_loopback_socket`가 test helper 구역에 추가된 것을 확인했다.
- `rg -n "_requires_local_loopback_socket|LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)" tests/test_web_app.py`
  - 통과. direct `LocalOnlyHTTPServer` 생성 지점 13개와 대응 decorator 13개를 확인했다.
- `python3 -m py_compile tests/test_web_app.py`
  - 통과. 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_http_payload_exposes_transition_mutation_identity_requirement tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_to_service tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_empty_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_json_syntax_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_utf8_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_non_object_json_request_body tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`
  - 통과. 현재 실행 환경에서는 socket bind가 가능해 `Ran 13 tests in 0.572s`, `OK`로 실제 HTTP handler assertions까지 실행됐다.
- `rg -n "Ran 1086|OK \\(skipped=13\\)|local loopback socket unavailable|PermissionError|FAILED" /tmp/projecth-unit-2075.log /tmp/projecth-unit-2074.log`
  - 통과. #2074 로그의 13개 `PermissionError` 실패와 #2075 로그의 `OK (skipped=13)` 및 `local loopback socket unavailable in this environment` skip reason을 대조했다.
- `git diff --check -- tests/test_web_app.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md`
  - 통과.
- `rg -n "LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)|_requires_local_loopback_socket|_local_loopback_socket_available" tests`
  - 확인. `tests/test_web_app.py` direct server cases는 guard 아래에 있고, `tests/test_http_integration.py`의 `HTTPIntegrationBase.setUp`에는 아직 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), self.service)`가 남아 있다.

## 판단

- 최신 `/work`의 핵심 주장은 현재 코드와 검증 결과에 부합한다.
- `tests/test_web_app.py`의 13개 direct HTTP handler tests는 socket-capable 환경에서는 계속 실제 assertion을 실행하고, no-socket aggregate 환경에서는 명시적 reason으로 skip된다.
- 이번 변경은 test-only이며 production `LocalOnlyHTTPServer`, HTTP response shape, reviewed-memory behavior를 변경하지 않았다.
- 다만 local socket guard가 `tests/test_web_app.py` 안에 파일-local helper로 남아 있고, `tests/test_http_integration.py`에도 동일한 socket-bound `LocalOnlyHTTPServer` bootstrap이 남아 있다. 같은 incident family의 재발 방지를 위해 shared test helper로 모으는 후속 slice가 명확하다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인

- 전체 #2074 aggregate command는 재실행하지 않았다. 이번 verify에서는 변경 파일과 claim을 검증하는 가장 좁은 범위로 `py_compile`, 13개 targeted unittest, 기존 aggregate log 대조, diff hygiene를 실행했다.
- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.
- release-ready, full-smoke-pass, publication-ready는 주장하지 않는다.

## 남은 확인과 위험

- `tests/test_http_integration.py`의 HTTP integration base는 아직 no-socket sandbox에서 직접 socket 생성 실패에 노출될 수 있다.
- `tests/test_web_app.py`와 `tests/test_http_integration.py`가 각자 별도 guard를 갖게 되면 향후 reason 문자열이나 probe 방식이 갈라질 수 있다.
- dirty bundle은 계속 크고 publication은 operator decision `HOLD_PUBLICATION` 상태다. commit, push, branch/PR publish, merge는 수행하지 않았다.

## 다음 control 판단

- `COUNCIL_DECISION: implement`
- `REASON_CODE: shared_local_socket_test_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2076`
- `EVIDENCE: work/5/21/2026-05-21-web-app-local-socket-test-guard.md`
- `EVIDENCE: verify/5/21/2026-05-21-web-app-local-socket-test-guard.md`
- `EVIDENCE: tests/test_web_app.py`
- `EVIDENCE: tests/test_http_integration.py`
- `REJECTED: operator_request` - dispatcher runtime surface는 running/recovering이며, 남은 일은 test-only local guard consolidation이다. destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 current evidence에서 next safe local slice가 결정된다.
- `REJECTED: rerun_full_aggregate_only` - aggregate는 #2075에서 `OK (skipped=13)`으로 닫혔고, 같은 guard family의 잔여 risk는 `tests/test_http_integration.py`와 helper duplication에 있다.
- 다음 safe local slice는 `tests/test_web_app.py`의 파일-local loopback socket guard를 shared test helper로 옮기고 `tests/test_http_integration.py`의 `HTTPIntegrationBase`에도 동일 guard를 적용해 같은 no-socket environment-held failure family를 한 helper로 닫는 것이다.
