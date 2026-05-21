# 2026-05-20 runtime launch socket guard surface

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`

## 사용 skill

- `security-gate`: runtime launch failure, local tmux socket permission, log detail 보존, operator routing을 건드리는 변경이라 안전 경계를 점검하기 위해 사용했습니다.
- `doc-sync`: runtime health/status contract에 새 canonical reason을 추가했으므로 운영 문서와 설계 문서를 구현과 맞추기 위해 사용했습니다.
- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2010`이 local tmux socket permission denial을 generic `runtime_launch_failed:RuntimeError` / `operator_required`로 과분류하지 않도록 runtime helper surface를 보강하라고 지시했습니다.
- 직전 reload sanity에서 새 run의 `logs/launch-error.log`는 `error connecting to /tmp/tmux-1000/default (Operation not permitted)`를 기록했지만, status는 generic runtime launch failure로 표면화했습니다.
- 이번 라운드는 live runtime restart가 아니라, 같은 local environment-held 실패를 canonical `local_socket_guard_auto_held` reason과 local verify follow-up으로 분류하는 code/test/doc 보강입니다.

## 핵심 변경

- `pipeline_runtime.automation_health.LOCAL_SOCKET_GUARD_AUTO_HELD_REASON` 상수를 추가하고 `VERIFY_FOLLOWUP_REASONS`에 포함했습니다.
- `derive_automation_health()`에서 `runtime_state=BROKEN`이더라도 `degraded_reason=local_socket_guard_auto_held`이면 `automation_health=attention`, `automation_next_action=verify_followup`으로 라우팅하도록 분기했습니다.
- `RuntimeSupervisor._runtime_launch_failure_reason()`와 tmux socket permission denial classifier를 추가해 `Operation not permitted`이 포함된 local tmux socket connection failure를 `local_socket_guard_auto_held`로 정규화했습니다.
- raw exception text는 기존처럼 `logs/launch-error.log`에 그대로 남기고, machine-local socket path를 canonical reason code에 넣지 않도록 유지했습니다.
- automation health와 supervisor unit coverage를 추가해 local socket guard는 verify follow-up으로, generic broken runtime은 operator-required로 남는 것을 각각 확인했습니다.
- `.pipeline/README.md`, runtime 기술설계 문서, 운영 runbook에 `local_socket_guard_auto_held` contract와 expected health/action을 동기화했습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `cbd0d924d61d151383ba7332e51a9f689d3270606a0e48340359f830a929c938`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_broken_local_socket_guard_routes_to_verify_followup tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_generic_broken_runtime_still_requires_operator tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_classifies_tmux_socket_permission_denial tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_runtime_launch_failure_reason_keeps_generic_runtime_errors`
  - 결과: PASS. `Ran 4 tests in 0.000s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 결과: PASS. `Ran 43 tests in 0.003s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-runtime-launch-socket-guard-surface.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 live `pipeline_runtime.cli start`, `tmux`, lane-local `status --json`, `doctor --json`을 실행하지 않았습니다. handoff가 재실행을 금지했고, local socket failure classifier의 unit-level 보강이 범위였기 때문입니다.
- controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다. browser-visible contract 변경이 아니라 runtime health helper/status contract 변경입니다.
- 작업 시작 전부터 같은 runtime/test/doc 파일에 이전 라운드의 dirty 변경이 있었습니다. 이번 #2010 라운드의 직접 범위는 `local_socket_guard_auto_held` reason, launch failure classifier, focused unit tests, 관련 runtime docs sync입니다.
- raw launch error는 계속 `logs/launch-error.log`에 남습니다. 이 로그는 local path를 포함할 수 있으므로 user-facing canonical reason에는 노출하지 않는 현재 경계를 유지해야 합니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
