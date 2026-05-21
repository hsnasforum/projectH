# 2026-05-20 runtime launch socket guard launch catch replay

## 변경 파일

- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-launch-catch-replay.md`

## 사용 skill

- `security-gate`: runtime `run()`의 launch failure catch 경로, raw launch log, local socket path 보존 경계를 다루므로 operator routing과 로그 노출 경계를 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2013`은 direct helper/status/event replay 이후 남은 `run()` launch failure catch 경로를 확인하라고 지시했습니다.
- 기존 테스트는 `_launch_failed_reason`이 이미 설정된 상태에서 status/event 표면을 검증했지만, `_launch_runtime()` 예외가 `run()`에서 잡힌 뒤 canonical reason과 raw log로 보존되는지는 직접 확인하지 않았습니다.
- 이번 라운드는 live runtime restart나 tmux 접근 없이 `_launch_runtime()`만 mock으로 실패시키는 deterministic unit replay입니다.

## 핵심 변경

- `tests/test_pipeline_runtime_supervisor.py`에 `test_run_launch_failure_preserves_local_socket_guard_reason_and_raw_log`를 추가했습니다.
- 테스트는 `RuntimeSupervisor(..., start_runtime=True)`를 temp root에서 만들고 `_launch_runtime()`을 local tmux socket permission denial `RuntimeError`로 mock 처리합니다.
- `_write_status()`를 wrapper로 감싸 첫 `BROKEN` status를 캡처한 뒤 `supervisor._stop_requested=True`로 설정해 run loop를 bounded하게 종료합니다.
- `supervisor._launch_failed_reason`이 `LOCAL_SOCKET_GUARD_AUTO_HELD_REASON`으로 설정되는지 확인합니다.
- `logs/launch-error.log`가 raw exception text와 local socket path를 그대로 보존하는지 확인합니다.
- 캡처한 첫 status가 `runtime_state=BROKEN`, `degraded_reason=local_socket_guard_auto_held`, `automation_next_action=verify_followup`을 내는지 확인합니다.
- source 동작 변경은 없었습니다. 이번 handoff에서 필요한 보강은 테스트 추가로 충족되었습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `5490141c23e551b549b1990d90d625e53fdeb523322bc5d6f6e347c1b3eb46c1`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_run_launch_failure_preserves_local_socket_guard_reason_and_raw_log tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_classifies_tmux_socket_permission_denial tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_record_status_events_preserves_local_socket_guard_automation_incident`
  - 결과: PASS. 4개 테스트 통과.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-launch-catch-replay.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- `pipeline_runtime/supervisor.py`는 변경하지 않았으므로 handoff의 조건부 generic classifier regression 재실행은 필요하지 않았습니다.
- live `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다. handoff가 runtime restart와 lane-local socket 접근을 금지했고, 이번 범위는 deterministic unit replay입니다.
- controller Playwright/webServer/full-smoke, release readiness, long soak는 실행하지 않았습니다. browser-visible contract 변경이나 release claim이 아닙니다.
- 작업 시작 전부터 `tests/test_pipeline_runtime_supervisor.py`에는 이전 라운드의 dirty 변경이 있었습니다. 이번 라운드에서 직접 추가한 것은 `run()` launch failure catch replay 테스트입니다.
- raw launch error의 local socket path는 계속 `logs/launch-error.log`에 보존됩니다. canonical reason code에는 path를 넣지 않는 경계를 유지해야 합니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
