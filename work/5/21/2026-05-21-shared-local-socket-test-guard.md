# 2026-05-21 shared local socket test guard

## 변경 파일

- `tests/local_socket_guard.py`
- `tests/test_web_app.py`
- `tests/test_http_integration.py`
- `work/5/21/2026-05-21-shared-local-socket-test-guard.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2076`은 `tests/test_web_app.py`의 파일-local loopback socket guard를 shared helper로 옮기고, 같은 no-socket 환경 실패군에 노출된 `tests/test_http_integration.py`에도 동일 guard를 적용하도록 요구했다.
- 이전 slice에서 `tests/test_web_app.py`는 no-socket sandbox에서 명시적 skip으로 전환됐지만, `tests/test_http_integration.py`의 `HTTPIntegrationBase.setUp`은 여전히 직접 `LocalOnlyHTTPServer(("127.0.0.1", 0), self.service)`를 생성하고 있었다.
- publication은 계속 `HOLD_PUBLICATION` 상태이며, 이번 라운드는 commit, push, branch/PR publish, merge, release와 무관하다.

## 핵심 변경

- `tests/local_socket_guard.py`를 추가해 `local_loopback_socket_available()`, `requires_local_loopback_socket`, `skip_unless_local_loopback_socket()`를 shared test helper로 제공했다.
- `tests/test_web_app.py`의 file-local `socket` import, `_local_loopback_socket_available()`, `_requires_local_loopback_socket` 정의를 제거하고 shared decorator import로 대체했다.
- `tests/test_web_app.py`의 13개 direct `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 테스트는 기존처럼 guard 아래에 남겼다.
- `tests/test_http_integration.py`의 `HTTPIntegrationBase.setUp` 초입에 `skip_unless_local_loopback_socket(self)`를 적용해 no-socket 환경에서 setup `PermissionError` 대신 같은 skip reason으로 닫히게 했다.
- production `LocalOnlyHTTPServer`, HTTP response shape, reviewed-memory behavior, product docs는 변경하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `80c56156109de1e9db44ddc4274c977cf1ba7c326782798629fc1a1bf9bd14f3`와 일치했다.
- `python3 -m py_compile tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py`
  - 통과: 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_http_payload_exposes_transition_mutation_identity_requirement tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_to_service tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_empty_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_json_syntax_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_utf8_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_non_object_json_request_body tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`
  - 통과: `Ran 13 tests in 0.558s`, `OK`.
- `python3 -m unittest -v tests.test_http_integration`
  - 통과: `Ran 25 tests in 12.685s`, `OK`.
  - 실행 중 기존 HTTP integration 경로에서 `ResourceWarning: unclosed <socket.socket ...>` 경고가 출력됐지만 실패로 승격되지는 않았다.
- `git diff --check -- tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py work/5/21/`
  - 통과: closeout 작성 전/후 모두 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null tests/local_socket_guard.py`
  - 통과: 출력 없이 `HELPER_NO_INDEX_RC=1`로 종료해, untracked helper 파일의 diff-present 상태에서 공백 오류가 없음을 확인했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-shared-local-socket-test-guard.md`
  - 통과: 출력 없이 `WORK_NO_INDEX_RC=1`로 종료해, untracked work note의 diff-present 상태에서 공백 오류가 없음을 확인했다.
- `rg -n "local_loopback_socket|requires_local_loopback_socket|skip_unless_local_loopback_socket|LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)" tests/local_socket_guard.py tests/test_web_app.py tests/test_http_integration.py`
  - 확인: `tests/test_web_app.py`의 direct server 생성 테스트는 shared decorator 아래에 있고, `tests/test_http_integration.py`는 shared `skip_unless_local_loopback_socket()`를 `setUp`에서 호출한다.

## 남은 리스크

- 현재 실행 환경에서는 loopback socket이 가능해 guarded tests가 실제 assertions까지 실행됐다. no-socket 환경에서는 shared reason `local loopback socket unavailable in this environment`로 skip되는 경로는 코드상 적용됐지만, 이번 라운드에서 별도 sandbox 모드 전환으로 강제 재현하지는 않았다.
- `tests.test_http_integration` 실행 중 `ResourceWarning` unclosed socket 경고가 출력됐다. 이번 slice의 범위는 no-socket guard consolidation이라 해당 경고를 별도 수정하지 않았다.
- Playwright, full controller smoke, broad e2e, runtime start/stop, `status --json`, `doctor --json`, `tmux`, release/publication 검증은 handoff 범위 밖이라 실행하지 않았다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
