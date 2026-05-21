# publish-held dirty Python socket-free aggregate

## 변경 파일

- `work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`

## 사용 skill

- `work-log-closeout`

## 변경 이유

- `.pipeline/implement_handoff.md#2074`의 `HOLD_PUBLICATION` 상태에서 현재 dirty Python/source 후보의 socket-free 컴파일/단위 테스트 증거를 갱신해야 했습니다.
- handoff SHA `7f646fa261a28c8a99f4aa0caff0c08bffe682b3d7e156832018f17b9343dcd0` 일치를 확인했습니다.
- publication 승인, release-ready, full-smoke-pass, next-slice 선택은 모두 범위 밖으로 유지했습니다.

## 핵심 변경

- 코드, 테스트, 제품 문서, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 수정하지 않았습니다.
- 지정된 `/work` closeout만 추가해 실제 실행 증거와 환경 blocker를 기록했습니다.
- 최초 비리다이렉트 단위 테스트 세션은 도구 세션에서 반환되지 않아 완료 증거로 사용하지 않았고, 동일 aggregate 명령을 `/tmp/projecth-unit-2074.log`로 리다이렉트한 뒤 `timeout 900`으로 재실행했습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 통과: handoff SHA가 `7f646fa261a28c8a99f4aa0caff0c08bffe682b3d7e156832018f17b9343dcd0`와 일치했습니다.
- `python3 -m py_compile app/handlers/reviewed_memory.py app/serializers.py controller/server.py pipeline_runtime/automation_health.py pipeline_runtime/cli.py pipeline_runtime/operator_autonomy.py pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py tests/test_controller_queue_presentation.py tests/test_controller_server.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_control_writers.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py tests/test_smoke.py tests/test_watcher_core.py tests/test_web_app.py verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py`
  - 통과: 출력 없이 종료했습니다.
- `timeout 900 bash -lc 'python3 -m unittest -v tests.test_pipeline_runtime_state_contract tests.test_controller_queue_presentation tests.test_controller_server tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_control_writers tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_smoke tests.test_web_app > /tmp/projecth-unit-2074.log 2>&1'`
  - 실패: `Ran 1086 tests in 86.009s`, `FAILED (errors=13)`.
  - 실패 원인은 `tests.test_web_app`의 HTTP handler/socket-bound 테스트들이 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 생성 중 `PermissionError: [Errno 1] Operation not permitted`로 막힌 것입니다.
  - 오류 테스트 예: `test_handler_returns_400_for_empty_request_body`, `test_handler_returns_400_for_malformed_json_syntax_request_body`, `test_reviewed_memory_transition_http_apply_result_reject_mismatched_aggregate_fingerprint`, `test_session_http_payload_exposes_transition_mutation_identity_requirement`.
  - 코드 동작 실패로 단정하지 않고 handoff STOP_RULES의 환경 blocker로 기록합니다.
- 참고 좁힘: 마지막으로 출력에 보였던 `test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled`의 16개 문구는 별도 45초 제한 로컬 재현에서 모두 `actions_taken == ["web_search"]`로 통과했습니다.
- `git diff --check -- app/handlers/reviewed_memory.py app/serializers.py controller/server.py pipeline_runtime/automation_health.py pipeline_runtime/cli.py pipeline_runtime/operator_autonomy.py pipeline_runtime/state_contract.py pipeline_runtime/supervisor.py tests/test_controller_queue_presentation.py tests/test_controller_server.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_control_writers.py tests/test_pipeline_runtime_state_contract.py tests/test_pipeline_runtime_supervisor.py tests/test_smoke.py tests/test_watcher_core.py tests/test_web_app.py verify_fsm.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py work/5/21/ verify/5/21/`
  - 통과: closeout 작성 전/후 모두 출력 없이 종료했습니다.
- `git diff --check --no-index -- /dev/null work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md`
  - 통과: 출력 없이 `NO_INDEX_RC=1`로 종료해, untracked 파일의 diff-present 상태에서 공백 오류가 없음을 확인했습니다.
- `git status --short -- work/5/21/2026-05-21-publish-held-dirty-python-socket-free-aggregate.md .pipeline/advisory_request.md .pipeline/operator_request.md .pipeline/implement_handoff.md`
  - 확인: 새 work note만 `??`로 표시됐고 `.pipeline/implement_handoff.md`, `.pipeline/operator_request.md`는 변경 표시가 없었습니다. `.pipeline/advisory_request.md`는 부재(`ADVISORY_ABSENT_RC=0`)를 확인했습니다.

## 남은 리스크

- socket-bound HTTP 단위 테스트 13개가 현재 로컬 sandbox의 소켓 생성 권한 거부로 환경-held 상태입니다.
- Playwright, controller smoke, broad e2e, runtime start/stop, `status --json`, `doctor --json`, `tmux`, release/publication 검증은 handoff 범위 밖이라 실행하지 않았습니다.
- publication은 계속 held 상태이며 commit, push, branch/PR publish, merge는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, 다음 handoff/control은 작성하지 않았습니다.
