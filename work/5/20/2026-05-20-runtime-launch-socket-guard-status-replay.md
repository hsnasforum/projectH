# 2026-05-20 runtime launch socket guard status replay

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-status-replay.md`

## 사용 skill

- `security-gate`: local tmux socket permission denial과 runtime status/export 경계를 다루는 테스트이므로 operator routing, log/path 노출, approval 경계가 바뀌지 않는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2011`은 직전 `local_socket_guard_auto_held` classifier/helper 검증 뒤 남은 gap을 닫으라고 지시했습니다.
- 기존 테스트는 launch failure classifier와 `derive_automation_health()` helper를 직접 보호했지만, `_launch_failed_reason=local_socket_guard_auto_held`가 `RuntimeSupervisor._write_status()`의 exported status JSON 및 `automation_health_source`까지 같은 reason/action으로 표면화되는지 확인하는 supervisor replay는 없었습니다.
- 이번 라운드는 live runtime restart나 tmux 접근 없이 file-backed status export 경로만 재현하는 한정 테스트입니다.

## 핵심 변경

- `tests/test_pipeline_runtime_supervisor.py`에 `test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup`를 추가했습니다.
- 테스트는 `RuntimeSupervisor(..., start_runtime=False)`를 사용하고, `_launch_failed_reason`을 `LOCAL_SOCKET_GUARD_AUTO_HELD_REASON`으로 설정한 뒤 `_write_status()`를 호출합니다.
- live tmux/socket 접근 없이 watcher, session, lane status, artifacts를 mock 처리했습니다.
- exported status가 `runtime_state=BROKEN`, `degraded_reason=local_socket_guard_auto_held`, `automation_health=attention`, `automation_next_action=verify_followup`을 내는지 확인합니다.
- `automation_health_source`의 `ruleset_version`, `derived_by`, `runtime_state`, `reason_code`, `next_action`도 함께 검증합니다.
- source 동작 변경은 없었습니다. 이번 handoff에서 필요한 보강은 테스트 추가로 충족되었습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `8559a7517307558027090590b176ed6042cb057d6e9ac2305f25c3f628b122ac`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_broken_local_socket_guard_routes_to_verify_followup`
  - 결과: PASS. 2개 테스트 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_classifies_tmux_socket_permission_denial tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_keeps_generic_runtime_errors`
  - 결과: PASS. 2개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-status-replay.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- live `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다. handoff가 runtime restart와 lane-local socket 접근을 금지했고, 이번 범위는 deterministic unit replay입니다.
- controller Playwright/webServer/full-smoke, release readiness, long soak는 실행하지 않았습니다. browser-visible contract 변경이나 release claim이 아닙니다.
- 작업 시작 전부터 `tests/test_pipeline_runtime_supervisor.py`에는 이전 라운드의 dirty 변경이 있었습니다. 이번 라운드에서 직접 추가한 것은 `_write_status()` local socket guard status replay 테스트입니다.
- raw launch error의 local socket path는 계속 canonical reason code가 아니라 launch error log에만 보존되어야 합니다. 이번 테스트는 이 경계를 바꾸지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
