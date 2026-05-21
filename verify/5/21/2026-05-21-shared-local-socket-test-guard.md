# 2026-05-21 shared local socket test guard 검증

## 검증 대상

- `work/5/21/2026-05-21-shared-local-socket-test-guard.md`
- `verify/5/21/2026-05-21-web-app-local-socket-test-guard.md`
- `.pipeline/implement_handoff.md#2076`

## 변경 파일

- `verify/5/21/2026-05-21-shared-local-socket-test-guard.md`
- 이 검증 단계는 코드, 테스트, 제품 문서, `/work`, `.pipeline/operator_request.md`, `.pipeline/advisory_request.md`를 수정하지 않았고 이 `/verify` 기록만 추가했다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 직전 `/verify`, 현재 테스트 파일, 실제 재실행 결과와 대조하는 데 사용했다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤 advisory 비활성 조건에서 다음 safe local slice를 고르는 데 사용했다.

## 실행한 확인

- `python3 -m py_compile tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py`
  - 통과. 출력 없이 종료했다.
- `sed -n '1,140p' tests/local_socket_guard.py`
  - 통과. shared helper가 `127.0.0.1:0` bind probe, `requires_local_loopback_socket`, `skip_unless_local_loopback_socket()`를 제공하는 것을 확인했다.
- `sed -n '1,120p' tests/test_http_integration.py`
  - 통과. `HTTPIntegrationBase.setUp()` 초입에서 `skip_unless_local_loopback_socket(self)`를 호출하고, 이후 기존 `LocalOnlyHTTPServer(("127.0.0.1", 0), self.service)` setup을 유지하는 것을 확인했다.
- `rg -n "local_loopback_socket|requires_local_loopback_socket|skip_unless_local_loopback_socket|LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)" tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py`
  - 통과. `tests/test_web_app.py`는 shared decorator를 import하고 13개 direct server tests에 guard를 유지한다. `tests/test_http_integration.py`는 shared skip helper를 `setUp()`에서 사용한다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_http_payload_exposes_transition_mutation_identity_requirement tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_to_service tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_empty_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_json_syntax_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_utf8_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_non_object_json_request_body tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`
  - 통과. `Ran 13 tests in 0.411s`, `OK`.
- `python3 -m unittest -v tests.test_http_integration`
  - 통과. `Ran 25 tests in 12.666s`, `OK`.
  - 실행 중 `ResourceWarning: unclosed <socket.socket ...>` 경고가 여러 번 재현됐다. 이는 `/work`의 남은 리스크와 일치하며, 현재 slice의 no-socket guard consolidation 자체를 실패시키지는 않는다.
- `git diff --check -- tests/test_web_app.py tests/test_http_integration.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md`
  - 통과. 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null tests/local_socket_guard.py`
  - 통과. `--no-index` 특성상 diff-present로 exit code 1을 반환했지만 출력은 없었고, untracked helper 파일의 공백 오류는 없었다.
- `git status --short -- tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py work/5/21/ verify/5/21/ .pipeline/implement_handoff.md .pipeline/operator_request.md .pipeline/advisory_request.md`
  - 확인. 관련 dirty state는 `tests/test_http_integration.py`, `tests/test_web_app.py`, `tests/local_socket_guard.py`, `work/5/21/`, `verify/5/21/`에 한정된다. advisory/operator control 파일은 이번 검증에서 수정하지 않았다.

## 판단

- 최신 `/work`의 핵심 주장은 현재 코드와 검증 결과에 부합한다.
- `tests/test_web_app.py`의 파일-local loopback socket guard는 shared helper import로 대체됐고, 13개 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` tests는 같은 guard 아래에 남아 있다.
- `tests/test_http_integration.py`는 socket-bound server setup 전에 shared `skip_unless_local_loopback_socket(self)`를 호출하므로 no-socket 환경에서 setup `PermissionError` 대신 명시적 unittest skip으로 닫히는 구조가 됐다.
- production `LocalOnlyHTTPServer`, HTTP response shape, reviewed-memory behavior, product docs는 변경되지 않았다.
- 현재 환경에서는 loopback socket이 가능해 guarded tests가 실제 assertions까지 실행됐다. no-socket 환경의 skip branch는 코드 경로로 확인했지만 별도 sandbox 모드 전환으로 강제 재현하지는 않았다.
- `RUNTIME_STATUS_AT_DISPATCH`는 `runtime_state: RUNNING`, `automation_health: recovering`, `automation_next_action: retrying`이므로 runtime liveness 판단에는 dispatcher surface를 authoritative로 사용했다. lane-local `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.

## 실행하지 않은 확인

- Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 검사는 실행하지 않았다.
- release-ready, full-smoke-pass, publication-ready는 주장하지 않는다.
- `python3 -W error::ResourceWarning -m unittest ...`는 이번 verify의 완료 판정에는 실행하지 않았다. `tests.test_http_integration` 일반 실행에서 이미 unclosed socket `ResourceWarning`이 재현되어 다음 local cleanup slice의 근거로 충분하다고 판단했다.

## 남은 확인과 위험

- `tests.test_http_integration`은 통과하지만 `ResourceWarning: unclosed <socket.socket ...>` 경고를 출력한다. `HTTPIntegrationBase.tearDown()`이 `shutdown()`과 thread join 뒤 server socket까지 닫지 않는 cleanup gap으로 보이며, 같은 socket test hygiene family의 다음 local risk reduction이다.
- dirty bundle은 계속 크고 publication은 operator decision `HOLD_PUBLICATION` 상태다. commit, push, branch/PR publish, merge는 수행하지 않았다.

## 다음 control 판단

- `COUNCIL_DECISION: implement`
- `REASON_CODE: http_integration_server_close_guard`
- `OWNER_ROLE: implement`
- `NEXT_CONTROL_FILE: .pipeline/implement_handoff.md`
- `NEXT_CONTROL_SEQ: 2077`
- `EVIDENCE: work/5/21/2026-05-21-shared-local-socket-test-guard.md`
- `EVIDENCE: verify/5/21/2026-05-21-shared-local-socket-test-guard.md`
- `EVIDENCE: tests/test_http_integration.py`
- `REJECTED: operator_request` - dispatcher runtime surface는 running/recovering이며, 남은 일은 test-only HTTP integration cleanup이다. destructive write, credential/auth, approval-record repair, truth-sync blocker, external publication, merge, immediate safety stop이 아니다.
- `REJECTED: advisory_request` - `ADVISORY_ENABLED: false`이며 current evidence에서 next safe local slice가 결정된다.
- 다음 safe local slice는 `tests/test_http_integration.py`의 `HTTPIntegrationBase.tearDown()`에서 `LocalOnlyHTTPServer` socket을 명시적으로 닫아 unclosed socket `ResourceWarning`을 제거하고, `ResourceWarning`을 error로 승격한 targeted unittest로 확인하는 것이다.
