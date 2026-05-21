# 2026-05-20 runtime launch socket guard aggregate unit guard

## 변경 파일

- `work/5/20/2026-05-20-runtime-launch-socket-guard-aggregate-unit-guard.md`

## 사용 skill

- `security-gate`: local tmux socket permission denial, raw launch log, runtime health/event routing 경계를 한 번에 검증하는 라운드라 canonical reason과 local path 노출 경계를 확인하기 위해 사용했습니다.
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2014`는 이전 helper/status/event/run-catch replay를 더 잘게 나누지 말고 local socket guard family를 한 번에 돌리는 aggregate unit guard를 실행하라고 지시했습니다.
- 이번 라운드는 새 source/test 코드를 추가하는 작업이 아니라, 이미 추가된 local socket guard 보호 테스트들이 한 세트로 함께 통과하는지 확인하는 guard 라운드입니다.
- aggregate가 통과했으므로 source/test 변경 없이 closeout만 남겼습니다.

## 핵심 변경

- local socket guard aggregate unit set 7개를 한 번에 실행했습니다.
- `local_socket_guard_auto_held`가 `BROKEN` runtime에서 `verify_followup`으로 라우팅되는 helper 경로를 확인했습니다.
- generic broken runtime이 여전히 `operator_required`로 남는 회귀 방지 경로를 함께 확인했습니다.
- supervisor classifier, status export, automation incident event, `run()` launch catch/raw log 경로를 같은 aggregate에서 확인했습니다.
- source/test 파일은 이번 라운드에서 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `e7a699ce5e08e5d6c1c5ea38c1a5f589411c42af6b8aef6cd22ac17fbfd4e273`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_broken_local_socket_guard_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_generic_broken_runtime_still_requires_operator tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_classifies_tmux_socket_permission_denial tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_keeps_generic_runtime_errors tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_local_socket_guard_launch_failure_as_verify_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_record_status_events_preserves_local_socket_guard_automation_incident tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_run_launch_failure_preserves_local_socket_guard_reason_and_raw_log`
  - 결과: PASS. 7개 테스트 통과.
- `git diff --check -- pipeline_runtime/automation_health.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_automation_health.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-aggregate-unit-guard.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 aggregate guard만 실행했으며 source/test 코드는 변경하지 않았습니다.
- live `python3 -m pipeline_runtime.cli start ...`, `tmux`, lane-local `status --json`, `doctor --json`는 실행하지 않았습니다. handoff가 runtime restart와 lane-local socket 접근을 금지했고, 이번 범위는 deterministic unit aggregate입니다.
- controller Playwright/webServer/full-smoke, release readiness, long soak는 실행하지 않았습니다. browser-visible contract 변경이나 release claim이 아닙니다.
- 작업 시작 전부터 `pipeline_runtime/automation_health.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_automation_health.py`, `tests/test_pipeline_runtime_supervisor.py`에는 이전 라운드의 dirty 변경이 있었습니다. 이번 라운드의 직접 변경은 이 `/work` closeout뿐입니다.
- raw launch error의 local socket path는 계속 `logs/launch-error.log`에 보존됩니다. canonical reason code에는 path를 넣지 않는 경계를 유지해야 합니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
