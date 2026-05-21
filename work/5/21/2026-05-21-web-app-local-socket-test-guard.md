# 2026-05-21 web app local socket test guard

## 변경 파일

- `tests/test_web_app.py`
- `work/5/21/2026-05-21-web-app-local-socket-test-guard.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 검증, 남은 리스크를 `/work` 형식으로 기록하는 데 사용했다.

## 변경 이유

- `.pipeline/implement_handoff.md#2075`는 `tests/test_web_app.py`의 socket-bound HTTP handler 테스트가 no-socket sandbox에서 제품 코드 실패처럼 보이지 않도록 test-only local socket availability guard를 요구했다.
- 직전 aggregate 단위 테스트는 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 생성 경로에서 `PermissionError: [Errno 1] Operation not permitted`로 환경-held 실패를 보였다.
- publication은 계속 `HOLD_PUBLICATION` 상태이며, 이번 라운드는 commit, push, branch/PR publish, merge, release와 무관하다.

## 핵심 변경

- `tests/test_web_app.py`에 `socket` import와 `_local_loopback_socket_available()` helper를 추가했다.
- `_requires_local_loopback_socket` decorator를 추가해 local loopback socket bind가 불가능한 환경에서 명시적 skip reason을 남기게 했다.
- `LocalOnlyHTTPServer(("127.0.0.1", 0), service)`를 직접 생성하는 13개 HTTP handler 테스트에만 decorator를 적용했다.
- 서비스 레벨, serializer, web-search, reviewed-memory 비소켓 테스트와 production `LocalOnlyHTTPServer` 동작은 변경하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `8495eef983bf73d55776c10434d73b338485525a4985bb03bc4055f87ffff94c`와 일치했다.
- `python3 -m py_compile tests/test_web_app.py`
  - 통과: 출력 없이 종료했다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_http_payload_exposes_transition_mutation_identity_requirement tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_conflict_check_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_reverse_to_service tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_returns_ok tests.test_web_app.WebAppServiceTest.test_handler_dispatches_aggregate_transition_stop_to_service tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_empty_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_json_syntax_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_malformed_utf8_request_body tests.test_web_app.WebAppServiceTest.test_handler_returns_400_for_non_object_json_request_body tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_actions_reject_mismatched_aggregate_fingerprint tests.test_web_app.WebAppServiceTest.test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`
  - 통과: `Ran 13 tests in 0.787s`, `OK`.
- `timeout 900 bash -lc 'python3 -m unittest -v tests.test_pipeline_runtime_state_contract tests.test_controller_queue_presentation tests.test_controller_server tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_smoke tests.test_web_app > /tmp/projecth-unit-2075.log 2>&1'`
  - 통과: `Ran 1086 tests in 89.964s`, `OK (skipped=13)`, `UNIT_RC=0`.
  - aggregate 로그에서 guarded tests 13개가 `local loopback socket unavailable in this environment` reason으로 skip됨을 확인했다.
- `git diff --check -- tests/test_web_app.py work/5/21/`
  - 통과: closeout 작성 전/후 모두 출력 없이 종료했다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-web-app-local-socket-test-guard.md`
  - 통과: 출력 없이 `WORK_NO_INDEX_RC=1`로 종료해, untracked 파일의 diff-present 상태에서 공백 오류가 없음을 확인했다.
- `rg -n "_requires_local_loopback_socket|LocalOnlyHTTPServer\\(\\(\\\"127\\.0\\.0\\.1\\\", 0\\)" tests/test_web_app.py`
  - 확인: direct `LocalOnlyHTTPServer` 생성 지점 13개와 대응 decorator 13개를 확인했다.

## 남은 리스크

- aggregate 실행 환경에서는 local loopback socket guard가 활성화되어 13개 HTTP handler 테스트가 skip되었다. socket-capable 환경에서는 해당 테스트가 실제 HTTP handler assertion까지 실행된다.
- Playwright, full controller smoke, broad e2e, runtime start/stop, `status --json`, `doctor --json`, `tmux`, release/publication 검증은 handoff 범위 밖이라 실행하지 않았다.
- `tests/test_web_app.py`는 이전 라운드의 dirty hunk를 포함하고 있었으며, 이번 라운드는 socket guard 관련 변경만 추가했다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았다.
